"""
A Python script to convert excel files into JSON.
"""

import os
import re
import sys
from collections import Counter
from typing import IO, Any

from pyxform import aliases, constants
from pyxform.constants import (
    _MSG_SUPPRESS_SPELLING,
    EXTERNAL_INSTANCE_EXTENSIONS,
    ROW_FORMAT_STRING,
    XML_IDENTIFIER_ERROR_MESSAGE,
)
from pyxform.elements import action as action_module
from pyxform.entities.entities_parsing import (
    get_entity_declaration,
    validate_entity_repeat_target,
    validate_entity_saveto,
)
from pyxform.errors import Detail, PyXFormError
from pyxform.parsing.expression import is_xml_tag
from pyxform.parsing.sheet_headers import dealias_and_group_headers
from pyxform.question_type_dictionary import get_meta_group
from pyxform.utils import (
    coalesce,
    default_is_dynamic,
    print_pyobj_to_json,
)
from pyxform.validators.pyxform import parameters_generic, select_from_file, unique_names
from pyxform.validators.pyxform import question_types as qt
from pyxform.validators.pyxform.android_package_name import validate_android_package_name
from pyxform.validators.pyxform.choices import validate_and_clean_choices
from pyxform.validators.pyxform.pyxform_reference import (
    has_pyxform_reference,
    is_pyxform_reference,
    validate_pyxform_references_in_workbook,
)
from pyxform.validators.pyxform.sheet_misspellings import find_sheet_misspellings
from pyxform.validators.pyxform.translations_checks import SheetTranslations
from pyxform.xls2json_backends import DefinitionData, get_xlsform

RE_BEGIN_CONTROL = re.compile(
    r"^(?P<begin>begin)(\s|_)(?P<type>("
    + "|".join(aliases.control)
    + r"))( (over )?(?P<list_name>\S+))?$"
)
RE_END_CONTROL = re.compile(
    r"^(?P<end>end)(\s|_)(?P<type>(" + "|".join(aliases.control) + r"))$"
)
RE_SELECT = re.compile(
    r"^(?P<select_command>("
    + "|".join(aliases.select)
    + r")) (?P<list_name>\S+)"
    + "( (?P<specify_other>(or specify other|or_other|or other)))?$"
)
RE_OSM = re.compile(
    r"(?P<osm_command>(" + "|".join(aliases.osm) + r")) (?P<list_name>\S+)"
)
SURVEY_001 = Detail(
    name="Survey Sheet Unmatched Group/Repeat/Loop End",
    msg=(
        "[row : {row}] Unmatched 'end_{type}'. "
        "No matching 'begin_{type}' was found for the name '{name}'."
    ),
)
SURVEY_002 = Detail(
    name="Survey Sheet Unmatched Group/Repeat/Loop Begin",
    msg=(
        "[row : {row}] Unmatched 'begin_{type}'. "
        "No matching 'end_{type}' was found for the name '{name}'."
    ),
)


def dealias_types(dict_array):
    """
    Look at all the type values in a dict array and if any aliases are found,
    replace them with the name they map to.
    """
    for row in dict_array:
        found_type = row.get(constants.TYPE)
        if found_type in aliases._type_alias_map:
            row[constants.TYPE] = aliases._type_alias_map[found_type]
    return dict_array


def group_dictionaries_by_key(list_of_dicts, key, remove_key=True):
    """
    Takes a list of dictionaries and returns a
    dictionary of lists of dictionaries with the same value for the given key.
    The grouping key is removed by default.
    If the key is not in any dictionary an empty dict is returned.
    """
    dict_of_lists = {}
    for dicty in list_of_dicts:
        if key not in dicty:
            continue
        dicty_value = dicty[key]
        if remove_key:
            dicty.pop(key)
        if dicty_value in dict_of_lists:
            dict_of_lists[dicty_value].append(dicty)
        else:
            dict_of_lists[dicty_value] = [dicty]
    return dict_of_lists


def add_flat_annotations(prompt_list, parent_relevant="", name_prefix=""):
    """
    This is a helper function for generating flat instances
    for the benefit of ODK Tables.
    It makes the following modifications to the survey:
    X Renames prompts with their group name as a prefix
      (Decided against chaning the names because it breaks formulas)
      (However, there could be namespace collisions now.)
    - "and"s group relevance formulas onto that of their children.
    - Adds a flat property to groups
      The flat property is used in the json2xform code
    """
    for prompt in prompt_list:
        prompt_relevant = prompt.get("bind", {}).get("relevant", "")
        new_relevant = ""
        if parent_relevant != "":
            new_relevant += parent_relevant
            if prompt_relevant != "":
                new_relevant += " and (" + prompt_relevant + ")"
        elif prompt_relevant != "":
            new_relevant = prompt_relevant

        children = prompt.get(constants.CHILDREN)
        if children:
            prompt["flat"] = True
            add_flat_annotations(
                children, new_relevant, name_prefix + "_" + prompt["name"]
            )
        elif new_relevant != "":
            prompt["bind"] = prompt.get("bind", {})
            prompt["bind"]["relevant"] = new_relevant
            # if name_prefix != '':
            #    prompt['name'] = name_prefix + prompt['name']


def process_range_question_type(
    row: dict[str, Any], parameters: parameters_generic.PARAMETERS_TYPE
) -> dict[str, Any]:
    """
    Returns a new row that includes the Range parameters start, end and step.

    Raises PyXFormError when invalid range parameters are used.
    """
    new_dict = row.copy()
    parameters = parameters_generic.validate(
        parameters=parameters, allowed=("start", "end", "step")
    )
    parameters_map = {"start": "start", "end": "end", "step": "step"}
    defaults = {"start": "1", "end": "10", "step": "1"}

    # set defaults
    for key in parameters_map.values():
        if key not in parameters:
            parameters[key] = defaults[key]

    has_float = False
    try:
        # Check all parameters.
        for x in parameters.values():
            if float(x) and "." in str(x):
                has_float = True
    except ValueError as range_err:
        raise PyXFormError(
            "Range parameters 'start', 'end' or 'step' must all be numbers."
        ) from range_err
    else:
        # is integer by default, convert to decimal if it has any float values
        if has_float:
            new_dict["bind"] = new_dict.get("bind", {})
            new_dict["bind"].update({"type": "decimal"})

    new_dict["parameters"] = parameters

    return new_dict


def process_image_default(default_value):
    # prepend image files with the correct prefix, if they don't have it.
    image_jr_prefix = "jr://images/"
    if image_jr_prefix not in default_value:
        return "{}{}".format("jr://images/", default_value)
    return default_value


