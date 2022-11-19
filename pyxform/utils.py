# -*- coding: utf-8 -*-
"""
pyxform utils module.
"""
import codecs
import copy
import csv
import json
import os
import re
from collections import namedtuple
from json.decoder import JSONDecodeError
from typing import List, Tuple
from xml.dom.minidom import Element, Text, parseString

import openpyxl
import xlrd

from pyxform.xls2json_backends import is_empty, xls_value_to_unicode, xlsx_value_to_str

SEP = "_"

INVALID_XFORM_TAG_REGEXP = r"[^a-zA-Z:_][^a-zA-Z:_0-9\-.]*"

LAST_SAVED_INSTANCE_NAME = "__last-saved"
BRACKETED_TAG_REGEX = re.compile(r"\${(last-saved#)?(.*?)}")
LAST_SAVED_REGEX = re.compile(r"\${last-saved#(.*?)}")

NSMAP = {
    "xmlns": "http://www.w3.org/2002/xforms",
    "xmlns:h": "http://www.w3.org/1999/xhtml",
    "xmlns:ev": "http://www.w3.org/2001/xml-events",
    "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
    "xmlns:jr": "http://openrosa.org/javarosa",
    "xmlns:orx": "http://openrosa.org/xforms",
    "xmlns:odk": "http://www.opendatakit.org/xforms",
}


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


class PatchedText(Text):
    def writexml(self, writer, indent="", addindent="", newl=""):
        """Same as original but no replacing double quotes with '&quot;'."""
        data = "%s%s%s" % (indent, self.data, newl)
        if data:
            data = data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        writer.write(data)


def node(*args, **kwargs):
    """
    args[0] -- a XML tag
    args[1:] -- an array of children to append to the newly created node
            or if a unicode arg is supplied it will be used to make a text node
    kwargs -- attributes
    returns a xml.dom.minidom.Element
    """
    blocked_attributes = ["tag"]
    tag = args[0] if len(args) > 0 else kwargs["tag"]
    args = args[1:]
    result = DetachableElement(tag)
    unicode_args = [u for u in args if type(u) == str]
    assert len(unicode_args) <= 1
    parsed_string = False

    # Convert the kwargs xml attribute dictionary to a xml.dom.minidom.Element. Sort the
    # attributes to guarantee a consistent order across Python versions.
    # See pyxform_test_case.reorder_attributes for details.
    for k, v in iter(sorted(kwargs.items())):
        if k in blocked_attributes:
            continue
        if k == "toParseString":
            if v is True and len(unicode_args) == 1:
                parsed_string = True
                # Add this header string so parseString can be used?
                s = (
                    '<?xml version="1.0" ?><'
                    + tag
                    + ">"
                    + unicode_args[0]
                    + "</"
                    + tag
                    + ">"
                )
                parsed_node = parseString(s.encode("utf-8")).documentElement
                # Move node's children to the result Element
                # discarding node's root
                for child in parsed_node.childNodes:
                    # No tests seem to involve moving elements with children.
                    # Deep clone used anyway in case of unknown edge cases.
                    result.appendChild(child.cloneNode(deep=True))
        else:
            result.setAttribute(k, v)

    if len(unicode_args) == 1 and not parsed_string:
        text_node = PatchedText()
        text_node.data = unicode_args[0]
        result.appendChild(text_node)
    for n in args:
        if type(n) == int or type(n) == float or type(n) == bytes:
            text_node = PatchedText()
            text_node.data = str(n)
            result.appendChild(text_node)
        elif type(n) is not str:
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
        fp = codecs.open(str_or_path, mode="r", encoding="utf-8")
        doc = json.load(fp)
    except (IOError, JSONDecodeError, OSError):
        # if it doesn't work load the text
        doc = json.loads(str_or_path)
    return doc


def flatten(li):
    for subli in li:
        for it in subli:
            yield it


def sheet_to_csv(workbook_path, csv_path, sheet_name):
    if workbook_path.endswith(".xls"):
        return xls_sheet_to_csv(workbook_path, csv_path, sheet_name)
    else:
        return xlsx_sheet_to_csv(workbook_path, csv_path, sheet_name)


