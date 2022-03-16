# -*- coding: utf-8 -*-
"""
A Python script to convert excel files into JSON.
"""
import codecs
import json
import os
import re
import sys
from collections import Counter
from typing import TYPE_CHECKING

from pyxform import aliases, constants
from pyxform.constants import EXTERNAL_INSTANCE_EXTENSIONS, ROW_FORMAT_STRING
from pyxform.errors import PyXFormError
from pyxform.utils import default_is_dynamic, is_valid_xml_tag, levenshtein_distance
from pyxform.validators.pyxform import select_from_file_params
from pyxform.validators.pyxform.missing_translations_check import (
    missing_translations_check,
)
from pyxform.xls2json_backends import csv_to_dict, xls_to_dict, xlsx_to_dict

if TYPE_CHECKING:
    from typing import Any, Dict, KeysView, List, Optional

SMART_QUOTES = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}
_MSG_SUPPRESS_SPELLING = (
    " If you do not mean to include a sheet, to suppress this message, "
    "prefix the sheet name with an underscore. For example 'setting' "
    "becomes '_setting'."
)


def print_pyobj_to_json(pyobj, path=None):
    """
    dump a python nested array/dict structure to the specified file
    or stdout if no file is specified
    """
    if path:
        fp = codecs.open(path, mode="w", encoding="utf-8")
        json.dump(pyobj, fp=fp, ensure_ascii=False, indent=4)
        fp.close()
    else:
        sys.stdout.write(json.dumps(pyobj, ensure_ascii=False, indent=4))


def merge_dicts(dict_a, dict_b, default_key="default"):
    """
    Recursively merge two nested dicts into a single dict.
    When keys match their values are merged using
    a recursive call to this function,
    otherwise they are just added to the output dict.
    """
    if dict_a is None or dict_a == {}:
        return dict_b
    if dict_b is None or dict_b == {}:
        return dict_a

    if type(dict_a) is not dict:
        if default_key in dict_b:
            return dict_b
        dict_a = {default_key: dict_a}
    if type(dict_b) is not dict:
        if default_key in dict_a:
            return dict_a
        dict_b = {default_key: dict_b}

    all_keys = set(dict_a.keys()).union(set(dict_b.keys()))

    out_dict = dict()
    for key in all_keys:
        out_dict[key] = merge_dicts(dict_a.get(key), dict_b.get(key), default_key)
    return out_dict


def list_to_nested_dict(lst):
    """
    [1,2,3,4] -> {1:{2:{3:4}}}
    """
    if len(lst) > 1:
        return {lst[0]: list_to_nested_dict(lst[1:])}
    else:
        return lst[0]


def replace_smart_quotes_in_dict(_d):
    for key, value in _d.items():
        _changed = False
        for smart_quote, dumb_quote in SMART_QUOTES.items():
            if isinstance(value, str):
                if smart_quote in value:
                    value = value.replace(smart_quote, dumb_quote)
                    _changed = True
        if _changed:
            _d[key] = value


def dealias_and_group_headers(
    dict_array: "List[Dict]",
    header_aliases: "Dict",
    use_double_colons: bool,
    default_language: str = constants.DEFAULT_LANGUAGE_VALUE,
    ignore_case: bool = False,
):
    """
    For each row in the worksheet, group all keys that contain a double colon.
    So
        {"text::english": "hello", "text::french" : "bonjour"}
    becomes
        {"text": {"english": "hello", "french" : "bonjour"}.
    Dealiasing is done to the first token
    (the first term separated by the delimiter).
    default_language -- used to group labels/hints/etc
    without a language specified with localized versions.
    """
    group_delimiter = "::"
    out_dict_array = list()
    for row in dict_array:
        out_row = dict()
        for header, val in row.items():

            if ignore_case:
                header = header.lower()

            if use_double_colons:
                tokens = header.split(group_delimiter)

            # else:
            #   We do the initial parse using single colons
            #   for backwards compatibility and
            #   only the first single is used
            #   in order to avoid nesting jr:something tokens.
            #   if len(tokens) > 1:
            #       tokens[1:] = [u":".join(tokens[1:])]
            else:
                # I think the commented out section above
                # break if there is something like media:image:english
                # so maybe a better backwards compatibility hack
                # is to join any jr token with the next token
                tokens = header.split(":")
                if "jr" in tokens:
                    jr_idx = tokens.index("jr")
                    tokens[jr_idx] = ":".join(tokens[jr_idx : jr_idx + 2])
                    tokens.pop(jr_idx + 1)

            dealiased_first_token = header_aliases.get(tokens[0], tokens[0])
            tokens = dealiased_first_token.split(group_delimiter) + tokens[1:]
            new_key = tokens[0]
            new_value = list_to_nested_dict(tokens[1:] + [val])
            out_row = merge_dicts(out_row, {new_key: new_value}, default_language)

        out_dict_array.append(out_row)
    return out_dict_array


def dealias_types(dict_array):
    """
    Look at all the type values in a dict array and if any aliases are found,
    replace them with the name they map to.
    """
    for row in dict_array:
        found_type = row.get(constants.TYPE)
        if found_type in aliases._type_alias_map.keys():
            row[constants.TYPE] = aliases._type_alias_map[found_type]
    return dict_array


