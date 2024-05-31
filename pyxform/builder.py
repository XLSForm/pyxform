"""
Survey builder functionality.
"""

import copy
import os
import re
from typing import TYPE_CHECKING, Any, Union

from pyxform import constants as const
from pyxform import file_utils, utils
from pyxform.entities.entity_declaration import EntityDeclaration
from pyxform.errors import PyXFormError
from pyxform.external_instance import ExternalInstance
from pyxform.question import (
    InputQuestion,
    MultipleChoiceQuestion,
    OsmUploadQuestion,
    Question,
    RangeQuestion,
    TriggerQuestion,
    UploadQuestion,
)
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.section import GroupedSection, RepeatingSection
from pyxform.survey import Survey
from pyxform.xls2json import SurveyReader

if TYPE_CHECKING:
    from pyxform.survey_element import SurveyElement

OR_OTHER_CHOICE = {
    const.NAME: "other",
    const.LABEL: "Other",
}
QUESTION_CLASSES = {
    "": Question,
    "action": Question,
    "input": InputQuestion,
    "odk:rank": MultipleChoiceQuestion,
    "osm": OsmUploadQuestion,
    "range": RangeQuestion,
    "select": MultipleChoiceQuestion,
    "select1": MultipleChoiceQuestion,
    "trigger": TriggerQuestion,
    "upload": UploadQuestion,
}
SECTION_CLASSES = {
    const.GROUP: GroupedSection,
    const.REPEAT: RepeatingSection,
    const.SURVEY: Survey,
}


def copy_json_dict(json_dict):
    """
    Returns a deep copy of the input json_dict
    """
    json_dict_copy = None
    items = None

    if isinstance(json_dict, list):
        json_dict_copy = [None] * len(json_dict)
        items = enumerate(json_dict)
    elif isinstance(json_dict, dict):
        json_dict_copy = {}
        items = json_dict.items()

    for key, value in items:
        if isinstance(value, dict | list):
            json_dict_copy[key] = copy_json_dict(value)
        else:
            json_dict_copy[key] = value

    return json_dict_copy


