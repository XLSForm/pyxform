"""
A Python script to convert excel files into JSON.
"""
import json
import re
import sys
import codecs
import os
import constants
from errors import PyXFormError
from xls2json_backends import xls_to_dict, csv_to_dict, get_cascading_json
from utils import is_valid_xml_tag

####### STATIC DATA #######

#Aliases:
#Ideally aliases should resolve to elements in the json form schema

#select, control and settings alias keys used for parsing,
#which is why self mapped keys are necessary.
control_aliases = {
    u"group" : constants.GROUP,
    u"lgroup" : constants.REPEAT,
    u"repeat" : constants.REPEAT,
    u"loop" : constants.LOOP,
    u"looped group": constants.REPEAT
}
select_aliases = {
      u"add select one prompt using" : constants.SELECT_ONE,
      u"add select multiple prompt using" : constants.SELECT_ALL_THAT_APPLY,
      u"select all that apply from" : constants.SELECT_ALL_THAT_APPLY,
      u"select one from" : constants.SELECT_ONE,
      u"select1" : constants.SELECT_ONE, 
      u"select_one" : constants.SELECT_ONE,
      u"select one" : constants.SELECT_ONE,
      u"select_multiple" : constants.SELECT_ALL_THAT_APPLY,
      u"select all that apply" : constants.SELECT_ALL_THAT_APPLY
}
cascading_aliases = {
    u'cascading select' : constants.CASCADING_SELECT,
    u'cascading_select' : constants.CASCADING_SELECT,
}
settings_header_aliases = {
    u"form_title" : constants.TITLE,
    u"set form title" : constants.TITLE,
    u"form_id" : constants.ID_STRING,
    u"set form id" : constants.ID_STRING,
    u"public_key" : constants.PUBLIC_KEY,
    u"submission_url" : constants.SUBMISSION_URL
}
#TODO: Check on bind prefix approach in json.
#Conversion dictionary from user friendly column names to meaningful values
survey_header_aliases = {
    u"repeat_count" : u"jr:count",
    u"read_only" : u"bind::readonly",
    u"readonly" : u"bind::readonly",
    u"relevant": u"bind::relevant",
    u"caption": constants.LABEL,
    u"appearance": u"control::appearance", #TODO: this is also an issue
    u"relevance": u"bind::relevant",
    u"required": u"bind::required",
    u"constraint": u"bind::constraint",
    u"constraining message": u"bind::jr:constraintMsg",
    u"constraint message": u"bind::jr:constraintMsg",
    u"constraint_message": u"bind::jr:constraintMsg",
    u"calculation": u"bind::calculate",
    u"command": constants.TYPE,
    u"tag": constants.NAME,
    u"value": constants.NAME,
    u"image": u"media::image",
    u"audio": u"media::audio",
    u"video": u"media::video",
    u"count": u"bind::jr:count"
}
list_header_aliases = {
    u"caption" : constants.LABEL,
    u"list_name" : constants.LIST_NAME,
    u"value" : constants.NAME,
    u"image": u"media::image",
    u"audio": u"media::audio",
    u"video": u"media::video"
}
#Note that most of the type aliasing happens in all.xls
type_aliases = {
    u"imei" : u"deviceid",
    u"image" : u"photo",
    u"add image prompt" : u"photo",
    u"add photo prompt" : u"photo",
    u"add audio prompt" : u"audio",
    u"add video prompt" : u"video"
}
yes_no_aliases = {
    "yes": "true()",
    "Yes": "true()",
    "YES": "true()",
    "true": "true()",
    "True": "true()",
    "TRUE": "true()",
    "no": "false()",
    "No": "false()",
    "NO": "false()",
    "false": "false()",
    "False": "false()",
    "FALSE": "false()"
}
label_optional_types = [
    u"deviceid",
    u"phonenumber",
    u"simserial",
    u"calculate",
    u"start",
    u"end",
    u"today"
]
####### END OF STATIC DATA #######

def print_pyobj_to_json(pyobj, path=None):
    """
    dump a python nested array/dict structure to the specified file or stdout if no file is specified
    """
    if path:
        fp = codecs.open(path, mode="w", encoding="utf-8")
        json.dump(pyobj, fp=fp, ensure_ascii=False, indent=4)
        fp.close()
    else:
        print json.dumps(pyobj, ensure_ascii=False, indent=4)
    
