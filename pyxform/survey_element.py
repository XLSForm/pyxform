"""
Survey Element base class for all survey elements.
"""

import json
import re
from collections import deque
from functools import lru_cache
from typing import TYPE_CHECKING, Any, ClassVar

from pyxform import aliases as alias
from pyxform import constants as const
from pyxform.errors import PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.utils import (
    BRACKETED_TAG_REGEX,
    INVALID_XFORM_TAG_REGEXP,
    default_is_dynamic,
    node,
)
from pyxform.xls2json import print_pyobj_to_json
from pyxform.xlsparseutils import is_valid_xml_tag

if TYPE_CHECKING:
    from pyxform.utils import DetachableElement

# The following are important keys for the underlying dict that describes SurveyElement
FIELDS = {
    "name": str,
    const.COMPACT_TAG: str,  # used for compact (sms) representation
    "sms_field": str,
    "sms_option": str,
    "label": str,
    "hint": str,
    "guidance_hint": str,
    "default": str,
    "type": str,
    "appearance": str,
    "parameters": dict,
    "intent": str,
    "jr:count": str,
    "bind": dict,
    "instance": dict,
    "control": dict,
    "media": dict,
    # this node will also have a parent and children, like a tree!
    "parent": lambda: None,
    "children": list,
    "itemset": str,
    "choice_filter": str,
    "query": str,
    "autoplay": str,
    "flat": lambda: False,
    "action": str,
    const.LIST_NAME_U: str,
    "trigger": str,
}


def _overlay(over, under):
    if isinstance(under, dict):
        result = under.copy()
        result.update(over)
        return result
    return over if over else under


@lru_cache(maxsize=65536)
def any_repeat(survey_element: "SurveyElement", parent_xpath: str) -> bool:
    """Return True if there ia any repeat in `parent_xpath`."""
    for item in survey_element.iter_descendants():
        if item.get_xpath() == parent_xpath and item.type == const.REPEAT:
            return True

    return False


