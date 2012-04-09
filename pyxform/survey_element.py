import json
from utils import is_valid_xml_tag, node
from xls2json import print_pyobj_to_json
from question_type_dictionary import QUESTION_TYPE_DICT
from errors import PyXFormError


def _overlay(over, under):
    if type(under) == dict:
        result = under.copy()
        result.update(over)
        return result
    return over if over else under


class SurveyElement(dict):
    """
    SurveyElement is the base class we'll looks for the following keys
    in kwargs: name, label, hint, type, bind, control, parent,
    children, and question_type_dictionary.
    """

    # the following are important keys for the underlying dict that
    # describes this survey element
    FIELDS = {
        u"name": unicode,
        u"label": unicode,
        u"hint": unicode,
        u"default": unicode,
        u"type": unicode,
        u"appearance": unicode,
        u"jr:count" : unicode,
        u"bind": dict,
        u"control": dict,
        u"media": dict,
        # this node will also have a parent and children, like a tree!
        u"parent": lambda: None,
        u"children": list,
        }

    def _default(self):
        # TODO: need way to override question type dictionary
        defaults = QUESTION_TYPE_DICT
        return defaults.get(self.get(u"type"), {})

    def __getattr__(self, key):
        """
        Get attributes from FIELDS rather than the class.
        """
        if key in self.FIELDS:
            question_type_dict = self._default()
            under = question_type_dict.get(key, None)
            over = self.get(key)
            if not under:
                return over
            return _overlay(over, under)
        raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __init__(self, **kwargs):
        for key, default in self.FIELDS.items():
            self[key] = kwargs.get(key, default())
        self._link_children()
        
        #Create a space label for unlabeled elements with the label appearance tag.
        #This is because such elements are used to label the options for selects in a field-list
        #and might want blank labels for themselves.
        if self.control.get(u"appearance") == u"label" and not self.label:
            self[u"label"] = u" "

    def _link_children(self):
        for child in self.children:
            child.parent = self

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_children(self, children):
        if type(children) == list:
            for child in children:
                self.add_child(child)
        else:
            self.add_child(children)

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

    def validate(self):
        if not is_valid_xml_tag(self.name):
            msg = "The name '%s' is an invalid xml tag. Names must begin with a letter, colon, or underscore, subsequent characters can include numbers, dashes, and periods." % self.name
            raise PyXFormError(msg)

    #TODO: Make sure renaming this doesn't cause any problems
    def iter_descendants(self):
        """
        A survey_element is a dictionary of survey_elements
        This method does a preorder traversal over them.
        For the time being this survery_element is included among its descendants
        """
        # it really seems like this method should not yield self
        yield self
        for e in self.children:
            for f in e.iter_descendants():
                yield f

    def get_lineage(self):
        """
        Return a the list [root, ..., self._parent, self]
        """
        result = [self]
        current_element = self
        while current_element.parent:
            current_element = current_element.parent
            result = [current_element] + result
        return result

    def get_root(self):
        return self.get_lineage()[0]

    def get_xpath(self):
        """
        Return the xpath of this survey element.
        """
        return u"/".join([u""] + [n.name for n in self.get_lineage()])

    def get_abbreviated_xpath(self):
        lineage = self.get_lineage()
        if len(lineage) >= 2:
            return u"/".join([unicode(n.name) for n in lineage[1:]])
        else:
            return lineage[0].name

    def to_json_dict(self):
        """
        Create a dict copy of this survey element by removing inappropriate attributes
        and converting its children to dicts
        """
        self.validate()
        result = self.copy()
        to_delete = [u"parent", u"question_type_dictionary", u"_created"]
        for key in to_delete:
            if key in result:
                del result[key]
        children = result.pop(u"children")
        result[u"children"] = []
        for child in children:
            result[u"children"].append(child.to_json_dict())
        # remove any keys with empty values
        for k, v in result.items():
            if not v:
                del result[k]
                
        return result

    def to_json(self):
        return json.dumps(self.to_json_dict())

    def json_dump(self, path=""):
        if not path:
            path = self.name + ".json"
        print_pyobj_to_json(self.to_json_dict(), path)

    def __eq__(self, y):
        # I need to look up how exactly to override the == operator.
        return self.to_json_dict() == y.to_json_dict()

    def _translation_path(self, display_element):
        return self.get_xpath() + ":" + display_element

    def get_translations(self, default_language):
        for display_element in [u'label', u'hint']:
            label_or_hint = self[display_element]
            
            if display_element is u'label' \
               and self.needs_itext_ref() \
               and type(label_or_hint) is not dict \
               and label_or_hint:
                label_or_hint = {default_language : label_or_hint}
                
            if type(label_or_hint) is dict:
                for lang, text in label_or_hint.items():
                    yield {
                        'display_element': display_element, #Not used
                        'path': self._translation_path(display_element),
                        'element': self, #Not used
                        'lang': lang,
                        'text': text,
                        }

    def get_media_keys(self):
        """
        @deprected
        I'm leaving this in just in case it has outside references.
        """
        return {
            u"media": u"%s:media" % self.get_xpath()
            }

    def needs_itext_ref(self):
        return type(self.label) is dict or (type(self.media) is dict and len(self.media) > 0)

    # XML generating functions, these probably need to be moved around.
    def xml_label(self):
        if self.needs_itext_ref():
            #If there is a dictionary label, or non-empty media dict, then we need to make a label with an itext ref
            ref = "jr:itext('%s')" % self._translation_path(u"label")
            return node(u"label", ref=ref)
        else:
            survey = self.get_root()
            label, outputInserted = survey.insert_output_values(self.label)
            return node(u"label", label, toParseString=outputInserted)

    def xml_hint(self):
        if type(self.hint) == dict:
            path = self._translation_path("hint")
            return node(u"hint", ref="jr:itext('%s')" % path)
        else:
            hint, outputInserted = self.get_root().insert_output_values(self.hint)
            return node(u"hint", hint, toParseString=outputInserted)

    def xml_label_and_hint(self):
        """
        Return a list containing one node for the label and if there
        is a hint one node for the hint.
        """
        result = []
        if self.label or self.media:
            result.append(self.xml_label())
        if self.hint:
            result.append(self.xml_hint())
        
        if len(result) == 0:
            msg = "The survey element named '%s' has no label or hint." % self.name
            raise PyXFormError(msg)
        
        return result
    
    def xml_binding(self):
        """
        Return the binding for this survey element.
        """
        survey = self.get_root()
        d = self.bind.copy()
        if d:
            for k, v in d.items():
                #I think all the binding conversions should be happening on the xls2json side.
                if hashable(v) and v in self.binding_conversions:
                    v = self.binding_conversions[v]
                d[k] = survey.insert_xpaths(v)
            return node(u"bind", nodeset=self.get_xpath(), **d)
        return None

    def xml_bindings(self):
        """
        Return a list of bindings for this node and all its descendants.
        """
        result = []
        for e in self.iter_descendants():
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
    
def hashable(v):
    """Determine whether `v` can be hashed."""
    try:
        hash(v)
    except TypeError:
        return False
    return True
