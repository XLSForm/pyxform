"""
XForm Survey element classes for different question types.
"""

import os.path
from collections.abc import Callable, Generator, Iterable
from itertools import chain
from typing import TYPE_CHECKING

from pyxform import constants
from pyxform.constants import (
    EXTERNAL_CHOICES_ITEMSET_REF_LABEL,
    EXTERNAL_CHOICES_ITEMSET_REF_LABEL_GEOJSON,
    EXTERNAL_CHOICES_ITEMSET_REF_VALUE,
    EXTERNAL_CHOICES_ITEMSET_REF_VALUE_GEOJSON,
    EXTERNAL_INSTANCE_EXTENSIONS,
)
from pyxform.elements import action
from pyxform.errors import PyXFormError
from pyxform.parsing.expression import maybe_strip
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS, SurveyElement
from pyxform.utils import (
    DetachableElement,
    combine_lists,
    default_is_dynamic,
    node,
)
from pyxform.validators.pyxform.pyxform_reference import has_pyxform_reference

if TYPE_CHECKING:
    from pyxform.survey import Survey


QUESTION_EXTRA_FIELDS = (
    "_dynamic_default",
    "_qtd_defaults",
    "_qtd_kwargs",
    "actions",
    "default",
    "guidance_hint",
    "instance",
    "query",
    "sms_field",
    "trigger",
    constants.BIND,
    constants.CHOICE_FILTER,
    constants.CONTROL,
    constants.HINT,
    constants.MEDIA,
    constants.PARAMETERS,
    constants.TYPE,
)
QUESTION_FIELDS = (*SURVEY_ELEMENT_FIELDS, *QUESTION_EXTRA_FIELDS)

SELECT_QUESTION_EXTRA_FIELDS = (
    constants.CHOICES,
    constants.ITEMSET,
    constants.LIST_NAME_U,
)
SELECT_QUESTION_FIELDS = (*QUESTION_FIELDS, *SELECT_QUESTION_EXTRA_FIELDS)

OSM_QUESTION_EXTRA_FIELDS = (constants.CHILDREN,)
OSM_QUESTION_FIELDS = (*QUESTION_FIELDS, *SELECT_QUESTION_EXTRA_FIELDS)

OPTION_EXTRA_FIELDS = (
    "_choice_itext_ref",
    constants.MEDIA,
    "sms_option",
)
OPTION_FIELDS = (*SURVEY_ELEMENT_FIELDS, *OPTION_EXTRA_FIELDS)


