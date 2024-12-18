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
from pyxform.errors import PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS, SurveyElement
from pyxform.utils import (
    PYXFORM_REFERENCE_REGEX,
    DetachableElement,
    coalesce,
    combine_lists,
    default_is_dynamic,
    node,
)

if TYPE_CHECKING:
    from pyxform.survey import Survey


QUESTION_EXTRA_FIELDS = (
    "_itemset_dyn_label",
    "_itemset_has_media",
    "_itemset_multi_language",
    "_qtd_defaults",
    "_qtd_kwargs",
    "action",
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
    constants.CHILDREN,
    constants.ITEMSET,
    constants.LIST_NAME_U,
)
SELECT_QUESTION_FIELDS = (*QUESTION_FIELDS, *SELECT_QUESTION_EXTRA_FIELDS)

OSM_QUESTION_EXTRA_FIELDS = (constants.CHILDREN,)
OSM_QUESTION_FIELDS = (*QUESTION_FIELDS, *SELECT_QUESTION_EXTRA_FIELDS)

OPTION_EXTRA_FIELDS = (
    "_choice_itext_id",
    constants.MEDIA,
    "sms_option",
)
OPTION_FIELDS = (*SURVEY_ELEMENT_FIELDS, *OPTION_EXTRA_FIELDS)

TAG_EXTRA_FIELDS = (constants.CHILDREN,)
TAG_FIELDS = (*SURVEY_ELEMENT_FIELDS, *TAG_EXTRA_FIELDS)


class Question(SurveyElement):
    __slots__ = QUESTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return QUESTION_FIELDS

    def __init__(self, fields: tuple[str, ...] | None = None, **kwargs):
        # Internals
        self._qtd_defaults: dict | None = None
        self._qtd_kwargs: dict | None = None

        # Structure
        self.action: dict[str, str] | None = None
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
        default_type = qtd.get(type_arg)
        if default_type is None:
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

    def validate(self):
        SurveyElement.validate(self)

        # make sure that the type of this question exists in the
        # question type dictionary.
        if self.type not in QUESTION_TYPE_DICT:
            raise PyXFormError(f"Unknown question type '{self.type}'.")

    def xml_instance(self, survey: "Survey", **kwargs):
        attributes = self.instance
        if attributes is None:
            attributes = {}
        else:
            for key, value in attributes.items():
                attributes[key] = survey.insert_xpaths(value, self)

        if self.default and not default_is_dynamic(self.default, self.type):
            return node(self.name, str(self.default), **attributes)
        return node(self.name, **attributes)

    def xml_control(self, survey: "Survey"):
        if self.type == "calculate" or (
            (self.bind is not None and "calculate" in self.bind or self.trigger)
            and not (self.label or self.hint)
        ):
            nested_setvalues = survey.get_trigger_values_for_question_name(
                self.name, "setvalue"
            )
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
            # Get nested setvalue and setgeopoint items
            setvalue_items = survey.get_trigger_values_for_question_name(
                self.name, "setvalue"
            )
            setgeopoint_items = survey.get_trigger_values_for_question_name(
                self.name, "setgeopoint"
            )

            # Only call nest_set_nodes if the respective nested items list is not empty
            if setvalue_items:
                self.nest_set_nodes(survey, xml_node, "setvalue", setvalue_items)
            if setgeopoint_items:
                self.nest_set_nodes(
                    survey, xml_node, "odk:setgeopoint", setgeopoint_items
                )

        return xml_node

    def xml_action(self):
        """
        Return the action for this survey element.
        """
        if self.action:
            return node(
                self.action["name"],
                ref=self.get_xpath(),
                **{k: v for k, v in self.action.items() if k != "name"},
            )

        return None

    def nest_set_nodes(self, survey, xml_node, tag, nested_items):
        for item in nested_items:
            node_attrs = {
                "ref": survey.insert_xpaths(f"${{{item[0]}}}", survey).strip(),
                "event": "xforms-value-changed",
            }
            if item[1]:
                node_attrs["value"] = survey.insert_xpaths(item[1], self)
            set_node = node(tag, **node_attrs)
            xml_node.appendChild(set_node)

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
        control_dict = self.control
        label_and_hint = self.xml_label_and_hint(survey=survey)
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()

        result = node(**control_dict)
        if label_and_hint:
            for element in self.xml_label_and_hint(survey=survey):
                if element:
                    result.appendChild(element)

        # Input types are used for selects with external choices sheets.
        if self.query:
            choice_filter = self.choice_filter
            if choice_filter is not None:
                pred = survey.insert_xpaths(choice_filter, self, True)
                query = f"""instance('{self.query}')/root/item[{pred}]"""
            else:
                query = f"""instance('{self.query}')/root/item"""
            result.setAttribute("query", query)
        return result


class TriggerQuestion(Question):
    def build_xml(self, survey: "Survey"):
        control_dict = self.control
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()
        return node("trigger", *self.xml_label_and_hint(survey=survey), **control_dict)


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.control["mediatype"]

    def build_xml(self, survey: "Survey"):
        control_dict = self.control
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()
        control_dict["mediatype"] = self._get_media_type()
        return node("upload", *self.xml_label_and_hint(survey=survey), **control_dict)


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
        self._choice_itext_id: str | None = None
        self.media: dict | None = media
        self.sms_option: str | None = sms_option

        super().__init__(name=name, label=label, **kwargs)

    def xml_value(self):
        return node("value", self.name)

    def xml(self, survey: "Survey"):
        item = node("item")
        item.appendChild(self.xml_label(survey=survey))
        item.appendChild(self.xml_value())

        return item

    def validate(self):
        pass

    def xml_control(self, survey: "Survey"):
        raise NotImplementedError()

    def _translation_path(self, display_element):
        if self._choice_itext_id is not None:
            return self._choice_itext_id
        return super()._translation_path(display_element=display_element)

    def to_json_dict(self, delete_keys: Iterable[str] | None = None) -> dict:
        to_delete = (k for k in self.get_slot_names() if k.startswith("_"))
        if delete_keys is not None:
            to_delete = chain(to_delete, delete_keys)
        return super().to_json_dict(delete_keys=to_delete)


