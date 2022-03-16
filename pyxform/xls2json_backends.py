# -*- coding: utf-8 -*-
"""
XLS-to-dict and csv-to-dict are essentially backends for xls2json.
"""
import csv
import datetime
import re
from collections import OrderedDict
from functools import reduce
from io import StringIO
from zipfile import BadZipFile

import openpyxl
import xlrd
from xlrd import XLRDError
from xlrd.xldate import XLDateAmbiguous

from pyxform import constants
from pyxform.errors import PyXFormError

XL_DATE_AMBIGOUS_MSG = (
    "The xls file provided has an invalid date on the %s sheet, under"
    " the %s column on row number %s"
)


def _list_to_dict_list(list_items):
    """
    Takes a list and creates a dict with the list values as keys.
    Returns a list of the created dict or an empty list
    """
    if list_items:
        k = OrderedDict()
        for item in list_items:
            k["%s" % item] = ""
        return [k]
    return []


def xls_to_dict(path_or_file):
    """
    Return a Python dictionary with a key for each worksheet
    name. For each sheet there is a list of dictionaries, each
    dictionary corresponds to a single row in the worksheet. A
    dictionary has keys taken from the column headers and values
    equal to the cell value for that row and column.
    All the keys and leaf elements are unicode text.
    """
    try:
        if isinstance(path_or_file, str):
            workbook = xlrd.open_workbook(filename=path_or_file)
        else:
            workbook = xlrd.open_workbook(file_contents=path_or_file.read())
    except XLRDError as error:
        raise PyXFormError("Error reading .xls file: %s" % error)

    def xls_to_dict_normal_sheet(sheet):
        def iswhitespace(string):
            return isinstance(string, str) and len(string.strip()) == 0

        # Check for duplicate column headers
        column_header_list = list()
        for column in range(0, sheet.ncols):
            column_header = sheet.cell_value(0, column)
            if column_header in column_header_list:
                raise PyXFormError("Duplicate column header: %s" % column_header)
            # xls file with 3 columns mostly have a 3 more columns that are
            # blank by default or something, skip during check
            if column_header is not None:
                if not iswhitespace(column_header):
                    # strip whitespaces from the header
                    clean_header = re.sub(r"( )+", " ", column_header.strip())
                    column_header_list.append(clean_header)

        result = []
        for row in range(1, sheet.nrows):
            row_dict = OrderedDict()
            for column in range(0, sheet.ncols):
                # Changing to cell_value function
                # convert to string, in case it is not string
                key = "%s" % sheet.cell_value(0, column)
                key = key.strip()
                value = sheet.cell_value(row, column)
                # remove whitespace at the beginning and end of value
                if isinstance(value, str):
                    value = value.strip()
                value_type = sheet.cell_type(row, column)
                if value is not None:
                    if not iswhitespace(value):
                        try:
                            row_dict[key] = xls_value_to_unicode(
                                value, value_type, workbook.datemode
                            )
                        except XLDateAmbiguous:
                            raise PyXFormError(
                                XL_DATE_AMBIGOUS_MSG % (sheet.name, column_header, row)
                            )
                # Taking this condition out so I can get accurate row numbers.
                # TODO: Do the same for csvs
                # if row_dict != {}:
            result.append(row_dict)
        return result, _list_to_dict_list(column_header_list)

    def xls_value_from_sheet(sheet, row, column):
        value = sheet.cell_value(row, column)
        value_type = sheet.cell_type(row, column)
        if value is not None and value != "":
            try:
                return xls_value_to_unicode(value, value_type, workbook.datemode)
            except XLDateAmbiguous:
                raise PyXFormError(XL_DATE_AMBIGOUS_MSG % (sheet.name, column, row))
        else:
            raise PyXFormError("Empty Value")

    result = OrderedDict()
    for sheet in workbook.sheets():
        # Note that the sheet exists but do no further processing here.
        result[sheet.name] = []
        # Do not process sheets that have nothing to do with XLSForm.
        if sheet.name not in constants.SUPPORTED_SHEET_NAMES:
            if len(workbook.sheets()) == 1:
                (
                    result[constants.SURVEY],
                    result["%s_header" % constants.SURVEY],
                ) = xls_to_dict_normal_sheet(sheet)
            else:
                continue
        else:
            (
                result[sheet.name],
                result["%s_header" % sheet.name],
            ) = xls_to_dict_normal_sheet(sheet)

    return result


