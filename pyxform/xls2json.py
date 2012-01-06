"""
A Python script to convert excel files into JSON.
I'm currently trying to shift this to a more functional style.
It might seem a bit strange right now because it's half way in-between being oo and functional.
"""

import json
import re
import sys
import codecs
import os
import constants
from errors import PyXFormError
from xls2json_backends import xls_to_dict, csv_to_dict

# STATIC DATA:

# The following are the possible sheet names:
SURVEY = u"survey"
SETTINGS = u"settings"
# These sheet names are for list sheets
CHOICES = u"choices"
COLUMNS = u"columns" #this is for loop statements
CHOICES_AND_COLUMNS = u"choices and columns"

#xls specific constants:
LIST_NAME = u"list name"

#Aliases:
#Ideally aliases should resolve to elements in the json form schema
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
#select and control alias keys used for parsing,
#which is why self mapped keys are necessary.
control_aliases = {
    constants.GROUP : constants.GROUP,
    u"lgroup" : constants.REPEAT,
    constants.REPEAT : constants.REPEAT,
    constants.LOOP : constants.LOOP,
    u"looped group": constants.REPEAT
}
select_aliases = {
      u"add select one prompt using" : u"select one",
      u"add select multiple prompt using" : u"select one",
      u"select all that apply from" : u"select all that apply",
      u"select one from" : u"select one",
      u"selec1" : u"select one", 
      u"select_one" : u"select one",
      u"select_multiple" : u"select all that apply"
}
#TODO: Check on bind prefix approach in json.
#Conversion dictionary from user friendly column names to meaningful values
survey_header_aliases = {
    u"constraint_message" : u"constraint message",#TODO: This is an issue (should it be under bind?)
    u"read_only" : constants.READONLY,
    u"relevant":u"bind:relevant",
    u"caption": constants.LABEL,
    u"appearance": u"control:appearance", #TODO: this is also an issue
    u"relevance": u"bind:relevant",
    u"required": u"bind:required",
    u"constraint": u"bind:constraint",
    u"constraining message": u"bind:jr:constraintMsg",
    u"calculation": u"bind:calculate",
    u"command": constants.TYPE,
    u"tag": constants.NAME,
    #u"label": u"caption",#TODO: this is also an issue
    u"skippable": u"required",
    u"value": constants.NAME,
    u"image": u"media:image",
    u"audio": u"media:audio",
    u"video": u"media:video",
    u"count": u"bind:jr:count"
}
settings_header_aliases = {
    u"form_title" : constants.TITLE,
    u"form_id" : constants.ID_STRING
}
list_header_aliases = {
    u"list_name" : LIST_NAME,
    u"value" : constants.NAME #Perhaps there should a different name constant for list item names?
}
type_aliases = {
    u"image": u"photo"
}

# This line makes a list out of all the unicode values in constants.
# survey_header_names = [x for x in constants.__dict__.values() if type(x) is type(unicode())]
# This is used column header validation, if we see a name that isn't in this list we will throw a warning.
# TODO: I'm thinking about not validating the column headers. If there is an unknown header, it will show up in the json,
# and we can validate the json instead and return the invalid name (which is the only really important info for this type of problem).
# survey_header_names = [ constants.TYPE, constants.NAME, constants.LABEL, constants.READONLY ]
#
# settings_header_names = [ LIST_NAME, u"name", u"label" ]


def print_pyobj_to_json(pyobj, path):
    """
    dump a python nested array/dict structure to the specified file
    """
    fp = codecs.open(path, mode="w", encoding="utf-8")
    json.dump(pyobj, fp=fp, ensure_ascii=False, indent=4)
    fp.close()