def merge_dicts(dict_a, dict_b, default_key = "default"):
    """
    Recursively merge two nested dicts into a single dict.
    When keys match their values are merged using a recursive call to this function,
    otherwise they are just added to the output dict.
    """
    if dict_a is None or dict_a == {}:
        return dict_b
    if dict_b is None or dict_b == {}:
        return dict_a
    
    if type(dict_a) is not dict:
        if default_key in dict_b:
            return dict_b
        dict_a = {default_key : dict_a}
    if type(dict_b) is not dict:
        if default_key in dict_a:
            return dict_a
        dict_b = {default_key : dict_b}
    
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
        return {lst[0] : list_to_nested_dict(lst[1:])}
    else:
        return lst[0]

def dealias_and_group_headers(dict_array, header_aliases, use_double_colons, default_language=u"default"):
    """
    For each row in the worksheet, group all keys that contain a double colon. So
    {"text::english": "hello", "text::french" : "bonjour"}
    becomes
    {"text": {"english": "hello", "french" : "bonjour"}.
    Dealiasing is done to the first token (the first term separated by the delimiter).
    default_language -- used to group labels/hints/etc without a language specified with localized versions.
    """
    GROUP_DELIMITER = u"::"
    out_dict_array = list()
    for row in dict_array:
        out_row = dict()
        for key, val in row.items():
            
            tokens = list()
            
            if use_double_colons:
                tokens = key.split(GROUP_DELIMITER)

#            else:
#                #We do the initial parse using single colons for backwards compatibility and
#                #only the first single is used in order to avoid nesting jr:something tokens.
#                if len(tokens) > 1:
#                    tokens[1:] = [u":".join(tokens[1:])]
            else:
                #I think the commented out section above break if there is something like media:image:english
                #so maybe a better backwards compatibility hack is to join any jr token with the next token
                tokens = key.split(u":")
                if "jr" in tokens:
                    jr_idx = tokens.index("jr")
                    tokens[jr_idx] = u":".join(tokens[jr_idx:jr_idx+2])
                    tokens.pop(jr_idx+1)
            
            dealiased_first_token = header_aliases.get(tokens[0],tokens[0])
            tokens = dealiased_first_token.split(GROUP_DELIMITER) + tokens[1:]
            new_key = tokens[0]
            new_value = list_to_nested_dict(tokens[1:] + [val])
            out_row = merge_dicts(out_row, { new_key : new_value }, default_language)
            
        out_dict_array.append(out_row)
    return out_dict_array


def dealias_types(dict_array):
    """
    Look at all the type values in a dict array and if any aliases are found,
    replace them with the name they map to.
    """
    for row in dict_array:
        found_type = row.get(constants.TYPE)
        if found_type in type_aliases.keys():
            row[constants.TYPE] = type_aliases[found_type]
    return dict_array

def clean_unicode_values(dict_array):
    """
    Go though the dict array and removing double spaces and trailing and leading spaces from all unicode values
    Note that the keys don't get cleaned, which could be an issue.
    """
    for row in dict_array:
        for key, value in row.items():
            if type(value) is unicode:
                row[key] = re.sub(r"\s+", " ", value.strip())
    return dict_array

#This is currently unused because name uniqueness is checked in the json2xform code.
def check_name_uniqueness(dict_array):
    """
    Make sure all names are unique
    Raises and exception if a duplicate is found
    """
    #This set is used to validate the uniqueness of names.
    name_set = set()
    row_number = 0 #TODO: There might be a bug with row numbers...
    for row in dict_array:
        row_number += 1
        name = row.get(constants.NAME)
        if name:
            if name in name_set:
                raise PyXFormError("Question name is not unique: " + str(name) +" Row: " + str(row_number))
            else:
                name_set.add(name)
    return dict_array


