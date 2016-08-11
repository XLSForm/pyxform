"""
A Python script to convert excel files into JSON.
"""
import json
import re
import sys
import codecs
import os
import constants
import aliases
from errors import PyXFormError
from xls2json_backends import xls_to_dict, csv_to_dict
from utils import is_valid_xml_tag


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
        print json.dumps(pyobj, ensure_ascii=False, indent=4)


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
        out_dict[key] = merge_dicts(
            dict_a.get(key), dict_b.get(key), default_key)
    return out_dict


def list_to_nested_dict(lst):
    """
    [1,2,3,4] -> {1:{2:{3:4}}}
    """
    if len(lst) > 1:
        return {lst[0]: list_to_nested_dict(lst[1:])}
    else:
        return lst[0]


def dealias_and_group_headers(dict_array, header_aliases, use_double_colons,
                              default_language=u"default", ignore_case=False):
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
    GROUP_DELIMITER = u"::"
    out_dict_array = list()
    for row in dict_array:
        out_row = dict()
        for header, val in row.items():

            if ignore_case:
                header = header.lower()

            tokens = list()

            if use_double_colons:
                tokens = header.split(GROUP_DELIMITER)

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
                tokens = header.split(u":")
                if "jr" in tokens:
                    jr_idx = tokens.index("jr")
                    tokens[jr_idx] = u":".join(tokens[jr_idx: jr_idx + 2])
                    tokens.pop(jr_idx + 1)

            dealiased_first_token = header_aliases.get(tokens[0], tokens[0])
            tokens = dealiased_first_token.split(GROUP_DELIMITER) + tokens[1:]
            new_key = tokens[0]
            new_value = list_to_nested_dict(tokens[1:] + [val])
            out_row = merge_dicts(
                out_row, {new_key: new_value}, default_language)

        out_dict_array.append(out_row)
    return out_dict_array


def dealias_types(dict_array):
    """
    Look at all the type values in a dict array and if any aliases are found,
    replace them with the name they map to.
    """
    for row in dict_array:
        found_type = row.get(constants.TYPE)
        if found_type in aliases._type.keys():
            row[constants.TYPE] = aliases._type[found_type]
    return dict_array


def clean_text_values(dict_array):
    """
    Go though the dict array and strips all text values.
    Also replaces multiple spaces with single spaces.
    Note that the keys don't get cleaned, which could be an issue.
    """
    for row in dict_array:
        for key, value in row.items():
            if isinstance(value, basestring):
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
                    "Question name is not unique: " +
                    str(name) + " Row: " + str(row_number))
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


def has_double_colon(workbook_dict):
    """
    Look for a column header with a doublecolon (::) and
    return true if one is found.
    """
    for sheet in workbook_dict.values():
        for row in sheet:
            for column_header in row.keys():
                if type(column_header) is not unicode:
                    continue
                if u"::" in column_header:
                    return True
    return False


def add_flat_annotations(prompt_list, parent_relevant='', name_prefix=''):
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
        prompt_relevant = prompt.get('bind', {}).get('relevant', '')
        new_relevant = ''
        if parent_relevant != '':
            new_relevant += parent_relevant
            if prompt_relevant != '':
                new_relevant += ' and (' + prompt_relevant + ')'
        elif prompt_relevant != '':
            new_relevant = prompt_relevant

        children = prompt.get(constants.CHILDREN)
        if children:
            prompt['flat'] = True
            add_flat_annotations(children, new_relevant,
                                 name_prefix + '_' + prompt['name'])
        else:
            if new_relevant != '':
                prompt['bind'] = prompt.get('bind', {})
                prompt['bind']['relevant'] = new_relevant
            # if name_prefix != '':
            #    prompt['name'] = name_prefix + prompt['name']