class SpreadsheetReader(object):
    
    def __init__(self, path_or_file):
        if isinstance(path_or_file, basestring):
            self._file_object = None
            path = path_or_file
        else:
            self._file_object = path_or_file
            path = self._file_object.name

        (filepath, filename) = os.path.split(path)
        (shortname, extension) = os.path.splitext(filename)
        self.filetype = None
        if extension == ".xlsx":
            raise PyXFormError("XLSX files are not supported at this time. Please save the spreadsheet as an XLS file (97).")
        elif extension == ".xls":
            self.filetype = "xls"
        elif extension == ".csv":
            self.filetype = "csv"
        self._path = path
        self._name = unicode(shortname)
        self._print_name = unicode(shortname)
        self._title = unicode(shortname)
        self._id = unicode(shortname)
        self._def_lang = unicode("English")
        self._parse_input()

    def _parse_input(self):
        if self.filetype == None:
            raise PyXFormError("File was not recognized")
        elif self.filetype == "xls":
            self._dict = xls_to_dict(self._file_object if self._file_object is not None else self._path)
        elif self.filetype == "csv":
            self._dict = csv_to_dict(self._file_object if self._file_object is not None else self._path)
        self._sheet_names = self._dict.keys()
        for sheet_name, sheet in self._dict.items():
            clean_unicode_values(sheet)
        self._fix_int_values()

    def _fix_int_values(self):
        """
        Excel only has floats, but we really want integer values to be
        ints.
        """
        for sheet_name, dicts in self._dict.items():
            for d in dicts:
                for k, v in d.items():
                    if type(v) == float and v == int(v):
                        d[k] = int(v)

    def to_json_dict(self):
        return self._dict

    #TODO: Make sure the unicode chars don't show up
    def print_json_to_file(self, filename=""):
        if not filename:
            filename = self._path[:-4] + ".json"
        print_pyobj_to_json(self.to_json_dict(), filename)

def list_to_nested_dict(lst):
    """
    [1,2,3,4] -> {1:{2:{3:4}}}
    """
    if len(lst) > 1:
        return {lst[0] : list_to_nested_dict(lst[1:])}
    else:
        return lst[0]
def merge_dicts(dict_a, dict_b, default_key = "default", default_key_2 = "default_2"):
    """
    Recursively merge two nested dicts into a single dict.
    If a non-dict value has a key that matches something else
    it will be put into a new dict under default_key
    or default_key_2 (if the default_key has already been used) and combined as such.
    """
    #print dict_a
    #print dict_b
    if dict_a is None:
        return dict_b
    if dict_b is None:
        return dict_a
    
    if type(dict_a) is not dict:
        dict_a = {default_key : dict_a}
        default_key = default_key_2 #This is how name collisions are avoided when merging two leaf elements
    if type(dict_b) is not dict:
        dict_b = {default_key : dict_b}
    
#    if len(dict_a) == 0:
#        return dict_b
#    if len(dict_b) == 0:
#        return dict_a
    
    all_keys = set(dict_a.keys()).union(set(dict_b.keys()))
    
    out_dict = dict()
    for key in all_keys:
        out_dict[key] = merge_dicts(dict_a.get(key), dict_b.get(key), default_key, default_key_2)
    return out_dict
    
def group_headers(dict_array):
    """
    For each row in the worksheet, group all keys that contain a
    colon. So {"text:english": "hello", "text:french" :
    "bonjour"} becomes {"text": {"english": "hello", "french" :
    "bonjour"}.
    """
    #TODO
    #Colons aren't the best syntax for this because they are also used in namespaces (i.e. jr:something)
    #For now I'm only parsing the first colon and hoping nobody ever tries a multi-level group.
    DICT_CHAR = u":"
    out_dict_array = list()
    for row in dict_array:
        out_row = dict()
        for k, v in row.items():
            tokens = k.split(DICT_CHAR)
            #print "begin"
            #print list_to_nested_dict(tokens)
            #tokens.append(v)
            #out_row = merge_dicts(out_row, list_to_nested_dict(tokens))
            if len(tokens) == 1:
                out_row[k] = v
            else:
                out_row = merge_dicts(out_row, {
                                                    tokens[0] :
                                                    {
                                                        DICT_CHAR.join(tokens[1:]) : v
                                                    }
                                                }
                                      )
            
        out_dict_array.append(out_row)
    return out_dict_array
    
def dealias_headers(dict_array, header_aliases):
    """
    Dealias the headers according to the given alias map
    Copies dict_array so this isn't super efficient.
    """
    out_dict_array = list()
    for row in dict_array:
        out_row = dict()
        for key in row.keys():
            if key in header_aliases.keys():
                out_row[header_aliases[key]] = row[key]
            else:
                out_row[key] = row[key]
        out_dict_array.append(out_row)
    return out_dict_array