class Question(SurveyElement):
    __slots__ = QUESTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return QUESTION_FIELDS

    def __init__(self, fields: tuple[str, ...] | None = None, **kwargs):
        # Internals
        self._dynamic_default: bool | None = None
        self._qtd_defaults: dict | None = None
        self._qtd_kwargs: dict | None = None

        # Structure
        self.actions: list[dict[str, str]] | None = None
        self.bind: dict | None = None
        self.control: dict | None = None
        self.instance: dict | None = None
        self.media: dict | None = None
        self.type: str | None = None

        # Common / template settings
        self.choice_filter: str | None = None
        self.default: str | None = None
        self.guidance_hint: str | dict | None = None
        self.hint: str | dict | None = None
        # constraint_message, required_message are placed in bind dict.
        self.parameters: dict | None = None
        self.query: str | None = None
        self.trigger: str | None = None

        # SMS / compact settings
        self.sms_field: str | None = None

        qtd = kwargs.pop("question_type_dictionary", QUESTION_TYPE_DICT)
        type_arg = kwargs.get("type")
        if type_arg not in qtd:
            raise PyXFormError(f"Unknown question type '{type_arg}'.")

        # Keeping original qtd_kwargs is only needed if output of QTD data is not
        # acceptable in to_json_dict() i.e. to exclude default bind/control values.
        self._qtd_defaults = qtd.get(type_arg)
        qtd_kwargs = None
        for k, v in self._qtd_defaults.items():
            if isinstance(v, dict):
                template = v.copy()
                if k in kwargs:
                    template.update(kwargs[k])
                    if qtd_kwargs is None:
                        qtd_kwargs = {}
                    qtd_kwargs[k] = kwargs[k]
                kwargs[k] = template
            elif k not in kwargs:
                kwargs[k] = v

        if qtd_kwargs:
            self._qtd_kwargs = qtd_kwargs

        if fields is None:
            fields = QUESTION_EXTRA_FIELDS
        else:
            fields = chain(QUESTION_EXTRA_FIELDS, fields)
        super().__init__(fields=fields, **kwargs)

    def xml_instance(self, survey: "Survey", **kwargs):
        if self.default and not default_is_dynamic(self.default, self.type):
            result = node(self.name, str(self.default))
        else:
            result = node(self.name)
        attributes = self.instance
        if attributes:
            for k, v in attributes.items():
                result.setAttribute(k, survey.insert_xpaths(text=v, context=self))
        return result

    def xml_control(self, survey: "Survey"):
        if self.type == "calculate" or (
            ((self.bind is not None and "calculate" in self.bind) or self.trigger)
            and not (self.label or self.hint)
        ):
            nested_setvalues = survey.setvalues_by_triggering_ref.get(self.name)
            if nested_setvalues:
                for setvalue in nested_setvalues:
                    msg = (
                        f"The question ${{{self.name}}} is not user-visible "
                        "so it can't be used as a calculation trigger for "
                        f"question ${{{setvalue[0]}}}."
                    )
                    raise PyXFormError(msg)
            return None

        xml_node = self.build_xml(survey=survey)

        if xml_node:
            setvalue = survey.setvalues_by_triggering_ref.get(self.name)
            setvalue_action = action.ActionLibrary.setvalue_value_changed.value
            if setvalue:
                for question_name, value in setvalue:
                    xml_node.appendChild(
                        action.ACTION_CLASSES[setvalue_action.name](
                            ref=survey.get_element_by_name(question_name).get_xpath(),
                            event=action.Event(setvalue_action.event),
                            value=survey.insert_xpaths(text=value, context=self),
                        ).node()
                    )

            setgeopoint = survey.setgeopoint_by_triggering_ref.get(self.name)
            setgeopoint_action = action.ActionLibrary.odk_setgeopoint_value_changed.value
            if setgeopoint:
                for question_name, value in setgeopoint:
                    xml_node.appendChild(
                        action.ACTION_CLASSES[setgeopoint_action.name](
                            ref=survey.get_element_by_name(question_name).get_xpath(),
                            event=action.Event(setgeopoint_action.event),
                            value=survey.insert_xpaths(text=value, context=self),
                        ).node()
                    )

        return xml_node

    def xml_actions(self, survey: "Survey", in_repeat: bool = False):
        """
        Return the action(s) for this survey element.
        """
        action_fields = {"name", "event", "value"}
        if self.actions:
            for _action in self.actions:
                event = action.Event(_action["event"])
                if (not in_repeat and event == action.Event.ODK_NEW_REPEAT.value) or (
                    in_repeat and event != action.Event.ODK_NEW_REPEAT
                ):
                    continue

                if self._dynamic_default is True or (
                    self.default and default_is_dynamic(self.default, self.type)
                ):
                    value = survey.insert_xpaths(text=self.default, context=self)
                elif self.default:
                    value = self.default
                else:
                    value = _action.get("value")

                yield action.ACTION_CLASSES[_action["name"]](
                    ref=self.get_xpath(),
                    event=event,
                    value=value,
                    **{k: v for k, v in _action.items() if k not in action_fields},
                ).node()

    def _build_xml(self, survey: "Survey") -> DetachableElement | None:
        """
        Initial control node result for further processing depending on Question type.
        """
        control_dict = self.control
        result = node(
            control_dict["tag"],
            *self.xml_label_and_hint(survey=survey),
            ref=self.get_xpath(),
        )
        # Resolve field references in attributes
        for k, v in control_dict.items():
            # "tag" is from the question type dict so it can't include references. Also,
            # if it did include references, then the node element name would be invalid.
            if k != "tag":
                result.setAttribute(k, survey.insert_xpaths(text=v, context=self))
        return result

    def build_xml(self, survey: "Survey") -> DetachableElement | None:
        return None

    def to_json_dict(self, delete_keys: Iterable[str] | None = None) -> dict:
        to_delete = (k for k in self.get_slot_names() if k.startswith("_"))
        if self._qtd_defaults:
            to_delete = chain(to_delete, self._qtd_defaults)
        if delete_keys is not None:
            to_delete = chain(to_delete, delete_keys)
        result = super().to_json_dict(delete_keys=to_delete)
        if self._qtd_kwargs:
            for k, v in self._qtd_kwargs.items():
                if v:
                    result[k] = v
        return result


