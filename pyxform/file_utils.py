import os
import glob
import utils
from xlrd import open_workbook

#Conversion dictionary from user friendly column names to meaningful values
col_name_conversions = {
    "caption": u"label",
    "appearance": u"control:appearance",
    "relevance": u"bind:relevant",
    "required": u"bind:required",
    "read only": u"bind:readonly",
    "constraint": u"bind:constraint",
    "constraing message": u"bind:jr:constraintMsg",
    "calculation": u"bind:calculate",
    "command": u"type",
    "tag": u"name",
    "label": u"caption",
    "relevant": u"bind:relevant",
    "skippable": u"required",
    "value": u"name",
    "image": u"media:image",
    "audio": u"media:audio",
    "video": u"media:video",
    "count": u"bind:jr:count"
}

def xls_to_dict(path):
    """
    Return a Python dictionary with a key for each worksheet
    name. For each sheet there is a list of dictionaries, each
    dictionary corresponds to a single row in the worksheet. A
    dictionary has keys taken from the column headers and values
    equal to the cell value for that row and column.
    """
    workbook = open_workbook(path)
    _dict = {}
    for sheet in workbook.sheets():
        _dict[sheet.name] = []
        for row in range(1, sheet.nrows):
            row_dict = {}
            for column in range(0, sheet.ncols):
                key = sheet.cell(0, column).value

                # Convert key from ui friendly to meaningful
                if key in col_name_conversions:
                    key = col_name_conversions[key]
                # Special case for converting captions because
                # they have languages
                key = key.replace("caption", "label")

                value = sheet.cell(row, column).value
                if value is not None and value != "":
                    row_dict[key] = value

            if row_dict:
                _dict[sheet.name].append(row_dict)
    return _dict


import csv
def csv_to_dict(path):
    _dict = {}
    def first_column_as_sheet_name(row):
        s_or_c = row[0]
        content = row[1:]
        if s_or_c == '':
            s_or_c = None
        if reduce(lambda x, y: x+y, content) == '':
            # content is a list of empty strings
            content = None
        return (s_or_c, content)
    with open(path, 'rU') as f:
        reader = csv.reader(f)
        push_mode = None
        current_headers = None
        for row in reader:
            survey_or_choices, content = first_column_as_sheet_name(row)
            if survey_or_choices != None:
                push_mode = survey_or_choices
                if push_mode not in _dict:
                    _dict[push_mode] = []
                current_headers = None
            if content != None:
                if current_headers == None:
                    current_headers = content
                else:
                    _d = {}
                    for key, val in zip(current_headers, content):
                        if val != "":
                            _d[key] = val
                    _dict[push_mode].append(_d)
    return _dict


def load_csv_to_dict(path):
    # Note, this does not include sections
    section_path = _section_name(path)
    # sections = {
    #     section_path: SurveyReader(path, filetype="csv").to_dict()
    # }
    # return {
    #     "title": section_path,
    #     "name_of_main_section": section_path,
    #     "sections": sections,
    #     }
