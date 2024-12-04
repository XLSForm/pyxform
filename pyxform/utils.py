"""
pyxform utils module.
"""

import copy
import csv
import json
import re
from collections.abc import Generator, Iterable
from io import StringIO
from itertools import chain
from json.decoder import JSONDecodeError
from typing import Any
from xml.dom import Node
from xml.dom.minidom import Element, Text, _write_data

from defusedxml.minidom import parseString

from pyxform import constants as const
from pyxform.errors import PyXFormError
from pyxform.parsing.expression import parse_expression

SEP = "_"
INVALID_XFORM_TAG_REGEXP = re.compile(r"[^a-zA-Z:_][^a-zA-Z:_0-9\-.]*")
LAST_SAVED_INSTANCE_NAME = "__last-saved"
BRACKETED_TAG_REGEX = re.compile(r"\${(last-saved#)?(.*?)}")
LAST_SAVED_REGEX = re.compile(r"\${last-saved#(.*?)}")
PYXFORM_REFERENCE_REGEX = re.compile(r"\$\{(.*?)\}")
NODE_TYPE_TEXT = (Node.TEXT_NODE, Node.CDATA_SECTION_NODE)


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
        Element.__init__(self, *args, **kwargs)
        self.ownerDocument = None

    def writexml(self, writer, indent="", addindent="", newl=""):
        # indent = current indentation
        # addindent = indentation to add to higher levels
        # newl = newline string
        writer.write(indent + "<" + self.tagName)

        attrs = self._get_attributes()

        for a_name in attrs.keys():
            writer.write(f' {a_name}="')
            _write_data(writer, attrs[a_name].value)
            writer.write('"')
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
                    cnode.writexml(writer, indent + addindent, addindent, newl)
                writer.write(indent)
            writer.write(f"</{self.tagName}>{newl}")
        else:
            writer.write(f"/>{newl}")


class PatchedText(Text):
    def writexml(self, writer, indent="", addindent="", newl=""):
        """Same as original but no replacing double quotes with '&quot;'."""
        data = "".join((indent, self.data, newl))
        if data:
            data = data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        writer.write(data)


def node(*args, **kwargs) -> DetachableElement:
    """
    args[0] -- a XML tag
    args[1:] -- an array of children to append to the newly created node
            or if a unicode arg is supplied it will be used to make a text node
    kwargs -- attributes
    returns a xml.dom.minidom.Element
    """
    blocked_attributes = {"tag"}
    tag = args[0] if len(args) > 0 else kwargs["tag"]
    args = args[1:]
    result = DetachableElement(tag)
    unicode_args = tuple(u for u in args if isinstance(u, str))
    if len(unicode_args) > 1:
        raise PyXFormError("""Invalid value for `unicode_args`.""")
    parsed_string = False

    # Convert the kwargs xml attribute dictionary to a xml.dom.minidom.Element.
    for k, v in kwargs.items():
        if k in blocked_attributes:
            continue
        if k == "toParseString":
            if v is True and len(unicode_args) == 1:
                parsed_string = True
                # Add this header string so parseString can be used?
                s = f"""<?xml version="1.0" ?><{tag}>{unicode_args[0]}</{tag}>"""
                parsed_node = parseString(s.encode("utf-8")).documentElement
                # Move node's children to the result Element
                # discarding node's root
                for child in parsed_node.childNodes:
                    result.appendChild(child.cloneNode(deep=False))
        else:
            result.setAttribute(k, v)

    if len(unicode_args) == 1 and not parsed_string:
        text_node = PatchedText()
        text_node.data = unicode_args[0]
        result.appendChild(text_node)
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


def flatten(li):
    for subli in li:
        yield from subli


def external_choices_to_csv(
    workbook_dict: dict[str, Any], warnings: list | None = None
) -> str | None:
    """
    Convert the 'external_choices' sheet data to CSV.

    :param workbook_dict: The result from xls2json.workbook_to_json.
    :param warnings: The conversions warnings list.
    """
    warnings = coalesce(warnings, [])
    if const.EXTERNAL_CHOICES not in workbook_dict:
        warnings.append(
            f"Could not export itemsets.csv, the '{const.EXTERNAL_CHOICES}' sheet is missing."
        )
        return None

    itemsets = StringIO(newline="")
    csv_writer = csv.writer(itemsets, quoting=csv.QUOTE_ALL)
    try:
        header = workbook_dict["external_choices_header"][0]
    except (IndexError, KeyError, TypeError):
        header = {k for d in workbook_dict[const.EXTERNAL_CHOICES] for k in d}
    csv_writer.writerow(header)
    for row in workbook_dict[const.EXTERNAL_CHOICES]:
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
    if not isinstance(element_default, str):
        return False

    tokens, _ = parse_expression(element_default)
    for t in tokens:
        # Data types which are likely to have non-dynamic defaults containing a hyphen.
        if element_type in ("date", "dateTime", "geopoint", "geotrace", "geoshape"):
            # Nested to avoid extra string comparisons if not a relevant data type.
            if t.name == "OPS_MATH" and t.value == "-":
                return False

        # A match on these lexer rules indicates a dynamic default.
        if t.name in {
            "OPS_MATH",
            "OPS_UNION",
            "XPATH_PRED",
            "PYXFORM_REF",
            "FUNC_CALL",
        }:
            return True

    # Otherwise assume not dynamic.
    return False


def has_dynamic_label(choice_list: "list[dict[str, str]]") -> bool:
    """
    If the first or second choice label includes a reference, we must use itext.

    Check the first two choices in case first is something like "Other".
    """
    for c in choice_list[:2]:
        choice_label = c.get("label")
        if (
            choice_label is not None
            and isinstance(choice_label, str)
            and re.search(BRACKETED_TAG_REGEX, choice_label) is not None
        ):
            return True
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