def clean_text_values(dict_array):
    """
    Go though the dict array and strips all text values.
    Also replaces multiple spaces with single spaces.
    """
    for row in dict_array:
        replace_smart_quotes_in_dict(row)
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = re.sub(r"( )+", " ", value.strip())
    return dict_array


# This is currently unused because name uniqueness is checked in json2xform.
def check_name_uniqueness(dict_array):
    """
    Make sure all names are unique
    Raises and exception if a duplicate is found
    """
    # This set is used to validate the uniqueness of names.
    name_set = set()
    row_number = 0  # TODO: There might be a bug with row numbers...
    for row in dict_array:
        row_number += 1
        name = row.get(constants.NAME)
        if name:
            if name in name_set:
                raise PyXFormError(
                    "Question name is not unique: "
                    + str(name)
                    + " Row: "
                    + str(row_number)
                )
            else:
                name_set.add(name)
    return dict_array


def group_dictionaries_by_key(list_of_dicts, key, remove_key=True):
    """
    Takes a list of dictionaries and returns a
    dictionary of lists of dictionaries with the same value for the given key.
    The grouping key is removed by default.
    If the key is not in any dictionary an empty dict is returned.
    """
    dict_of_lists = dict()
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


def has_double_colon(workbook_dict) -> bool:
    """
    Look for a column header with a doublecolon (::) and
    return true if one is found.
    """
    for sheet in workbook_dict.values():
        for row in sheet:
            for column_header in row.keys():
                if type(column_header) is not str:
                    continue
                if "::" in column_header:
                    return True
    return False


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
        else:
            if new_relevant != "":
                prompt["bind"] = prompt.get("bind", {})
                prompt["bind"]["relevant"] = new_relevant
                # if name_prefix != '':
                #    prompt['name'] = name_prefix + prompt['name']


def process_range_question_type(row):
    """Returns a new row that includes the Range parameters start, end and
    step.

    Raises PyXFormError when invalid range parameters are used.
    """
    new_dict = row.copy()
    parameters = get_parameters(new_dict.get("parameters", ""), ["start", "end", "step"])
    parameters_map = {"start": "start", "end": "end", "step": "step"}
    defaults = {"start": "1", "end": "10", "step": "1"}

    # set defaults
    for key in parameters_map.values():
        if key not in parameters:
            parameters[key] = defaults[key]

    try:
        has_float = any([float(x) and "." in str(x) for x in parameters.values()])
    except ValueError:
        raise PyXFormError(
            "Range parameters 'start', " "'end' or 'step' must all be numbers."
        )
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


def find_sheet_misspellings(key: str, keys: "KeysView") -> "Optional[str]":
    """
    Find possible sheet name misspellings to warn the user about.

    It's possible that this will warn about sheet names for sheets that have
    auxilliary metadata that is not meant for processing by pyxform. For
    example the "osm" sheet name may be similar to many other initialisms.

    :param key: The sheet name to look for.
    :param keys: The workbook sheet names.
    """
    candidates = tuple(
        _k  # thanks to black
        for _k in keys
        if 2 >= levenshtein_distance(_k.lower(), key)
        and _k not in constants.SUPPORTED_SHEET_NAMES
        and not _k.startswith("_")
    )
    if 0 < len(candidates):
        msg = (
            "When looking for a sheet named '{k}', the following sheets with "
            "similar names were found: {c}."
        ).format(k=key, c=str(", ".join(("'{}'".format(c) for c in candidates))))
        return msg
    else:
        return None


