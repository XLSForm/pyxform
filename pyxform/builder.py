"""
Survey builder functionality.
"""

import os
from collections import defaultdict
from typing import Any

from pyxform import constants as const
from pyxform import file_utils, utils
from pyxform.entities.entity_declaration import EntityDeclaration
from pyxform.errors import PyXFormError
from pyxform.external_instance import ExternalInstance
from pyxform.question import (
    InputQuestion,
    MultipleChoiceQuestion,
    Option,
    OsmUploadQuestion,
    Question,
    RangeQuestion,
    TriggerQuestion,
    UploadQuestion,
)
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.section import GroupedSection, RepeatingSection
from pyxform.survey import Survey
from pyxform.survey_element import SurveyElement
from pyxform.xls2json import SurveyReader

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


class SurveyElementBuilder:
    def __init__(self, **kwargs):
        # I don't know why we would need an explicit none option for
        # select alls
        self._add_none_option = False
        self._sections: dict[str, dict] | None = None
        self.set_sections(kwargs.get("sections", {}))

        # dictionary of setvalue target and value tuple indexed by triggering element
        self.setvalues_by_triggering_ref = defaultdict(list)
        # dictionary of setgeopoint target and value tuple indexed by triggering element
        self.setgeopoint_by_triggering_ref = defaultdict(list)

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
        self, d: dict[str, Any], choices: dict[str, tuple[Option, ...]] | None = None
    ) -> SurveyElement | list[SurveyElement]:
        """
        Convert from a nested python dictionary/array structure (a json dict I
        call it because it corresponds directly with a json object)
        to a survey object

        :param d: data to use for constructing SurveyElements.
        """
        if "add_none_option" in d:
            self._add_none_option = d["add_none_option"]

        if d[const.TYPE] in SECTION_CLASSES:
            section = self._create_section_from_dict(d=d, choices=choices)

            if d[const.TYPE] == const.SURVEY:
                section.setvalues_by_triggering_ref = self.setvalues_by_triggering_ref
                section.setgeopoint_by_triggering_ref = self.setgeopoint_by_triggering_ref

            return section
        elif d[const.TYPE] == const.LOOP:
            return self._create_loop_from_dict(d=d, choices=choices)
        elif d[const.TYPE] == "include":
            section_name = d[const.NAME]
            if section_name not in self._sections:
                raise PyXFormError(
                    "This section has not been included.",
                    section_name,
                    self._sections.keys(),
                )
            d = self._sections[section_name]
            full_survey = self.create_survey_element_from_dict(d=d, choices=choices)
            return full_survey.children
        elif d[const.TYPE] in {"xml-external", "csv-external"}:
            return ExternalInstance(**d)
        elif d[const.TYPE] == "entity":
            return EntityDeclaration(**d)
        else:
            self._save_trigger(d=d)
            return self._create_question_from_dict(
                d=d,
                question_type_dictionary=QUESTION_TYPE_DICT,
                add_none_option=self._add_none_option,
                choices=choices,
            )

    def _save_trigger(self, d: dict) -> None:
        if "trigger" in d:
            triggering_ref = d["trigger"].strip()
            value = ""
            if const.BIND in d and "calculate" in d[const.BIND]:
                value = d[const.BIND]["calculate"]
            question_ref = (d[const.NAME], value)
            if d[const.TYPE] == "background-geopoint":
                self.setgeopoint_by_triggering_ref[triggering_ref].append(question_ref)
            else:
                self.setvalues_by_triggering_ref[triggering_ref].append(question_ref)

    @staticmethod
    def _create_question_from_dict(
        d: dict[str, Any],
        question_type_dictionary: dict[str, Any],
        add_none_option: bool = False,
        choices: dict[str, tuple[Option, ...]] | None = None,
    ) -> Question | tuple[Question, ...]:
        question_type_str = d[const.TYPE]

        # TODO: Keep add none option?
        if add_none_option and question_type_str.startswith(const.SELECT_ALL_THAT_APPLY):
            SurveyElementBuilder._add_none_option_to_select_all_that_apply(d)

        question_class = SurveyElementBuilder._get_question_class(
            question_type_str, question_type_dictionary
        )

        if question_class:
            if const.CHOICES in d and choices:
                return question_class(
                    question_type_dictionary=question_type_dictionary,
                    choices=choices.get(d[const.ITEMSET], d[const.CHOICES]),
                    **{k: v for k, v in d.items() if k != const.CHOICES},
                )
            else:
                return question_class(
                    question_type_dictionary=question_type_dictionary, **d
                )

        return ()

    @staticmethod
    def _add_none_option_to_select_all_that_apply(d_copy):
        choice_list = d_copy.get(const.CHOICES, d_copy.get(const.CHILDREN, ()))
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
        control_tag = ""
        question_type = question_type_dictionary.get(question_type_str)
        if question_type:
            control_dict = question_type.get(const.CONTROL)
            if control_dict:
                control_tag = control_dict.get("tag")
                if control_tag == "upload" and control_dict.get("mediatype") == "osm/*":
                    control_tag = "osm"

        return QUESTION_CLASSES[control_tag]

    def _create_section_from_dict(
        self, d: dict[str, Any], choices: dict[str, tuple[Option, ...]] | None = None
    ) -> Survey | GroupedSection | RepeatingSection:
        children = d.get(const.CHILDREN)
        section_class = SECTION_CLASSES[d[const.TYPE]]
        if d[const.TYPE] == const.SURVEY and const.TITLE not in d:
            d[const.TITLE] = d[const.NAME]
        result = section_class(**d)
        if children:
            for child in children:
                if isinstance(result, Survey):
                    survey_element = self.create_survey_element_from_dict(
                        d=child, choices=result.choices
                    )
                else:
                    survey_element = self.create_survey_element_from_dict(
                        d=child, choices=choices
                    )
                result.add_children(survey_element)

        return result

    def _create_loop_from_dict(
        self, d: dict[str, Any], choices: dict[str, tuple[Option, ...]] | None = None
    ):
        """
        Takes a json_dict of "loop" type
        Returns a GroupedSection
        """
        children = d.get(const.CHILDREN)
        result = GroupedSection(**d)

        # columns is a left over from when this was
        # create_table_from_dict, I will need to clean this up
        for column_dict in d.get(const.COLUMNS, ()):
            # If this is a none option for a select all that apply
            # question then we should skip adding it to the result
            if column_dict[const.NAME] == "none":
                continue

            column = GroupedSection(type=const.GROUP, **column_dict)
            if children is not None:
                for child in children:
                    question_dict = self._name_and_label_substitutions(child, column_dict)
                    question = self.create_survey_element_from_dict(
                        d=question_dict, choices=choices
                    )
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
        info_by_lang = None
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
                    if info_by_lang and isinstance(column_headers[const.LABEL], dict):
                        result[key][key2] %= info_by_lang.get(key2, column_headers)
                    else:
                        result[key][key2] %= column_headers
        return result

    def create_survey_element_from_json(self, str_or_path):
        d = utils.get_pyobj_from_json(str_or_path)
        # Loading JSON creates a new dictionary structure so no need to re-copy.
        return self.create_survey_element_from_dict(d=d)


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
