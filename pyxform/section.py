"""
Section survey element module.
"""

from collections.abc import Generator, Iterable
from itertools import chain
from typing import TYPE_CHECKING

from pyxform import constants
from pyxform.errors import PyXFormError
from pyxform.external_instance import ExternalInstance
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS, SurveyElement
from pyxform.utils import DetachableElement, node

if TYPE_CHECKING:
    from pyxform.question import Question
    from pyxform.survey import Survey


SECTION_EXTRA_FIELDS = (
    constants.BIND,
    constants.CHILDREN,
    constants.CONTROL,
    constants.HINT,
    constants.MEDIA,
    constants.TYPE,
    "instance",
    "flat",
    "sms_field",
)
SECTION_FIELDS = (*SURVEY_ELEMENT_FIELDS, *SECTION_EXTRA_FIELDS)


class Section(SurveyElement):
    __slots__ = SECTION_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return SECTION_FIELDS

    def __init__(
        self,
        name: str,
        type: str,
        label: str | dict | None = None,
        hint: str | dict | None = None,
        bind: dict | None = None,
        control: dict | None = None,
        instance: dict | None = None,
        media: dict | None = None,
        flat: bool | None = None,
        sms_field: str | None = None,
        fields: tuple[str, ...] | None = None,
        **kwargs,
    ):
        # Structure
        self.bind: dict | None = bind
        self.children: list[Section | Question] | None = None
        self.control: dict | None = control
        # instance is for custom instance attrs from survey e.g. instance::abc:xyz
        self.instance: dict | None = instance
        # TODO: is media valid for groups? No tests for it, but it behaves like Questions.
        self.media: dict | None = media
        self.type: str | None = type

        # Group settings are generally put in bind/control dicts.
        self.hint: str | dict | None = hint
        self.flat: bool | None = flat
        self.sms_field: str | None = sms_field

        # Recursively creating child objects currently handled by the builder module.
        kwargs.pop(constants.CHILDREN, None)
        super().__init__(name=name, label=label, fields=fields, **kwargs)

    def validate(self):
        super().validate()
        for element in self.children:
            element.validate()
        self._validate_uniqueness_of_element_names()

    # there's a stronger test of this when creating the xpath
    # dictionary for a survey.
    def _validate_uniqueness_of_element_names(self):
        element_slugs = set()
        for element in self.children:
            elem_lower = element.name.lower()
            if elem_lower in element_slugs:
                raise PyXFormError(
                    f"There are more than one survey elements named '{elem_lower}' "
                    f"(case-insensitive) in the section named '{self.name}'."
                )
            element_slugs.add(elem_lower)

    def xml_instance(self, survey: "Survey", **kwargs):
        """
        Creates an xml representation of the section
        """
        append_template = kwargs.pop("append_template", False)

        attributes = {}
        attributes.update(kwargs)
        if self.instance:
            attributes.update(self.instance)
        # Resolve field references in attributes
        for key, value in attributes.items():
            attributes[key] = survey.insert_xpaths(value, self)
        result = node(self.name, **attributes)

        for child in self.children:
            repeating_template = None
            if hasattr(child, "flat") and child.get("flat"):
                for grandchild in child.xml_instance_array(survey=survey):
                    result.appendChild(grandchild)
            elif isinstance(child, ExternalInstance):
                continue
            else:
                if isinstance(child, RepeatingSection) and not append_template:
                    append_template = not append_template
                    repeating_template = child.generate_repeating_template(survey=survey)
                result.appendChild(
                    child.xml_instance(survey=survey, append_template=append_template)
                )
            if append_template and repeating_template:
                append_template = not append_template
                result.insertBefore(repeating_template, result._get_lastChild())
        return result

    def generate_repeating_template(self, survey: "Survey", **kwargs):
        attributes = {"jr:template": ""}
        result = node(self.name, **attributes)
        for child in self.children:
            if isinstance(child, RepeatingSection):
                result.appendChild(child.template_instance(survey=survey))
            else:
                result.appendChild(child.xml_instance(survey=survey))
        return result

    def xml_instance_array(self, survey: "Survey"):
        """
        This method is used for generating flat instances.
        """
        for child in self.children:
            if hasattr(child, "flat") and child.get("flat"):
                yield from child.xml_instance_array(survey=survey)
            else:
                yield child.xml_instance(survey=survey)

    def xml_control(self, survey: "Survey"):
        """
        Ideally, we'll have groups up and rolling soon, but for now
        let's just yield controls from all the children of this section
        """
        for e in self.children:
            control = e.xml_control(survey=survey)
            if control is not None:
                yield control