def workbook_to_json(
    workbook_dict,
    form_name=None,
    fallback_form_name=None,
    default_language=constants.DEFAULT_LANGUAGE_VALUE,
    warnings=None,
) -> "Dict[str, Any]":
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
    if warnings is None:
        warnings = []
    is_valid = False
    # Sheet names should be case-insensitive
    workbook_dict = {x.lower(): y for x, y in workbook_dict.items()}
    workbook_keys = workbook_dict.keys()
    if constants.SURVEY not in workbook_dict:
        msg = "You must have a sheet named '{k}'. ".format(k=constants.SURVEY)
        similar = find_sheet_misspellings(key=constants.SURVEY, keys=workbook_keys)
        if similar is not None:
            msg += similar
        raise PyXFormError(msg)

    # ensure required headers are present
    for row in workbook_dict.get(constants.SURVEY, []):
        is_valid = "type" in [z.lower() for z in row]
        if is_valid:
            break
    if not is_valid:
        # TODO - could we state what headers are missing?
        raise PyXFormError(
            "The survey sheet is either empty or missing important column headers."
        )

    # Make sure the passed in vars are unicode
    form_name = str(form_name)
    default_language = str(default_language)

    # We check for double columns to determine whether to use them
    # or single colons to delimit grouped headers.
    # Single colons are bad because they conflict with with the xform namespace
    # syntax (i.e. jr:constraintMsg),
    # so we only use them if we have to for backwards compatibility.
    use_double_colons = has_double_colon(workbook_dict)

    # Break the spreadsheet dict into easier to access objects
    # (settings, choices, survey_sheet):
    # ########## Settings sheet ##########
    k = constants.SETTINGS
    if k not in workbook_dict:
        similar = find_sheet_misspellings(key=k, keys=workbook_keys)
        if similar is not None:
            warnings.append(similar + _MSG_SUPPRESS_SPELLING)
    settings_sheet_headers = workbook_dict.get(constants.SETTINGS, [])
    try:
        if (
            sum(
                [
                    element in [constants.ID_STRING, "form_id"]
                    for element in settings_sheet_headers[0].keys()
                ]
            )
            == 2
        ):
            settings_sheet_headers[0].pop(constants.ID_STRING, None)
            warnings.append(
                "The form_id and id_sting column headers are both"
                " specified in the settings sheet provided."
                " This may cause errors during conversion."
                " In future, its best to avoid specifying both"
                " column headers in the settings sheet."
            )
    except IndexError:  # In case there is no settings sheet
        settings_sheet_headers = []

    settings_sheet = dealias_and_group_headers(
        settings_sheet_headers, aliases.settings_header, use_double_colons
    )
    settings = settings_sheet[0] if len(settings_sheet) > 0 else {}
    replace_smart_quotes_in_dict(settings)

    default_language = settings.get(constants.DEFAULT_LANGUAGE_KEY, default_language)

    # add_none_option is a boolean that when true,
    # indicates a none option should automatically be added to selects.
    # It should probably be deprecated but I haven't checked yet.
    if "add_none_option" in settings:
        settings["add_none_option"] = aliases.yes_no.get(
            settings["add_none_option"], False
        )

    # Here we create our json dict root with default settings:
    id_string = settings.get(constants.ID_STRING, fallback_form_name)
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

    # ########## External Choices sheet ##########
    external_choices_sheet = workbook_dict.get(constants.EXTERNAL_CHOICES, [])
    for choice_item in external_choices_sheet:
        replace_smart_quotes_in_dict(choice_item)

    external_choices_sheet = dealias_and_group_headers(
        external_choices_sheet, aliases.list_header, use_double_colons, default_language
    )
    external_choices = group_dictionaries_by_key(
        external_choices_sheet, constants.LIST_NAME
    )

    # ########## Choices sheet ##########
    choices_sheet = workbook_dict.get(constants.CHOICES, [])
    for choice_item in choices_sheet:
        replace_smart_quotes_in_dict(choice_item)
    choices_sheet = dealias_and_group_headers(
        choices_sheet, aliases.list_header, use_double_colons, default_language
    )
    combined_lists = group_dictionaries_by_key(choices_sheet, constants.LIST_NAME)
    # To combine the warning into one message, the check for missing choices translation
    # columns is run with Survey sheet below.

    choices = combined_lists
    # Make sure all the options have the required properties:
    warnedabout = set()
    for list_name, options in choices.items():
        for option in options:
            if "name" not in option:
                info = "[list_name : " + list_name + "]"
                raise PyXFormError(
                    "On the choices sheet there is " "a option with no name. " + info
                )
            if "label" not in option:
                info = "[list_name : " + list_name + "]"
                warnings.append(
                    "On the choices sheet there is a option with no label. " + info
                )
            # chrislrobert's fix for a cryptic error message:
            # see: https://code.google.com/p/opendatakit/issues/detail?id=832&start=200 # noqa
            option_keys = list(option.keys())
            for headername in option_keys:
                # Using warnings and removing the bad columns
                # instead of throwing errors because some forms
                # use choices column headers for notes.
                if " " in headername:
                    if headername not in warnedabout:
                        warnedabout.add(headername)
                        warnings.append(
                            "On the choices sheet there is "
                            + 'a column ("'
                            + headername
                            + '") with an illegal header. '
                            + "Headers cannot include spaces."
                        )
                    del option[headername]
                elif headername == "":
                    warnings.append(
                        "On the choices sheet there is a value"
                        + " in a column with no header."
                    )
                    del option[headername]
        list_name_choices = [option.get("name") for option in options]
        if len(list_name_choices) != len(set(list_name_choices)):
            duplicate_setting = settings.get("allow_choice_duplicates")
            for k, v in Counter(list_name_choices).items():
                if v > 1:
                    if not duplicate_setting or duplicate_setting.capitalize() != "Yes":
                        choice_duplicates = [
                            item
                            for item, count in Counter(list_name_choices).items()
                            if count > 1
                        ]

                        if choice_duplicates:
                            raise PyXFormError(
                                "The name column for the '{}' choice list contains these duplicates: {}. Duplicate names "
                                "will be impossible to identify in analysis unless a previous value in a cascading "
                                "select differentiates them. If this is intentional, you can set the "
                                "allow_choice_duplicates setting to 'yes'. Learn more: https://xlsform.org/#choice-names.".format(
                                    list_name,
                                    ", ".join(
                                        [
                                            "'{}'".format(dupe)
                                            for dupe in choice_duplicates
                                        ]
                                    ),
                                )
                            )  # noqa

    # ########## Survey sheet ###########
    survey_sheet = workbook_dict[constants.SURVEY]
    # Process the headers:
    clean_text_values_enabled = aliases.yes_no.get(
        settings.get("clean_text_values", "true()")
    )
    if clean_text_values_enabled:
        survey_sheet = clean_text_values(survey_sheet)
    survey_sheet = dealias_and_group_headers(
        survey_sheet, aliases.survey_header, use_double_colons, default_language
    )
    survey_sheet = dealias_types(survey_sheet)

    # Check for missing translations. The choices sheet is checked here so that the
    # warning can be combined into one message.
    warnings = missing_translations_check(
        survey_sheet=survey_sheet,
        choices_sheet=choices_sheet,
        warnings=warnings,
    )

    # No spell check for OSM sheet (infrequently used, many spurious matches).
    osm_sheet = dealias_and_group_headers(
        workbook_dict.get(constants.OSM, []), aliases.list_header, True
    )
    osm_tags = group_dictionaries_by_key(osm_sheet, constants.LIST_NAME)
    # #################################

    # Parse the survey sheet while generating a survey in our json format:
    row_number = 1  # We start at 1 because the column header row is not
    #                 included in the survey sheet (presumably).
    # A stack is used to keep track of begin/end expressions
    stack = [
        {
            "control_type": None,
            "control_name": None,
            "parent_children": json_dict.get(constants.CHILDREN),
        }
    ]
    # If a group has a table-list appearance flag
    # this will be set to the name of the list
    table_list = None

    # For efficiency we compile all the regular expressions
    # that will be used to parse types:
    end_control_regex = re.compile(
        r"^(?P<end>end)(\s|_)(?P<type>(" + "|".join(aliases.control.keys()) + r"))$"
    )
    begin_control_regex = re.compile(
        r"^(?P<begin>begin)(\s|_)(?P<type>("
        + "|".join(aliases.control.keys())
        + r"))( (over )?(?P<list_name>\S+))?$"
    )
    select_regexp = re.compile(
        r"^(?P<select_command>("
        + "|".join(aliases.select.keys())
        + r")) (?P<list_name>\S+)"
        + "( (?P<specify_other>(or specify other|or_other|or other)))?$"
    )
    osm_regexp = re.compile(
        r"(?P<osm_command>(" + "|".join(aliases.osm.keys()) + r")) (?P<list_name>\S+)"
    )

    # Rows from the survey sheet that should be nested in meta
    survey_meta = []

    # row by row, validate questions, throwing errors and adding warnings
    # where needed.
    for row in survey_sheet:
        row_number += 1
        if stack[-1] is not None:
            prev_control_type = stack[-1]["control_type"]
            parent_children_array = stack[-1]["parent_children"]
        else:
            prev_control_type = None
            parent_children_array = []
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
        if len(row) == 0:
            continue

        # Get question type
        question_type = row.get(constants.TYPE)
        question_name = row.get(constants.NAME)

        if not question_type:
            # if name and label are also missing,
            # then its a comment row, and we skip it with warning
            if not ((constants.NAME in row) or (constants.LABEL in row)):
                warnings.append(
                    ROW_FORMAT_STRING % row_number
                    + " Row without name, text, or label is being skipped:\n"
                    + str(row)
                )
                continue
            raise PyXFormError(
                ROW_FORMAT_STRING % row_number + " Question with no type.\n" + str(row)
            )

        # Pull out questions that will go in meta block
        if question_type == "audit":
            # Force audit name to always be "audit" to follow XForms spec
            if "name" in row and row["name"] not in [None, "", "audit"]:
                raise PyXFormError(
                    ROW_FORMAT_STRING % row_number
                    + " Audits must always be named 'audit.'"
                    + " The name column should be left blank."
                )
            row["name"] = "audit"

            new_dict = row.copy()
            parameters = get_parameters(
                new_dict.get("parameters", ""),
                [
                    constants.LOCATION_PRIORITY,
                    constants.LOCATION_MIN_INTERVAL,
                    constants.LOCATION_MAX_AGE,
                    constants.TRACK_CHANGES,
                    constants.IDENTIFY_USER,
                    constants.TRACK_CHANGES_REASONS,
                ],
            )

            if constants.TRACK_CHANGES in parameters.keys():
                if (
                    parameters[constants.TRACK_CHANGES] != "true"
                    and parameters[constants.TRACK_CHANGES] != "false"
                ):
                    raise PyXFormError(
                        constants.TRACK_CHANGES + " must be set to true or false: "
                        "'%s' is an invalid value" % parameters[constants.TRACK_CHANGES]
                    )
                else:
                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {
                            "odk:"
                            + constants.TRACK_CHANGES: parameters[constants.TRACK_CHANGES]
                        }
                    )

            if constants.TRACK_CHANGES_REASONS in parameters.keys():
                if parameters[constants.TRACK_CHANGES_REASONS] != "on-form-edit":
                    raise PyXFormError(
                        constants.TRACK_CHANGES_REASONS + " must be set to on-form-edit"
                    )
                else:
                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {"odk:" + constants.TRACK_CHANGES_REASONS: "on-form-edit"}
                    )

            if constants.IDENTIFY_USER in parameters.keys():
                if (
                    parameters[constants.IDENTIFY_USER] != "true"
                    and parameters[constants.IDENTIFY_USER] != "false"
                ):
                    raise PyXFormError(
                        constants.IDENTIFY_USER + " must be set to true or false: "
                        "'%s' is an invalid value" % parameters[constants.IDENTIFY_USER]
                    )
                else:
                    new_dict["bind"] = new_dict.get("bind", {})
                    new_dict["bind"].update(
                        {
                            "odk:"
                            + constants.IDENTIFY_USER: parameters[constants.IDENTIFY_USER]
                        }
                    )

            location_parameters = (
                constants.LOCATION_PRIORITY,
                constants.LOCATION_MIN_INTERVAL,
                constants.LOCATION_MAX_AGE,
            )
            if any(k in parameters.keys() for k in location_parameters):
                if all(k in parameters.keys() for k in location_parameters):

                    if parameters[constants.LOCATION_PRIORITY] not in [
                        "no-power",
                        "low-power",
                        "balanced",
                        "high-accuracy",
                    ]:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_PRIORITY
                            + " must be set to no-power, low-power, balanced,"
                            " or high-accuracy: '%s' is an invalid value"
                            % parameters[constants.LOCATION_PRIORITY]
                        )

                    try:
                        int(parameters[constants.LOCATION_MIN_INTERVAL])
                    except ValueError:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MIN_INTERVAL
                            + " must have an integer value."
                        )
                    if int(parameters[constants.LOCATION_MIN_INTERVAL]) < 0:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MIN_INTERVAL
                            + " must be greater than or equal to zero."
                        )

                    try:
                        int(parameters[constants.LOCATION_MAX_AGE])
                    except ValueError:
                        raise PyXFormError(
                            "Parameter "
                            + constants.LOCATION_MAX_AGE
                            + " must have an integer value."
                        )
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
                            "odk:"
                            + constants.LOCATION_MAX_AGE: parameters[
                                constants.LOCATION_MAX_AGE
                            ],
                            "odk:"
                            + constants.LOCATION_MIN_INTERVAL: parameters[
                                constants.LOCATION_MIN_INTERVAL
                            ],
                            "odk:"
                            + constants.LOCATION_PRIORITY: parameters[
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

            survey_meta.append(new_dict)
            continue

        if question_type == "calculate":
            calculation = row.get("bind", {}).get("calculate")
            question_default = row.get("default")
            if not calculation and not (
                question_default and default_is_dynamic(question_default, question_type)
            ):
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
        end_control_parse = end_control_regex.search(question_type)
        if end_control_parse:
            parse_dict = end_control_parse.groupdict()
            if parse_dict.get("end") and "type" in parse_dict:
                control_type = aliases.control[parse_dict["type"]]
                control_name = question_name
                if prev_control_type != control_type or len(stack) == 1:
                    raise PyXFormError(
                        ROW_FORMAT_STRING % row_number
                        + " Unmatched end statement. Previous control type: "
                        + str(prev_control_type)
                        + ", Control type: "
                        + str(control_type)
                        + ", Control name: "
                        + str(control_name)
                    )
                stack.pop()
                table_list = None
                continue

        # Make sure the row has a valid name
        if constants.NAME not in row:
            if row["type"] == "note":
                # autogenerate names for notes without them
                row["name"] = "generated_note_name_" + str(row_number)
            # elif 'group' in row['type'].lower():
            #     # autogenerate names for groups without them
            #     row['name'] = "generated_group_name_" + str(row_number)
            else:
                raise PyXFormError(
                    ROW_FORMAT_STRING % row_number + " Question or group with no name."
                )
        question_name = str(row[constants.NAME])
        if not is_valid_xml_tag(question_name):
            if isinstance(question_name, bytes):
                question_name = question_name.encode("utf-8")
            error_message = ROW_FORMAT_STRING % row_number
            error_message += " Invalid question name [" + question_name + "] "
            error_message += "Names must begin with a letter, colon," + " or underscore."
            error_message += (
                "Subsequent characters can include numbers," + " dashes, and periods."
            )
            raise PyXFormError(error_message)

        # Try to parse question as begin control statement
        # (i.e. begin loop/repeat/group):
        begin_control_parse = begin_control_regex.search(question_type)
        if begin_control_parse:
            parse_dict = begin_control_parse.groupdict()
            if parse_dict.get("begin") and "type" in parse_dict:
                # Create a new json dict with children, and the proper type,
                # and add it to parent_children_array in place of a question.
                # parent_children_array will then be set to its children array
                # (so following questions are nested under it)
                # until an end command is encountered.
                control_type = aliases.control[parse_dict["type"]]
                control_name = question_name

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
                    and not (
                        row.get("default")
                        and default_is_dynamic(row.get("default"), question_type)
                    )
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
                        + " %s has no label: " % control_type.capitalize()
                        + str(msg_dict)
                    )

                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = control_type
                child_list = list()
                new_json_dict[constants.CHILDREN] = child_list
                if control_type is constants.LOOP:
                    if not parse_dict.get("list_name"):
                        # TODO: Perhaps warn and make repeat into a group?
                        raise PyXFormError(
                            ROW_FORMAT_STRING % row_number
                            + " Repeat loop without list name."
                        )
                    list_name = parse_dict["list_name"]
                    if list_name not in choices:
                        raise PyXFormError(
                            ROW_FORMAT_STRING % row_number
                            + " List name not in columns sheet: "
                            + list_name
                        )
                    new_json_dict[constants.COLUMNS] = choices[list_name]

                # Generate a new node for the jr:count column so
                # xpath expressions can be used.
                repeat_count_expression = new_json_dict.get("control", {}).get("jr:count")
                if repeat_count_expression:
                    generated_node_name = new_json_dict["name"] + "_count"
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
                    new_json_dict["control"]["jr:count"] = (
                        "${" + generated_node_name + "}"
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
                        "control_name": control_name,
                        "parent_children": child_list,
                    }
                )
                continue

        # Try to parse question as a select:
        select_parse = select_regexp.search(question_type)
        if select_parse:
            parse_dict = select_parse.groupdict()
            if parse_dict.get("select_command"):
                select_type = aliases.select[parse_dict["select_command"]]
                if select_type == "select one external" and "choice_filter" not in row:
                    warnings.append(
                        ROW_FORMAT_STRING % row_number
                        + " select one external is only meant for"
                        " filtered selects."
                    )
                list_name = parse_dict["list_name"]
                list_file_name, file_extension = os.path.splitext(list_name)
                if (
                    select_type == "select one external"
                    and list_name not in external_choices
                ):
                    if not external_choices:
                        k = constants.EXTERNAL_CHOICES
                        msg = "There should be an external_choices sheet in this xlsform."
                        similar = find_sheet_misspellings(key=k, keys=workbook_keys)
                        if similar is not None:
                            msg = msg + " " + similar
                        raise PyXFormError(
                            msg
                            + " Please ensure that the external_choices sheet has columns"
                            " 'list name', and 'name'."
                        )
                    raise PyXFormError(
                        ROW_FORMAT_STRING % row_number
                        + "List name not in external choices sheet: "
                        + list_name
                    )
                if (
                    list_name not in choices
                    and select_type != "select one external"
                    and file_extension not in EXTERNAL_INSTANCE_EXTENSIONS
                    and not re.match(r"\$\{(.*?)\}", list_name)
                ):
                    if not choices:
                        k = constants.CHOICES
                        msg = "There should be a choices sheet in this xlsform."
                        similar = find_sheet_misspellings(key=k, keys=workbook_keys)
                        if similar is not None:
                            msg = msg + " " + similar
                        raise PyXFormError(
                            msg + " Please ensure that the choices sheet has the"
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
                    select_type += " or specify other"

                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = select_type

                select_params_allowed = ["randomize", "seed"]
                if parse_dict["select_command"] in (
                    "select_one_from_file",
                    "select_multiple_from_file",
                ):
                    select_params_allowed += ["value", "label"]

                # Look at parameters column for select parameters
                parameters = get_parameters(
                    row.get("parameters", ""), select_params_allowed
                )

                if "randomize" in parameters.keys():
                    if (
                        parameters["randomize"] != "true"
                        and parameters["randomize"] != "false"
                    ):
                        raise PyXFormError(
                            "randomize must be set to true or false: "
                            "'%s' is an invalid value" % parameters["randomize"]
                        )

                    if "seed" in parameters.keys():
                        if not parameters["seed"].startswith("${"):
                            try:
                                float(parameters["seed"])
                            except ValueError:
                                raise PyXFormError(
                                    "seed value must be a number or a reference to another field."
                                )
                elif "seed" in parameters.keys():
                    raise PyXFormError(
                        "Parameters must include randomize=true to use a seed."
                    )

                if "value" in parameters.keys():
                    select_from_file_params.value_or_label_check(
                        name="value",
                        value=parameters["value"],
                        row_number=row_number,
                    )
                if "label" in parameters.keys():
                    select_from_file_params.value_or_label_check(
                        name="label",
                        value=parameters["label"],
                        row_number=row_number,
                    )

                new_json_dict["parameters"] = parameters

                if row.get("choice_filter"):
                    if select_type == "select one external":
                        new_json_dict["query"] = list_name
                    else:
                        new_json_dict["itemset"] = list_name
                        json_dict["choices"] = choices
                        if choices.get(list_name):
                            new_json_dict["list_name"] = list_name
                            new_json_dict[constants.CHOICES] = choices[list_name]
                elif (
                    "randomize" in parameters.keys() and parameters["randomize"] == "true"
                ):
                    new_json_dict["itemset"] = list_name
                    json_dict["choices"] = choices
                elif file_extension in EXTERNAL_INSTANCE_EXTENSIONS or re.match(
                    r"\$\{(.*?)\}", list_name
                ):
                    new_json_dict["itemset"] = list_name
                else:
                    new_json_dict["list_name"] = list_name
                    new_json_dict[constants.CHOICES] = choices[list_name]

                # Code to deal with table_list appearance flags
                # (for groups of selects)
                if table_list is not None:
                    # Then this row is the first select in a table list
                    if not isinstance(table_list, str):
                        table_list = list_name
                        table_list_header = {
                            constants.TYPE: select_type,
                            constants.NAME: "reserved_name_for_field_list_labels_"
                            + str(row_number),
                            # Adding row number for uniqueness # noqa
                            constants.CONTROL: {"appearance": "label"},
                            constants.CHOICES: choices[list_name],
                            # Do we care about filtered selects in table lists?
                            # 'itemset' : list_name,
                        }
                        parent_children_array.append(table_list_header)

                    if table_list != list_name:
                        error_message = ROW_FORMAT_STRING % row_number
                        error_message += (
                            " Badly formatted table list,"
                            " list names don't match: " + table_list + " vs. " + list_name
                        )
                        raise PyXFormError(error_message)

                    control = new_json_dict["control"] = new_json_dict.get("control", {})
                    control["appearance"] = "list-nolabel"
                parent_children_array.append(new_json_dict)
                if specify_other_question:
                    parent_children_array.append(specify_other_question)
                continue

        # Try to parse question as osm:
        osm_parse = osm_regexp.search(question_type)
        if osm_parse:
            parse_dict = osm_parse.groupdict()
            new_dict = row.copy()
            new_dict["type"] = constants.OSM

            if parse_dict.get("list_name") is not None:
                tags = osm_tags.get(parse_dict.get("list_name"))
                for tag in tags:
                    if osm_tags.get(tag.get("name")):
                        tag["choices"] = osm_tags.get(tag.get("name"))
                new_dict["tags"] = tags

            parent_children_array.append(new_dict)

            continue

        # range question_type
        if question_type == "range":
            new_dict = process_range_question_type(row)
            parent_children_array.append(new_dict)
            continue

        if question_type == "photo":
            new_dict = row.copy()

            if row.get("default"):
                new_dict["default"] = process_image_default(row["default"])
            # Validate max-pixels
            parameters = get_parameters(row.get("parameters", ""), ["max-pixels"])
            if "max-pixels" in parameters.keys():
                try:
                    int(parameters["max-pixels"])
                except ValueError:
                    raise PyXFormError("Parameter max-pixels must have an integer value.")

                new_dict["bind"] = new_dict.get("bind", {})
                new_dict["bind"].update({"orx:max-pixels": parameters["max-pixels"]})
            else:
                warnings.append(
                    (ROW_FORMAT_STRING % row_number)
                    + " Use the max-pixels parameter to speed up submission sending and save storage space. Learn more: https://xlsform.org/#image"
                )
            parent_children_array.append(new_dict)
            continue

        if question_type == "audio":
            new_dict = row.copy()
            parameters = get_parameters(row.get("parameters", ""), ["quality"])

            if "quality" in parameters.keys():
                if parameters["quality"] not in [
                    constants.AUDIO_QUALITY_VOICE_ONLY,
                    constants.AUDIO_QUALITY_LOW,
                    constants.AUDIO_QUALITY_NORMAL,
                    constants.AUDIO_QUALITY_EXTERNAL,
                ]:
                    raise PyXFormError("Invalid value for quality.")

                new_dict["bind"] = new_dict.get("bind", {})
                new_dict["bind"].update({"odk:quality": parameters["quality"]})

            parent_children_array.append(new_dict)
            continue

        if question_type == "background-audio":
            new_dict = row.copy()
            parameters = get_parameters(row.get("parameters", ""), ["quality"])

            if "quality" in parameters.keys():
                if parameters["quality"] not in [
                    constants.AUDIO_QUALITY_VOICE_ONLY,
                    constants.AUDIO_QUALITY_LOW,
                    constants.AUDIO_QUALITY_NORMAL,
                ]:
                    raise PyXFormError("Invalid value for quality.")

                new_dict["action"] = new_dict.get("action", {})
                new_dict["action"].update({"odk:quality": parameters["quality"]})

            parent_children_array.append(new_dict)
            continue

        if question_type in ["geopoint", "geoshape", "geotrace"]:
            new_dict = row.copy()

            if question_type == "geopoint":
                parameters = get_parameters(
                    row.get("parameters", ""),
                    ["allow-mock-accuracy", "capture-accuracy", "warning-accuracy"],
                )
            else:
                parameters = get_parameters(
                    row.get("parameters", ""), ["allow-mock-accuracy"]
                )

            if "allow-mock-accuracy" in parameters.keys():
                if parameters["allow-mock-accuracy"] not in ["true", "false"]:
                    raise PyXFormError("Invalid value for allow-mock-accuracy.")

                new_dict["bind"] = new_dict.get("bind", {})
                new_dict["bind"].update(
                    {"odk:allow-mock-accuracy": parameters["allow-mock-accuracy"]}
                )

            new_dict["control"] = new_dict.get("control", {})
            if "capture-accuracy" in parameters.keys():
                try:
                    float(parameters["capture-accuracy"])
                    new_dict["control"].update(
                        {"accuracyThreshold": parameters["capture-accuracy"]}
                    )
                except ValueError:
                    raise PyXFormError(
                        "Parameter capture-accuracy must have a numeric value"
                    )

            if "warning-accuracy" in parameters.keys():
                try:
                    float(parameters["warning-accuracy"])
                    new_dict["control"].update(
                        {"unacceptableAccuracyThreshold": parameters["warning-accuracy"]}
                    )
                except ValueError:
                    raise PyXFormError(
                        "Parameter warning-accuracy must have a numeric value"
                    )

            parent_children_array.append(new_dict)
            continue

        # TODO: Consider adding some question_type validation here.

        # Put the row in the json dict as is:
        parent_children_array.append(row)

    if len(stack) != 1:
        raise PyXFormError(
            "Unmatched begin statement: "
            + str(stack[-1]["control_type"] + " (" + stack[-1]["control_name"] + ")")
        )

    if settings.get("flat", False):
        # print "Generating flattened instance..."
        add_flat_annotations(stack[0]["parent_children"])

    meta_children = [] + survey_meta

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

    if "instance_name" in settings:
        # Automatically add an instanceName element:
        meta_children.append(
            {
                "name": "instanceName",
                "bind": {"calculate": settings["instance_name"]},
                "type": "calculate",
            }
        )

    if len(meta_children) > 0:
        meta_element = {
            "name": "meta",
            "type": "group",
            "control": {"bodyless": True},
            "children": meta_children,
        }
        survey_children_array = stack[0]["parent_children"]
        survey_children_array.append(meta_element)

    # print_pyobj_to_json(json_dict)
    return json_dict


def parse_file_to_workbook_dict(path, file_object=None):
    """
    Given a xls or csv workbook file use xls2json_backends to create
    a python workbook_dict.
    workbook_dicts are organized as follows:
    {sheetname : [{column_header : column_value_in_array_indexed_row}]}
    """

    (filepath, filename) = os.path.split(path)
    if not filename:
        raise PyXFormError("No filename.")
    (shortname, extension) = os.path.splitext(filename)
    if not extension:
        raise PyXFormError("No extension.")

    if extension in constants.XLS_EXTENSIONS:
        return xls_to_dict(file_object if file_object is not None else path)
    elif extension in constants.XLSX_EXTENSIONS:
        return xlsx_to_dict(file_object if file_object is not None else path)
    elif extension == ".csv":
        return csv_to_dict(file_object if file_object is not None else path)
    else:
        raise PyXFormError("File was not recognized")


def get_filename(path):
    """
    Get the extensionless filename from a path
    """
    return os.path.splitext((os.path.basename(path)))[0]


def parse_file_to_json(
    path,
    default_name="data",
    default_language=constants.DEFAULT_LANGUAGE_VALUE,
    warnings=None,
    file_object=None,
):
    """
    A wrapper for workbook_to_json
    """
    if warnings is None:
        warnings = []
    workbook_dict = parse_file_to_workbook_dict(path, file_object)
    fallback_form_name = str(get_filename(path))
    return workbook_to_json(
        workbook_dict, default_name, fallback_form_name, default_language, warnings
    )


def organize_by_values(dict_list, key):
    """
    dict_list -- a list of dicts
    key -- a key shared by all the dicts in dict_list
    Returns a dict of dicts keyed by the value of the specified key
    in each dictionary.
    If two dictionaries fall under the same key an error is thrown.
    If a dictionary is doesn't have the specified key it is omitted
    """
    result = {}
    for dicty in dict_list:
        if key in dicty:
            dicty_copy = dicty.copy()
            val = dicty_copy.pop(key)
            if val in result:
                raise Exception("Duplicate key: " + val)
            result[val] = dicty_copy
    return result


def get_parameters(raw_parameters, allowed_parameters):
    parts = raw_parameters.split(";")
    if len(parts) == 1:
        parts = raw_parameters.split(",")
    if len(parts) == 1:
        parts = raw_parameters.split()

    params = {}
    for param in parts:
        if "=" not in param:
            raise PyXFormError(
                "Expecting parameters to be in the form of "
                "'parameter1=value parameter2=value'."
            )
        k, v = param.split("=")[:2]
        key = k.lower().strip()
        if key in allowed_parameters:
            params[key] = v.lower().strip()
        else:
            raise PyXFormError(
                "Accepted parameters are "
                "'%s': '%s' is an invalid parameter."
                % (", ".join(allowed_parameters), key)
            )

    return params


class SpreadsheetReader:
    def __init__(self, path_or_file):
        path = path_or_file
        try:
            path = path.name
        except AttributeError:
            pass
        self._dict = parse_file_to_workbook_dict(path)
        self._path = path
        self._id = str(get_filename(path))
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
        warn_out = open(warn_out_file, "w")
        warn_out.write("\n".join(self._warnings))


class QuestionTypesReader(SpreadsheetReader):
    """
    Class for reading spreadsheet file that specifies the available
    question types.
    @see question_type_dictionary
    """

    def __init__(self, path):
        super(QuestionTypesReader, self).__init__(path)
        self._setup_question_types_dictionary()

    def _setup_question_types_dictionary(self):
        use_double_colons = has_double_colon(self._dict)
        types_sheet = "question types"
        self._dict = self._dict[types_sheet]
        self._dict = dealias_and_group_headers(
            dict_array=self._dict,
            header_aliases={},
            use_double_colons=use_double_colons,
            default_language=constants.DEFAULT_LANGUAGE_VALUE,
        )
        self._dict = organize_by_values(self._dict, "name")


# Not used internally (or on formhub)
# TODO: If this is used anywhere else it is probably broken
#      from the changes I made to SpreadsheetReader.
class VariableNameReader(SpreadsheetReader):
    def __init__(self, path):
        SpreadsheetReader.__init__(self, path)
        self._organize_renames()

    def _organize_renames(self):
        new_dict = {}
        variable_names_so_far = []
        assert "Dictionary" in self._dict
        for d in self._dict["Dictionary"]:
            if "Variable Name" in d:
                assert d["Variable Name"] not in variable_names_so_far, d["Variable Name"]
                variable_names_so_far.append(d["Variable Name"])
                new_dict[d["XPath"]] = d["Variable Name"]
            else:
                variable_names_so_far.append(d["XPath"])
        self._dict = new_dict


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
