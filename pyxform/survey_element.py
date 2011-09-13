import json
from utils import is_valid_xml_tag, node
from collections import defaultdict
from question_type_dictionary import DEFAULT_QUESTION_TYPE_DICTIONARY
from xls2json import print_pyobj_to_json


class SurveyElement(object):
    """
    SurveyElement is the base class we'll looks for the following keys
    in kwargs: name, label, hint, type, bind, control, parent,
    children, and question_type_dictionary.
    """

    binding_conversions = {
        "yes": "true()",
        "Yes": "true()",
        "YES": "true()",
        "true": "true()",
        "True": "true()",
        "TRUE": "true()",
        "no": "false()",
        "No": "false()",
        "NO": "false()",
        "false": "false()",
        "False": "false()",
        "FALSE": "false()"
    }

    #Supported media types for attaching to questions
    SUPPORTED_MEDIA = [
        "image",
        "audio",
        "video"
    ]

    # the following are important keys for the underlying dict that
    # describes this survey element
    NAME = u"name"
    LABEL = u"label"
    HINT = u"hint"
    DEFAULT = u"default"
    TYPE = u"type"
    APPEARANCE = u"appearance"
    BIND = u"bind"
    CONTROL = u"control"
    MEDIA = u"media"
    # this node will also have a parent and children, like a tree!
    # these will not be stored in the dict.
    PARENT = u"parent"
    CHILDREN = u"children"

    _DEFAULT_VALUES = {
        NAME: u"",
        LABEL: {},
        HINT: {},
        DEFAULT: {},
        TYPE: u"",
        BIND: {},
        CONTROL: {},
        MEDIA: {}
        }

    def __init__(self, *args, **kwargs):
        self._dict = defaultdict(dict)
        for k, default_value in self._DEFAULT_VALUES.items():
            self._dict[k] = kwargs.get(k, default_value)
        self._parent = kwargs.get(u"parent", None)
        self._children = []
        for element in kwargs.get(u"children", []):
            self.add_child(element)
        self._question_type_dictionary = kwargs.get(
            u"question_type_dictionary", None
            )

    def get_question_type_dictionary(self):
        """
        Return the dictionary of question types this SurveyElement is
        associated with.
        """
        if self._question_type_dictionary:
            return self._question_type_dictionary
        elif self._parent:
            return self._parent.get_question_type_dictionary()
        else:
            return DEFAULT_QUESTION_TYPE_DICTIONARY

    def add_child(self, element):
        """
        Add a SurveyElement to this SurveyElement's children. As a
        slight hack, this method also accepts a list of elements.
        """
        # I should probably rename this function, because now it handles lists
        if type(element) == list:
            for list_element in element:
                self.add_child(list_element)
        else:
            element._set_parent(self)
            self._children.append(element)

    def get_children(self):
        """
        Return this SurveyElement's children.
        """
        return self._children

    def get(self, key):
        # name, type, control, bind, label, hint, default
        return self._dict[key]

    def set(self, key, value):
        self._dict[key] = value

    def set_name(self, name):
        self._dict[self.NAME] = name

    def validate(self):
        if not is_valid_xml_tag(self.get_name()):
            msg = "The name of this survey element is an invalid xml tag. Names must begin with a letter, colon, or underscore, subsequent characters can include numbers, dashes, and periods."
            raise Exception(self.get_name(), msg)                

    def _set_parent(self, parent):
        self._parent = parent

    def iter_children(self):
        # it really seems like this method should not yield self
        yield self
        for e in self._children:
            for f in e.iter_children():
                yield f

    def get_lineage(self):
        """
        Return a the list [root, ..., self._parent, self]
        """
        result = [self]
        current_element = self
        while current_element._parent:
            current_element = current_element._parent
            result = [current_element] + result
        return result

    def get_root(self):
        return self.get_lineage()[0]

    def get_xpath(self):
        """
        Return the xpath of this survey element.
        """
        return u"/".join([u""] + [n.get_name() for n in self.get_lineage()])

    def get_abbreviated_xpath(self):
        lineage = self.get_lineage()
        if len(lineage) >= 2:
            return u"/".join([n.get_name() for n in lineage[1:]])
        else:
            return lineage[0].get_name()

    def to_dict(self):
        self.validate()
        result = dict([(k, v) for k, v in self._dict.items()])
        assert u"children" not in result
        result[u"children"] = [e.to_dict() for e in self._children]
        # remove any keys with empty values
        for k, v in result.items():
            if not v:
                del result[k]
        return result

    def to_json(self):
        return json.dumps(self.to_dict())

    def json_dump(self, path=""):
        if not path:
            path = self.get_name() + ".json"
        print_pyobj_to_json(self.to_dict(), path)

    def __eq__(self, y):
        # I need to look up how exactly to override the == operator.
        return self.to_dict() == y.to_dict()

    def _translation_path(self, display_element):
        return self.get_xpath() + ":" + display_element

    def get_translations(self):
        for display_element in ['label', 'hint']:
            label_or_hint = self.get(display_element)
            if type(label_or_hint) == dict:
                for lang, text in label_or_hint.items():
                    yield {
                        'display_element': display_element,
                        'path': self._translation_path(display_element),
                        'element': self,
                        'lang': lang,
                        'text': text,
                        }

    def get_media_keys(self):
        return {
            u"media": u"%s:media" % self.get_xpath()
            }

    # XML generating functions, these probably need to be moved around.
    def xml_label(self):
        if not self.get_label() and not self.get(self.TYPE) == "group"and len(self.get('media')) == 0:
            return None

        if type(self.get_label()) == dict or not len(self.get('media')) == 0:
            if len(self.get_label()) == 0 and self.get(self.TYPE) == "group":
                return None
            return node(u"label", ref="jr:itext('%s')" % self._translation_path(u"label"))
        else:
            label, outputInserted = self.get_root().insert_output_values(self.get_label())
            return node(u"label", label, toParseString=outputInserted)

    def xml_hint(self):
        if type(self.get_hint()) == dict:
            path = self._translation_path("hint")
            return node(u"hint", ref="jr:itext('%s')" % path)
        else:
            hint, outputInserted = self.get_root().insert_output_values(self.get_hint())
            return node(u"hint", hint, toParseString=outputInserted)

    def xml_label_and_hint(self):
        """
        Return a list containing one node for the label and if there
        is a hint one node for the hint.
        """
        if self.get_label() and self.get_hint():
            return [self.xml_label(), self.xml_hint()]
        elif self.get_label():
            return [self.xml_label()]
        elif self.get_hint():
            return [self.xml_hint()]
        else:
            return None

    def xml_binding(self):
        """
        Return the binding for this survey element.
        """
        survey = self.get_root()
        d = self.get_bind().copy()
        if d:
            for k, v in d.items():
                if v in self.binding_conversions:
                    v = self.binding_conversions[v]
                d[k] = survey.insert_xpaths(v)
            return node(u"bind", nodeset=self.get_xpath(), **d)
        return None

    def xml_bindings(self):
        """
        Return a list of bindings for this node and all its descendents.
        """
        result = []
        for e in self.iter_children():
            xml_binding = e.xml_binding()
            if xml_binding != None:
                result.append(xml_binding)
        return result

    def xml_control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise Exception("Control not implemented")


# add a bunch of get methods to the SurveyElement class
def add_get_method(cls, key):
    def get_method(self):
        return self.get(key)
    get_method.__name__ = str("get_%s" % key)
    setattr(cls, get_method.__name__, get_method)

for key in SurveyElement._DEFAULT_VALUES.keys():
    add_get_method(SurveyElement, key)