class MultipleChoiceQuestion(Question):
    __slots__ = SELECT_QUESTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return SELECT_QUESTION_FIELDS

    def __init__(
        self, itemset: str | None = None, list_name: str | None = None, **kwargs
    ):
        # Internals
        self._itemset_dyn_label: bool = False
        self._itemset_has_media: bool = False
        self._itemset_multi_language: bool = False

        # Structure
        self.children: tuple[Option, ...] | None = None
        self.itemset: str | None = itemset
        self.list_name: str | None = list_name

        # Notice that choices can be specified under choices or children.
        # I'm going to try to stick to just choices.
        # Aliases in the json format will make it more difficult
        # to use going forward.
        kw_choices = kwargs.pop(constants.CHOICES, None)
        kw_children = kwargs.pop(constants.CHILDREN, None)
        choices = coalesce(kw_choices, kw_children)
        if isinstance(choices, tuple) and isinstance(next(iter(choices)), Option):
            self.children = choices
        elif choices:
            self.children = tuple(
                Option(**c) for c in combine_lists(kw_choices, kw_children)
            )
        super().__init__(**kwargs)

    def validate(self):
        Question.validate(self)
        if self.children:
            for child in self.children:
                child.validate()

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
        if self.bind["type"] not in {"string", "odk:rank"}:
            raise PyXFormError("""Invalid value for `self.bind["type"]`.""")

        # Resolve field references in attributes
        control_dict = {
            key: survey.insert_xpaths(value, self) for key, value in self.control.items()
        }
        control_dict["ref"] = self.get_xpath()

        result = node(**control_dict)
        for element in self.xml_label_and_hint(survey=survey):
            if element:
                result.appendChild(element)

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

            multi_language = self._itemset_multi_language
            has_media = self._itemset_has_media
            has_dyn_label = self._itemset_dyn_label
            is_previous_question = bool(PYXFORM_REFERENCE_REGEX.search(self.itemset))

            if file_extension in EXTERNAL_INSTANCE_EXTENSIONS:
                pass
            elif not multi_language and not has_media and not has_dyn_label:
                itemset = self.itemset
            else:
                itemset = self.itemset
                itemset_label_ref = "jr:itext(itextId)"

            choice_filter = self.choice_filter
            if choice_filter is not None:
                choice_filter = survey.insert_xpaths(
                    choice_filter, self, True, is_previous_question
                )
            if is_previous_question:
                path = (
                    survey.insert_xpaths(self.itemset, self, reference_parent=True)
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
                        if params["seed"].startswith("${"):
                            seed = survey.insert_xpaths(params["seed"], self).strip()
                            nodeset = f"{nodeset}, {seed}"
                        else:
                            nodeset = f"""{nodeset}, {params["seed"]}"""

                    nodeset += ")"

            itemset_children = [
                node("value", ref=itemset_value_ref),
                node("label", ref=itemset_label_ref),
            ]
            result.appendChild(node("itemset", *itemset_children, nodeset=nodeset))
        elif self.children:
            for child in self.children:
                result.appendChild(child.xml(survey=survey))

        return result


class Tag(SurveyElement):
    __slots__ = TAG_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return TAG_FIELDS

    def __init__(self, name: str, label: str | dict | None = None, **kwargs):
        self.children: tuple[Option, ...] | None = None

        kw_choices = kwargs.pop(constants.CHOICES, None)
        kw_children = kwargs.pop(constants.CHILDREN, None)
        choices = coalesce(kw_choices, kw_children)
        if isinstance(choices, tuple) and isinstance(next(iter(choices)), Option):
            self.children = choices
        elif choices:
            self.children = tuple(
                Option(**c) for c in combine_lists(kw_choices, kw_children)
            )
        super().__init__(name=name, label=label, **kwargs)

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

    def xml(self, survey: "Survey"):
        result = node("tag", key=self.name)
        result.appendChild(self.xml_label(survey=survey))
        if self.children:
            for choice in self.children:
                result.appendChild(choice.xml(survey=survey))

        return result

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
        self.children: tuple[Option, ...] | None = None

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
        control_dict = self.control
        control_dict["ref"] = self.get_xpath()
        control_dict["mediatype"] = self._get_media_type()
        result = node("upload", *self.xml_label_and_hint(survey=survey), **control_dict)

        if self.children:
            for osm_tag in self.children:
                result.appendChild(osm_tag.xml(survey=survey))

        return result


class RangeQuestion(Question):
    def build_xml(self, survey: "Survey"):
        control_dict = self.control
        label_and_hint = self.xml_label_and_hint(survey=survey)
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()
        params = self.parameters
        if params:
            control_dict.update(params)
        result = node(**control_dict)
        if label_and_hint:
            for element in self.xml_label_and_hint(survey=survey):
                result.appendChild(element)

        return result