def xls_sheet_to_csv(workbook_path, csv_path, sheet_name):
    wb = xlrd.open_workbook(workbook_path)
    try:
        sheet = wb.sheet_by_name(sheet_name)
    except xlrd.biffh.XLRDError:
        return False
    if not sheet or sheet.nrows < 2:
        return False
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        mask = [v and len(v.strip()) > 0 for v in sheet.row_values(0)]
        for row_idx in range(sheet.nrows):
            csv_data = []
            try:
                for v, m in zip(sheet.row(row_idx), mask):
                    if m:
                        value = v.value
                        value_type = v.ctype
                        data = xls_value_to_unicode(value, value_type, wb.datemode)
                        # clean the values of leading and trailing whitespaces
                        data = data.strip()
                        csv_data.append(data)
            except TypeError:
                continue
            writer.writerow(csv_data)

    return True


def xlsx_sheet_to_csv(workbook_path, csv_path, sheet_name):
    wb = openpyxl.open(workbook_path, read_only=True, data_only=True)
    try:
        sheet = wb.get_sheet_by_name(sheet_name)
    except KeyError:
        return False

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        mask = [not is_empty(cell.value) for cell in sheet[1]]
        for row in sheet.rows:
            csv_data = []
            try:
                for v, m in zip(row, mask):
                    if m:
                        data = xlsx_value_to_str(v.value)
                        # clean the values of leading and trailing whitespaces
                        data = data.strip()
                        csv_data.append(data)
            except TypeError:
                continue
            writer.writerow(csv_data)
    wb.close()
    return True


def has_external_choices(json_struct):
    """
    Returns true if a select one external prompt is used in the survey.
    """
    if isinstance(json_struct, dict):
        for k, v in json_struct.items():
            if k == "type" and isinstance(v, str) and v.startswith("select one external"):
                return True
            elif has_external_choices(v):
                return True
    elif isinstance(json_struct, list):
        for v in json_struct:
            if has_external_choices(v):
                return True
    return False


def get_languages_with_bad_tags(languages):
    """
    Returns languages with invalid or missing IANA subtags.
    """
    with open(os.path.join(os.path.dirname(__file__), "iana_subtags.txt")) as f:
        iana_subtags = f.read().splitlines()

    lang_code_regex = re.compile(r"\((.*)\)$")

    languages_with_bad_tags = []
    for lang in languages:
        lang_code = re.search(lang_code_regex, lang)

        if lang != "default" and (
            not (lang_code) or not (lang_code.group(1) in iana_subtags)
        ):
            languages_with_bad_tags.append(lang)
    return languages_with_bad_tags


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