class RepeatingSection(Section):
    def xml_control(self, survey: "Survey"):
        """
        <group>
        <label>Fav Color</label>
        <repeat nodeset="fav-color">
          <select1 ref=".">
            <label ref="jr:itext('fav')" />
            <item><label ref="jr:itext('red')" /><value>red</value></item>
            <item><label ref="jr:itext('green')" /><value>green</value></item>
            <item><label ref="jr:itext('blue')" /><value>blue</value></item>
          </select1>
        </repeat>
        </group>
        """
        # Resolve field references in attributes
        if self.control:
            control_dict = {
                key: survey.insert_xpaths(value, self)
                for key, value in self.control.items()
            }
            repeat_node = node("repeat", nodeset=self.get_xpath(), **control_dict)
        else:
            repeat_node = node("repeat", nodeset=self.get_xpath())

        for n in Section.xml_control(self, survey=survey):
            repeat_node.appendChild(n)

        for setvalue_node in self._dynamic_defaults_helper(current=self, survey=survey):
            repeat_node.appendChild(setvalue_node)

        label = self.xml_label(survey=survey)
        if label:
            return node("group", label, repeat_node, ref=self.get_xpath())
        if self.control:
            return node("group", repeat_node, ref=self.get_xpath(), **self.control)
        else:
            return node("group", repeat_node, ref=self.get_xpath())

    # Get setvalue nodes for all descendants of this repeat that have dynamic defaults and aren't nested in other repeats.
    def _dynamic_defaults_helper(
        self, current: "Section", survey: "Survey"
    ) -> Generator[DetachableElement, None, None]:
        if not isinstance(current, Section):
            return
        for e in current.children:
            if e.type != "repeat":  # let nested repeats handle their own defaults
                dynamic_default = e.get_setvalue_node_for_dynamic_default(
                    in_repeat=True, survey=survey
                )
                if dynamic_default:
                    yield dynamic_default
                yield from self._dynamic_defaults_helper(current=e, survey=survey)

    # I'm anal about matching function signatures when overriding a function,
    # but there's no reason for kwargs to be an argument
    def template_instance(self, survey: "Survey", **kwargs):
        return super().generate_repeating_template(survey=survey, **kwargs)


class GroupedSection(Section):
    # I think this might be a better place for the table-list stuff, however it
    # doesn't allow for as good of validation as putting it in xls2json
    # def __init__(self, **kwargs):
    #        control = kwargs.get(u"control")
    #        if control:
    #            appearance = control.get(u"appearance")
    #            if appearance is u"table-list":
    #                print "HI"
    #                control[u"appearance"] = "field-list"
    #                kwargs["children"].insert(0, kwargs["children"][0])
    #        super(GroupedSection, self).__init__(kwargs)

    def xml_control(self, survey: "Survey"):
        if self.control and self.control.get("bodyless"):
            return None

        children = []

        # Resolve field references in attributes
        if self.control:
            attributes = {
                key: survey.insert_xpaths(value, self)
                for key, value in self.control.items()
            }
            if "appearance" in self.control:
                attributes["appearance"] = self.control["appearance"]
        else:
            attributes = {}

        if not self.get("flat"):
            attributes["ref"] = self.get_xpath()

        if "label" in self and self.label is not None and len(self["label"]) > 0:
            children.append(self.xml_label(survey=survey))
        for n in Section.xml_control(self, survey=survey):
            children.append(n)

        return node("group", *children, **attributes)

    def to_json_dict(self, delete_keys: Iterable[str] | None = None) -> dict:
        to_delete = (constants.BIND,)
        if delete_keys is not None:
            to_delete = chain(to_delete, delete_keys)
        result = super().to_json_dict(delete_keys=to_delete)
        # This is quite hacky, might want to think about a smart way
        # to approach this problem.
        result["type"] = "group"
        return result
