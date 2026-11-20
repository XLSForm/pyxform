"""pyxform utils module."""

import copy
import csv
import io
import json
import sys
from collections.abc import Generator, Iterable
from functools import lru_cache
from io import StringIO
from itertools import chain
from json.decoder import JSONDecodeError
from typing import TYPE_CHECKING
from xml.dom import Node

from pyxform import constants as const
from pyxform.parsing.expression import lex_expression
from pyxform.xls2json_backends import DefinitionData

if TYPE_CHECKING:
    from xml.dom.minidom import Attr


LAST_SAVED_INSTANCE_NAME = "__last-saved"
SPACE_TRANS_TABLE = str.maketrans({" ": "_"})
XML_TEXT_SUBS = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
XML_TEXT_TABLE = str.maketrans(XML_TEXT_SUBS)


class DetachableElement:
    """
    Similar to the xml.dom.minidom.Node API, but for writing Element/Attr/Text XML only.

    The DOM tracking/editing/other features offered by minidom are not used by pyxform,
    so this class offers a minimal API for building and writing a XML tree structure.
    """

    __slots__ = ("_attrs", "childNodes", "tagName")
    nodeType = Node.ELEMENT_NODE

    def __init__(self, tagName: str):
        self._attrs: dict | None = None
        self.childNodes: list[DetachableElement | Text] | None = None
        self.tagName: str = tagName

    @property
    def attributes(self):
        return self._attrs

    def writexml(self, writer, indent="", addindent="", newl=""):
        # indent = current indentation
        # addindent = indentation to add to higher levels
        # newl = newline string
        writer.write(f"{indent}<{self.tagName}")

        if self._attrs:
            for k, v in self._attrs.items():
                # First space prefix separates attr from tagName, then it separates attrs.
                writer.write(f' {k}="{escape_text_for_xml(v, attribute=True)}"')
        if self.childNodes:
            writer.write(">")
            # For text or mixed content, write without adding indents or newlines.
            if any(c.nodeType == Node.TEXT_NODE for c in self.childNodes):
                for cnode in self.childNodes:
                    cnode.writexml(writer, "", "", "")
            else:
                writer.write(newl)
                for cnode in self.childNodes:
                    cnode.writexml(writer, f"{indent}{addindent}", addindent, newl)
                writer.write(indent)
            writer.write(f"</{self.tagName}>{newl}")
        else:
            writer.write(f"/>{newl}")

    def toxml(self):
        return self.toprettyxml("", "")

    def toprettyxml(self, indent="\t", newl="\n"):
        writer = io.StringIO()
        self.writexml(writer, "", indent, newl)
        return writer.getvalue()

    def setAttribute(self, attname, value):
        if self._attrs is None:
            self._attrs = {}
        self._attrs[attname] = value

    def setAttributeNode(self, attr: "Attr"):
        self.setAttribute(attr._name, attr._value)

    def setAttributeBatch(self, attrs):
        if self._attrs is None:
            self._attrs = attrs
        else:
            self._attrs.update(attrs)

    def appendChild(self, node: "DetachableElement | Text"):
        if self.childNodes is None:
            self.childNodes = []
        self.childNodes.append(node)
        return node


@lru_cache(maxsize=64)
def escape_text_for_xml(text: str, attribute: bool = False) -> str:
    chars = set(text)
    if any(c in chars for c in XML_TEXT_SUBS):
        text = text.translate(XML_TEXT_TABLE)
    if attribute and '"' in chars:
        text = text.replace('"', "&quot;")
    return text


class Text:
    __slots__ = ("data",)
    nodeType = Node.TEXT_NODE

    def __init__(self, data: str = "") -> None:
        # Shortcut for base class pattern: `t = Text(); t.data = data`.
        self.data = data

    def writexml(self, writer, indent="", addindent="", newl=""):
        """Same as original but no replacing double quotes with '&quot;'."""
        if self.data:
            writer.write(f"{indent}{escape_text_for_xml(text=self.data)}{newl}")


def node(tag: str, *args, **kwargs) -> DetachableElement:
    """
    Create an Element, with attached child elements (args) and attributes (kwargs).

    :param tag: The Element XML tag name.
    """
    result = DetachableElement(tag)

    # Convert the kwargs xml attribute dictionary to a xml.dom.minidom.Element.
    if kwargs:
        result.setAttributeBatch(kwargs)

    if args:
        for n in args:
            if isinstance(n, str | int | float | bytes):
                result.appendChild(Text(data=str(n)))
            elif isinstance(n, list | Generator):
                for e in n:
                    if isinstance(e, DetachableElement | Text):
                        result.appendChild(e)
            elif isinstance(n, DetachableElement | Text):
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
    Dump a python nested array/dict structure to the specified file
    or stdout if no file is specified.
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
    """Returns true if a select one external prompt is used in the survey."""
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

    tokens = lex_expression(element_default)
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