def add_choices_info_to_question(
    question: dict[str, Any],
    list_name: str,
    choices: dict[str, list],
    choice_filter: str,
    file_extension: str,
):
    """
    Add choices-related info to the question dict, e.g. itemset, list_name, choices, etc.

    :param question: A dict with question details.
    :param list_name: The choice list name for the question.
    :param choices: The available choices in the survey.
    :param choice_filter: The question's choice_filter, if any.
    :param file_extension: The question's external select file_extension, if any.
    :return: The updated question dict.
    """
    if choice_filter is None:
        choice_filter = ""
    if file_extension is None:
        file_extension = ""

    question[constants.ITEMSET] = list_name

    if choice_filter:
        # External selects e.g. type = "select_one_external city".
        if question[constants.TYPE] == constants.SELECT_ONE_EXTERNAL:
            question["query"] = list_name
        elif choices.get(list_name):
            # Reference to list name for data dictionary tools (ilri/odktools).
            question[constants.LIST_NAME_U] = list_name
            # Copy choices for data export tools (onaio/onadata).
            # TODO: could onadata use the list_name to look up the list for
            #  export, instead of pyxform internally duplicating choices data?
            question[constants.CHOICES] = choices[list_name]
    elif not (
        # Select with randomized choices.
        (
            constants.RANDOMIZE in question[constants.PARAMETERS]
            and question[constants.PARAMETERS][constants.RANDOMIZE] == "true"
        )
        # Select from file e.g. type = "select_one_from_file cities.xml".
        or file_extension in EXTERNAL_INSTANCE_EXTENSIONS
        # Select from previous answers e.g. type = "select_one ${q1}".
        or has_pyxform_reference(list_name)
    ):
        question[constants.LIST_NAME_U] = list_name
        question[constants.CHOICES] = choices[list_name]


