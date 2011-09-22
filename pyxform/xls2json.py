"""
A Python script to convert excel files into JSON.
"""

import json
import re
import sys
import codecs
import os


def print_pyobj_to_json(pyobj, path):
    fp = codecs.open(path, mode="w", encoding="utf-8")
    json.dump(pyobj, fp=fp, ensure_ascii=False, indent=4)
    fp.close()

# the following are the three sheet names that this program expects
SURVEY_SHEET = u"survey"
CHOICES_SHEET_NAMES = [u"choices", u"choices and columns"]
COLUMNS_SHEET = u"columns"
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
        if extension == ".xls":
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
        if self.filetype == "xls":
            self._dict = xls_to_dict(self._file_object if self._file_object is not None else self._path)
        elif self.filetype == "csv":
            self._dict = csv_to_dict(self._path)
        self._sheet_names = self._dict.keys()
        self._set_choices_and_columns_sheet_name()
        self._strip_unicode_values()
        self._fix_int_values()
        self._group_dictionaries()

    def _set_choices_and_columns_sheet_name(self):
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

    def to_dict(self):
        return self._dict

    def print_json_to_file(self, filename=""):
        if not filename:
            filename = self._path[:-4] + ".json"
        print_pyobj_to_json(self.to_dict(), filename)


class SurveyReader(SpreadsheetReader):
    def __init__(self, path):
        SpreadsheetReader.__init__(self, path)
        self._setup_survey()

    def _setup_survey(self):
        assert SURVEY_SHEET in self._dict, "You must have a sheet named: " + SURVEY_SHEET
        self._remove_questions_without_types()
        self._process_question_type()
        self._construct_choice_lists()
        self._insert_lists()
        self._save_settings()
        self._organize_sections()

    def _save_settings(self):
        # the excel reader gives a list of dicts, one dict for each
        # row after the headers, we're only going to use the first
        # row.
        self._settings = self._dict.get(u"settings", [{}])[0]

    def _remove_questions_without_types(self):
        self._dict[SURVEY_SHEET] = [
            q for q in self._dict[SURVEY_SHEET] if u"type" in q
            ]

    def _process_question_type(self):
        """
        We need to handle question types that look like select one
        from list-name or specify other.

        select one from list-name
        select all that apply from list-name
        select one from list-name or specify other
        select all that apply from list-name or specify other

        let's make it a requirement that list-names have no spaces
        """
        to_remove = []
        for q in self._dict[SURVEY_SHEET]:
            if q[TYPE] == SET_TITLE:
                if not q[NAME].strip().find(" ") == -1:
                    raise Exception("Form title must not include any spaces", q[NAME])
                self._title = q[NAME]
                to_remove.append(q)
                continue

            if q[TYPE] == SET_ID:
                if not q[NAME].strip().find(" ") == -1:
                    raise Exception("Form id must not include any spaces", q[NAME])
                self._id = q[NAME]
                to_remove.append(q)
                continue

            if q[TYPE] == SET_DEFAULT_LANG:
                self._def_lang = q[NAME]
                to_remove.append(q)
                continue

            if DISABLED in q:
                disabled = q["disabled"]
                if disabled in yes_no_conversions:
                    disabled = yes_no_conversions[disabled]
                if disabled == 'true()':
                    to_remove.append(q)
                continue

            question_type = q[TYPE]
            question_type.strip()
            re.sub(r"\s+", " ", question_type)

            if u"select" in question_type:
                self._prepare_multiple_choice_question(q, question_type)
            if question_type.startswith(u"begin loop"):
                self._prepare_begin_loop(q, question_type)

        if not self._id.find(" ") == -1:
            raise Exception("Form id must not include any spaces", self._id)

        if not self._name.find(" ") == -1:
            self._name = self._id

        for q in to_remove:
            self._dict[SURVEY_SHEET].remove(q)

    def _prepare_multiple_choice_question(self, q, question_type):
        regexp = r"^(?P<select_command>select one|select all that apply) from (?P<list_name>\S+)( (?P<specify_other>or specify other))?$"
        m = re.search(regexp, question_type)
        assert m, "unsupported select syntax:" + question_type
        assert CHOICES not in q
        d = m.groupdict()
        q[CHOICES] = d["list_name"]
        if d["specify_other"]:
            q[TYPE] = " ".join([d["select_command"], d["specify_other"]])
        else:
            q[TYPE] = d["select_command"]

    def _prepare_begin_loop(self, q, question_type):
        m = re.search(r"^(?P<type>begin loop) over (?P<list_name>\S+)$", question_type)
        assert m, "unsupported select syntax:" + question_type
        assert COLUMNS not in q
        d = m.groupdict()
        q[COLUMNS] = d["list_name"]
        q[TYPE] = d["type"]

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
                list_name = choice.pop(LIST_NAME)
            except KeyError:
                raise Exception("For some reason this choice isn't associated with a list.", choice)
            if list_name in choices:
                choices[list_name].append(choice)
            else:
                choices[list_name] = [choice]
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
                raise Exception("There is no list of %s by this name" % key, list_name)
            q[key] = lists_by_name[list_name]

    def _organize_sections(self):
        # this needs to happen after columns have been inserted
        self._dict = self._dict[SURVEY_SHEET]
        result = {u"type": u"survey", u"name": self._name, u"children": []}
        result.update(self._settings)
        stack = [result]
        for cmd in self._dict:
            cmd_type = cmd[u"type"]
            match_begin = re.match(r"begin (?P<type>group|repeat|loop)", cmd_type)
            match_end = re.match(r"end (?P<type>group|repeat|loop)", cmd_type)
            # Todo: combine the begin and end patterns below with those above.
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
                    raise Exception("This end group does not match the previous begin", cmd)
            else:
                stack[-1][u"children"].append(cmd)
        self._dict = result


class QuestionTypesReader(SpreadsheetReader):
    def __init__(self, path):
        SpreadsheetReader.__init__(self, path)
        self._setup_question_types_dictionary()

    def _setup_question_types_dictionary(self):
        self._dict = self._dict[TYPES_SHEET]
        self._organize_by_type_name()

    def _organize_by_type_name(self):
        result = {}
        for question_type in self._dict:
            result[question_type.pop(u"name")] = question_type
        self._dict = result


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
    print json.dumps(converter.to_dict(), ensure_ascii=False, indent=4)