class SurveyElement(dict):
    """
    SurveyElement is the base class we'll looks for the following keys
    in kwargs: name, label, hint, type, bind, control, parent,
    children, and question_type_dictionary.
    """

    __name__ = "SurveyElement"
    FIELDS: ClassVar[dict[str, Any]] = FIELDS.copy()

    def _default(self):
        # TODO: need way to override question type dictionary
        defaults = QUESTION_TYPE_DICT
        return defaults.get(self.get("type"), {})

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

    def __hash__(self):
        return hash(id(self))

    def __setattr__(self, key, value):
        self[key] = value

    def __init__(self, **kwargs):
        for key, default in self.FIELDS.items():
            self[key] = kwargs.get(key, default())
        self._link_children()

        # Create a space label for unlabeled elements with the label
        # appearance tag. # This is because such elements are used to label the
        # options for selects in a field-list and might want blank labels for
        # themselves.
        if self.control.get("appearance") == "label" and not self.label:
            self["label"] = " "

    def _link_children(self):
        for child in self.children:
            child.parent = self

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_children(self, children):
        if isinstance(children, list):
            for child in children:
                self.add_child(child)
        else:
            self.add_child(children)

    # Supported media types for attaching to questions
    SUPPORTED_MEDIA = ("image", "big-image", "audio", "video")

    def validate(self):
        if not is_valid_xml_tag(self.name):
            invalid_char = re.search(INVALID_XFORM_TAG_REGEXP, self.name)
            raise PyXFormError(
                f"The name '{self.name}' contains an invalid character '{invalid_char.group(0)}'. Names {const.XML_IDENTIFIER_ERROR_MESSAGE}"
            )

    # TODO: Make sure renaming this doesn't cause any problems
    def iter_descendants(self):
        """
        A survey_element is a dictionary of survey_elements
        This method does a preorder traversal over them.
        For the time being this survery_element is included among its
        descendants
        """
        # it really seems like this method should not yield self
        yield self
        for e in self.children:
            yield from e.iter_descendants()

    def any_repeat(self, parent_xpath: str) -> bool:
        """Return True if there ia any repeat in `parent_xpath`."""
        return any_repeat(survey_element=self, parent_xpath=parent_xpath)

    def get_lineage(self):
        """
        Return a the list [root, ..., self._parent, self]
        """
        result = deque((self,))
        current_element = self
        while current_element.parent:
            current_element = current_element.parent
            result.appendleft(current_element)
        # For some reason the root element has a True flat property...
        output = [result.popleft()]
        output.extend([i for i in result if not i.get("flat")])
        return output

    def get_root(self):
        return self.get_lineage()[0]

    def get_xpath(self):
        """
        Return the xpath of this survey element.
        """
        return "/".join([""] + [n.name for n in self.get_lineage()])

    def get_abbreviated_xpath(self):
        lineage = self.get_lineage()
        if len(lineage) >= 2:
            return "/".join([str(n.name) for n in lineage[1:]])
        else:
            return lineage[0].name

    def _delete_keys_from_dict(self, dictionary: dict, keys: list):
        """
        Deletes a list of keys from a dictionary.
        Credits: https://stackoverflow.com/a/49723101
        """
        for key in keys:
            if key in dictionary:
                del dictionary[key]

        for value in dictionary.values():
            if isinstance(value, dict):
                self._delete_keys_from_dict(value, keys)

    def to_json_dict(self):
        """
        Create a dict copy of this survey element by removing inappropriate
        attributes and converting its children to dicts
        """
        self.validate()
        result = self.copy()
        to_delete = ["parent", "question_type_dictionary", "_created"]
        # Delete all keys that may cause a "Circular Reference"
        # error while converting the result to JSON
        self._delete_keys_from_dict(result, to_delete)
        children = result.pop("children")
        result["children"] = []
        for child in children:
            result["children"].append(child.to_json_dict())
        # Translation items with "output_context" have circular references.
        if "_translations" in result:
            for lang in result["_translations"].values():
                for item in lang.values():
                    for form in item.values():
                        if callable(getattr(form, "pop", None)):
                            form.pop("output_context", None)
        # remove any keys with empty values
        for k, v in list(result.items()):
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
        return (
            hasattr(y, "to_json_dict")
            and callable(y.to_json_dict)
            and self.to_json_dict() == y.to_json_dict()
        )

    def _translation_path(self, display_element: str) -> str:
        """Get an itextId based on the element XPath and display type."""
        return self.get_xpath() + ":" + display_element

    def get_translations(self, default_language):
        """
        Returns translations used by this element so they can be included in
        the <itext> block. @see survey._setup_translations
        """
        bind_dict = self.get("bind")
        if bind_dict and isinstance(bind_dict, dict):
            constraint_msg = bind_dict.get("jr:constraintMsg")
            if isinstance(constraint_msg, dict):
                for lang, text in constraint_msg.items():
                    yield {
                        "path": self._translation_path("jr:constraintMsg"),
                        "lang": lang,
                        "text": text,
                        "output_context": self,
                    }
            elif constraint_msg and re.search(BRACKETED_TAG_REGEX, constraint_msg):
                yield {
                    "path": self._translation_path("jr:constraintMsg"),
                    "lang": default_language,
                    "text": constraint_msg,
                    "output_context": self,
                }

            required_msg = bind_dict.get("jr:requiredMsg")
            if isinstance(required_msg, dict):
                for lang, text in required_msg.items():
                    yield {
                        "path": self._translation_path("jr:requiredMsg"),
                        "lang": lang,
                        "text": text,
                        "output_context": self,
                    }
            elif required_msg and re.search(BRACKETED_TAG_REGEX, required_msg):
                yield {
                    "path": self._translation_path("jr:requiredMsg"),
                    "lang": default_language,
                    "text": required_msg,
                    "output_context": self,
                }
            no_app_error_string = bind_dict.get("jr:noAppErrorString")
            if isinstance(no_app_error_string, dict):
                for lang, text in no_app_error_string.items():
                    yield {
                        "path": self._translation_path("jr:noAppErrorString"),
                        "lang": lang,
                        "text": text,
                        "output_context": self,
                    }

        for display_element in ["label", "hint", "guidance_hint"]:
            label_or_hint = self[display_element]

            if (
                display_element == "label"
                and self.needs_itext_ref()
                and not isinstance(label_or_hint, dict)
                and label_or_hint
            ):
                label_or_hint = {default_language: label_or_hint}

            # always use itext for guidance hints because that's
            # how they're defined - https://opendatakit.github.io/xforms-spec/#languages
            if (
                display_element == "guidance_hint"
                and not isinstance(label_or_hint, dict)
                and len(label_or_hint) > 0
            ):
                label_or_hint = {default_language: label_or_hint}

            # always use itext for hint if there's a guidance hint
            if (
                display_element == "hint"
                and not isinstance(label_or_hint, dict)
                and len(label_or_hint) > 0
                and "guidance_hint" in self.keys()
                and len(self["guidance_hint"]) > 0
            ):
                label_or_hint = {default_language: label_or_hint}

            if isinstance(label_or_hint, dict):
                for lang, text in label_or_hint.items():
                    yield {
                        "display_element": display_element,  # Not used
                        "path": self._translation_path(display_element),
                        "element": self,  # Not used
                        "output_context": self,
                        "lang": lang,
                        "text": text,
                    }

    def get_media_keys(self):
        """
        @deprected
        I'm leaving this in just in case it has outside references.
        """
        return {"media": f"{self.get_xpath()}:media"}

    def needs_itext_ref(self):
        return isinstance(self.label, dict) or (
            isinstance(self.media, dict) and len(self.media) > 0
        )

    def get_setvalue_node_for_dynamic_default(self, in_repeat=False):
        if not self.default or not default_is_dynamic(self.default, self.type):
            return None

        default_with_xpath_paths = self.get_root().insert_xpaths(self.default, self)

        triggering_events = "odk-instance-first-load"
        if in_repeat:
            triggering_events += " odk-new-repeat"

        return node(
            "setvalue",
            ref=self.get_xpath(),
            value=default_with_xpath_paths,
            event=triggering_events,
        )

    # XML generating functions, these probably need to be moved around.
    def xml_label(self):
        if self.needs_itext_ref():
            # If there is a dictionary label, or non-empty media dict,
            # then we need to make a label with an itext ref
            ref = f"""jr:itext('{self._translation_path("label")}')"""
            return node("label", ref=ref)
        else:
            survey = self.get_root()
            label, output_inserted = survey.insert_output_values(self.label, self)
            return node("label", label, toParseString=output_inserted)

    def xml_hint(self):
        if isinstance(self.hint, dict) or self.guidance_hint:
            path = self._translation_path("hint")
            return node("hint", ref=f"jr:itext('{path}')")
        else:
            hint, output_inserted = self.get_root().insert_output_values(self.hint, self)
            return node("hint", hint, toParseString=output_inserted)

    def xml_label_and_hint(self) -> list["DetachableElement"]:
        """
        Return a list containing one node for the label and if there
        is a hint one node for the hint.
        """
        result = []
        label_appended = False
        if self.label or self.media:
            result.append(self.xml_label())
            label_appended = True

        if self.hint or self.guidance_hint:
            if not label_appended:
                result.append(self.xml_label())
            result.append(self.xml_hint())

        msg = f"The survey element named '{self.name}' has no label or hint."
        if len(result) == 0:
            raise PyXFormError(msg)

        # Guidance hint alone is not OK since they may be hidden by default.
        if not any((self.label, self.media, self.hint)) and self.guidance_hint:
            raise PyXFormError(msg)

        # big-image must combine with image
        if "image" not in self.media and "big-image" in self.media:
            raise PyXFormError(
                "To use big-image, you must also specify an image for the survey element named {self.name}."
            )

        return result

    def xml_bindings(self):
        """
        Return the binding(s) for this survey element.
        """
        survey = self.get_root()
        bind_dict = self.bind.copy()
        if self.get("flat"):
            # Don't generate bind element for flat groups.
            return None
        if bind_dict:
            # the expression goes in a setvalue action
            if self.trigger and "calculate" in self.bind:
                del bind_dict["calculate"]

            for k, v in bind_dict.items():
                # I think all the binding conversions should be happening on
                # the xls2json side.
                if (
                    hashable(v)
                    and v in alias.BINDING_CONVERSIONS
                    and k in const.CONVERTIBLE_BIND_ATTRIBUTES
                ):
                    v = alias.BINDING_CONVERSIONS[v]
                if k == "jr:constraintMsg" and (
                    isinstance(v, dict) or re.search(BRACKETED_TAG_REGEX, v)
                ):
                    v = f"""jr:itext('{self._translation_path("jr:constraintMsg")}')"""
                if k == "jr:requiredMsg" and (
                    isinstance(v, dict) or re.search(BRACKETED_TAG_REGEX, v)
                ):
                    v = f"""jr:itext('{self._translation_path("jr:requiredMsg")}')"""
                if k == "jr:noAppErrorString" and isinstance(v, dict):
                    v = f"""jr:itext('{self._translation_path("jr:noAppErrorString")}')"""
                bind_dict[k] = survey.insert_xpaths(v, context=self)
            return [node("bind", nodeset=self.get_xpath(), **bind_dict)]
        return None

    def xml_descendent_bindings(self):
        """
        Return a list of bindings for this node and all its descendants.
        """
        result = []
        for e in self.iter_descendants():
            xml_bindings = e.xml_bindings()
            if xml_bindings is not None:
                result.extend(xml_bindings)

            # dynamic defaults for repeats go in the body. All other dynamic defaults (setvalue actions) go in the model
            if (
                len(
                    [
                        ancestor
                        for ancestor in e.get_lineage()
                        if ancestor.type == "repeat"
                    ]
                )
                == 0
            ):
                dynamic_default = e.get_setvalue_node_for_dynamic_default()
                if dynamic_default:
                    result.append(dynamic_default)
        return result

    def xml_control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise NotImplementedError("Control not implemented")

    def xml_action(self):
        """
        Return the action for this survey element.
        """
        if self.action:
            action_dict = self.action.copy()
            if action_dict:
                name = action_dict["name"]
                del action_dict["name"]
                return node(name, ref=self.get_xpath(), **action_dict)

        return None

    def xml_actions(self):
        """
        Return a list of actions for this node and all its descendants.
        """
        result = []
        for e in self.iter_descendants():
            xml_action = e.xml_action()
            if xml_action is not None:
                result.append(xml_action)
        return result


def hashable(v):
    """Determine whether `v` can be hashed."""
    try:
        hash(v)
    except TypeError:
        return False
    return True