def workbook_to_json(
        workbook_dict, form_name=None,
        default_language=u"default", warnings=[]):
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
    # ensure required headers are present
    is_valid = False
    for row in workbook_dict.get('survey', []):
        is_valid = 'type' in row
        if is_valid:
            break
    if not is_valid:
        raise PyXFormError(u"The survey sheet is either empty or missing important "
                            u"column headers.")

    rowFormatString = '[row : %s]'

    # Make sure the passed in vars are unicode
    form_name = unicode(form_name)
    default_language = unicode(default_language)

    # We check for double columns to determine whether to use them
    # or single colons to delimit grouped headers.
    # Single colons are bad because they conflict with with the xform namespace
    # syntax (i.e. jr:constraintMsg),
    # so we only use them if we have to for backwards compatibility.
    use_double_colons = has_double_colon(workbook_dict)

    # Break the spreadsheet dict into easier to access objects
    # (settings, choices, survey_sheet):
    # ########## Settings sheet ##########
    settings_sheet = dealias_and_group_headers(
        workbook_dict.get(constants.SETTINGS, []),
        aliases.settings_header, use_double_colons)
    settings = settings_sheet[0] if len(settings_sheet) > 0 else {}

    default_language = settings.get(
        constants.DEFAULT_LANGUAGE, default_language)

    # add_none_option is a boolean that when true,
    # indicates a none option should automatically be added to selects.
    # It should probably be deprecated but I haven't checked yet.
    if u"add_none_option" in settings:
        settings[u"add_none_option"] = aliases.yes_no.get(
            settings[u"add_none_option"], False)

    # Here we create our json dict root with default settings:
    id_string = settings.get(constants.ID_STRING, form_name)
    sms_keyword = settings.get(constants.SMS_KEYWORD, id_string)
    json_dict = {
        constants.TYPE: constants.SURVEY,
        constants.NAME: form_name,
        constants.TITLE: id_string,
        constants.ID_STRING: id_string,
        constants.SMS_KEYWORD: sms_keyword,
        constants.DEFAULT_LANGUAGE: default_language,
        # By default the version is based on the date and time yyyymmddhh
        # Leaving default version out for now since it might cause
        # problems for formhub.
        # constants.VERSION : datetime.datetime.now().strftime("%Y%m%d%H"),
        constants.CHILDREN: []
    }
    # Here the default settings are overridden by those in the settings sheet
    json_dict.update(settings)

    # ########## Choices sheet ##########
    # Columns and "choices and columns" sheets are deprecated,
    # but we combine them with the choices sheet for backwards-compatibility.
    choices_and_columns_sheet = workbook_dict.get(
        constants.CHOICES_AND_COLUMNS, {})
    choices_and_columns_sheet = dealias_and_group_headers(
        choices_and_columns_sheet, aliases.list_header,
        use_double_colons, default_language)

    columns_sheet = workbook_dict.get(constants.COLUMNS, [])
    columns_sheet = dealias_and_group_headers(
        columns_sheet, aliases.list_header,
        use_double_colons, default_language)

    choices_sheet = workbook_dict.get(constants.CHOICES, [])
    choices_sheet = dealias_and_group_headers(
        choices_sheet, aliases.list_header, use_double_colons,
        default_language)
    # ########## Cascading Select sheet ###########
    cascading_choices = workbook_dict.get(constants.CASCADING_CHOICES, [])
    if len(cascading_choices):
        if 'choices' in cascading_choices[0]:
            choices_sheet = choices_sheet + cascading_choices[0]['choices']

    combined_lists = group_dictionaries_by_key(
        choices_and_columns_sheet + choices_sheet + columns_sheet,
        constants.LIST_NAME)

    choices = combined_lists
    # Make sure all the options have the required properties:
    warnedabout = set()
    for list_name, options in choices.items():
        for option in options:
            if 'name' not in option:
                info = "[list_name : " + list_name + ']'
                raise PyXFormError("On the choices sheet there is "
                                   "a option with no name. " + info)
            if 'label' not in option:
                info = "[list_name : " + list_name + ']'
                warnings.append(
                    "On the choices sheet there is a option with no label. " +
                    info)
            # chrislrobert's fix for a cryptic error message:
            # see: https://code.google.com/p/opendatakit/issues/detail?id=832&start=200 # noqa
            for headername in option.keys():
                # Using warnings and removing the bad columns
                # instead of throwing errors because some forms
                # use choices column headers for notes.
                if ' ' in headername:
                    if headername not in warnedabout:
                        warnedabout.add(headername)
                        warnings.append("On the choices sheet there is " +
                                        "a column (\"" +
                                        headername +
                                        "\") with an illegal header. " +
                                        "Headers cannot include spaces.")
                    del option[headername]
                elif headername == '':
                    warnings.append("On the choices sheet there is a value" +
                                    " in a column with no header.")
                    del option[headername]
    # ########## Survey sheet ###########
    if constants.SURVEY not in workbook_dict:
        raise PyXFormError(
            "You must have a sheet named (case-sensitive): " +
            constants.SURVEY)
    survey_sheet = workbook_dict[constants.SURVEY]
    # Process the headers:
    clean_text_values_enabled = aliases.yes_no.get(
        settings.get("clean_text_values", "true()"))
    if clean_text_values_enabled:
        survey_sheet = clean_text_values(survey_sheet)
    survey_sheet = dealias_and_group_headers(
        survey_sheet, aliases.survey_header,
        use_double_colons, default_language)
    survey_sheet = dealias_types(survey_sheet)

    osm_sheet = workbook_dict.get(constants.OSM, [])
    osm_tags = group_dictionaries_by_key(osm_sheet, constants.LIST_NAME)
    # #################################

    # Parse the survey sheet while generating a survey in our json format:

    row_number = 1  # We start at 1 because the column header row is not
    #                 included in the survey sheet (presumably).
    # A stack is used to keep track of begin/end expressions
    stack = [(None, json_dict.get(constants.CHILDREN))]
    # If a group has a table-list appearance flag
    # this will be set to the name of the list
    table_list = None
    # For efficiency we compile all the regular expressions
    # that will be used to parse types:
    end_control_regex = re.compile(r"^(?P<end>end)(\s|_)(?P<type>(" +
                                   '|'.join(aliases.control.keys()) + r"))$")
    begin_control_regex = re.compile(r"^(?P<begin>begin)(\s|_)(?P<type>(" +
                                     '|'.join(aliases.control.keys()) +
                                     r"))( (over )?(?P<list_name>\S+))?$")
    select_regexp = re.compile(
        r"^(?P<select_command>(" + '|'.join(aliases.select.keys()) +
        r")) (?P<list_name>\S+)" +
        "( (?P<specify_other>(or specify other|or_other|or other)))?$")
    cascading_regexp = re.compile(
        r"^(?P<cascading_command>(" +
        '|'.join(aliases.cascading.keys()) +
        r")) (?P<cascading_level>\S+)?$")
    osm_regexp = re.compile(
        r"(?P<osm_command>(" + '|'.join(aliases.osm.keys()) +
        ')) (?P<list_name>\S+)')

    for row in survey_sheet:
        row_number += 1
        prev_control_type, parent_children_array = stack[-1]
        # Disabled should probably be first
        # so the attributes below can be disabled.
        if u"disabled" in row:
            warnings.append(
                rowFormatString % row_number +
                " The 'disabled' column header is not part of the current" +
                " spec. We recommend using relevant instead.")
            disabled = row.pop(u"disabled")
            if aliases.yes_no.get(disabled):
                continue

        # skip empty rows
        if len(row) == 0:
            continue

        # Get question type
        question_type = row.get(constants.TYPE)
        if not question_type:
            # if name and label are also missing,
            # then its a comment row, and we skip it with warning
            if not ((constants.NAME in row) or (constants.LABEL in row)):
                    warnings.append(
                        rowFormatString % row_number + " Row without name,"
                        " text, or label is being skipped:\n" + str(row))
                    continue
            raise PyXFormError(
                rowFormatString % row_number +
                " Question with no type.\n" + str(row))
            continue

        if question_type == 'calculate':
            calculation = row.get('bind', {}).get('calculate')
            if not calculation:
                raise PyXFormError(
                    rowFormatString % row_number + " Missing calculation.")

        # Check if the question is actually a setting specified
        # on the survey sheet
        settings_type = aliases.settings_header.get(question_type)
        if settings_type:
            json_dict[settings_type] = unicode(row.get(constants.NAME))
            continue

        # Try to parse question as a end control statement
        # (i.e. end loop/repeat/group):
        end_control_parse = end_control_regex.search(question_type)
        if end_control_parse:
            parse_dict = end_control_parse.groupdict()
            if parse_dict.get("end") and "type" in parse_dict:
                control_type = aliases.control[parse_dict["type"]]
                if prev_control_type != control_type or len(stack) == 1:
                    raise PyXFormError(
                        rowFormatString % row_number +
                        " Unmatched end statement. Previous control type: " +
                        str(prev_control_type) +
                        ", Control type: " + str(control_type))
                stack.pop()
                table_list = None
                continue

        # Make sure the row has a valid name
        if constants.NAME not in row:
            if row['type'] == 'note':
                # autogenerate names for notes without them
                row['name'] = "generated_note_name_" + str(row_number)
            # elif 'group' in row['type'].lower():
            #     # autogenerate names for groups without them
            #     row['name'] = "generated_group_name_" + str(row_number)
            else:
                raise PyXFormError(rowFormatString % row_number +
                                   " Question or group with no name.")
        question_name = unicode(row[constants.NAME])
        if not is_valid_xml_tag(question_name):
            error_message = rowFormatString % row_number
            error_message += " Invalid question name [" + question_name.encode('utf-8') + "] "
            error_message += "Names must begin with a letter, colon,"\
                             + " or underscore."
            error_message += "Subsequent characters can include numbers,"\
                             + " dashes, and periods."
            raise PyXFormError(error_message)

        if constants.LABEL not in row and \
           row.get(constants.MEDIA) is None and \
           question_type not in aliases.label_optional_types:
            # TODO: Should there be a default label?
            #      Not sure if we should throw warnings for groups...
            #      Warnings can be ignored so I'm not too concerned
            #      about false positives.
            warnings.append(
                rowFormatString % row_number +
                " Question has no label: " + str(row))

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
                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = control_type
                child_list = list()
                new_json_dict[constants.CHILDREN] = child_list
                if control_type is constants.LOOP:
                    if not parse_dict.get("list_name"):
                        # TODO: Perhaps warn and make repeat into a group?
                        raise PyXFormError(
                            rowFormatString % row_number +
                            " Repeat loop without list name.")
                    list_name = parse_dict["list_name"]
                    if list_name not in choices:
                        raise PyXFormError(
                            rowFormatString % row_number +
                            " List name not in columns sheet: " + list_name)
                    new_json_dict[constants.COLUMNS] = choices[list_name]

                # Generate a new node for the jr:count column so
                # xpath expressions can be used.
                repeat_count_expression = new_json_dict.get(
                    'control', {}).get('jr:count')
                if repeat_count_expression:
                    generated_node_name = new_json_dict['name'] + "_count"
                    parent_children_array.append({
                        "name": generated_node_name,
                        "bind": {
                            "readonly": "true()",
                            "calculate": repeat_count_expression,
                        },
                        "type": "calculate",
                    })
                    new_json_dict['control']['jr:count'] = \
                        "${" + generated_node_name + "}"

                # Code to deal with table_list appearance flags
                # (for groups of selects)
                ctrl_ap = new_json_dict.get(u"control", {}).get(u"appearance")
                if ctrl_ap == constants.TABLE_LIST:
                    table_list = True
                    new_json_dict[u"control"][u"appearance"] = u"field-list"
                    # Generate a note label element so hints and labels
                    # work as expected in table-lists.
                    # see https://github.com/modilabs/pyxform/issues/62
                    if 'label' in new_json_dict or 'hint' in new_json_dict:
                        generated_label_element = {
                            "type": "note",
                            "name":
                            "generated_table_list_label_" + str(row_number)
                        }
                        if 'label' in new_json_dict:
                            generated_label_element[constants.LABEL] = \
                                new_json_dict[constants.LABEL]
                            del new_json_dict[constants.LABEL]
                        if 'hint' in new_json_dict:
                            generated_label_element['hint'] = \
                                new_json_dict['hint']
                            del new_json_dict['hint']
                        child_list.append(generated_label_element)

                parent_children_array.append(new_json_dict)
                stack.append((control_type, child_list))
                continue

        # try to parse as a cascading select
        cascading_parse = cascading_regexp.search(question_type)
        if cascading_parse:
            parse_dict = cascading_parse.groupdict()
            if parse_dict.get("cascading_command"):
                cascading_level = parse_dict["cascading_level"]
                cascading_prefix = row.get(constants.NAME)
                if not cascading_prefix:
                    raise PyXFormError(
                        rowFormatString % row_number +
                        " Cascading select needs a name.")
                # cascading_json = get_cascading_json(
                # cascading_choices, cascading_prefix, cascading_level)
                if len(cascading_choices) <= 0 or\
                        'questions' not in cascading_choices[0]:
                    raise PyXFormError(
                        "Found a cascading_select " +
                        cascading_level + ", but could not"
                        " find " + cascading_level + "in cascades sheet.")
                cascading_json = cascading_choices[0]['questions']
                json_dict['choices'] = choices
                include_bindings = False
                if 'bind' in row:
                    include_bindings = True
                for cq in cascading_json:
                    # include bindings
                    if include_bindings:
                        cq['bind'] = row['bind']

                    def replace_prefix(d, prefix):
                        for k, v in d.items():
                            if isinstance(v, basestring):
                                d[k] = v.replace('$PREFIX$', prefix)
                            elif isinstance(v, dict):
                                d[k] = replace_prefix(v, prefix)
                            elif isinstance(v, list):
                                d[k] = map(
                                    lambda x: replace_prefix(x, prefix), v)
                        return d
                    parent_children_array.append(
                        replace_prefix(cq, cascading_prefix))
                continue  # so the row isn't put in as is

        # Try to parse question as a select:
        select_parse = select_regexp.search(question_type)
        if select_parse:
            parse_dict = select_parse.groupdict()
            if parse_dict.get("select_command"):
                select_type = aliases.select[parse_dict["select_command"]]
                if select_type == 'select one external'\
                        and 'choice_filter' not in row:
                    warnings.append(
                        rowFormatString % row_number +
                        u" select one external is only meant for"
                        u" filtered selects.")
                    select_type = aliases.select['select_one']
                list_name = parse_dict["list_name"]
                list_file_name, file_extension = os.path.splitext(list_name)

                if list_name not in choices \
                        and select_type != 'select one external' \
                        and file_extension not in ['.csv', '.xml']:
                    if not choices:
                        raise PyXFormError(
                            u"There should be a choices sheet in this xlsform."
                            u" Please ensure that the choices sheet name is "
                            u"all in small caps and has columns 'list name', "
                            u"'name', and 'label' (or aliased column names).")
                    raise PyXFormError(
                        rowFormatString % row_number +
                        " List name not in choices sheet: " + list_name)

                # Validate select_multiple choice names by making sure
                # they have no spaces (will cause errors in exports).
                if select_type == constants.SELECT_ALL_THAT_APPLY \
                        and file_extension not in ['.csv', '.xml']:
                    for choice in choices[list_name]:
                        if ' ' in choice[constants.NAME]:
                            raise PyXFormError(
                                "Choice names with spaces cannot be added "
                                "to multiple choice selects. See [" +
                                choice[constants.NAME] + "] in [" +
                                list_name + "]")

                specify_other_question = None
                if parse_dict.get("specify_other") is not None:
                    select_type += u" or specify other"
                    # With this code we no longer need to handle or_other
                    # questions in survey builder.
                    # However, it depends on being able to use choice filters
                    # and xpath expressions that return empty sets.
                    # choices[list_name].append(
                    # {
                    #     'name': 'other',
                    #     'label': {default_language : 'Other'},
                    #     'orOther': 'true',
                    # })
                    # or_other_xpath = 'isNull(orOther)'
                    # if 'choice_filter' in row:
                    #   row['choice_filter'] += ' or ' + or_other_xpath
                    # else:
                    #   row['choice_filter'] = or_other_xpath

                    # specify_other_question = \
                    # {
                    #       'type':'text',
                    #       'name': row['name'] + '_specify_other',
                    #       'label':
                    #        'Specify Other for:\n"' + row['label'] + '"',
                    #       'bind' : {'relevant':
                    #                "selected(../%s, 'other')" % row['name']},
                    #     }

                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = select_type

                if row.get('choice_filter'):
                    if select_type == 'select one external':
                        new_json_dict['query'] = list_name
                    else:
                        new_json_dict['itemset'] = list_name
                        json_dict['choices'] = choices
                elif file_extension in ['.csv', '.xml']:
                    new_json_dict['itemset'] = list_name
                else:
                    new_json_dict[constants.CHOICES] = choices[list_name]

                # Code to deal with table_list appearance flags
                # (for groups of selects)
                if table_list is not None:
                    # Then this row is the first select in a table list
                    if not isinstance(table_list, basestring):
                        table_list = list_name
                        table_list_header = {
                            constants.TYPE: select_type,
                            constants.NAME:
                            "reserved_name_for_field_list_labels_" +
                            str(row_number),  # Adding row number for uniqueness # noqa
                            constants.CONTROL: {u"appearance": u"label"},
                            constants.CHOICES: choices[list_name],
                            # Do we care about filtered selects in table lists?
                            # 'itemset' : list_name,
                        }
                        parent_children_array.append(table_list_header)

                    if table_list != list_name:
                        error_message = rowFormatString % row_number
                        error_message += " Badly formatted table list,"\
                                         " list names don't match: " +\
                                         table_list + " vs. " + list_name
                        raise PyXFormError(error_message)

                    control = new_json_dict[u"control"] = \
                        new_json_dict.get(u"control", {})
                    control[u"appearance"] = "list-nolabel"
                parent_children_array.append(new_json_dict)
                if specify_other_question:
                    parent_children_array.append(specify_other_question)
                continue

        # Try to parse question as osm:
        osm_parse = osm_regexp.search(question_type)
        if osm_parse:
            parse_dict = osm_parse.groupdict()
            new_dict = row.copy()
            new_dict['type'] = constants.OSM

            if parse_dict.get('list_name') is not None:
                tags = osm_tags.get(parse_dict.get('list_name'))
                for tag in tags:
                    if osm_tags.get(tag.get('name')):
                        tag['choices'] = osm_tags.get(tag.get('name'))
                new_dict['tags'] = tags

            parent_children_array.append(new_dict)

            continue

        # TODO: Consider adding some question_type validation here.

        # Put the row in the json dict as is:
        parent_children_array.append(row)

    if len(stack) != 1:
        raise PyXFormError("Unmatched begin statement: " + str(stack[-1][0]))

    if settings.get('flat', False):
        # print "Generating flattened instance..."
        add_flat_annotations(stack[0][1])

    meta_children = []

    if aliases.yes_no.get(settings.get("omit_instanceID")):
        if settings.get("public_key"):
            raise PyXFormError(
                "Cannot omit instanceID, it is required for encryption.")
    else:
        # Automatically add an instanceID element:
        meta_children.append({
            "name": "instanceID",
            "bind": {
                "readonly": "true()",
                "calculate": settings.get(
                    "instance_id", "concat('uuid:', uuid())"),
            },
            "type": "calculate",
        })

    if 'instance_name' in settings:
        # Automatically add an instanceName element:
        meta_children.append({
            "name": "instanceName",
            "bind": {
                "calculate": settings['instance_name']
            },
            "type": "calculate",
        })

    if len(meta_children) > 0:
        meta_element = \
            {
                "name": "meta",
                "type": "group",
                "control": {
                    "bodyless": True
                },
                "children": meta_children
            }
        noop, survey_children_array = stack[0]
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

    if extension == ".xls" or extension == ".xlsx":
        return xls_to_dict(file_object if file_object is not None else path)
    elif extension == ".csv":
        return csv_to_dict(file_object if file_object is not None else path)
    else:
        raise PyXFormError("File was not recognized")