class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """

    def build_xml(self, survey: "Survey"):
        result = self._build_xml(survey=survey)

        # Input types are used for selects with external choices sheets.
        if self.query:
            choice_filter = self.choice_filter
            if choice_filter:
                pred = survey.insert_xpaths(
                    text=choice_filter, context=self, use_current=True
                )
                query = f"""instance('{self.query}')/root/item[{pred}]"""
            else:
                query = f"""instance('{self.query}')/root/item"""
            result.setAttribute("query", query)
        return result


class TriggerQuestion(Question):
    def build_xml(self, survey: "Survey"):
        return self._build_xml(survey=survey)


class UploadQuestion(Question):
    def build_xml(self, survey: "Survey"):
        return self._build_xml(survey=survey)


class Option(SurveyElement):
    __slots__ = OPTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return OPTION_FIELDS

    def __init__(
        self,
        name: str,
        label: str | dict | None = None,
        media: dict | None = None,
        sms_option: str | None = None,
        **kwargs,
    ):
        self._choice_itext_ref: str | None = None
        self.media: dict | None = media
        self.sms_option: str | None = sms_option

        super().__init__(name=name, label=label, **kwargs)

    def validate(self):
        pass

    def xml_control(self, survey: "Survey"):
        raise NotImplementedError()

    def to_json_dict(self, delete_keys: Iterable[str] | None = None) -> dict:
        to_delete = (k for k in self.get_slot_names() if k.startswith("_"))
        if delete_keys is not None:
            to_delete = chain(to_delete, delete_keys)
        return super().to_json_dict(delete_keys=to_delete)


class Itemset:
    """Itemset details and metadata detection."""

    __slots__ = ("name", "options", "requires_itext", "used_by_search")

    def __init__(self, name: str, choices: Iterable[dict]):
        self.requires_itext: bool = False
        self.used_by_search: bool = False
        self.name: str = name
        self.options: tuple[Option, ...] = tuple(o for o in self.get_options(choices))

    def get_options(self, choices: Iterable[dict]) -> Generator[Option, None, None]:
        requires_itext = False
        for c in choices:
            option = Option(**c)
            if not requires_itext:
                # Media: dict of image, audio, etc. Defaults to None.
                if option.media:
                    requires_itext = True
                else:
                    choice_label = option.label
                    # Multi-language: dict of labels etc per language. Can be just a string.
                    if isinstance(choice_label, dict):
                        requires_itext = True
                    # Dynamic label: string contains a pyxform reference.
                    elif choice_label and has_pyxform_reference(choice_label):
                        requires_itext = True
            yield option
        self.requires_itext = requires_itext


class MultipleChoiceQuestion(Question):
    __slots__ = SELECT_QUESTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return SELECT_QUESTION_FIELDS

    def __init__(
        self, itemset: str | None = None, list_name: str | None = None, **kwargs
    ):
        if not itemset and not list_name:
            raise PyXFormError(
                "Arguments 'itemset' and 'list_name' must not both be None or empty."
            )

        # Structure
        self.choices: Itemset | None = None
        self.itemset: str | None = itemset
        self.list_name: str | None = list_name

        choices = kwargs.pop(constants.CHOICES, None)
        if isinstance(choices, Itemset):
            self.choices = choices
        super().__init__(**kwargs)

    def build_xml(self, survey: "Survey"):
        if self.bind["type"] not in {"string", "odk:rank"}:
            raise PyXFormError("""Invalid value for `self.bind["type"]`.""")

        result = self._build_xml(survey=survey)
        choices = None
        if survey.choices:
            choices = survey.choices.get(self.itemset, None)
        if not choices:
            choices = self.choices

        # itemset are only supposed to be strings,
        # check to prevent the rare dicts that show up
        if self.itemset and isinstance(self.itemset, str):
            itemset, file_extension = os.path.splitext(self.itemset)

            if file_extension == ".geojson":
                itemset_value_ref = EXTERNAL_CHOICES_ITEMSET_REF_VALUE_GEOJSON
                itemset_label_ref = EXTERNAL_CHOICES_ITEMSET_REF_LABEL_GEOJSON
            else:
                itemset_value_ref = EXTERNAL_CHOICES_ITEMSET_REF_VALUE
                itemset_label_ref = EXTERNAL_CHOICES_ITEMSET_REF_LABEL
            if self.parameters is not None:
                itemset_value_ref = self.parameters.get("value", itemset_value_ref)
                itemset_label_ref = self.parameters.get("label", itemset_label_ref)

            is_previous_question = has_pyxform_reference(self.itemset)

            if file_extension in EXTERNAL_INSTANCE_EXTENSIONS:
                pass
            elif choices and choices.requires_itext:
                itemset = self.itemset
                itemset_label_ref = "jr:itext(itextId)"
            else:
                itemset = self.itemset

            choice_filter = self.choice_filter
            if choice_filter:
                choice_filter = survey.insert_xpaths(
                    text=choice_filter,
                    context=self,
                    use_current=True,
                    reference_parent=is_previous_question,
                )
            if is_previous_question:
                path = (
                    survey.insert_xpaths(
                        text=self.itemset, context=self, reference_parent=True
                    )
                    .strip()
                    .split("/")
                )
                nodeset = "/".join(path[:-1])
                itemset_value_ref = path[-1]
                itemset_label_ref = path[-1]
                if choice_filter:
                    choice_filter = choice_filter.replace(
                        f"current()/{nodeset}", "."
                    ).replace(nodeset, ".")
                else:
                    # Choices must have a value. Filter out repeat instances without
                    # an answer for the linked question
                    name = path[-1]
                    choice_filter = f"./{name} != ''"
            else:
                nodeset = f"instance('{itemset}')/root/item"

            if choice_filter:
                nodeset += f"[{choice_filter}]"

            if self.parameters:
                params = self.parameters

                if "randomize" in params and params["randomize"] == "true":
                    nodeset = f"randomize({nodeset}"

                    if "seed" in params:
                        seed = maybe_strip(
                            survey.insert_xpaths(text=params["seed"], context=self)
                        )
                        nodeset = f"{nodeset}, {seed}"

                    nodeset += ")"

            result.appendChild(
                node(
                    "itemset",
                    node("value", ref=itemset_value_ref),
                    node("label", ref=itemset_label_ref),
                    nodeset=nodeset,
                )
            )
        elif choices:
            # Options processing specific to XLSForms using the "search()" function.
            # The _choice_itext_ref is prepared by Survey._redirect_is_search_itext.
            if choices.used_by_search:
                for option in choices.options:
                    if choices.requires_itext:
                        label_node = node("label", ref=option._choice_itext_ref)
                    elif self.label:
                        label, output_inserted = survey.insert_output_values(
                            option.label, option
                        )
                        label_node = node("label", label, toParseString=output_inserted)
                    else:
                        label_node = node("label")
                    result.appendChild(
                        node("item", label_node, node("value", option.name))
                    )

        return result


class Tag(SurveyElement):
    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return SURVEY_ELEMENT_FIELDS

    def xml(self, survey: "Survey"):
        return node("tag", self.xml_label(survey=survey), key=self.name)

    def validate(self):
        pass

    def xml_control(self, survey: "Survey"):
        raise NotImplementedError()


class OsmUploadQuestion(UploadQuestion):
    __slots__ = OSM_QUESTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return OSM_QUESTION_FIELDS

    def __init__(self, **kwargs):
        self.children: tuple[Tag, ...] | None = None

        choices = combine_lists(
            a=kwargs.pop("tags", None), b=kwargs.pop(constants.CHILDREN, None)
        )
        if choices:
            self.children = tuple(Tag(**c) for c in choices)

        super().__init__(**kwargs)

    def iter_descendants(
        self,
        condition: Callable[["SurveyElement"], bool] | None = None,
        iter_into_section_items: bool = False,
    ) -> Generator["SurveyElement", None, None]:
        if condition is None:
            yield self
        elif condition(self):
            yield self
        if iter_into_section_items and self.children:
            for e in self.children:
                yield from e.iter_descendants(
                    condition=condition,
                    iter_into_section_items=iter_into_section_items,
                )

    def build_xml(self, survey: "Survey"):
        result = self._build_xml(survey=survey)
        if self.children:
            for osm_tag in self.children:
                result.appendChild(osm_tag.xml(survey=survey))
        return result


class RangeQuestion(Question):
    def build_xml(self, survey: "Survey"):
        result = self._build_xml(survey=survey)
        params = self.parameters
        if params:
            for k, v in params.items():
                result.setAttribute(k, v)
        return result
