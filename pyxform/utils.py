"""
pyxform utils module.
"""

import copy
import csv
import json
import re
import sys
from collections.abc import Generator, Iterable
from functools import lru_cache
from io import StringIO
from itertools import chain
from json.decoder import JSONDecodeError
from xml.dom import Node
from xml.dom.minidom import Element, Text

from defusedxml.minidom import parseString

from pyxform import constants as const
from pyxform.errors import PyXFormError
from pyxform.parsing.expression import parse_expression
from pyxform.xls2json_backends import DefinitionData

INVALID_XFORM_TAG_REGEXP = re.compile(r"[^a-zA-Z:_][^a-zA-Z:_0-9\-.]*")
LAST_SAVED_INSTANCE_NAME = "__last-saved"
NODE_TYPE_TEXT = {Node.TEXT_NODE, Node.CDATA_SECTION_NODE}
SPACE_TRANS_TABLE = str.maketrans({" ": "_"})
XML_TEXT_SUBS = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
XML_TEXT_TABLE = str.maketrans(XML_TEXT_SUBS)


class DetachableElement(Element):
    """
    Element classes are not meant to be instantiated directly.   This
    restriction was not strictly enforced in Python 2, but is effectively
    enforced in Python 3 via http://bugs.python.org/issue15290.

    A simple workaround (for now) is to set an extra attribute on the Element
    class.  The long term fix will probably be to rewrite node() to use
    document.createElement rather than Element.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ownerDocument = None

    def writexml(self, writer, indent="", addindent="", newl=""):
        # indent = current indentation
        # addindent = indentation to add to higher levels
        # newl = newline string
        writer.write(f"{indent}<{self.tagName}")

        if self._attrs:
            for k, v in self._attrs.items():
                # First space prefix separates attr from tagName, then it separates attrs.
                writer.write(f' {k}="{escape_text_for_xml(v.value, attribute=True)}"')
        if self.childNodes:
            writer.write(">")
            # For text or mixed content, write without adding indents or newlines.
            if any(c.nodeType in NODE_TYPE_TEXT for c in self.childNodes):
                # Conditions to match old Survey.py regex for remaining whitespace.
                child_nodes = len(self.childNodes)
                for idx, cnode in enumerate(self.childNodes):
                    if 1 < child_nodes and idx == 0 and cnode.nodeType in NODE_TYPE_TEXT:
                        writer.write(" ")
                    cnode.writexml(writer, "", "", "")
                    if 1 < child_nodes and (idx + 1) == child_nodes:
                        writer.write(" ")
            else:
                writer.write(newl)
                for cnode in self.childNodes:
                    cnode.writexml(writer, f"{indent}{addindent}", addindent, newl)
                writer.write(indent)
            writer.write(f"</{self.tagName}>{newl}")
        else:
            writer.write(f"/>{newl}")


@lru_cache(maxsize=64)
def escape_text_for_xml(text: str, attribute: bool = False) -> str:
    chars = set(text)
    if any(c in chars for c in XML_TEXT_SUBS):
        text = text.translate(XML_TEXT_TABLE)
    if attribute and '"' in chars:
        text = text.replace('"', "&quot;")
    return text


class PatchedText(Text):
    def writexml(self, writer, indent="", addindent="", newl=""):
        """Same as original but no replacing double quotes with '&quot;'."""
        data = f"{indent}{self.data}{newl}"
        if data:
            data = escape_text_for_xml(text=data)
        writer.write(data)


def node(tag: str, *args, toParseString: bool = False, **kwargs) -> DetachableElement:
    """
    Create an Element, with attached child elements (args) and attributes (kwargs).

    :param tag: The Element XML tag name.
    :param toParseString: If True, parse the first text arg as XML and add it to the tag.
    """
    result = DetachableElement(tag)
    unicode_args = tuple(u for u in args if isinstance(u, str))
    if len(unicode_args) > 1:
        raise PyXFormError("""Invalid value for `unicode_args`.""")
    elif len(unicode_args) == 1:
        if toParseString:
            # Add this header string so parseString can be used?
            s = f"""<?xml version="1.0" ?><{tag}>{unicode_args[0]}</{tag}>"""
            parsed_node = parseString(s.encode("utf-8")).documentElement
            # Move node's children to the result Element
            # discarding node's root
            for child in parsed_node.childNodes:
                result.appendChild(child.cloneNode(deep=False))
        else:
            text_node = PatchedText()
            text_node.data = unicode_args[0]
            result.appendChild(text_node)

    # Convert the kwargs xml attribute dictionary to a xml.dom.minidom.Element.
    for k, v in kwargs.items():
        result.setAttribute(k, v)

    for n in args:
        if isinstance(n, int | float | bytes):
            text_node = PatchedText()
            text_node.data = str(n)
            result.appendChild(text_node)
        elif isinstance(n, Generator):
            for e in n:
                if e is not None:
                    result.appendChild(e)
        elif not isinstance(n, str):
            result.appendChild(n)
    return result


def get_pyobj_from_json(str_or_path):
    """
    This function takes either a json string or a path to a json file,
    it loads the json into memory and returns the corresponding Python
    object.
    """
    try:
        # see if treating str_or_path as a path works
        with open(str_or_path, encoding="utf-8") as fp:
            doc = json.load(fp)
    except (JSONDecodeError, OSError):
        # if it doesn't work load the text
        doc = json.loads(str_or_path)
    return doc


def print_pyobj_to_json(pyobj, path=None):
    """
    dump a python nested array/dict structure to the specified file
    or stdout if no file is specified
    """
    if path:
        with open(path, mode="w", encoding="utf-8") as fp:
            json.dump(pyobj, fp=fp, ensure_ascii=False, indent=4)
    else:
        sys.stdout.write(json.dumps(pyobj, ensure_ascii=False, indent=4))


def flatten(li):
    for subli in li:
        yield from subli


def external_choices_to_csv(
    workbook_dict: DefinitionData, warnings: list | None = None
) -> str | None:
    """
    Convert the 'external_choices' sheet data to CSV.

    :param workbook_dict: The result from xls2json.workbook_to_json.
    :param warnings: The conversions warnings list.
    """
    warnings = coalesce(warnings, [])
    if not workbook_dict.external_choices:
        warnings.append(
            f"Could not export itemsets.csv, the '{const.EXTERNAL_CHOICES}' sheet is missing."
        )
        return None

    itemsets = StringIO(newline="")
    csv_writer = csv.writer(itemsets, quoting=csv.QUOTE_ALL)
    try:
        header = workbook_dict.external_choices_header[0]
    except (IndexError, KeyError, TypeError):
        header = {k for d in workbook_dict.external_choices for k in d}
    csv_writer.writerow(header)
    for row in workbook_dict.external_choices:
        csv_writer.writerow(row.values())
    return itemsets.getvalue()


def has_external_choices(json_struct):
    """
    Returns true if a select one external prompt is used in the survey.
    """
    if isinstance(json_struct, dict):
        for k, v in json_struct.items():
            if (
                k == const.TYPE
                and isinstance(v, str)
                and v.startswith(const.SELECT_ONE_EXTERNAL)
            ):
                return True
            elif has_external_choices(v):
                return True
    elif isinstance(json_struct, list):
        for v in json_struct:
            if has_external_choices(v):
                return True
    return False


def default_is_dynamic(element_default, element_type=None):
    """
    Returns true if the default value is a dynamic value.

    Dynamic value for now is defined as:
    * Contains arithmetic operator, including 'div' and 'mod' (except '-' for 'date' type).
    * Contains brackets, parentheses or braces.
    """
    if not element_default or not isinstance(element_default, str):
        return False

    tokens = parse_expression(element_default)
    for t in tokens:
        # Data types which are likely to have non-dynamic defaults containing a hyphen.
        if element_type in {"date", "dateTime", "geopoint", "geotrace", "geoshape"}:
            # Nested to avoid extra string comparisons if not a relevant data type.
            if t.type == "OPS_MATH" and t.value == "-":
                return False

        # A match on these lexer rules indicates a dynamic default.
        if t.type in {
            "OPS_MATH",
            "OPS_UNION",
            "XPATH_PRED",
            "PYXFORM_REF",
            "FUNC_CALL",
        }:
            return True

    # Otherwise assume not dynamic.
    return False


def levenshtein_distance(a: str, b: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    A Python translation of the "iterative with two matrix rows" algorithm from
    Wikipedia: https://en.wikipedia.org/wiki/Levenshtein_distance

    :param a: The first string to compare.
    :param b: The second string to compare.
    :return:
    """
    m = len(a)
    n = len(b)

    # create two work vectors of integer distances
    v1 = [0 for _ in range(n + 1)]

    # initialize v0 (the previous row of distances)
    # this row is A[0][i]: edit distance for an empty s
    # the distance is just the number of characters to delete from t
    v0 = list(range(n + 1))

    for i in range(m):
        # calculate v1 (current row distances) from the previous row v0

        # first element of v1 is A[i+1][0]
        #   edit distance is delete (i+1) chars from s to match empty t
        v1[0] = i + 1

        # use formula to fill in the rest of the row
        for j in range(n):
            # calculating costs for A[i+1][j+1]
            deletion_cost = v0[j + 1] + 1
            insertion_cost = v1[j] + 1
            if a[i] == b[j]:
                substitution_cost = v0[j]
            else:
                substitution_cost = v0[j] + 1

            v1[j + 1] = min((deletion_cost, insertion_cost, substitution_cost))

        # copy v1 (current row) to v0 (previous row) for next iteration
        # since data in v1 is always invalidated, a swap without copy could be more efficient
        v0 = copy.copy(v1)
    # after the last swap, the results of v1 are now in v0
    return v0[n]


def coalesce(*args):
    return next((a for a in args if a is not None), None)


def combine_lists(
    a: Iterable | None = None,
    b: Iterable | None = None,
) -> Iterable | None:
    """Get the list that is not None, or both lists combined, or an empty list."""
    if b is None:
        if a is None:
            return None
        else:
            return a
    elif a is None:
        return b
    else:
        return chain(a, b)