def get_filename(path):
    """
    Get the extensionless filename from a path
    """
    return os.path.splitext((os.path.basename(path)))[0]


def parse_file_to_json(path, default_name=None, default_language=u"default",
                       warnings=[], file_object=None):
    """
    A wrapper for workbook_to_json
    """
    workbook_dict = parse_file_to_workbook_dict(path, file_object)
    if default_name is None:
        default_name = unicode(get_filename(path))
    return workbook_to_json(
        workbook_dict, default_name, default_language, warnings)


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


class SpreadsheetReader(object):
    def __init__(self, path_or_file):
        path = path_or_file
        if type(path_or_file) is file:
            path = path.name
        self._dict = parse_file_to_workbook_dict(path)
        self._path = path
        self._id = unicode(get_filename(path))
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
    def __init__(self, path_or_file):
        if isinstance(path_or_file, basestring):
            self._file_object = None
            path = path_or_file
        else:
            self._file_object = path_or_file
            path = path_or_file.name

        self._warnings = []
        self._dict = parse_file_to_json(
            path, warnings=self._warnings, file_object=self._file_object)
        self._path = path

    def print_warning_log(self, warn_out_file):
        # Open file to print warning log to.
        warn_out = open(warn_out_file, 'w')
        warn_out.write('\n'.join(self._warnings))


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
        TYPES_SHEET = u"question types"
        self._dict = self._dict[TYPES_SHEET]
        self._dict = dealias_and_group_headers(
            self._dict, {}, use_double_colons, u"default")
        self._dict = organize_by_values(self._dict, u"name")


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
        assert u"Dictionary" in self._dict
        for d in self._dict[u"Dictionary"]:
            if u"Variable Name" in d:
                assert d[u"Variable Name"] not in variable_names_so_far, \
                    d[u"Variable Name"]
                variable_names_so_far.append(d[u"Variable Name"])
                new_dict[d[u"XPath"]] = d[u"Variable Name"]
            else:
                variable_names_so_far.append(d[u"XPath"])
        self._dict = new_dict

if __name__ == "__main__":
    # Open the excel file specified by the argument of this python call,
    # convert that file to json, then print it
    if len(sys.argv) < 2:
        # print "You must supply a file argument."
        filename = "xlsform_spec_test.xls"
        path = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/"
        path += filename
    else:
        path = sys.argv[1]

    warnings = []
    json_dict = parse_file_to_json(path, warnings=warnings)
    print_pyobj_to_json(json_dict)

    if len(warnings) > 0:
        sys.stderr.write("Warnings:" + '\n')
        sys.stderr.write('\n'.join(warnings) + '\n')