def xls_value_to_unicode(value, value_type, datemode):
    """
    Take a xls formatted value and try to make a unicode string
    representation.
    """
    if value_type == xlrd.XL_CELL_BOOLEAN:
        return "TRUE" if value else "FALSE"
    elif value_type == xlrd.XL_CELL_NUMBER:
        # Try to display as an int if possible.
        int_value = int(value)
        if int_value == value:
            return str(int_value)
        else:
            return str(value)
    elif value_type is xlrd.XL_CELL_DATE:
        # Warn that it is better to single quote as a string.
        # error_location = cellFormatString % (ss_row_idx, ss_col_idx)
        # raise Exception(
        #   "Cannot handle excel formatted date at " + error_location)
        datetime_or_time_only = xlrd.xldate_as_tuple(value, datemode)
        if datetime_or_time_only[:3] == (0, 0, 0):
            # must be time only
            return str(datetime.time(*datetime_or_time_only[3:]))
        return str(datetime.datetime(*datetime_or_time_only))
    else:
        # ensure unicode and replace nbsp spaces with normal ones
        # to avoid this issue:
        # https://github.com/modilabs/pyxform/issues/83
        return str(value).replace(chr(160), " ")


def xlsx_to_dict(path_or_file):
    """
    Return a Python dictionary with a key for each worksheet
    name. For each sheet there is a list of dictionaries, each
    dictionary corresponds to a single row in the worksheet. A
    dictionary has keys taken from the column headers and values
    equal to the cell value for that row and column.
    All the keys and leaf elements are strings.
    """
    try:
        workbook = openpyxl.open(filename=path_or_file, read_only=True, data_only=True)
    except (OSError, BadZipFile, KeyError) as error:
        raise PyXFormError("Error reading .xlsx file: %s" % error)

    def xlsx_to_dict_normal_sheet(sheet):

        # Check for duplicate column headers
        column_header_list = list()

        first_row = next(sheet.rows, [])
        for cell in first_row:
            column_header = cell.value
            # xls file with 3 columns mostly have a 3 more columns that are
            # blank by default or something, skip during check
            if is_empty(column_header):
                # Preserve column order (will filter later)
                column_header_list.append(None)
            else:
                if column_header in column_header_list:
                    raise PyXFormError("Duplicate column header: %s" % column_header)
                # strip whitespaces from the header
                clean_header = re.sub(r"( )+", " ", column_header.strip())
                column_header_list.append(clean_header)

        result = []
        for row in sheet.iter_rows(min_row=2):
            row_dict = OrderedDict()
            for column, key in enumerate(column_header_list):
                if key is None:
                    continue

                try:
                    value = row[column].value
                    if isinstance(value, str):
                        value = value.strip()

                    if not is_empty(value):
                        row_dict[key] = xlsx_value_to_str(value)
                except IndexError:
                    pass  # rows may not have values for every column

            result.append(row_dict)

        column_header_list = [key for key in column_header_list if key is not None]

        return result, _list_to_dict_list(column_header_list)

    result = OrderedDict()
    for sheetname in workbook.sheetnames:
        sheet = workbook[sheetname]
        # Note that the sheet exists but do no further processing here.
        result[sheetname] = []
        # Do not process sheets that have nothing to do with XLSForm.
        if sheetname not in constants.SUPPORTED_SHEET_NAMES:
            if len(workbook.sheetnames) == 1:
                (
                    result[constants.SURVEY],
                    result[f"{constants.SURVEY}_header"],
                ) = xlsx_to_dict_normal_sheet(sheet)
            else:
                continue
        else:
            (
                result[sheetname],
                result[f"{sheetname}_header"],
            ) = xlsx_to_dict_normal_sheet(sheet)

    workbook.close()
    return result