def validate_headers(dict_array, header_names):
    """
    throw warnings for unknown headers.
    """
    for row in dict_array:
        for key in row.keys():
                if key not in header_names:
                    #TODO warning
                    print "Unknown column header: " + key 

def dealias_types(dict_array):
    """
    Look at all the type values in a dict array and if any aliases are found,
    replace them with the name they map to.
    """
    for row in dict_array:
        if constants.TYPE in dict_array:
            found_type = row[constants.TYPE]
            if found_type in type_aliases:
                row[constants.TYPE] = type_aliases[constants.TYPE]
    return dict_array

def clean_unicode_values(dict_array):
    """
    Go though the dict array and removing double spaces and trailing and leading spaces from all unicode values
    Note that the keys don't get cleaned, which could be an issue.
    """
    for row in dict_array:
        for key in row.keys():
            value = row[key]
            if type(value) is unicode:
                row[key] = re.sub(r"\s+", " ", value.strip())
    return dict_array

def check_name_uniqueness(dict_array):
    """
    Make sure all names are unique
    Raises and exception if a duplicate is found
    """
    #This set is used to validate the uniqueness of names.
    name_set = set()
    row_number = 0
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
        dicty_key = dicty[key]
        if remove_key: dicty.pop(key)
        if dicty_key in dict_of_lists:
            dict_of_lists[dicty_key].append(dicty)
        else:
            dict_of_lists[dicty_key] = [dicty]
    return dict_of_lists

#TODO: This function might not be necessary... It is used to look up question type templates, but this function is only needed
# if they are stored in the same format as the survey sheets. Plus I'm not processing question types here anymore.
def find_dictionary_with_key_value_pair(dict_of_dicts, key, value):
    """
    Look through a dictionary of dictionaries for the specified key value pair and return the first dictionary that contains it
    If the pair is not found return none.
    """
    for dicty in dict_of_dicts:
        if key in dicty and dicty[key] == value:
            return dicty
    return None


