from xml.dom.minidom import Text, Element, parseString
import re
import codecs
import json

SEP = "_"

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {
    "start": TAG_START_CHAR,
    "char": TAG_CHAR
    }


def is_valid_xml_tag(tag):
    return re.search(r"^" + XFORM_TAG_REGEXP + r"$", tag)


def node(tag, *args, **kwargs):
    result = Element(tag)

    unicode_args = [u for u in args if type(u) == unicode]
    assert len(unicode_args) <= 1

    parsedString = False
    for k, v in kwargs.iteritems():
        if k == 'toParseString':
            if v == True and len(unicode_args) == 1:
                parsedString = True
                s = u'<?xml version="1.0" ?><'+tag+'>' + unicode_args[0] + u'</'+tag+'>'
                node = parseString(s.encode("utf-8")).documentElement
                childNodes = []
                for child in node.childNodes:
                    childNodes.append(child)
                for child in childNodes:
                    result.appendChild(child)
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
        elif type(n) != unicode:
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
