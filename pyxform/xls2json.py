"""
A Python script to convert excel files into JSON.
"""

import json
import re
import sys
import codecs
import os
from errors import PyXFormError


def print_pyobj_to_json(pyobj, path):
    fp = codecs.open(path, mode="w", encoding="utf-8")
    json.dump(pyobj, fp=fp, ensure_ascii=False, indent=4)
    fp.close()

# the following are the three sheet names that this program expects
SURVEY_SHEET = u"survey"
CHOICES_SHEET_NAMES = [u"choices", u"choices and columns"]
COLUMNS_SHEET = u"columns" #Not used
TYPES_SHEET = u"question types"

LIST_NAME = u"list name"
DICT_CHAR = u":"

TYPE = u"type"
NAME = u"name"
CHOICES = u"choices"
COLUMNS = u"columns"

DISABLED = u'disabled'

# Special reserved values for type column that allow the user to set
# the form's title or id.
SET_TITLE = u"set form title"
SET_ID = u"set form id"
SET_DEFAULT_LANG = u"set default language"


group_name_conversions = {
    "looped group": u"repeat"
}

yes_no_conversions = {
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

from xls2json_backends import xls_to_dict, csv_to_dict


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
        self._set_choices_and_columns_sheet_name()
        self._strip_unicode_values()
        self._fix_int_values()
        self._group_dictionaries()

    def _set_choices_and_columns_sheet_name(self):
        """
        If the xls file has a sheet with a name in CHOICES_SHEET_NAMES
        _lists_sheet_name is set to it.
        """
        sheet_names = self._dict.keys()

        self._lists_sheet_name = None
        for sheet_name in sheet_names:
            if sheet_name in CHOICES_SHEET_NAMES:
                self._lists_sheet_name = sheet_name

    def _strip_unicode_values(self):
        for sheet_name, dicts in self._dict.items():
            for d in dicts:
                for k, v in d.items():
                    if type(v) == unicode:
                        d[k] = v.strip()

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

    def _group_dictionaries(self):
        """
        For each row in the worksheet, group all keys that contain a
        colon. So {"text:english": "hello", "text:french" :
        "bonjour"} becomes {"text": {"english": "hello", "french" :
        "bonjour"}.
        """
        for sheet_name, dicts in self._dict.items():
            for d in dicts:
                groups = {}
                for k, v in d.items():
                    l = k.split(DICT_CHAR)
                    if len(l) >= 2:
                        if l[0] not in groups:
                            groups[l[0]] = {}
                        groups[l[0]][DICT_CHAR.join(l[1:])] = v
                        del d[k]
                for k, v in groups.items():
                    assert k not in d
                    d[k] = v

    def to_json_dict(self):
        return self._dict

    def print_json_to_file(self, filename=""):
        if not filename:
            filename = self._path[:-4] + ".json"
        print_pyobj_to_json(self.to_json_dict(), filename)

class ParseQuestionException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SurveyReader(SpreadsheetReader):

    def __init__(self, path):
        super(SurveyReader, self).__init__(path)
        self._setup_survey()

    def _setup_survey(self):
        """
        Does some parsing on the survey sheet.
        I think this should probably go somewhere else so all the parsing happens in the same place.
        """
        if SURVEY_SHEET not in self._dict:
            raise PyXFormError("You must have a sheet named: " + SURVEY_SHEET)
        
        self._process_questions()
        self._construct_choice_lists()
        self._insert_lists()
        self._save_settings()
        self._organize_sections()

    def _save_settings(self):
        """
        sets _settings to the settings worksheet.
        """
        # the excel reader gives a list of dicts, one dict for each
        # row after the headers, we're only going to use the first
        # row.
        self._settings = self._dict.get(u"settings", [{}])[0]

    def _process_questions(self):
        """
        A question is dictionary representing a row in the survey worksheet where the keys are the column headers.
        This function does some light parsing on them, for example it will:
        remove disabled questions, set the survey title and id, break apart select and group statements.
        """
        new_question_list = list()
        for question in self._dict[SURVEY_SHEET]:
            if u"type" not in question:
                continue
            #Disabled should probably be first so the attributes below can be disabled.
            if DISABLED in question:
                disabled = question["disabled"]
                if disabled in yes_no_conversions:
                    disabled = yes_no_conversions[disabled]
                if disabled == 'true()':
                    continue
                
            #TODO: These should be on the settings sheet... I'm not sure if we need to support them being on the survey sheet as well
            #    Except default lang, I don't know what to do with that.
            if question[TYPE] == SET_TITLE:
                if not question[NAME].strip().find(" ") == -1:
                    raise PyXFormError("Form title must not include any spaces", question[NAME])
                self._title = question[NAME]
                continue
    
            if question[TYPE] == SET_ID:
                #TODO: Can any name cell ever contain spaces? Move this up if not
                if not question[NAME].strip().find(" ") == -1:
                    raise PyXFormError("Form id must not include any spaces", question[NAME])
                self._id = question[NAME]
                continue
            
            if question[TYPE] == SET_DEFAULT_LANG:
                self._def_lang = question[NAME]#We need to hold onto this because it is used when generating itext elements
                continue
            
            new_question_list.append(self._process_question_type(question))
            
        self._dict[SURVEY_SHEET] = new_question_list
        
        #Make sure form name and ID are properly set:
        if self._id.find(" ") != -1:
            raise PyXFormError("Form id must not include any spaces", self._id)

        if self._name.find(" ") != -1:
            self._name = self._id

    def _process_question_type(self, question):
        question_type = question[TYPE]
        question_type.strip()
        question_type = re.sub(r"\s+", " ", question_type) #Remove double spaces?

        try:
            return self._prepare_multiple_choice_question(question, question_type)
        except ParseQuestionException:
            try:
                return self._prepare_begin_loop(question, question_type)
            except ParseQuestionException as e:
                #print e.value #just for debug, maybe this should print to a logfile
                #raise PyXFormError("Unsupported syntax: '%s'" % question_type)
                return question

    def _prepare_multiple_choice_question(self, question, question_type):
        """
        Parse a multple choice question
        Throws ParseQuestionException
        Returns the passed in reference to the question object
        """
        selectCommands = {#Old commands
                          "select all that apply from" : u"select all that apply",
                          "select one from" : u"select one", 
                          #New commands
                          "select_one" : u"select one",
                          "select_multiple" : u"select all that apply" }
        
        select_regexp = r"^(?P<select_command>(" + '|'.join(selectCommands.keys()) + r")) (?P<list_name>\S+)( (?P<specify_other>or specify other))?$"
        select_parse = re.search(select_regexp, question_type)
        if select_parse:
            parse_dict = select_parse.groupdict()
            if parse_dict["select_command"]:
                select_type = selectCommands[parse_dict["select_command"]]
                list_name = parse_dict["list_name"] #TODO: should check that this is valid at some point
                
                #TODO: specify_other is not in the new spec
                specify_other = ("specify_other" in parse_dict and parse_dict["specify_other"]) or (" or specify other" in parse_dict and parse_dict[" or specify other"]) #old version

                question[TYPE] = select_type
                if specify_other:
                    question[TYPE] += " or specify other"
                question[CHOICES] = list_name
                
                return question
                
        raise ParseQuestionException("")

    def _prepare_begin_loop(self, q, question_type):
        m = re.search(r"^(?P<type>begin loop) over (?P<list_name>\S+)$", question_type)
        if not m:
            raise ParseQuestionException("Regex search returned None")
            #raise PyXFormError("unsupported loop syntax:" + question_type)
        assert COLUMNS not in q
        d = m.groupdict()
        q[COLUMNS] = d["list_name"]
        q[TYPE] = d["type"]
        return q

    def _construct_choice_lists(self):
        """
        Each choice has a list name associated with it. Go through the
        list of choices, grouping all the choices by their list name.
        """
        if self._lists_sheet_name is None:
            return
        choice_list = self._dict[self._lists_sheet_name]
        choices = {}
        for choice in choice_list:
            try:
                #TODO: decide whether there should be an underscore in list_name so we can get rid of this.
                list_name_string_wo_underscore = re.sub(" ", "_", LIST_NAME) if LIST_NAME not in choice else LIST_NAME
                list_name = choice.pop(list_name_string_wo_underscore)
                if list_name in choices:
                    choices[list_name].append(choice)
                else:
                    choices[list_name] = [choice]
            except KeyError:
                raise PyXFormError("For some reason this choice isn't associated with a list.", choice)
        self._dict[self._lists_sheet_name] = choices

    def _insert_lists(self):
        """
        For each multiple choice question and loop in the survey find
        the corresponding list and add it to that question.
        """
        lists_by_name = self._dict.get(self._lists_sheet_name, {})
        for q in self._dict[SURVEY_SHEET]:
            self._insert_list(q, CHOICES, lists_by_name)
            self._insert_list(q, COLUMNS, lists_by_name)

    def _insert_list(self, q, key, lists_by_name):
        if key in q:
            list_name = q[key]
            if list_name not in lists_by_name:
                raise PyXFormError("There is no list of %s by this name" % key, list_name)
            q[key] = lists_by_name[list_name]

    def _organize_sections(self):
        """
        This function arranges all the sections into a tree structure
        """
        # this needs to happen after columns have been inserted
        self._dict = self._dict[SURVEY_SHEET]
        result = {u"type": u"survey", u"name": self._name, u"children": []}
        result.update(self._settings)
        stack = [result]
        for cmd in self._dict:
            cmd_type = cmd[u"type"]
            match_begin = re.match(r"begin (?P<type>group|repeat|loop)", cmd_type)
            match_end = re.match(r"end (?P<type>group|repeat|loop)", cmd_type)
            # TODO: combine the begin and end patterns below with those above.
            # match_begin = re.match(r"begin (?P<type>lgroup|group|looped group|repeat)", cmd_type)
            # match_end = re.match(r"end (?P<type>lgroup|group|looped group|repeat)", cmd_type)
            if match_begin:
                # start a new section
                cmd[u"type"] = match_begin.group(1)

                if cmd[u"type"] in group_name_conversions:
                    cmd[u"type"] = group_name_conversions[cmd[u"type"]]

                cmd[u"children"] = []
                stack[-1][u"children"].append(cmd)
                stack.append(cmd)
            elif match_end:
                match_end = match_end.group(1)
                if match_end in group_name_conversions:
                    match_end = group_name_conversions[match_end]

                begin_cmd = stack.pop()
                if begin_cmd[u"type"] != match_end:
                    raise PyXFormError("This end group does not match the previous begin", cmd)
            else:
                stack[-1][u"children"].append(cmd)
        self._dict = result


class QuestionTypesReader(SpreadsheetReader):
    """
    Class for reading spreadsheet file that specifies the available question types.
    @see question_type_dictionary
    """
    def __init__(self, path):
        super(QuestionTypesReader, self).__init__(path)
        self._setup_question_types_dictionary()

    def _setup_question_types_dictionary(self):
        self._dict = self._dict[TYPES_SHEET]
        self._organize_by_type_name()

    def _organize_by_type_name(self):
        result = {}
        for question_type in self._dict:
            result[question_type.pop(u"name")] = question_type
        self._dict = result


#Not used
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