def workbook_to_json(
    workbook_dict: DefinitionData,
    form_name: str | None = None,
    fallback_form_name: str | None = None,
    default_language: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """
    workbook_dict -- nested dictionaries representing a spreadsheet.
                    should be similar to those returned by xls_to_dict
    form_name -- The spreadsheet's filename
    default_language -- default_language does two things:
    1. In the xform the default language is the language reverted to when
       there is no translation available for some itext element. Because
       of this every itext element must have a default language translation.
    2. In the workbook if media/labels/hints that do not have a
       language suffix will be treated as though their suffix is the
       default language.
       If the default language is used as a suffix for media/labels/hints,
       then the suffixless version will be overwritten.
    warnings -- an optional list which warnings will be appended to

    returns a nested dictionary equivalent to the format specified in the
    json form spec.
    """
    warnings = coalesce(warnings, [])
    sheet_names = workbook_dict.sheet_names
    if not workbook_dict.survey and not workbook_dict.survey_header:
        msg = f"You must have a sheet named '{constants.SURVEY}'. "
        similar = find_sheet_misspellings(key=constants.SURVEY, keys=sheet_names)
        if similar is not None:
            msg += similar
        raise PyXFormError(msg)

    # Make sure the passed in vars are unicode
    form_name = str(coalesce(form_name, constants.DEFAULT_FORM_NAME))
    default_language = str(coalesce(default_language, constants.DEFAULT_LANGUAGE_VALUE))

    # Break the spreadsheet dict into easier to access objects
    # (settings, choices, survey_sheet):

    # ########## Settings sheet ##########
    settings = {}
    if workbook_dict.settings:
        settings_sheet_headers = workbook_dict.settings_header or []
        settings_sheet = workbook_dict.settings or []
        try:
            if (
                sum(
                    [
                        element in {constants.ID_STRING, "form_id"}
                        for element in settings_sheet_headers[0]
                    ]
                )
                == 2
            ):
                settings_sheet_headers[0].pop(constants.ID_STRING, None)
                settings_sheet[0].pop(constants.ID_STRING, None)
                warnings.append(
                    "The form_id and id_string column headers are both"
                    " specified in the settings sheet provided."
                    " This may cause errors during conversion."
                    " In future, its best to avoid specifying both"
                    " column headers in the settings sheet."
                )
        except IndexError:  # In case there is no settings sheet
            pass

        from pyxform.survey import Survey

        settings_sheet = dealias_and_group_headers(
            sheet_name=constants.SETTINGS,
            sheet_data=settings_sheet,
            sheet_header=settings_sheet_headers,
            header_aliases=aliases.settings_header,
            header_columns=set(Survey.get_slot_names()),
        )
        settings = settings_sheet.data[0]
    else:
        similar = find_sheet_misspellings(key=constants.SETTINGS, keys=sheet_names)
        if similar is not None:
            warnings.append(similar + _MSG_SUPPRESS_SPELLING)

    clean_text_values_enabled = aliases.yes_no.get(
        settings.get("clean_text_values", "yes"), True
    )
    default_language = settings.get(constants.DEFAULT_LANGUAGE_KEY, default_language)
    # add_none_option is a boolean that when true,
    # indicates a none option should automatically be added to selects.
    # It should probably be deprecated but I haven't checked yet.
    if "add_none_option" in settings:
        settings["add_none_option"] = aliases.yes_no.get(
            settings.get("add_none_option", "no"), False
        )
    if constants.CLIENT_EDITABLE in settings:
        settings[constants.CLIENT_EDITABLE] = aliases.yes_no.get(
            settings.get(constants.CLIENT_EDITABLE, "no"), False
        )

    # Here we create our json dict root with default settings:
    id_string = settings.get(
        constants.ID_STRING, coalesce(fallback_form_name, constants.DEFAULT_FORM_NAME)
    )
    sms_keyword = settings.get(constants.SMS_KEYWORD, id_string)
    json_dict = {
        constants.TYPE: constants.SURVEY,
        constants.NAME: form_name,
        constants.TITLE: id_string,
        constants.ID_STRING: id_string,
        constants.SMS_KEYWORD: sms_keyword,
        constants.DEFAULT_LANGUAGE_KEY: default_language,
        # By default the version is based on the date and time yyyymmddhh
        # Leaving default version out for now since it might cause
        # problems for formhub.
        # constants.VERSION : datetime.datetime.now().strftime("%Y%m%d%H"),
        constants.CHILDREN: [],
    }
    # Here the default settings are overridden by those in the settings sheet
    json_dict.update(settings)
    from pyxform.question import Option

    option_fields = set(Option.get_slot_names())

    # ########## External Choices sheet ##########
    external_choices = workbook_dict.external_choices
    if external_choices:
        external_choices = dealias_and_group_headers(
            sheet_name=constants.EXTERNAL_CHOICES,
            sheet_data=external_choices,
            sheet_header=workbook_dict.external_choices_header,
            header_aliases=aliases.list_header,
            header_columns=option_fields,
            default_language=default_language,
        )
        external_choices = group_dictionaries_by_key(
            list_of_dicts=external_choices.data, key=constants.LIST_NAME_S
        )

    # ########## Choices sheet ##########
    choices_sheet = workbook_dict.choices
    choices = {}
    if choices_sheet:
        choices_sheet = dealias_and_group_headers(
            sheet_name=constants.CHOICES,
            sheet_data=choices_sheet,
            sheet_header=workbook_dict.choices_header,
            header_aliases=aliases.list_header,
            header_columns=option_fields,
            headers_required={constants.NAME},
            default_language=default_language,
            add_row_number=True,
        )
        choices = group_dictionaries_by_key(
            list_of_dicts=choices_sheet.data, key=constants.LIST_NAME_S
        )
        # To combine the warning into one message, the check for missing choices translation
        # columns is run with Survey sheet below.

        # Warn and remove invalid headers in case the form uses headers for notes.
        choices = validate_and_clean_choices(
            choices=choices,
            warnings=warnings,
            headers=choices_sheet.headers,
            allow_duplicates=aliases.yes_no.get(
                settings.get("allow_choice_duplicates", "no"), False
            ),
        )
        if choices:
            json_dict[constants.CHOICES] = choices

    # ########## Entities sheet ###########
    entity_declaration = None
    if workbook_dict.entities:
        entities_sheet = dealias_and_group_headers(
            sheet_name=constants.ENTITIES,
            sheet_data=workbook_dict.entities,
            sheet_header=workbook_dict.entities_header,
            header_aliases=aliases.entities_header,
            header_columns={i.value for i in constants.EntityColumns.value_list()},
        )
        entity_declaration = get_entity_declaration(entities_sheet=entities_sheet.data)
    else:
        similar = find_sheet_misspellings(key=constants.ENTITIES, keys=sheet_names)
        if similar is not None:
            warnings.append(similar + constants._MSG_SUPPRESS_SPELLING)

    # ########## Survey sheet ###########
    # Process the headers:
    from pyxform.question import MultipleChoiceQuestion

    survey_sheet = dealias_and_group_headers(
        sheet_name=constants.SURVEY,
        sheet_data=workbook_dict.survey,
        sheet_header=workbook_dict.survey_header,
        header_aliases=aliases.survey_header,
        header_columns=set(MultipleChoiceQuestion.get_slot_names()),
        headers_required={constants.TYPE},
        default_language=default_language,
        strip_whitespace=clean_text_values_enabled,
    )
    survey_sheet.data = dealias_types(dict_array=survey_sheet.data)

    # Check for missing translations. The choices sheet is checked here so that the
    # warning can be combined into one message.
    if not choices_sheet:
        choices_headers = ()
    else:
        choices_headers = choices_sheet.headers
    sheet_translations = SheetTranslations(
        survey_sheet=survey_sheet.headers,
        choices_sheet=choices_headers,
    )
    sheet_translations.missing_check(warnings=warnings)

    # ########## OSM sheet ###########
    # No spell check for OSM sheet (infrequently used, many spurious matches).
    osm_tags = None
    if workbook_dict.osm:
        osm_sheet = dealias_and_group_headers(
            sheet_data=workbook_dict.osm,
            sheet_name=constants.OSM,
            sheet_header=workbook_dict.osm_header,
            header_aliases=aliases.list_header,
            header_columns=option_fields,
        )
        osm_tags = group_dictionaries_by_key(
            list_of_dicts=osm_sheet.data, key=constants.LIST_NAME_S
        )

    # #################################

    # Parse the survey sheet while generating a survey in our json format:
    # A stack is used to keep track of begin/end expressions
    stack: list[dict[str, Any]] = [
        {
            "control_type": None,
            "control_name": None,
            "parent_children": json_dict.get(constants.CHILDREN),
            "child_names": set(),
            "child_names_lower": set(),
            "row_number": None,
        }
    ]
    # If a group has a table-list appearance flag
    # this will be set to the name of the list
    table_list = None

    # Rows from the survey sheet that should be nested in meta
    meta_children = []
    # To check that questions with triggers refer to other questions that exist.
    question_names = set()
    element_names = Counter()
    trigger_references: list[tuple[str, int]] = []
    repeat_names = set()

    # row by row, validate questions, throwing errors and adding warnings where needed.
    for row_number, row in enumerate(survey_sheet.data, start=2):
        prev_control_type = stack[-1]["control_type"]
        parent_children_array = stack[-1]["parent_children"]
        child_names = stack[-1]["child_names"]
        child_names_lower = stack[-1]["child_names_lower"]

        # Disabled should probably be first
        # so the attributes below can be disabled.
        if "disabled" in row:
            warnings.append(
                ROW_FORMAT_STRING % row_number
                + " The 'disabled' column header is not part of the current"
                + " spec. We recommend using relevant instead."
            )
            disabled = row.pop("disabled")
            if aliases.yes_no.get(disabled):
                continue

        # skip empty rows
        if not row:
            continue

        # Get question type
        question_type = row.get(constants.TYPE)

        if not question_type:
            # if name and label are also missing,
            # then its a comment row, and we skip it with warning
            if not (constants.NAME in row or constants.LABEL in row):
                warnings.append(
                    ROW_FORMAT_STRING % row_number
                    + " Row without name, text, or label is being skipped:\n"
                    + str(row)
                )
                continue
            raise PyXFormError(
                ROW_FORMAT_STRING % row_number + " Question with no type.\n" + str(row)
            )

        if "trigger" in row:
            row["trigger"] = qt.process_trigger(
                trigger=row["trigger"],
                row_num=row_number,
                trigger_references=trigger_references,
            )

        if "default" in row:
            question_default = row.get("default")
            if question_default and default_is_dynamic(question_default, question_type):
                row["_dynamic_default"] = True
                row["actions"] = row.get("actions", [])
                row["actions"].append(
                    action_module.ActionLibrary.setvalue_first_load.value.to_dict()
                )
                if next(
                    (i for i in reversed(stack) if i["control_type"] == "repeat"), False
                ):
                    row["actions"].append(
                        action_module.ActionLibrary.setvalue_new_repeat.value.to_dict()
                    )

        parameters = parameters_generic.parse(raw_parameters=row.get("parameters", ""))

        # Pull out questions that will go in meta block
        if question_type == "audit":
            # Force audit name to always be "audit" to follow XForms spec
            if "name" in row and row["name"] not in {None, "", "audit"}:
                raise PyXFormError(
                    ROW_FORMAT_STRING % row_number
                    + " Audits must always be named 'audit.'"
                    + " The name column should be left blank."
                )
            row["name"] = "audit"

            new_dict = row.copy()
            parameters_generic.validate(
                parameters=parameters,
                allowed=(
                    constants.LOCATION_PRIORITY,
                    constants.LOCATION_MIN_INTERVAL,
                    constants.LOCATION_MAX_AGE,
                    constants.TRACK_CHANGES,
                    constants.IDENTIFY_USER,
                    constants.TRACK_CHANGES_REASONS,
                ),
            )

            if constants.TRACK_CHANGES in parameters:
                if (
                    parameters[constants.TRACK_CHANGES] != "true"
                    and parameters[constants.TRACK_CHANGES] != "false"
                ):
                    msg = (
                        f"{constants.TRACK_CHANGES} must be set to true or false: "
                        f"'{parameters[constants.TRACK_CHANGES]}' is an invalid value."
                    )
                    raise PyXFormError(msg)
                else:
                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {
                            "odk:" + constants.TRACK_CHANGES: parameters[
                                constants.TRACK_CHANGES
                            ]
                        }
                    )

            if constants.TRACK_CHANGES_REASONS in parameters:
                if parameters[constants.TRACK_CHANGES_REASONS] != "on-form-edit":
                    raise PyXFormError(
                        constants.TRACK_CHANGES_REASONS + " must be set to on-form-edit"
                    )
                else:
                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {"odk:" + constants.TRACK_CHANGES_REASONS: "on-form-edit"}
                    )

            if constants.IDENTIFY_USER in parameters:
                if (
                    parameters[constants.IDENTIFY_USER] != "true"
                    and parameters[constants.IDENTIFY_USER] != "false"
                ):
                    msg = (
                        f"{constants.IDENTIFY_USER} must be set to true or false: "
                        f"'{parameters[constants.IDENTIFY_USER]}' is an invalid value."
                    )
                    raise PyXFormError(msg)
                else:
                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {
                            "odk:" + constants.IDENTIFY_USER: parameters[
                                constants.IDENTIFY_USER
                            ]
                        }
                    )

            location_parameters = {
                constants.LOCATION_PRIORITY,
                constants.LOCATION_MIN_INTERVAL,
                constants.LOCATION_MAX_AGE,
            }
            if any(k in parameters for k in location_parameters):
                if all(k in parameters for k in location_parameters):
                    if parameters[constants.LOCATION_PRIORITY] not in {
                        "no-power",
                        "low-power",
                        "balanced",
                        "high-accuracy",
                    }:
                        msg = (
                            f"Parameter {constants.LOCATION_PRIORITY} must be set to "
                            "no-power, low-power, balanced, or high-accuracy:"
                            f"'{parameters[constants.LOCATION_PRIORITY]}' is an invalid value"
                        )
                        raise PyXFormError(msg)

                    try:
                        int(parameters[constants.LOCATION_MIN_INTERVAL])
                    except ValueError as lmi_err:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MIN_INTERVAL
                            + " must have an integer value."
                        ) from lmi_err
                    if int(parameters[constants.LOCATION_MIN_INTERVAL]) < 0:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MIN_INTERVAL
                            + " must be greater than or equal to zero."
                        )

                    try:
                        int(parameters[constants.LOCATION_MAX_AGE])
                    except ValueError as lma_err:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MAX_AGE
                            + " must have an integer value."
                        ) from lma_err
                    if int(parameters[constants.LOCATION_MAX_AGE]) < 0:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MAX_AGE
                            + " must be greater  than or equal to zero."
                        )

                    if int(parameters[constants.LOCATION_MAX_AGE]) < int(
                        parameters[constants.LOCATION_MIN_INTERVAL]
                    ):
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MAX_AGE
                            + " must be greater than or equal to "
                            + constants.LOCATION_MIN_INTERVAL
                            + "."
                        )

                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {
                            "odk:" + constants.LOCATION_MAX_AGE: parameters[
                                constants.LOCATION_MAX_AGE
                            ],
                            "odk:" + constants.LOCATION_MIN_INTERVAL: parameters[
                                constants.LOCATION_MIN_INTERVAL
                            ],
                            "odk:" + constants.LOCATION_PRIORITY: parameters[
                                constants.LOCATION_PRIORITY
                            ],
                        }
                    )
                else:
                    raise PyXFormError(
                        "To include location information in"
                        + " the audit, '"
                        + constants.LOCATION_PRIORITY
                        + "', '"
                        + constants.LOCATION_MIN_INTERVAL
                        + "', and '"
                        + constants.LOCATION_MAX_AGE
                        + "' are required"
                        + " parameters."
                    )

            meta_children.append(new_dict)
            continue

        if question_type == "calculate":
            calculation = row.get("bind", {}).get("calculate")
            if not calculation and not row.get("_dynamic_default", False):
                raise PyXFormError(
                    ROW_FORMAT_STRING % row_number + " Missing calculation."
                )
        if question_type in constants.DEPRECATED_DEVICE_ID_METADATA_FIELDS:
            warnings.append(
                (ROW_FORMAT_STRING % row_number)
                + " "
                + question_type
                + " is no longer supported on most devices. "
                "Only old versions of Collect on Android versions older than 11 still support it."
            )
        # Check if the question is actually a setting specified
        # on the survey sheet
        settings_type = aliases.settings_header.get(question_type)
        if settings_type:
            json_dict[settings_type] = str(row.get(constants.NAME))
            continue

        # Try to parse question as a end control statement
        # (i.e. end loop/repeat/group):
        end_control_parse = RE_END_CONTROL.search(question_type)
        if end_control_parse:
            parse_dict = end_control_parse.groupdict()
            if parse_dict.get("end") and "type" in parse_dict:
                if validate_entity_repeat_target(
                    entity_declaration=entity_declaration,
                    stack=stack,
                ):
                    parent_children_array.append(
                        get_meta_group(children=[entity_declaration])
                    )
                    json_dict[constants.ENTITY_VERSION] = (
                        constants.EntityVersion.v2025_1_0
                    )
                    entity_declaration = None
                control_type = aliases.control[parse_dict["type"]]
                if prev_control_type != control_type or len(stack) == 1:
                    raise PyXFormError(
                        SURVEY_001.format(
                            row=row_number,
                            type=control_type,
                            name=row.get(constants.NAME),
                        )
                    )
                stack.pop()
                table_list = None
                continue

        # Make sure the row has a valid name
        if constants.NAME not in row:
            if row[constants.TYPE] == "note":
                # autogenerate names for notes without them
                row[constants.NAME] = "generated_note_name_" + str(row_number)
            else:
                raise PyXFormError(
                    ROW_FORMAT_STRING % row_number + " Question or group with no name."
                )
        question_name = str(row[constants.NAME])
        if not is_xml_tag(question_name):
            raise PyXFormError(
                f"{ROW_FORMAT_STRING % row_number} Invalid question name '{question_name}'. Names {XML_IDENTIFIER_ERROR_MESSAGE}"
            )
        element_names.update((question_name,))

        unique_names.validate_question_group_repeat_name(
            row_number=row_number,
            name=question_name,
            seen_names=child_names,
            seen_names_lower=child_names_lower,
            warnings=warnings,
        )
        validate_entity_saveto(
            row=row,
            row_number=row_number,
            stack=stack,
            entity_declaration=entity_declaration,
        )

        # Try to parse question as begin control statement
        # (i.e. begin loop/repeat/group):
        begin_control_parse = RE_BEGIN_CONTROL.search(question_type)
        if begin_control_parse:
            parse_dict = begin_control_parse.groupdict()
            if parse_dict.get("begin") and "type" in parse_dict:
                # Create a new json dict with children, and the proper type,
                # and add it to parent_children_array in place of a question.
                # parent_children_array will then be set to its children array
                # (so following questions are nested under it)
                # until an end command is encountered.
                control_type = aliases.control[parse_dict["type"]]

                unique_names.validate_repeat_name(
                    row_number=row_number,
                    name=question_name,
                    control_type=control_type,
                    instance_element_name=json_dict[constants.NAME],
                    seen_names=repeat_names,
                )

                # Check if the control item has a label, if applicable.
                # This label check used to apply to all items, but no longer is
                # relevant for questions since label nodes are added by default.
                # There isn't an easy and neat place to put this besides here.
                # Could potentially be simplified for control item cases.
                if (
                    constants.LABEL not in row
                    and row.get(constants.MEDIA) is None
                    and question_type not in aliases.label_optional_types
                    and not row.get("bind", {}).get("calculate")
                    and not row.get("_dynamic_default", False)
                    and not (
                        control_type is constants.GROUP
                        and row.get("control", {}).get("appearance")
                        == constants.FIELD_LIST
                    )
                ):
                    # Row number, name, and type probably enough for user message.
                    # Also means the error message text is stable for tests.
                    msg_dict = {"name": row.get("name"), "type": row.get("type")}
                    warnings.append(
                        ROW_FORMAT_STRING % row_number
                        + f" {control_type.capitalize()} has no label: {msg_dict}"
                    )

                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = control_type
                child_list = []
                new_json_dict[constants.CHILDREN] = child_list
                if control_type == constants.LOOP:
                    if not parse_dict.get(constants.LIST_NAME_U):
                        # TODO: Perhaps warn and make repeat into a group?
                        raise PyXFormError(
                            ROW_FORMAT_STRING % row_number
                            + " Repeat loop without list name."
                        )
                    list_name = parse_dict[constants.LIST_NAME_U]
                    if list_name not in choices:
                        raise PyXFormError(
                            ROW_FORMAT_STRING % row_number
                            + " List name not in columns sheet: "
                            + list_name
                        )
                    new_json_dict[constants.COLUMNS] = choices[list_name]

                # Generate a new node for the jr:count column so xpath expressions can be used.
                repeat_count_expression = new_json_dict.get("control", {}).get("jr:count")
                if repeat_count_expression:
                    # Simple expressions don't require a new node, they can reference directly.
                    if not is_pyxform_reference(value=repeat_count_expression):
                        generated_node_name = f"""{new_json_dict["name"]}_count"""
                        parent_children_array.append(
                            {
                                "name": generated_node_name,
                                "bind": {
                                    "readonly": "true()",
                                    "calculate": repeat_count_expression,
                                },
                                "type": "calculate",
                            }
                        )
                        # This re-directs the body/repeat ref to the above generated node.
                        new_json_dict["control"]["jr:count"] = (
                            f"${{{generated_node_name}}}"
                        )

                # Code to deal with table_list appearance flags
                # (for groups of selects)
                ctrl_ap = new_json_dict.get("control", {}).get("appearance")

                if ctrl_ap:
                    appearance_mods_as_list = ctrl_ap.split()
                    if constants.TABLE_LIST in appearance_mods_as_list:
                        # Table List modifier should add field list to the new dict,
                        # as well as appending other appearance modifiers.
                        table_list = True
                        appearance_string = "field-list"
                        for w in appearance_mods_as_list:
                            if w != constants.TABLE_LIST:
                                appearance_string += " " + str(w)
                        new_json_dict["control"]["appearance"] = appearance_string

                        # Generate a note label element so hints and labels
                        # work as expected in table-lists.
                        # see https://github.com/modilabs/pyxform/issues/62
                        if "label" in new_json_dict or "hint" in new_json_dict:
                            generated_label_element = {
                                "type": "note",
                                "name": "generated_table_list_label_" + str(row_number),
                            }
                            if "label" in new_json_dict:
                                generated_label_element[constants.LABEL] = new_json_dict[
                                    constants.LABEL
                                ]
                                del new_json_dict[constants.LABEL]
                            if "hint" in new_json_dict:
                                generated_label_element["hint"] = new_json_dict["hint"]
                                del new_json_dict["hint"]
                            child_list.append(generated_label_element)
                if "intent" in new_json_dict:
                    new_json_dict["control"] = new_json_dict.get("control", {})
                    new_json_dict["control"]["intent"] = new_json_dict["intent"]

                parent_children_array.append(new_json_dict)
                stack.append(
                    {
                        "control_type": control_type,
                        "control_name": question_name,
                        "parent_children": child_list,
                        "child_names": set(),
                        "child_names_lower": set(),
                        "row_number": row_number,
                    }
                )
                validate_entity_repeat_target(
                    stack=stack,
                    entity_declaration=entity_declaration,
                )
                continue

        # Assuming a question is anything not processed above as a loop/repeat/group.
        question_names.add(question_name)

        # Try to parse question as a select:
        select_parse = RE_SELECT.search(question_type)
        if select_parse:
            parse_dict = select_parse.groupdict()
            if parse_dict.get("select_command"):
                select_type = aliases.select[parse_dict["select_command"]]
                if (
                    select_type == constants.SELECT_ONE_EXTERNAL
                    and constants.CHOICE_FILTER not in row
                ):
                    warnings.append(
                        ROW_FORMAT_STRING % row_number
                        + " select one external is only meant for filtered selects."
                    )
                list_name = parse_dict[constants.LIST_NAME_U]
                file_extension = os.path.splitext(list_name)[1]
                if select_type == constants.SELECT_ONE_EXTERNAL:
                    if not external_choices:
                        k = constants.EXTERNAL_CHOICES
                        msg = "There should be an external_choices sheet in this xlsform."
                        similar = find_sheet_misspellings(key=k, keys=sheet_names)
                        if similar is not None:
                            msg = msg + " " + similar
                        raise PyXFormError(
                            msg
                            + " Please ensure that the external_choices sheet has columns"
                            " 'list name', and 'name'."
                        )
                    if list_name not in external_choices:
                        raise PyXFormError(
                            ROW_FORMAT_STRING % row_number
                            + "List name not in external choices sheet: "
                            + list_name
                        )
                select_from_file.validate_list_name_extension(
                    select_command=parse_dict["select_command"],
                    list_name=list_name,
                    row_number=row_number,
                )
                if (
                    list_name not in choices
                    and select_type != constants.SELECT_ONE_EXTERNAL
                    and file_extension not in EXTERNAL_INSTANCE_EXTENSIONS
                    and not has_pyxform_reference(list_name)
                ):
                    if not choices:
                        k = constants.CHOICES
                        msg = "There should be a choices sheet in this xlsform."
                        similar = find_sheet_misspellings(key=k, keys=sheet_names)
                        if similar is not None:
                            msg = f"{msg} {similar}"
                        raise PyXFormError(
                            f"{msg} Please ensure that the choices sheet has the"
                            " mandatory columns 'list_name', 'name', and 'label'."
                        )
                    raise PyXFormError(
                        ROW_FORMAT_STRING % row_number
                        + " List name not in choices sheet: "
                        + list_name
                    )

                # Validate select_multiple choice names by making sure
                # they have no spaces (will cause errors in exports).
                if (
                    select_type == constants.SELECT_ALL_THAT_APPLY
                    and file_extension not in EXTERNAL_INSTANCE_EXTENSIONS
                ):
                    for choice in choices[list_name]:
                        if " " in choice[constants.NAME]:
                            raise PyXFormError(
                                "Choice names with spaces cannot be added "
                                "to multiple choice selects. See ["
                                + choice[constants.NAME]
                                + "] in ["
                                + list_name
                                + "]"
                            )

                specify_other_question = None
                if parse_dict.get("specify_other") is not None:
                    sheet_translations.or_other_seen = True
                    if row.get(constants.CHOICE_FILTER):
                        msg = (
                            ROW_FORMAT_STRING % row_number
                            + " Choice filter not supported with or_other."
                        )
                        raise PyXFormError(msg)
                    itemset_choices = choices.get(list_name, None)
                    if not itemset_choices:
                        msg = (
                            ROW_FORMAT_STRING % row_number
                            + " Please specify choices for this 'or other' question."
                        )
                        raise PyXFormError(msg)
                    if (
                        itemset_choices is not None
                        and isinstance(itemset_choices, list)
                        and not any(
                            c[constants.NAME] == constants.OR_OTHER_CHOICE[constants.NAME]
                            for c in itemset_choices
                        )
                    ):
                        if any(
                            isinstance(c.get(constants.LABEL), dict)
                            for c in itemset_choices
                        ):
                            itemset_choices.append(
                                {
                                    constants.NAME: constants.OR_OTHER_CHOICE[
                                        constants.NAME
                                    ],
                                    constants.LABEL: dict.fromkeys(
                                        {
                                            lang
                                            for c in itemset_choices
                                            for lang in c[constants.LABEL]
                                            if isinstance(c.get(constants.LABEL), dict)
                                        },
                                        constants.OR_OTHER_CHOICE[constants.LABEL],
                                    ),
                                }
                            )
                        else:
                            itemset_choices.append(constants.OR_OTHER_CHOICE)
                    specify_other_question = {
                        constants.TYPE: "text",
                        constants.NAME: f"{row[constants.NAME]}_other",
                        constants.LABEL: "Specify other.",
                        constants.BIND: {
                            "relevant": f"selected(../{row[constants.NAME]}, 'other')"
                        },
                    }

                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = select_type

                select_params_allowed = ["randomize", "seed"]
                if parse_dict["select_command"] in {
                    "select_one_from_file",
                    "select_multiple_from_file",
                }:
                    select_params_allowed += ["value", "label"]

                # Look at parameters column for select parameters
                parameters_generic.validate(
                    parameters=parameters, allowed=select_params_allowed
                )

                if "randomize" in parameters:
                    if (
                        parameters["randomize"] != "true"
                        and parameters["randomize"] != "false"
                    ):
                        raise PyXFormError(
                            "randomize must be set to true or false: "
                            f"""'{parameters["randomize"]}' is an invalid value"""
                        )

                    if "seed" in parameters:
                        if not is_pyxform_reference(parameters["seed"]):
                            try:
                                float(parameters["seed"])
                            except ValueError as seed_err:
                                raise PyXFormError(
                                    "seed value must be a number or a reference to another field."
                                ) from seed_err
                elif "seed" in parameters:
                    raise PyXFormError(
                        "Parameters must include randomize=true to use a seed."
                    )

                if "value" in parameters:
                    select_from_file.value_or_label_check(
                        name="value",
                        value=parameters["value"],
                        row_number=row_number,
                    )
                if "label" in parameters:
                    select_from_file.value_or_label_check(
                        name="label",
                        value=parameters["label"],
                        row_number=row_number,
                    )

                new_json_dict[constants.PARAMETERS] = parameters

                add_choices_info_to_question(
                    question=new_json_dict,
                    list_name=list_name,
                    choices=choices,
                    choice_filter=row.get(constants.CHOICE_FILTER),
                    file_extension=file_extension,
                )

                # Code to deal with table_list appearance flags
                # (for groups of selects)
                if table_list is not None:
                    # Then this row is the first select in a table list
                    if not isinstance(table_list, str):
                        table_list = list_name
                        if row.get(constants.CHOICE_FILTER, None) is not None:
                            msg = (
                                ROW_FORMAT_STRING % row_number
                                + " Choice filter not supported for table-list appearance."
                            )
                            raise PyXFormError(msg)
                        table_list_header = {
                            constants.TYPE: select_type,
                            constants.NAME: "reserved_name_for_field_list_labels_"
                            + str(row_number),
                            # Adding row number for uniqueness
                            constants.CONTROL: {constants.APPEARANCE: "label"},
                            constants.CHOICES: choices[list_name],
                            constants.ITEMSET: list_name,
                        }
                        parent_children_array.append(table_list_header)

                    if table_list != list_name:
                        error_message = ROW_FORMAT_STRING % row_number
                        error_message += (
                            " Badly formatted table list,"
                            " list names don't match: " + table_list + " vs. " + list_name
                        )
                        raise PyXFormError(error_message)

                    if constants.CONTROL not in new_json_dict:
                        new_json_dict[constants.CONTROL] = {}
                    new_json_dict[constants.CONTROL][constants.APPEARANCE] = (
                        constants.LIST_NOLABEL
                    )
                parent_children_array.append(new_json_dict)
                if specify_other_question:
                    parent_children_array.append(specify_other_question)
                continue

        # Try to parse question as osm:
        osm_parse = RE_OSM.search(question_type)
        if osm_parse:
            parse_dict = osm_parse.groupdict()
            new_dict = row.copy()
            new_dict["type"] = constants.OSM

            if osm_tags and parse_dict.get(constants.LIST_NAME_U) is not None:
                tags = osm_tags.get(parse_dict.get(constants.LIST_NAME_U))
                for tag in tags:
                    if osm_tags.get(tag.get("name")):
                        tag["choices"] = osm_tags.get(tag.get("name"))
                new_dict["tags"] = tags

            parent_children_array.append(new_dict)

            continue

        # range question_type
        if question_type == "range":
            new_dict = process_range_question_type(row=row, parameters=parameters)
            parent_children_array.append(new_dict)
            continue

        if question_type == "text":
            new_dict = row.copy()
            parameters_generic.validate(parameters=parameters, allowed=("rows",))

            if "rows" in parameters:
                try:
                    int(parameters["rows"])
                except ValueError as rows_err:
                    raise PyXFormError(
                        (ROW_FORMAT_STRING % row_number)
                        + " Parameter rows must have an integer value."
                    ) from rows_err

                new_dict["control"] = new_dict.get("control", {})
                new_dict["control"].update({"rows": parameters["rows"]})

            parent_children_array.append(new_dict)
            continue

        if question_type == "photo":
            new_dict = row.copy()

            if row.get("default"):
                new_dict["default"] = process_image_default(row["default"])
            parameters_generic.validate(
                parameters=parameters,
                allowed=(
                    "max-pixels",
                    "app",
                ),
            )
            if "max-pixels" in parameters:
                try:
                    int(parameters["max-pixels"])
                except ValueError as mp_err:
                    raise PyXFormError(
                        "Parameter max-pixels must have an integer value."
                    ) from mp_err

                new_dict["bind"] = new_dict.get("bind", {})
                new_dict["bind"].update({"orx:max-pixels": parameters["max-pixels"]})
            else:
                warnings.append(
                    (ROW_FORMAT_STRING % row_number)
                    + " Use the max-pixels parameter to speed up submission sending and save storage space. Learn more: https://xlsform.org/#image"
                )

            if "app" in parameters:
                appearance = row.get("control", {}).get("appearance")
                if appearance is None or appearance == "annotate":
                    app_package_name = str(parameters["app"])
                    validation_result = validate_android_package_name(app_package_name)
                    if validation_result is None:
                        new_dict["control"] = new_dict.get("control", {})
                        new_dict["control"].update({"intent": app_package_name})
                    else:
                        raise PyXFormError(
                            (ROW_FORMAT_STRING % row_number) + " " + validation_result
                        )

            parent_children_array.append(new_dict)
            continue

        if question_type == "audio":
            new_dict = row.copy()
            parameters_generic.validate(parameters=parameters, allowed=("quality",))

            if "quality" in parameters:
                if parameters["quality"] not in {
                    constants.AUDIO_QUALITY_VOICE_ONLY,
                    constants.AUDIO_QUALITY_LOW,
                    constants.AUDIO_QUALITY_NORMAL,
                    constants.AUDIO_QUALITY_EXTERNAL,
                }:
                    raise PyXFormError("Invalid value for quality.")

                new_dict["bind"] = new_dict.get("bind", {})
                new_dict["bind"].update({"odk:quality": parameters["quality"]})

            parent_children_array.append(new_dict)
            continue

        if question_type == "background-audio":
            new_dict = row.copy()
            parameters_generic.validate(parameters=parameters, allowed=("quality",))
            action = (
                action_module.ActionLibrary.odk_recordaudio_instance_load.value.to_dict()
            )

            if "quality" in parameters:
                if parameters["quality"] not in {
                    constants.AUDIO_QUALITY_VOICE_ONLY,
                    constants.AUDIO_QUALITY_LOW,
                    constants.AUDIO_QUALITY_NORMAL,
                }:
                    raise PyXFormError("Invalid value for quality.")

                action["odk:quality"] = parameters["quality"]

            new_dict["actions"] = new_dict.get("actions", [])
            new_dict["actions"].append(action)

            parent_children_array.append(new_dict)
            continue

        if question_type in {"geopoint", "geoshape", "geotrace"}:
            new_dict = row.copy()

            if question_type == "geopoint":
                parameters_generic.validate(
                    parameters=parameters,
                    allowed=(
                        "allow-mock-accuracy",
                        "capture-accuracy",
                        "warning-accuracy",
                    ),
                )
            else:
                parameters_generic.validate(
                    parameters=parameters, allowed=("allow-mock-accuracy", "incremental")
                )

            if "allow-mock-accuracy" in parameters:
                if parameters["allow-mock-accuracy"] not in {"true", "false"}:
                    raise PyXFormError("Invalid value for allow-mock-accuracy.")

                new_dict["bind"] = new_dict.get("bind", {})
                new_dict["bind"].update(
                    {"odk:allow-mock-accuracy": parameters["allow-mock-accuracy"]}
                )

            new_dict["control"] = new_dict.get("control", {})
            if "capture-accuracy" in parameters:
                try:
                    float(parameters["capture-accuracy"])
                    new_dict["control"].update(
                        {"accuracyThreshold": parameters["capture-accuracy"]}
                    )
                except ValueError as ca_err:
                    raise PyXFormError(
                        "Parameter capture-accuracy must have a numeric value"
                    ) from ca_err

            if "warning-accuracy" in parameters:
                try:
                    float(parameters["warning-accuracy"])
                    new_dict["control"].update(
                        {"unacceptableAccuracyThreshold": parameters["warning-accuracy"]}
                    )
                except ValueError as wa_err:
                    raise PyXFormError(
                        "Parameter warning-accuracy must have a numeric value"
                    ) from wa_err

            if "incremental" in parameters:
                try:
                    qt.validate_geo_parameter_incremental(value=parameters["incremental"])
                except PyXFormError as e:
                    e.context.update(
                        sheet=constants.SURVEY,
                        column=constants.PARAMETERS,
                        row=row_number,
                    )
                    raise
                else:
                    new_dict["control"]["incremental"] = "true"

            parent_children_array.append(new_dict)
            continue
        # TODO: Consider adding some question_type validation here.

        if question_type == "start-geopoint":
            new_dict = row.copy()
            new_dict["actions"] = new_dict.get("actions", [])
            new_dict["actions"].append(
                action_module.ActionLibrary.odk_setgeopoint_first_load.value.to_dict()
            )
            parent_children_array.append(new_dict)
            continue

        if question_type == "background-geopoint":
            qt.validate_background_geopoint_trigger(
                trigger=row.get("trigger"), row_num=row_number
            )
            qt.validate_background_geopoint_calculation(row=row, row_num=row_number)

        # Put the row in the json dict as is:
        parent_children_array.append(row)

    sheet_translations.or_other_check(warnings=warnings)
    try:
        qt.validate_references(referrers=trigger_references, questions=question_names)
    except PyXFormError as e:
        e.context.update(sheet="survey", column="trigger")
        raise

    if len(stack) > 1:
        raise PyXFormError(
            SURVEY_002.format(
                row=stack[-1]["row_number"],
                type=stack[-1]["control_type"],
                name=stack[-1]["control_name"],
            )
        )

    if settings.get("flat", False):
        # print "Generating flattened instance..."
        add_flat_annotations(stack[0]["parent_children"])

    if aliases.yes_no.get(settings.get("omit_instanceID")):
        if settings.get("public_key"):
            raise PyXFormError("Cannot omit instanceID, it is required for encryption.")
    else:
        # Automatically add an instanceID element:
        meta_children.append(
            {
                "name": "instanceID",
                "bind": {
                    "readonly": "true()",
                    "jr:preload": settings.get("instance_id", "uid"),
                },
                "type": "calculate",
            }
        )
        # Allow ${instanceID} reference for longitudinal / entities workflows.
        element_names.update(("instanceID",))

    if "instance_name" in settings:
        # Automatically add an instanceName element:
        meta_children.append(
            {
                "name": "instanceName",
                "bind": {"calculate": settings["instance_name"]},
                "type": "calculate",
            }
        )

    if entity_declaration:
        validate_entity_repeat_target(entity_declaration=entity_declaration)
        json_dict[constants.ENTITY_VERSION] = constants.EntityVersion.v2024_1_0
        meta_children.append(entity_declaration)

    if len(meta_children) > 0:
        meta_element = get_meta_group(children=meta_children)
        survey_children_array = stack[0]["parent_children"]
        survey_children_array.append(meta_element)

    validate_pyxform_references_in_workbook(
        workbook_dict=workbook_dict,
        survey_headers=survey_sheet.headers,
        choices_headers=choices_headers,
        element_names=element_names,
    )

    # print_pyobj_to_json(json_dict)
    return json_dict