def xlsx_value_to_str(value):
    """
    Take a xls formatted value and try to make a string representation.
    """
    if value is True:
        return "TRUE"
    elif value is False:
        return "FALSE"
    elif isinstance(value, float) and value.is_integer():
        # Try to display as an int if possible.
        return str(int(value))
    elif isinstance(value, (int, datetime.datetime, datetime.time)):
        return str(value)
    else:
        # ensure unicode and replace nbsp spaces with normal ones
        # to avoid this issue:
        # https://github.com/modilabs/pyxform/issues/83
        return str(value).replace(chr(160), " ")


def is_empty(value):
    if value is None:
        return True
    elif isinstance(value, str) and value.strip() == "":
        return True
    else:
        return False


def get_cascading_json(sheet_list, prefix, level):
    return_list = []
    for row in sheet_list:
        if "stopper" in row:
            if row["stopper"] == level:
                # last element's name IS the prefix; doesn't need level
                return_list[-1]["name"] = prefix
                return return_list
            else:
                continue
        elif "lambda" in row:

            def replace_prefix(d, prefix):
                for k, v in d.items():
                    if isinstance(v, str):
                        d[k] = v.replace("$PREFIX$", prefix)
                    elif isinstance(v, dict):
                        d[k] = replace_prefix(v, prefix)
                    elif isinstance(v, list):
                        d[k] = map(lambda x: replace_prefix(x, prefix), v)
                return d

            return_list.append(replace_prefix(row["lambda"], prefix))
    raise PyXFormError(
        "Found a cascading_select "
        + level
        + ", but could not find "
        + level
        + "in cascades sheet."
    )


def csv_to_dict(path_or_file):
    if isinstance(path_or_file, str):
        csv_data = open(path_or_file, "r", encoding="utf-8", newline="")
    else:
        csv_data = path_or_file

    _dict = OrderedDict()

    def first_column_as_sheet_name(row):
        if len(row) == 0:
            return None, None
        elif len(row) == 1:
            return row[0], None
        else:
            s_or_c = row[0]
            content = row[1:]
            if s_or_c == "":
                s_or_c = None
            # concatenate all the strings in content
            if reduce(lambda x, y: x + y, content) == "":
                # content is a list of empty strings
                content = None
            return s_or_c, content

    reader = csv.reader(csv_data)
    sheet_name = None
    current_headers = None
    for row in reader:
        survey_or_choices, content = first_column_as_sheet_name(row)
        if survey_or_choices is not None:
            sheet_name = survey_or_choices
            if sheet_name not in _dict:
                _dict[str(sheet_name)] = []
            current_headers = None
        if content is not None:
            if current_headers is None:
                current_headers = content
                _dict["%s_header" % sheet_name] = _list_to_dict_list(current_headers)
            else:
                _d = OrderedDict()
                for key, val in zip(current_headers, content):
                    if val != "":
                        # Slight modification so values are striped
                        # this is because csvs often spaces following commas
                        # (but the csv reader might already handle that.)
                        _d[str(key)] = str(val.strip())
                _dict[sheet_name].append(_d)
    csv_data.close()
    return _dict


"""
I want the ability to go:

    xls => csv
so that we can go:
    xls => csv => survey

and some day:
    csv => xls

"""


def convert_file_to_csv_string(path):
    """
    This will open a csv or xls file and return a CSV in the format:
        sheet_name1
        ,col1,col2
        ,r1c1,r1c2
        ,r2c1,r2c2
        sheet_name2
        ,col1,col2
        ,r1c1,r1c2
        ,r2c1,r2c2

    Currently, it processes csv files and xls files to ensure consistent
    csv delimiters, etc. for tests.
    """
    if path.endswith(".csv"):
        imported_sheets = csv_to_dict(path)
    else:
        imported_sheets = xls_to_dict(path)
    foo = StringIO(newline="")
    writer = csv.writer(foo, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for sheet_name, rows in imported_sheets.items():
        writer.writerow([sheet_name])
        out_keys = []
        out_rows = []
        for row in rows:
            out_row = []
            for key in row.keys():
                if key not in out_keys:
                    out_keys.append(key)
            for out_key in out_keys:
                out_row.append(row.get(out_key, None))
            out_rows.append(out_row)
        writer.writerow([None] + out_keys)
        for out_row in out_rows:
            writer.writerow([None] + out_row)
    return foo.getvalue()