def group_dictionaries_by_key(list_of_dicts, key, remove_key = True):
    """
    Takes a list of dictionaries and returns a dictionary of lists of dictionaries with the same value for the given key.
    The grouping key is removed by default.
    If the key is not in any dictionary an empty dict is returned.
    """
    dict_of_lists = dict()
    for dicty in list_of_dicts:
        if key not in dicty: continue
        dicty_value = dicty[key]
        if remove_key: dicty.pop(key)
        if dicty_value in dict_of_lists:
            dict_of_lists[dicty_value].append(dicty)
        else:
            dict_of_lists[dicty_value] = [dicty]
    return dict_of_lists


def has_double_colon(workbook_dict):
    """
    Look for a column header with a doublecolon (::) and return true if one is found.
    """
    for sheet in workbook_dict.values():
        for row in sheet:
            for column_header in row.keys():
                if type(column_header) is not unicode:
                    continue
                if u"::" in column_header:
                    return True
    return False

def workbook_to_json(workbook_dict, form_name=None, default_language=u"default", warnings=None):
    """
    workbook_dict -- nested dictionaries representing a spreadsheet. should be similar to those returned by xls_to_dict
    form_name -- The spreadsheet's filename
    default_language -- default_language does two things:
    1. In the xform the default language is the language reverted to when there is no translation available for some itext element.
       Because of this every itext element must have a default language translation.
    2. In the workbook if media/labels/hints that do not have a language suffix will be treated as though their suffix is the default language.
       If the default language is used as a suffix for media/labels/hints, then the suffixless version will be overwritten.
    warnings -- an optional list which warnings will be appended to
    
    returns a nested dictionary equivalent to the format specified in the json form spec.
    """
    if warnings is None:
        #Set warnings to a list that will be discarded.
        warnings = []
    
    #Make sure the passed in vars are unicode
    form_name = unicode(form_name)
    default_language = unicode(default_language)

    #We check for double columns to determine whether to use them or single colons to delimit grouped headers.
    #Single colons are bad because they conflict with with the xform namespace syntax (i.e. jr:constraintMsg),
    #so we only use them if we have to for backwards compatibility.
    use_double_colons = has_double_colon(workbook_dict)
    
    #Break the spreadsheet dict into easier to access objects (settings, choices, survey_sheet):
    ########### Settings sheet ##########
    settings_sheet = dealias_and_group_headers(workbook_dict.get(constants.SETTINGS, []), settings_header_aliases, use_double_colons)
    settings = settings_sheet[0] if len(settings_sheet) > 0 else {}
    
    default_language = settings.get(constants.DEFAULT_LANGUAGE, default_language)
    
    #add_none_option is a boolean that when true, indicates a none option should automatically be added to selects.
    #It should probably be deprecated but I haven't checked yet.
    if u"add_none_option" in settings:
        settings[u"add_none_option"] = yes_no_aliases.get(settings[u"add_none_option"], u"false()") == u"true()"
    
    #Here we create our json dict root with default settings:
    id_string = settings.get(constants.ID_STRING, form_name)
    json_dict = {
       constants.TYPE : constants.SURVEY,
       constants.NAME : form_name,
       constants.TITLE : id_string,
       constants.ID_STRING : id_string,
       constants.DEFAULT_LANGUAGE : default_language,
       constants.CHILDREN : []
    }
    #Here the default settings are overridden by those in the settings sheet
    json_dict.update(settings)
    
    ########### Choices sheet ##########
    #Columns and "choices and columns" sheets are deprecated, but we combine them with the choices sheet for backwards-compatibility.
    choices_and_columns_sheet = workbook_dict.get(constants.CHOICES_AND_COLUMNS, {})
    choices_and_columns_sheet = dealias_and_group_headers(choices_and_columns_sheet, list_header_aliases, use_double_colons, default_language)
    
    columns_sheet = workbook_dict.get(constants.COLUMNS, [])
    columns_sheet = dealias_and_group_headers(columns_sheet, list_header_aliases, use_double_colons, default_language)
    
    choices_sheet = workbook_dict.get(constants.CHOICES, [])
    choices_sheet = dealias_and_group_headers(choices_sheet, list_header_aliases, use_double_colons, default_language)
    
    combined_lists = group_dictionaries_by_key(choices_and_columns_sheet + choices_sheet + columns_sheet, constants.LIST_NAME)
    
                
    choices = combined_lists

    ########### Cascading Select sheet ###########
    cascading_choices = workbook_dict.get(constants.CASCADING_CHOICES, {})
    
    ########### Survey sheet ###########
    if constants.SURVEY not in workbook_dict:
        raise PyXFormError("You must have a sheet named (case-sensitive): " + constants.SURVEY)
    survey_sheet = workbook_dict[constants.SURVEY]
    #Process the headers:
    survey_sheet = clean_unicode_values(survey_sheet)
    survey_sheet = dealias_and_group_headers(survey_sheet, survey_header_aliases, use_double_colons, default_language)
    survey_sheet = dealias_types(survey_sheet)
    ##################################
    
    #Parse the survey sheet while generating a survey in our json format:
    
    row_number = 1 #We start at 1 because the column header row is not included in the survey sheet (presumably).
    #A stack is used to keep track of begin/end expressions
    stack = [(None, json_dict.get(constants.CHILDREN))]
    #If a group has a table-list appearance flag this will be set to the name of the list
    table_list = None
    begin_table_list = False
    #For efficiency we compile all the regular expressions that will be used to parse types:
    end_control_regex = re.compile(r"^(?P<end>end)(\s|_)(?P<type>("
                                   + '|'.join(control_aliases.keys()) + r"))$")
    begin_control_regex = re.compile(r"^(?P<begin>begin)(\s|_)(?P<type>("
                                     + '|'.join(control_aliases.keys())
                                     + r"))( (over )?(?P<list_name>\S+))?$")
    select_regexp = re.compile(r"^(?P<select_command>("
                               + '|'.join(select_aliases.keys())
                               + r")) (?P<list_name>\S+)( (?P<specify_other>(or specify other|or_other|or other)))?$")
    cascading_regexp = re.compile(r"^(?P<cascading_command>("
                               + '|'.join(cascading_aliases.keys())
                               + r")) (?P<cascading_level>\S+)?$")
    for row in survey_sheet:
        row_number += 1
        prev_control_type, parent_children_array = stack[-1]
        
        #Disabled should probably be first so the attributes below can be disabled.
        if u"disabled" in row:
            warnings.append("The 'disabled' column header is not part of the current spec. We recommend using relevant instead.")
            disabled = row.pop(u"disabled")
            if disabled in yes_no_aliases:
                disabled = yes_no_aliases[disabled]
            if disabled == 'true()':
                continue
        
        #skip empty rows
        if len(row) == 0: continue
        
        #Get question type
        question_type = row.get(constants.TYPE)
        if not question_type:
            # if name and label are also missing, then its a comment row, and we skip it with warning
            if not ((constants.NAME in row) and (constants.LABEL in row)):
                    warnings.append("Row wihtout name, text, or label is being skipped " + str(row_number) + ": " + str(row))
                    continue
            raise PyXFormError("Question with no type on row " + str(row_number))
            continue
        
        #Check if the question is actually a setting specified on the survey sheet
        settings_type = settings_header_aliases.get(question_type)
        if settings_type:
            json_dict[settings_type] = unicode(row.get(constants.NAME))
            continue
        
        #Try to parse question as a end control statement (i.e. end loop/repeat/group):
        end_control_parse = end_control_regex.search(question_type)
        if end_control_parse:
            parse_dict = end_control_parse.groupdict()
            if parse_dict.get("end") and "type" in parse_dict:
                control_type = control_aliases[parse_dict["type"]]
                if prev_control_type != control_type or len(stack) == 1:
                    raise PyXFormError("Unmatched end statement. Previous control type: " + str(prev_control_type) + ", Control type: " + str(control_type))
                stack.pop()
                table_list = None
                continue
        
        #Make sure the question has a valid name
        question_name = unicode(row.get(constants.NAME))
        if not question_name:
            raise PyXFormError("Question with no name on row " + str(row_number))
        if not is_valid_xml_tag(question_name):
            error_message = "Invalid question name [" + question_name + "] on row " + str(row_number) + "\n"
            error_message += "Names must begin with a letter, colon, or underscore. Subsequent characters can include numbers, dashes, and periods."
            raise PyXFormError(error_message)
        
        if constants.LABEL not in row and \
           row.get(constants.MEDIA) is None and \
           question_type not in label_optional_types:
            #TODO: Should there be a default label?
            #      Not sure if we should throw warnings for groups...
            #      Warnings can be ignored so I'm not too concerned about false positives.
            warnings.append("Warning unlabeled question in row " + str(row_number) + ": " + str(row))
        
        #Try to parse question as begin control statement (i.e. begin loop/repeat/group:
        begin_control_parse = begin_control_regex.search(question_type)
        if begin_control_parse:
            parse_dict = begin_control_parse.groupdict()
            if parse_dict.get("begin") and "type" in parse_dict:
                #Create a new json dict with children, and the proper type, and add it to parent_children_array in place of a question.
                #parent_children_array will then be set to its children array (so following questions are nested under it)
                #until an end command is encountered.
                control_type = control_aliases[parse_dict["type"]]
                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = control_type
                child_list = list()
                new_json_dict[constants.CHILDREN] = child_list
                if control_type is constants.LOOP:
                    if not parse_dict.get("list_name"):
                        #TODO: Perhaps warn and make repeat into a group?
                        raise PyXFormError("Repeat without list name " + " Error on row: " + str(row_number))
                    list_name = parse_dict["list_name"]
                    if list_name not in choices:
                        raise PyXFormError("List name not in columns sheet: " + list_name + " Error on row: " + str(row_number))
                    new_json_dict[constants.COLUMNS] = choices[list_name]
                
                #Code to deal with table_list appearance flags (for groups of selects)
                if new_json_dict.get(u"control",{}).get(u"appearance") == constants.TABLE_LIST:
                    begin_table_list = True
                    new_json_dict[u"control"][u"appearance"] = u"field-list"
                    
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
                    raise PyXFormError("Cascading select needs a name. Error on row: %s" % row_number)
                cascading_json = get_cascading_json(cascading_choices, cascading_prefix, cascading_level)
                
                for c in cascading_json: parent_children_array.append(c)
                continue # so the row isn't put in as is

        #Try to parse question as a select:
        select_parse = select_regexp.search(question_type)
        if select_parse:
            parse_dict = select_parse.groupdict()
            if parse_dict.get("select_command"):
                select_type = select_aliases[parse_dict["select_command"]]
                list_name = parse_dict["list_name"]

                if list_name not in choices:
                    raise PyXFormError("List name not in choices sheet: " + list_name + " Error on row: " + str(row_number))

                #Validate select_multiple choice names by making sure they have no spaces (will cause errors in exports).
                if select_type == constants.SELECT_ALL_THAT_APPLY:
                    for choice in choices[list_name]:
                        if ' ' in choice[constants.NAME]:
                                raise PyXFormError("Choice names with spaces cannot be added to multiple choice selects. See [" + choice[constants.NAME] + "] in [" + list_name + "]")

                if parse_dict.get("specify_other") is not None:
                    select_type += u" or specify other"
                    
                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = select_type
                new_json_dict[constants.CHOICES] = choices[list_name]
                
                #Code to deal with table_list appearance flags (for groups of selects)
                if table_list or begin_table_list:
                    if begin_table_list: #If this row is the first select in a table list
                        table_list = list_name
                        table_list_header = {
                            constants.TYPE : select_type,
                            constants.NAME : "reserved_name_for_field_list_labels_" + str(row_number), #Adding row number for uniqueness
                            constants.CONTROL : { u"appearance" : u"label" },
                            constants.CHOICES : choices[list_name]
                        }
                        parent_children_array.append(table_list_header)
                        begin_table_list = False

                    if table_list <> list_name:
                        error_message = "Error on row: " + str(row_number) + "\n"
                        error_message += "Badly formatted table list, list names don't match: " + table_list + " vs. " + list_name
                        raise PyXFormError(error_message)
                    
                    control = new_json_dict[u"control"] = new_json_dict.get(u"control", {})
                    control[u"appearance"] = "list-nolabel"
                        
                parent_children_array.append(new_json_dict)
                continue
            
        #TODO: Consider adding some question_type validation here.
        
        #Put the row in the json dict as is:
        parent_children_array.append(row)
    
    if len(stack) != 1:
        raise PyXFormError("unmatched begin statement: " + str(stack[-1][0]))
    #print_pyobj_to_json(json_dict)
    return json_dict

