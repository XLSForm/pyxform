from xml.dom.minidom import Text, Element, parseString
import re
import codecs
import json
import copy
import csv
import xlrd

SEP = "_"

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {
    "start": TAG_START_CHAR,
    "char": TAG_CHAR
    }


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
    blocked_attributes = ['tag']
    tag = args[0] if len(args) > 0 else kwargs['tag']
    args = args[1:]
    result = Element(tag)
    unicode_args = [u for u in args if type(u) == unicode]
    assert len(unicode_args) <= 1
    parsedString = False
    # kwargs is an xml attribute dictionary,
    # here we convert it to a xml.dom.minidom.Element
    for k, v in kwargs.iteritems():
        if k in blocked_attributes:
            continue
        if k == 'toParseString':
            if v is True and len(unicode_args) == 1:
                parsedString = True
                # Add this header string so parseString can be used?
                s = u'<?xml version="1.0" ?><'+tag+'>' + unicode_args[0]\
                    + u'</'+tag+'>'
                node = parseString(s.encode("utf-8")).documentElement
                # Move node's children to the result Element
                # discarding node's root
                for child in node.childNodes:
                    result.appendChild(copy.deepcopy(child))
        else:
            result.setAttribute(k, v)

    if len(unicode_args) == 1 and not parsedString:
        text_node = Text()
        text_node.data = unicode_args[0]
        result.appendChild(text_node)
    for n in args:
        if type(n) == int or type(n) == float or type(n) == str:
            text_node = Text()
            text_node.data = unicode(n)
            result.appendChild(text_node)
        elif type(n) is not unicode:
            try:
                result.appendChild(n)
            except:
                raise Exception(type(n), n)
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
    except:
        # if it doesn't work load the text
        doc = json.loads(str_or_path)
    return doc


def flatten(li):
    for subli in li:
        for it in subli:
            yield it


def sheet_to_csv(workbook_path, csv_path, sheet_name):
    wb = xlrd.open_workbook(workbook_path)
    try:
        sheet = wb.sheet_by_name(sheet_name)
    except xlrd.biffh.XLRDError:
        return False
    if not sheet or sheet.nrows < 2:
        return False
    with open(csv_path, 'wb') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        mask = [v and len(v.strip()) > 0 for v in sheet.row_values(0)]
        for r in range(sheet.nrows):
            writer.writerow(
                [v for v, m in zip(sheet.row_values(r), mask) if m])
    return True


def has_external_choices(json_struct):
    """
    Returns true if a select one external prompt is used in the survey.
    """
    if isinstance(json_struct, dict):
        for k, v in json_struct.items():
            if k == u"type" and isinstance(v, basestring) \
                    and v.startswith(u"select one external"):
                return True
            elif has_external_choices(v):
                return True
    elif isinstance(json_struct, list):
        for v in json_struct:
            if has_external_choices(v):
                return True
    return False