def parse_file_to_json(
    path: str,
    default_name: str = constants.DEFAULT_FORM_NAME,
    default_language: str = constants.DEFAULT_LANGUAGE_VALUE,
    warnings: list[str] | None = None,
    file_object: IO | None = None,
) -> dict[str, Any]:
    """
    A wrapper for workbook_to_json
    """
    if warnings is None:
        warnings = []
    workbook_dict = get_xlsform(xlsform=coalesce(path, file_object))
    return workbook_to_json(
        workbook_dict=workbook_dict,
        form_name=default_name,
        fallback_form_name=workbook_dict.fallback_form_name,
        default_language=default_language,
        warnings=warnings,
    )


class SpreadsheetReader:
    def __init__(self, path_or_file):
        path = path_or_file
        try:
            path = path.name
        except AttributeError:
            pass
        self._dict = get_xlsform(xlsform=path)
        self._path = path
        self._id = str(os.path.splitext(os.path.basename(path))[0])
        self._name = self._print_name = self._title = self._id

    def to_json_dict(self):
        return self._dict

    # TODO: Make sure the unicode chars don't show up
    def print_json_to_file(self, filename=""):
        if not filename:
            filename = self._path[:-4] + ".json"
        print_pyobj_to_json(self.to_json_dict(), filename)