class SurveyElementBuilder:
    def __init__(self, **kwargs):
        # I don't know why we would need an explicit none option for
        # select alls
        self._add_none_option = False
        self._sections: dict[str, dict] | None = None
        self.set_sections(kwargs.get("sections", {}))

        # dictionary of setvalue target and value tuple indexed by triggering element
        self.setvalues_by_triggering_ref = {}
        # For tracking survey-level choices while recursing through the survey.
        self._choices: dict[str, Any] = {}

    def set_sections(self, sections):
        """
        sections is a dict of python objects, a key in this dict is
        the name of the section and the value is a dict that can be
        used to create a whole survey.
        """
        if not isinstance(sections, dict):
            raise PyXFormError("""Invalid value for `sections`.""")
        self._sections = sections

    def create_survey_element_from_dict(
        self, d: dict[str, Any]
    ) -> Union["SurveyElement", list["SurveyElement"]]:
        """
        Convert from a nested python dictionary/array structure (a json dict I
        call it because it corresponds directly with a json object)
        to a survey object
        """
        if "add_none_option" in d:
            self._add_none_option = d["add_none_option"]

        if d[const.TYPE] in SECTION_CLASSES:
            if d[const.TYPE] == const.SURVEY:
                self._choices = copy.deepcopy(d.get(const.CHOICES, {}))

            section = self._create_section_from_dict(d)

            if d[const.TYPE] == const.SURVEY:
                section.setvalues_by_triggering_ref = self.setvalues_by_triggering_ref
                section.choices = self._choices

            return section
        elif d[const.TYPE] == const.LOOP:
            return self._create_loop_from_dict(d)
        elif d[const.TYPE] == "include":
            section_name = d[const.NAME]
            if section_name not in self._sections:
                raise PyXFormError(
                    "This section has not been included.",
                    section_name,
                    self._sections.keys(),
                )
            d = self._sections[section_name]
            full_survey = self.create_survey_element_from_dict(d)
            return full_survey.children
        elif d[const.TYPE] in ["xml-external", "csv-external"]:
            return ExternalInstance(**d)
        elif d[const.TYPE] == "entity":
            return EntityDeclaration(**d)
        else:
            self._save_trigger_as_setvalue_and_remove_calculate(d)

            return self._create_question_from_dict(
                d, copy_json_dict(QUESTION_TYPE_DICT), self._add_none_option
            )

    def _save_trigger_as_setvalue_and_remove_calculate(self, d):
        if "trigger" in d:
            triggering_ref = re.sub(r"\s+", "", d["trigger"])
            value = ""
            if const.BIND in d and "calculate" in d[const.BIND]:
                value = d[const.BIND]["calculate"]

            if triggering_ref in self.setvalues_by_triggering_ref:
                self.setvalues_by_triggering_ref[triggering_ref].append(
                    (d[const.NAME], value)
                )
            else:
                self.setvalues_by_triggering_ref[triggering_ref] = [
                    (d[const.NAME], value)
                ]

    @staticmethod
    def _create_question_from_dict(
        d: dict[str, Any],
        question_type_dictionary: dict[str, Any],
        add_none_option: bool = False,
    ) -> Question | list[Question]:
        question_type_str = d[const.TYPE]
        d_copy = d.copy()

        # TODO: Keep add none option?
        if add_none_option and question_type_str.startswith(const.SELECT_ALL_THAT_APPLY):
            SurveyElementBuilder._add_none_option_to_select_all_that_apply(d_copy)

        # Handle or_other on select type questions
        or_other_len = len(const.SELECT_OR_OTHER_SUFFIX)
        if question_type_str.endswith(const.SELECT_OR_OTHER_SUFFIX):
            question_type_str = question_type_str[: len(question_type_str) - or_other_len]
            d_copy[const.TYPE] = question_type_str
            SurveyElementBuilder._add_other_option_to_multiple_choice_question(d_copy)
            return [
                SurveyElementBuilder._create_question_from_dict(
                    d_copy, question_type_dictionary, add_none_option
                ),
                SurveyElementBuilder._create_specify_other_question_from_dict(d_copy),
            ]

        question_class = SurveyElementBuilder._get_question_class(
            question_type_str, question_type_dictionary
        )

        # todo: clean up this spaghetti code
        d_copy["question_type_dictionary"] = question_type_dictionary
        if question_class:
            return question_class(**d_copy)

        return []

    @staticmethod
    def _add_other_option_to_multiple_choice_question(d: dict[str, Any]) -> None:
        # ideally, we'd just be pulling from children
        choice_list = d.get(const.CHOICES, d.get(const.CHILDREN, []))
        if len(choice_list) <= 0:
            raise PyXFormError("There should be choices for this question.")
        if not any(c[const.NAME] == OR_OTHER_CHOICE[const.NAME] for c in choice_list):
            choice_list.append(SurveyElementBuilder._get_or_other_choice(choice_list))

    @staticmethod
    def _get_or_other_choice(
        choice_list: list[dict[str, Any]],
    ) -> dict[str, str | dict]:
        """
        If the choices have any translations, return an OR_OTHER choice for each lang.
        """
        if any(isinstance(c.get(const.LABEL), dict) for c in choice_list):
            langs = {
                lang
                for c in choice_list
                for lang in c[const.LABEL]
                if isinstance(c.get(const.LABEL), dict)
            }
            return {
                const.NAME: OR_OTHER_CHOICE[const.NAME],
                const.LABEL: {lang: OR_OTHER_CHOICE[const.LABEL] for lang in langs},
            }
        return OR_OTHER_CHOICE

    @staticmethod
    def _add_none_option_to_select_all_that_apply(d_copy):
        choice_list = d_copy.get(const.CHOICES, d_copy.get(const.CHILDREN, []))
        if len(choice_list) <= 0:
            raise PyXFormError("There should be choices for this question.")
        none_choice = {const.NAME: "none", const.LABEL: "None"}
        if none_choice not in choice_list:
            choice_list.append(none_choice)
            none_constraint = "(.='none' or not(selected(., 'none')))"
            if const.BIND not in d_copy:
                d_copy[const.BIND] = {}
            if "constraint" in d_copy[const.BIND]:
                d_copy[const.BIND]["constraint"] += " and " + none_constraint
            else:
                d_copy[const.BIND]["constraint"] = none_constraint

    @staticmethod
    def _get_question_class(question_type_str, question_type_dictionary):
        """
        Read the type string from the json format,
        and find what class it maps to going through
        type_dictionary -> QUESTION_CLASSES
        """
        question_type = question_type_dictionary.get(question_type_str, {})
        control_dict = question_type.get(const.CONTROL, {})
        control_tag = control_dict.get("tag", "")
        if control_tag == "upload" and control_dict.get("mediatype") == "osm/*":
            control_tag = "osm"

        return QUESTION_CLASSES[control_tag]

    @staticmethod
    def _create_specify_other_question_from_dict(d: dict[str, Any]) -> InputQuestion:
        kwargs = {
            const.TYPE: "text",
            const.NAME: f"{d[const.NAME]}_other",
            const.LABEL: "Specify other.",
            const.BIND: {"relevant": f"selected(../{d[const.NAME]}, 'other')"},
        }
        return InputQuestion(**kwargs)

    def _create_section_from_dict(self, d):
        d_copy = d.copy()
        children = d_copy.pop(const.CHILDREN, [])
        section_class = SECTION_CLASSES[d_copy[const.TYPE]]
        if d[const.TYPE] == const.SURVEY and const.TITLE not in d:
            d_copy[const.TITLE] = d[const.NAME]
        result = section_class(**d_copy)
        for child in children:
            # Deep copying the child is a hacky solution to the or_other bug.
            # I don't know why it works.
            # And I hope it doesn't break something else.
            # I think the good solution would be to rewrite this class.
            survey_element = self.create_survey_element_from_dict(copy.deepcopy(child))
            if child[const.TYPE].endswith(const.SELECT_OR_OTHER_SUFFIX):
                select_question = survey_element[0]
                itemset_choices = self._choices.get(select_question[const.ITEMSET], None)
                if (
                    itemset_choices is not None
                    and isinstance(itemset_choices, list)
                    and not any(
                        c[const.NAME] == OR_OTHER_CHOICE[const.NAME]
                        for c in itemset_choices
                    )
                ):
                    itemset_choices.append(self._get_or_other_choice(itemset_choices))
                # This is required for builder_tests.BuilderTests.test_loop to pass.
                self._add_other_option_to_multiple_choice_question(d=child)
            if survey_element:
                result.add_children(survey_element)

        return result

    def _create_loop_from_dict(self, d):
        """
        Takes a json_dict of "loop" type
        Returns a GroupedSection
        """
        d_copy = d.copy()
        children = d_copy.pop(const.CHILDREN, [])
        columns = d_copy.pop(const.COLUMNS, [])
        result = GroupedSection(**d_copy)

        # columns is a left over from when this was
        # create_table_from_dict, I will need to clean this up
        for column_dict in columns:
            # If this is a none option for a select all that apply
            # question then we should skip adding it to the result
            if column_dict[const.NAME] == "none":
                continue

            column = GroupedSection(**column_dict)
            for child in children:
                question_dict = self._name_and_label_substitutions(child, column_dict)
                question = self.create_survey_element_from_dict(question_dict)
                column.add_child(question)
            result.add_child(column)
        if result.name != "":
            return result

        # TODO: Verify that nothing breaks if this returns a list
        return result.children

    @staticmethod
    def _name_and_label_substitutions(question_template, column_headers):
        # if the label in column_headers has multiple languages setup a
        # dictionary by language to do substitutions.
        info_by_lang = {}
        if isinstance(column_headers[const.LABEL], dict):
            info_by_lang = {
                lang: {
                    const.NAME: column_headers[const.NAME],
                    const.LABEL: column_headers[const.LABEL][lang],
                }
                for lang in column_headers[const.LABEL].keys()
            }

        result = question_template.copy()
        for key in result.keys():
            if isinstance(result[key], str):
                result[key] %= column_headers
            elif isinstance(result[key], dict):
                result[key] = result[key].copy()
                for key2 in result[key].keys():
                    if isinstance(column_headers[const.LABEL], dict):
                        result[key][key2] %= info_by_lang.get(key2, column_headers)
                    else:
                        result[key][key2] %= column_headers
        return result

    def create_survey_element_from_json(self, str_or_path):
        d = utils.get_pyobj_from_json(str_or_path)
        return self.create_survey_element_from_dict(d)