def spreadsheet_to_json(spreadsheet_dict, form_name=None, default_language=u"english", warn_out_file='warnings.txt'):
    """
    spreadsheet_dict -- nested dictionaries representing a spreadsheet. should be similar to those returned by xls_to_dict
    form_name -- The spreadsheet's filename
    default_language -- if there are multilingual elements this will be the default language they are put in.
    returns a nested dictionary equivalent to the format specified in the json form spec.
    """
    #Make sure the passed in vars are unicode
    form_name = unicode(form_name)
    default_language = unicode(default_language)
    
    #Open file to print warning log to.
    warn_out = open(warn_out_file, 'w')
    
    #Load primative question types
    #Took the question types out because there is already code that validates and
    #adds attributes to questions with it the the json2xform half.
    #import question_type_dictionary
    #question_types = question_type_dictionary.DEFAULT_QUESTION_TYPE_DICTIONARY
    #question_types = xls_to_dict("question_types/base.xls").popitem()[1]

    #Break apart the spreadsheet dict down into easier to access objects
    if SURVEY not in spreadsheet_dict:
        raise PyXFormError("You must have a sheet named: " + SURVEY)
    survey_sheet = spreadsheet_dict[SURVEY]
    #Process the headers
    survey_sheet = dealias_headers(survey_sheet, survey_header_aliases)
    #Dealiasing first since aliases might resolve to expressions with unparsed colons
    survey_sheet = group_headers(survey_sheet)
    #print survey_sheet
    #validate_headers(survey_sheet, survey_header_names)
    
    #survey_sheet = clean_unicode_values(survey_sheet)
    survey_sheet = dealias_types(survey_sheet)
    
    #The logic for the choices and columns sheets is sort of complicated because of the different naming conventions.
    #Basically, I combine everything into one list. If this breaks something we can come up with a complicated scheme later on.
    choices_and_columns_sheet = spreadsheet_dict.get(CHOICES_AND_COLUMNS, {})
    choices_and_columns_sheet = dealias_headers(choices_and_columns_sheet, list_header_aliases)
    choices_and_columns_sheet = group_headers(choices_and_columns_sheet)
    
    choices_sheet = spreadsheet_dict.get(CHOICES, [])
    choices_sheet = dealias_headers(choices_sheet, list_header_aliases)
    choices_sheet = group_headers(choices_sheet)

    columns_sheet = spreadsheet_dict.get(COLUMNS, [])
    columns_sheet = dealias_headers(columns_sheet, list_header_aliases)
    columns_sheet = group_headers(columns_sheet)
    
    combined_lists = group_dictionaries_by_key(choices_and_columns_sheet + choices_sheet + columns_sheet, LIST_NAME)
    choices = columns = combined_lists
    
    settings_sheet = group_headers(dealias_headers(spreadsheet_dict.get(SETTINGS, []), settings_header_aliases))
    settings = settings_sheet[0] if len(settings_sheet) > 0 else {}

    #Here we create our json dict root with default settings:
    id_string = settings.get(constants.ID_STRING, form_name)
    json_dict = {
       constants.TYPE : SURVEY,
       constants.NAME : form_name,
       constants.TITLE : id_string,
       constants.ID_STRING : id_string,
       constants.CHILDREN : []
    }
    #Here the default settings are overridden by those in the settings sheet
    json_dict.update(settings)
    
    check_name_uniqueness(survey_sheet)
    #TODO: We could also check the choices/columns lists for unique names (within the list).
    
    #Parse the survey sheet while generating a survey in our json format:
    row_number = 0
    #A stack is used to keep track of begin/end expressions
    stack = [(None, json_dict.get(constants.CHILDREN))]
    for row in survey_sheet:
        row_number += 1
        prev_control_type, parent_children_array = stack[-1]
        
        #Disabled should probably be first so the attributes below can be disabled.
        if u"disabled" in row:
            warn_out.write("The 'disabled' column header is not part of the current spec. We recommend using relevant instead.")#TODO Warn
            disabled = row.pop(u"disabled")
            if disabled in yes_no_aliases:
                disabled = yes_no_aliases[disabled]
            if disabled == 'true()':
                continue
        
        #skip empty rows
        if len(row) == 0: continue
        
        #Get question type
        question_type = row.get(u"type")
        if not question_type:
            raise PyXFormError("Question with no type on row " + str(row_number))
            continue
        
        #Try to read form title and id from the survey sheet if they happen to be specified there
        #(done only for backwards compatibility, settings should be in the settings sheet)
        if u"set form title" == question_type:
            warn_out.write("Please put the form title on a separate settings sheet.")
            json_dict[constants.TITLE] = unicode(row.get(constants.NAME))
            continue
        if u"set form id" == question_type:
            warn_out.write("Please put the form id on a separate settings sheet.")
            json_dict[constants.ID_STRING] = unicode(row.get(constants.NAME))
            continue
        
        #Try to parse question as a end control statement (i.e. end loop/repeat/group):
        end_control_parse = re.search(r"(?P<end>end)(\s|_)(?P<type>("
                                  + '|'.join(control_aliases.keys()) + r"))$", question_type)
        if end_control_parse:
            parse_dict = end_control_parse.groupdict()
            if parse_dict.get("end") and "type" in parse_dict:
                control_type = control_aliases[parse_dict["type"]]
                if prev_control_type != control_type or len(stack) == 1:
                    raise PyXFormError("Unmatched end statement. Previous control type: " + prev_control_type + ", Control type: " + control_type)   
                stack.pop()
                continue
        
        #Make sure the question has a valid name
        question_name = unicode(row.get(constants.NAME))
        if not question_name:
            raise PyXFormError("Question with no name on row " + str(row_number))
        if u" " in question_name:
            #I don't think it's ever ok for there to be spaces in this attribute but I could be wrong... TODO:Check for other bad chars
            raise PyXFormError("Spaces in question name on row " + str(row_number))
        
        if constants.LABEL not in row:
            #TODO: Should there be a default label?
            warn_out.write("Warning unlabeled question in row" + str(row_number))
        
        #Try to parse question as begin control statement (i.e. begin loop/repeat/group:
        begin_control_parse = re.search(r"(?P<begin>begin)(\s|_)(?P<type>("
                                  + '|'.join(control_aliases.keys())
                                  + r"))( (over )?(?P<list_name>\S+))?$", question_type)
        if begin_control_parse:
            parse_dict = begin_control_parse.groupdict()
            if parse_dict.get("begin") and "type" in parse_dict:
                #Create a new json dict with children, and the proper type, and add it to  parent_children_array in place of a question.
                #Its children will become the parent_children_array (so following questions are nested under it) until an end command is encountered.
                control_type = control_aliases[parse_dict["type"]]
                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = control_type
                child_list = list()
                new_json_dict[constants.CHILDREN] = child_list
                if control_type is constants.LOOP:
                    if not parse_dict.get("list_name"):
                        #TODO: Perhaps warn and make repeat into a group?
                        raise PyXFormError("repeat without list name", "Error on row: " + str(row_number))
                    list_name = parse_dict["list_name"]
                    if list_name not in columns:
                        raise PyXFormError("List name not in columns sheet: " + list_name + " Error on row: " + str(row_number))
                    new_json_dict[constants.COLUMNS] = columns[list_name]
                parent_children_array.append(new_json_dict)
                stack.append((control_type, child_list))
                continue

        #Try to parse question as a select:
        select_regexp = (r"^(?P<select_command>("
                         + '|'.join(select_aliases.keys())
                         + r")) (?P<list_name>\S+)( (?P<specify_other>(or specify other|or_other)))?$")
        select_parse = re.search(select_regexp, question_type)
        if select_parse:
            parse_dict = select_parse.groupdict()
            if parse_dict.get("select_command"):
                select_type = select_aliases[parse_dict["select_command"]]
                list_name = parse_dict["list_name"]

                if list_name not in choices:
                    raise PyXFormError("List name not in choices sheet: " + list_name, "Error on row: " + str(row_number))
                
                #print "choices[list_name]choices[list_name]choices[list_name]" + str(choices[list_name])
                if parse_dict.get("specify_other") is not None:
                    select_type += u" or specify other"
                    
                new_json_dict = row.copy()
                new_json_dict[constants.TYPE] = select_type
                new_json_dict[constants.CHOICES] = choices[list_name]
                    
                parent_children_array.append(new_json_dict)
                continue
        
        #Try to parse question using the primative types
        #TODO: Fix and add back in the stuff for processing primative question types.
        #question_type_template = find_dictionary_with_key_value_pair(question_types, constants.TYPE, question_type)
        if True:#question_type_template:
            #new_json_dict = question_type_template.copy()
            #new_json_dict.update(row)
            #parent_children_array.append(new_json_dict)
            parent_children_array.append(row)
            continue
        
        #Give up on this row.
        warn_out.write("count not parse type: " + question_type + " on row " + str(row_number))
    #print json.dumps(json_dict, indent=4, ensure_ascii=False)
    if len(stack) != 1:
        raise PyXFormError("unmatched begin statement: " + str(stack[-1][0]))
    return json_dict

