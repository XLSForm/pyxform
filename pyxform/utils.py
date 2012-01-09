from xml.dom.minidom import Text, Element, parseString
import re
import codecs
import json
import copy

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

def node(tag, *args, **kwargs):
    """
    tag -- a XML tag
    args -- an array of children to append to the newly created node
            or if a unicode arg is supplied it will be used to make a text node
    returns a xml.dom.minidom.Element
    """
    result = Element(tag)
    unicode_args = [u for u in args if type(u) == unicode]
    assert len(unicode_args) <= 1
    parsedString = False
    #kwargs is an xml attribute dictionary, here we convert it to a xml.dom.minidom.Element
    for k, v in kwargs.iteritems():
        if k == 'toParseString':
            if v == True and len(unicode_args) == 1:
                parsedString = True
                #Add this header string so parseString can be used?
                s = u'<?xml version="1.0" ?><'+tag+'>' + unicode_args[0] + u'</'+tag+'>'
                node = parseString(s.encode("utf-8")).documentElement
                #Move node's children to the result Element discarding node's root
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
