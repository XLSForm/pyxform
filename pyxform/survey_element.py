"""
Survey Element base class for all survey elements.
"""

import json
import re
from collections.abc import Callable, Generator
from itertools import chain
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pyxform import aliases as alias
from pyxform import constants as const
from pyxform.errors import PyXFormError
from pyxform.parsing.expression import is_xml_tag
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.utils import (
    BRACKETED_TAG_REGEX,
    INVALID_XFORM_TAG_REGEXP,
    default_is_dynamic,
    node,
)
from pyxform.xls2json import print_pyobj_to_json

if TYPE_CHECKING:
    from pyxform.survey import Survey
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


SURVEY_ELEMENT_LOCAL_KEYS = {
    "_survey_element_default_type",
    "_survey_element_xpath",
}


class SurveyElement(dict):
    """
    SurveyElement is the base class we'll looks for the following keys
    in kwargs: name, label, hint, type, bind, control, parent,
    children, and question_type_dictionary.
    """

    __name__ = "SurveyElement"
    FIELDS: ClassVar[dict[str, Any]] = FIELDS.copy()

    def _dict_get(self, key):
        """Built-in dict.get to bypass __getattr__"""
        return dict.get(self, key)

    def __getattr__(self, key):
        """
        Get attributes from FIELDS rather than the class.
        """
        if key in self.FIELDS:
            under = None
            default = self._dict_get("_survey_element_default_type")
            if default is not None:
                under = default.get(key, None)
            if not under:
                return self._dict_get(key)
            return _overlay(self._dict_get(key), under)
        raise AttributeError(key)

    def __hash__(self):
        return hash(id(self))

    def __setattr__(self, key, value):
        if key == "parent":
            # If object graph position changes then invalidate cached.
            self._survey_element_xpath = None
        self[key] = value

    def __init__(self, **kwargs):
        self._survey_element_default_type: dict = kwargs.get(
            "question_type_dict", QUESTION_TYPE_DICT
        ).get(kwargs.get("type"), {})
        self._survey_element_xpath: str | None = None
        for key, default in self.FIELDS.items():
            self[key] = kwargs.get(key, default())
        self._link_children()

        # Create a space label for unlabeled elements with the label
        # appearance tag. # This is because such elements are used to label the
        # options for selects in a field-list and might want blank labels for
        # themselves.
        if self.control.get("appearance") == "label" and not self.label:
            self["label"] = " "
        super().__init__()

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
        if not is_xml_tag(self.name):
            invalid_char = re.search(INVALID_XFORM_TAG_REGEXP, self.name)
            raise PyXFormError(
                f"The name '{self.name}' contains an invalid character '{invalid_char.group(0)}'. Names {const.XML_IDENTIFIER_ERROR_MESSAGE}"
            )

    # TODO: Make sure renaming this doesn't cause any problems
    def iter_descendants(
        self, condition: Callable[["SurveyElement"], bool] | None = None
    ) -> Generator["SurveyElement", None, None]:
        """
        Get each of self.children.

        :param condition: If this evaluates to True, yield the element.
        """
        # it really seems like this method should not yield self
        if condition is not None:
            if condition(self):
                yield self
        else:
            yield self
        for e in self.children:
            yield from e.iter_descendants(condition=condition)

    def iter_ancestors(
        self, condition: Callable[["SurveyElement"], bool] | None = None
    ) -> Generator[tuple["SurvekyElement", int], None, None]:
        """
        Get each self.parent with their distance from self (starting at 1).

        :param condition: If this evaluates to True, yield the element.
        """
        distance = 1
        current = self.parent
        while current is not None:
            if condition is not None:
                if condition(current):
                    yield current, distance
            else:
                yield current, distance
            current = current.parent
            distance += 1

    def has_common_repeat_parent(
        self, other: "SurveyElement"
    ) -> tuple[str, int | None, Optional["SurveyElement"]]:
        """
        Get the relation type, steps (generations), and the common ancestor.
        """
        # Quick check for immediate relation.
        if self.parent is other:
            return "Parent (other)", 1, other
        elif other.parent is self:
            return "Parent (self)", 1, self

        # Traversal tracking
        self_ancestors = {}
        other_ancestors = {}
        self_current = self
        other_current = other
        self_distance = 0
        other_distance = 0

        # Traverse up both ancestor chains as far as necessary.
        while self_current or other_current:
            # Step up the self chain
            if self_current:
                self_distance += 1
                self_current = self_current.parent
                if self_current:
                    self_ancestors[self_current] = self_distance
                    if (
                        self_current.type == const.REPEAT
                        and self_current in other_ancestors
                    ):
                        max_steps = max(self_distance, other_ancestors[self_current])
                        return "Common Ancestor Repeat", max_steps, self_current

            # Step up the other chain
            if other_current:
                other_distance += 1
                other_current = other_current.parent
                if other_current:
                    other_ancestors[other_current] = other_distance
                    if (
                        other_current.type == const.REPEAT
                        and other_current in self_ancestors
                    ):
                        max_steps = max(other_distance, self_ancestors[other_current])
                        return "Common Ancestor Repeat", max_steps, other_current

        # No common ancestor found.
        return "Unrelated", None, None

    def get_xpath(self):
        """
        Return the xpath of this survey element.
        """
        # Imported here to avoid circular references.
        from pyxform.survey import Survey

        def condition(e):
            # The "flat" setting was added in 2013 to support ODK Tables, and results in
            # a data instance with no element nesting. Not sure if still needed.
            return isinstance(e, Survey) or (
                not isinstance(e, Survey) and not e.get("flat")
            )

        current_value = self._dict_get("_survey_element_xpath")
        if current_value is None:
            if condition(self):
                self_element = (self,)
            else:
                self_element = ()
            lineage = chain(
                reversed(tuple(i[0] for i in self.iter_ancestors(condition=condition))),
                self_element,
            )
            new_value = f'/{"/".join(n.name for n in lineage)}'
            self._survey_element_xpath = new_value
            return new_value
        return current_value

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
        to_delete = [
            "parent",
            "question_type_dictionary",
            "_created",
            "_xpath",
            *SURVEY_ELEMENT_LOCAL_KEYS,
        ]
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

    def needs_itext_ref(self):
        return isinstance(self.label, dict) or (
            isinstance(self.media, dict) and len(self.media) > 0
        )

    def get_setvalue_node_for_dynamic_default(self, survey: "Survey", in_repeat=False):
        if not self.default or not default_is_dynamic(self.default, self.type):
            return None

        default_with_xpath_paths = survey.insert_xpaths(self.default, self)

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
    def xml_label(self, survey: "Survey"):
        if self.needs_itext_ref():
            # If there is a dictionary label, or non-empty media dict,
            # then we need to make a label with an itext ref
            ref = f"""jr:itext('{self._translation_path("label")}')"""
            return node("label", ref=ref)
        else:
            label, output_inserted = survey.insert_output_values(self.label, self)
            return node("label", label, toParseString=output_inserted)

    def xml_hint(self, survey: "Survey"):
        if isinstance(self.hint, dict) or self.guidance_hint:
            path = self._translation_path("hint")
            return node("hint", ref=f"jr:itext('{path}')")
        else:
            hint, output_inserted = survey.insert_output_values(self.hint, self)
            return node("hint", hint, toParseString=output_inserted)

    def xml_label_and_hint(self, survey: "Survey") -> list["DetachableElement"]:
        """
        Return a list containing one node for the label and if there
        is a hint one node for the hint.
        """
        result = []
        label_appended = False
        if self.label or self.media:
            result.append(self.xml_label(survey=survey))
            label_appended = True

        if self.hint or self.guidance_hint:
            if not label_appended:
                result.append(self.xml_label(survey=survey))
            result.append(self.xml_hint(survey=survey))

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

    def xml_bindings(self, survey: "Survey"):
        """
        Return the binding(s) for this survey element.
        """
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
                elif k == "jr:constraintMsg" and (
                    isinstance(v, dict) or re.search(BRACKETED_TAG_REGEX, v)
                ):
                    v = f"""jr:itext('{self._translation_path("jr:constraintMsg")}')"""
                elif k == "jr:requiredMsg" and (
                    isinstance(v, dict) or re.search(BRACKETED_TAG_REGEX, v)
                ):
                    v = f"""jr:itext('{self._translation_path("jr:requiredMsg")}')"""
                elif k == "jr:noAppErrorString" and isinstance(v, dict):
                    v = f"""jr:itext('{self._translation_path("jr:noAppErrorString")}')"""
                bind_dict[k] = survey.insert_xpaths(v, context=self)
            return [node("bind", nodeset=self.get_xpath(), **bind_dict)]
        return None

    def xml_control(self, survey: "Survey"):
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
            return node(action_dict.pop("name"), ref=self.get_xpath(), **action_dict)

        return None


def hashable(v):
    """Determine whether `v` can be hashed."""
    try:
        hash(v)
    except TypeError:
        return False
    return True
