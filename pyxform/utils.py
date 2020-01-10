# -*- coding: utf-8 -*-
"""
pyxform utils module.
"""
import codecs
import copy
import json
import os
import re
from xml.dom.minidom import Element, Text, parseString

import unicodecsv as csv
import xlrd

from pyxform.constants import COMPLEX_RELEVANT_VARIABLES_MAX_THRESHOLD, row_format_string

try:
    from json.decoder import JSONDecodeError
except ImportError:
    # json module raises a ValueError exception when it encounters an invalid JSON
    JSONDecodeError = ValueError

try:
    unicode("str")
except NameError:
    unicode = str
    basestring = str
    unichr = chr
else:
    try:
        unicode = unicode
        basestring = basestring
        unichr = unichr
    except NameError:  # special cases where unicode is defined in python3
        unicode = str
        basestring = str
        unichr = chr

SEP = "_"

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {"start": TAG_START_CHAR, "char": TAG_CHAR}

INVALID_XFORM_TAG_REGEXP = r"[^a-zA-Z:_][^a-zA-Z:_0-9\-.]*"

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


def is_valid_xml_tag(tag):
    """
    Use a regex to see if there are any invalid characters (i.e. spaces).
    """
    return re.search(r"^" + XFORM_TAG_REGEXP + r"$", tag)


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
    unicode_args = [u for u in args if type(u) == unicode]
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
                    result.appendChild(copy.deepcopy(child))
        else:
            result.setAttribute(k, v)

    if len(unicode_args) == 1 and not parsed_string:
        text_node = PatchedText()
        text_node.data = unicode_args[0]
        result.appendChild(text_node)
    for n in args:
        if type(n) == int or type(n) == float or type(n) == bytes:
            text_node = PatchedText()
            text_node.data = unicode(n)
            result.appendChild(text_node)
        elif type(n) is not unicode:
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
        doc = json.load(fp, encoding="utf-8")
    except (IOError, JSONDecodeError, OSError):
        # if it doesn't work load the text
        doc = json.loads(str_or_path)
    return doc


def flatten(li):
    for subli in li:
        for it in subli:
            yield it


def sheet_to_csv(workbook_path, csv_path, sheet_name):
    from pyxform.xls2json_backends import xls_value_to_unicode

    wb = xlrd.open_workbook(workbook_path)
    try:
        sheet = wb.sheet_by_name(sheet_name)
    except xlrd.biffh.XLRDError:
        return False
    if not sheet or sheet.nrows < 2:
        return False
    with open(csv_path, "wb") as f:
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


def has_external_choices(json_struct):
    """
    Returns true if a select one external prompt is used in the survey.
    """
    if isinstance(json_struct, dict):
        for k, v in json_struct.items():
            if (
                k == "type"
                and isinstance(v, basestring)
                and v.startswith("select one external")
            ):
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
    iana_subtags = []
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
    * Contains balanced set of [] and/or {} and/or ().
    """
    if not isinstance(element_default, basestring):
        return False

    expression = []
    arithmetic_text = {" mod ", " div "}
    contains_dynamic = any(s in element_default for s in arithmetic_text)
    arithmetic_construct = {"*", "|", "+", "-"}
    if element_type is not None and element_type == "date":
        arithmetic_construct.remove("-")

    expression_construct = {"[", "]", "{", "}", "(", ")"}
    expression_pair = {"]": "[", "}": "{", ")": "("}
    for expression_element in element_default:
        contains_dynamic = (
            contains_dynamic
            or expression_element in expression_construct
            or expression_element in arithmetic_construct
        )
        if expression_element in expression_construct:
            if expression and expression.pop() != expression_pair[expression_element]:
                return False
            else:
                expression.append(expression_element)
    return contains_dynamic

def expression_is_repeated(expression, expression_hash_map, row_number):
    """
    Checks If a logical expression repeated

    expression (str) - text representing expression to be tested
    expression_hash_map (dict) - store hashes of the expressions as keys
        and their indexes as values on the work sheet
    row_number (int) - location of the row in the sheet
    return (bool) True if expression is already in surveySheet
    """
    if expression in expression_hash_map.keys():
        return (
            row_format_string % row_number
            + " Duplicate expression detected. In future, "
            + "it is best to store repeated logic in calculate"
            + " and referring to that calculate."
        )
    else:
        expression_hash_map[expression] = row_number
        return ''


def expression_is_complex(expression, row_number):
    """
    A heuristic that checks whether a logical relevance expression is complex.
    using the number of logical combinations, which is imperatively a function
    of the total number of operands whose operators are logical in nature i.e. and & or

    expression (str) - text representing expression to be tested
    row_number (int) - location of the row in the sheet
    return (string) - the warning message, blank string if no warning
    """
    regex = r"or|and"
    num_of_variables = re.split(regex, expression)
    if len(num_of_variables) > COMPLEX_RELEVANT_VARIABLES_MAX_THRESHOLD:
        return (
            row_format_string % row_number
            + " Possible complex or long logical expression detected, "
            + " This may cause stack overflows during form submission."
        )
    return ''