class SurveyReader(SpreadsheetReader):
    def __init__(self, path):
        super(SurveyReader, self).__init__(path)
        #I would rather find these by calling specific functions i.e.
        #workbook_dict = get_dict_from_workbook(path)
        default_name = self._name
        default_language = self._def_lang
        self._dict = spreadsheet_to_json(self._dict, default_name, default_language)

def organize_by_type_name(dict_list, key):
    """
    Transform a list of dicts, into a dict or dicts keyed by the value of the specified key in each dictionary.
    If two dictionaries fall under the same key, or one doesn't have the key, an error is thrown.
    """
    result = {}
    for dicty in dict_list:
        if key in dicty:
            result[dicty.pop(key)] = dicty
    return result

class QuestionTypesReader(SpreadsheetReader):
    """
    Class for reading spreadsheet file that specifies the available question types.
    @see question_type_dictionary
    """
    def __init__(self, path):
        super(QuestionTypesReader, self).__init__(path)
        self._setup_question_types_dictionary()
        
    def _setup_question_types_dictionary(self):
        TYPES_SHEET = u"question types"
        self._dict = self._dict[TYPES_SHEET]
        #print self._dict
        self._dict = group_headers(self._dict)
        #print json.dumps(self._dict, indent=4, ensure_ascii=False)
        self._dict = organize_by_type_name(self._dict, u"name")
        

#Not used internally
#TODO: If this is used anywhere else it is probably broken from the changes I made to SpreadsheetReader
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
    # Open the excel file that is the second argument to this python
    # call, convert that file to json and save that json to a file
    path = sys.argv[1]
    converter = SurveyReader(path)
    # converter.print_json_to_file()
    print json.dumps(converter.to_json_dict(), ensure_ascii=False, indent=4)