# If the first or second choice label includes a reference, we must use itext.
# Check the first two choices in case first is something like "Other".
def has_dynamic_label(choice_list, multi_language):
    if not multi_language:
        for i in range(0, min(2, len(choice_list))):
            if (
                choice_list[i].get("label") is not None
                and re.search(BRACKETED_TAG_REGEX, choice_list[i].get("label"))
                is not None
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
    v1 = [0 for _ in range(0, n + 1)]

    # initialize v0 (the previous row of distances)
    # this row is A[0][i]: edit distance for an empty s
    # the distance is just the number of characters to delete from t
    v0 = [i for i in range(0, n + 1)]

    for i in range(0, m):
        # calculate v1 (current row distances) from the previous row v0

        # first element of v1 is A[i+1][0]
        #   edit distance is delete (i+1) chars from s to match empty t
        v1[0] = i + 1

        # use formula to fill in the rest of the row
        for j in range(0, n):
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


def get_expression_lexer() -> re.Scanner:  # noqa
    """
    Get a expression lexer (scanner) for parsing.
    """
    # ncname regex adapted from eulxml https://github.com/emory-libraries/eulxml/blob/2e1a9f71ffd1fd455bd8326ec82125e333b352e0/eulxml/xpath/lexrules.py
    # (C) 2010,2011 Emory University Libraries [Apache v2.0 License]
    # They in turn adapted it from https://www.w3.org/TR/REC-xml/#NT-NameStartChar
    # and https://www.w3.org/TR/REC-xml-names/#NT-NCName
    namestartchar = (
        r"([A-Z]|_|[a-z]|\xc0-\xd6]|[\xd8-\xf6]|[\xf8-\u02ff]|"
        + r"[\u0370-\u037d]|[\u037f-\u1fff]|[\u200c-\u200d]|[\u2070-\u218f]|"
        + r"[\u2c00-\u2fef]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]"
        + r"|[\U00010000-\U000EFFFF])"
    )
    # additional characters allowed in NCNames after the first character
    namechar_extra = r"[-.0-9\xb7\u0300-\u036f\u203f-\u2040]"
    ncname_regex = (
        r"(" + namestartchar + r")(" + namestartchar + r"|" + namechar_extra + r")*"
    )
    ncname_regex = ncname_regex + r"(:" + ncname_regex + r")?"

    date_regex = r"-?\d{4}-\d{2}-\d{2}"
    time_regex = r"\d{2}:\d{2}:\d{2}(\.\s+)?(((\+|\-)\d{2}:\d{2})|Z)?"
    date_time_regex = date_regex + "T" + time_regex

    # Rule order is significant - match priority runs top to bottom.
    lexer_rules = {
        # https://www.w3.org/TR/xmlschema-2/#dateTime
        "DATETIME": date_time_regex,
        "DATE": date_regex,
        "TIME": time_regex,
        "NUMBER": r"-?\d+\.\d*|-?\.\d+|-?\d+",
        # https://www.w3.org/TR/1999/REC-xpath-19991116/#exprlex
        "OPS_MATH": r"[\*\+\-]|mod|div",
        "OPS_COMP": r"\=|\!\=|\<|\>|\<=|>=",
        "OPS_BOOL": r"and|or",
        "OPS_UNION": r"\|",
        "OPEN_PAREN": r"\(",
        "CLOSE_PAREN": r"\)",
        "BRACKET": r"\[\]\{\}",
        "PARENT_REF": r"\.\.",
        "SELF_REF": r"\.",
        "PATH_SEP": r"\/",  # javarosa.xpath says "//" is an "unsupported construct".
        "SYSTEM_LITERAL": r""""[^"]*"|'[^']*'""",
        "COMMA": r",",
        "WHITESPACE": r"\s+",
        "PYXFORM_REF": r"\$\{" + ncname_regex + r"(#" + ncname_regex + r")?" + r"\}",
        "FUNC_CALL": ncname_regex + r"\(",
        "XPATH_PRED": ncname_regex + r"\[",
        "URI_SCHEME": ncname_regex + r"://",
        "NAME": ncname_regex,  # Must be after rules containing ncname_regex.
        "OTHER": r".+?",  # Catch any other character so that parsing doesn't stop.
    }

    def get_tokenizer(name):
        def tokenizer(scan, value):
            return ExpLexerToken(name, value, scan.match.start(), scan.match.end())

        return tokenizer

    lexicon = [(v, get_tokenizer(k)) for k, v in lexer_rules.items()]
    # re.Scanner is undocumented but has been around since at least 2003
    # https://mail.python.org/pipermail/python-dev/2003-April/035075.html
    return re.Scanner(lexicon)  # noqa


# Scanner takes a few 100ms to compile so use this shared instance.
ExpLexerToken = namedtuple("ExpLexerToken", ["name", "value", "start", "end"])
EXPRESSION_LEXER = get_expression_lexer()


def parse_expression(text: str) -> Tuple[List[ExpLexerToken], str]:
    """
    Parse a "default" expression, well enough to identify dynamic defaults vs. not.

    :param text: The expression.
    :return: The parsed tokens, and any remaining unparsed text.
    """
    tokens, remainder = EXPRESSION_LEXER.scan(text)
    return tokens, remainder


def coalesce(*args):
    return next((a for a in args if a is not None), None)