class SurveyReader(SpreadsheetReader):
    """
    SurveyReader is a wrapper for the parse_file_to_json function.
    It allows us to use the old interface where a SpreadsheetReader
    based object is created then a to_json_dict function is called on it.
    """

    def __init__(self, path_or_file, default_name=None):
        if isinstance(path_or_file, str):
            self._file_object = None
            path = path_or_file
        else:
            self._file_object = path_or_file
            path = path_or_file.name

        self._warnings = []
        self._dict = parse_file_to_json(
            path,
            default_name=default_name,
            warnings=self._warnings,
            file_object=self._file_object,
        )
        self._path = path

    def print_warning_log(self, warn_out_file):
        # Open file to print warning log to.
        warn_out = open(warn_out_file, mode="w", encoding="utf-8")
        warn_out.write("\n".join(self._warnings))


if __name__ == "__main__":
    # Open the excel file specified by the argument of this python call,
    # convert that file to json, then print it
    if len(sys.argv) < 2:
        # print "You must supply a file argument."
        _filename = "xlsform_spec_test.xls"
        _path = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/"
        _path += _filename
    else:
        _path = sys.argv[1]

    _warnings = []

    _json_dict = parse_file_to_json(path=_path, warnings=_warnings)
    print_pyobj_to_json(pyobj=_json_dict)

    if len(_warnings) > 0:
        sys.stderr.write("Warnings:" + "\n")
        sys.stderr.write("\n".join(_warnings) + "\n")