def parse_file_to_workbook_dict(path, file_object=None):
    """
    Given a xls or csv workbook file use xls2json_backends to create a python workbook_dict.
    workbook_dicts are organized as follows:
    {sheetname : [{column_header : column_value_in_array_indexed_row}]}
    """
    (filepath, filename) = os.path.split(path)
    if not filename: raise PyXFormError("No filename.")
    (shortname, extension) = os.path.splitext(filename)
    if not extension: raise PyXFormError("No extension.")
    
    if extension == ".xls":
        return xls_to_dict(file_object if file_object is not None else path)
    elif extension == ".csv":
        return csv_to_dict(file_object if file_object is not None else path)
    elif extension == ".xlsx":
        raise PyXFormError("XLSX files are not supported at this time. Please save the spreadsheet as an XLS file (97).")
    else:
        raise PyXFormError("File was not recognized")

def get_filename(path):
    """
    Get the extensionless filename from a path
    """
    return os.path.splitext((os.path.basename(path)))[0]

def parse_file_to_json(path, default_name = None, default_language = u"default", warnings=None, file_object=None):
    """
    A wrapper for workbook_to_json
    """
    workbook_dict = parse_file_to_workbook_dict(path, file_object)
    if default_name is None:
        default_name = unicode(get_filename(path))
    return workbook_to_json(workbook_dict, default_name, default_language, warnings)