def create_survey_element_from_dict(d, sections=None):
    """
    Creates a Survey from a dictionary in the format provided by SurveyReader
    """
    if sections is None:
        sections = {}
    builder = SurveyElementBuilder()
    builder.set_sections(sections)
    return builder.create_survey_element_from_dict(d)


def create_survey_element_from_json(str_or_path):
    d = utils.get_pyobj_from_json(str_or_path)
    return create_survey_element_from_dict(d)


def create_survey_from_xls(path_or_file, default_name=None):
    excel_reader = SurveyReader(path_or_file, default_name=default_name)
    d = excel_reader.to_json_dict()
    survey = create_survey_element_from_dict(d)
    if not survey.id_string:
        survey.id_string = excel_reader._name
    return survey


def create_survey(
    name_of_main_section: str | None = None,
    sections: dict[str, dict] | None = None,
    main_section: dict[str, Any] | None = None,
    id_string: str | None = None,
    title: str | None = None,
) -> Survey:
    """
    name_of_main_section -- a string key used to find the main section in the
                            sections dict if it is not supplied in the
                            main_section arg
    main_section -- a json dict that represents a survey
    sections -- a dictionary of sections that can be drawn from to build the
                survey
    This function uses the builder class to create and return a survey.
    """
    if sections is None:
        sections = {}
    if main_section is None:
        main_section = sections[name_of_main_section]
    builder = SurveyElementBuilder()
    builder.set_sections(sections)

    # assert name_of_main_section in sections, name_of_main_section
    if "id_string" not in main_section:
        main_section["id_string"] = (
            name_of_main_section if id_string is None else name_of_main_section
        )
    survey = builder.create_survey_element_from_dict(main_section)

    # not sure where to do this without repeating ourselves,
    # but it's needed to pass xls2xform tests
    # TODO: I would assume that the json-dict is valid
    # (i.e. that it has a id string), then throw an error here.
    #        We can set the id to whatever we want in xls2json.
    #        Although to be totally modular, maybe we do need to repeat a lot
    #       of the validation and setting default value stuff from xls2json
    if id_string is not None:
        survey.id_string = id_string

    if title is not None:
        survey.title = title
    return survey


def create_survey_from_path(path: str, include_directory: bool = False) -> Survey:
    """
    include_directory -- Switch to indicate that all the survey forms in the
                         same directory as the specified file should be read
                         so they can be included through include types.
    @see: create_survey
    """
    directory, file_name = os.path.split(path)
    if include_directory:
        main_section_name = file_utils._section_name(file_name)
        sections = file_utils.collect_compatible_files_in_directory(directory)
    else:
        main_section_name, section = file_utils.load_file_to_dict(path)
        sections = {main_section_name: section}
    return create_survey(name_of_main_section=main_section_name, sections=sections)
