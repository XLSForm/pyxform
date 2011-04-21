from xml.dom.minidom import Text, Element
import re
import codecs
import json

nsmap = {
    None : "http://www.w3.org/2002/xforms",
    "h" : "http://www.w3.org/1999/xhtml",
    "ev" : "http://www.w3.org/2001/xml-events",
    "xsd" : "http://www.w3.org/2001/XMLSchema",
    "jr" : "http://openrosa.org/javarosa",
    }

SEP = "_"

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {"start" : TAG_START_CHAR, "char" : TAG_CHAR}

def ns(abbrev, text):
    return "{" + nsmap[abbrev] + "}" + text

def is_valid_xml_tag(tag):
    return re.search(r"^" + XFORM_TAG_REGEXP + r"$", tag)

def node(tag, *args, **kwargs):
    result = Element(tag)
    for k, v in kwargs.iteritems():
        result.setAttribute(k, v)
    unicode_args = [u for u in args if type(u)==unicode]
    assert len(unicode_args)<=1
    if len(unicode_args)==1:
        text_node = Text()
        text_node.data = unicode_args[0]
        result.appendChild(text_node)
    for n in args:
        if type(n)!=unicode:
            try:
                result.appendChild(n)
            except:
                raise Exception(n)
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