def organize_by_values(dict_list, key):
    """
    dict_list -- a list of dicts
    key -- a key shared by all the dicts in dict_list
    Returns a dict of dicts keyed by the value of the specified key in each dictionary.
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
        self._dict = workbook_dict = parse_file_to_workbook_dict(path)
        self._path = path
        self._name = self._print_name = self._title = self._id = unicode(get_filename(path))

    def to_json_dict(self):
        return self._dict

    #TODO: Make sure the unicode chars don't show up
    def print_json_to_file(self, filename=""):
        if not filename:
            filename = self._path[:-4] + ".json"
        print_pyobj_to_json(self.to_json_dict(), filename)

class SurveyReader(SpreadsheetReader):
    """
    SurveyReader is a wrapper for the parse_file_to_json function.
    It allows us to use the old interface where a SpreadsheetReader based object is created
    then a to_json_dict function is called on it.
    """
    def __init__(self, path_or_file):
        if isinstance(path_or_file, basestring):
            self._file_object = None
            path = path_or_file
        else:
            self._file_object = path_or_file
            path = path_or_file.name

        self._warnings = []
        self._dict =  parse_file_to_json(path, warnings=self._warnings, file_object=self._file_object)
        self._path = path
    def print_warning_log(self, warn_out_file):
        #Open file to print warning log to.
        warn_out = open(warn_out_file, 'w')
        warn_out.write('\n'.join(self._warnings))

class QuestionTypesReader(SpreadsheetReader):
    """
    Class for reading spreadsheet file that specifies the available question types.
    @see question_type_dictionary
    """
    def __init__(self, path):
        super(QuestionTypesReader, self).__init__(path)
        self._setup_question_types_dictionary()
        
    def _setup_question_types_dictionary(self):
        use_double_colons = has_double_colon(self._dict)
        TYPES_SHEET = u"question types"
        self._dict = self._dict[TYPES_SHEET]
        self._dict = dealias_and_group_headers(self._dict, {}, use_double_colons, u"default")
        self._dict = organize_by_values(self._dict, u"name")

#Not used internally (or on formhub)
#TODO: If this is used anywhere else it is probably broken from the changes I made to SpreadsheetReader.
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
        #print "You must supply a file argument."
        path = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/xlsform_spec_test.xls"
    else:
        path = sys.argv[1]
    
    warnings = []
    json_dict = parse_file_to_json(path, warnings=warnings)
    print_pyobj_to_json(json_dict)
    
    if len(warnings) > 0:
        sys.stderr.write("Warnings:" + '\n')
        sys.stderr.write('\n'.join(warnings) + '\n')
