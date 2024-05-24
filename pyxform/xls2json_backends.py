"""
XLS-to-dict and csv-to-dict are essentially backends for xls2json.
"""

import csv
import datetime
import os
import re
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import closing
from functools import reduce
from io import StringIO
from typing import Any
from zipfile import BadZipFile

import xlrd
from openpyxl.cell import Cell as pyxlCell
from openpyxl.reader.excel import ExcelReader
from openpyxl.workbook import Workbook as pyxlWorkbook
from openpyxl.worksheet.worksheet import Worksheet as pyxlWorksheet
from xlrd.book import Book as xlrdBook
from xlrd.sheet import Cell as xlrdCell
from xlrd.sheet import Sheet as xlrdSheet
from xlrd.xldate import XLDateAmbiguous

from pyxform import constants
from pyxform.errors import PyXFormError

aCell = xlrdCell | pyxlCell
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
            k[str(item)] = ""
        return [k]
    return []


def trim_trailing_empty(a_list: list, n_empty: int) -> list:
    """
    Trim trailing empty columns or rows. Avoids `[:-0] == []`, and unnecessary list copy.
    """
    if 0 < n_empty:
        offset = len(a_list) - n_empty
        a_list = a_list[:offset]
    return a_list


def get_excel_column_headers(first_row: Iterator[str | None]) -> list[str | None]:
    """Get column headers from the first row; stop if there's a run of empty columns."""
    max_adjacent_empty_columns = 20
    column_header_list = []
    adjacent_empty_cols = 0
    for column_header in first_row:
        if is_empty(column_header):
            # Preserve column order (will filter later)
            column_header_list.append(None)
            # After a run of empty cols, assume we've reached the end of the data.
            if max_adjacent_empty_columns == adjacent_empty_cols:
                break
            adjacent_empty_cols += 1
        else:
            adjacent_empty_cols = 0
            # Check for duplicate column headers.
            if column_header in column_header_list:
                raise PyXFormError(f"Duplicate column header: {column_header}")
            # Strip whitespaces from the header.
            clean_header = re.sub(r"( )+", " ", column_header.strip())
            column_header_list.append(clean_header)

    return trim_trailing_empty(column_header_list, adjacent_empty_cols)


def get_excel_rows(
    headers: Iterator[str | None],
    rows: Iterator[tuple[aCell, ...]],
    cell_func: Callable[[aCell, int, str], Any],
) -> list[dict[str, Any]]:
    """Get rows of cleaned data; stop if there's a run of empty rows."""
    max_adjacent_empty_rows = 60
    col_header_enum = list(enumerate(headers))
    adjacent_empty_rows = 0
    result_rows = []
    for row_n, row in enumerate(rows):
        row_dict = OrderedDict()
        for col_n, key in col_header_enum:
            if key is None:
                continue
            try:
                cell = row[col_n]
                if not is_empty(cell.value):
                    row_dict[key] = cell_func(cell, row_n, key)
            except IndexError:
                pass  # rows may not have values for every column

        if 0 == len(row_dict):
            # After a run of empty rows, assume we've reached the end of the data.
            if max_adjacent_empty_rows == adjacent_empty_rows:
                break
            adjacent_empty_rows += 1
        else:
            adjacent_empty_rows = 0

        # There may be some empty rows amongst the XLSForm data. These are included
        # so that any warning messages that mention row numbers are accurate.
        result_rows.append(row_dict)

    return trim_trailing_empty(result_rows, adjacent_empty_rows)


def xls_to_dict(path_or_file):
    """
    Return a Python dictionary with a key for each worksheet
    name. For each sheet there is a list of dictionaries, each
    dictionary corresponds to a single row in the worksheet. A
    dictionary has keys taken from the column headers and values
    equal to the cell value for that row and column.
    All the keys and leaf elements are unicode text.
    """

    def xls_clean_cell(
        wb: xlrdBook, wb_sheet: xlrdSheet, cell: xlrdCell, row_n: int, col_key: str
    ) -> str | None:
        value = cell.value
        if isinstance(value, str):
            value = value.strip()
        if not is_empty(value):
            try:
                return xls_value_to_unicode(value, cell.ctype, wb.datemode)
            except XLDateAmbiguous as date_err:
                raise PyXFormError(
                    XL_DATE_AMBIGOUS_MSG % (wb_sheet.name, col_key, row_n)
                ) from date_err

        return None

    def xls_to_dict_normal_sheet(wb: xlrdBook, wb_sheet: xlrdSheet):
        # XLS format: max cols 256, max rows 65536
        first_row = (c.value for c in next(wb_sheet.get_rows(), []))
        headers = get_excel_column_headers(first_row=first_row)
        row_iter = (
            tuple(wb_sheet.cell(r, c) for c in range(len(headers)))
            for r in range(1, wb_sheet.nrows)
        )

        # Inject wb/sheet as closure since functools.partial isn't typing friendly.
        def clean_func(cell: xlrdCell, row_n: int, col_key: str) -> str | None:
            return xls_clean_cell(
                wb=wb, wb_sheet=wb_sheet, cell=cell, row_n=row_n, col_key=col_key
            )

        rows = get_excel_rows(headers=headers, rows=row_iter, cell_func=clean_func)
        column_header_list = [key for key in headers if key is not None]
        return rows, _list_to_dict_list(column_header_list)

    def process_workbook(wb: xlrdBook):
        result_book = OrderedDict()
        for wb_sheet in wb.sheets():
            # Note that the sheet exists but do no further processing here.
            result_book[wb_sheet.name] = []
            # Do not process sheets that have nothing to do with XLSForm.
            if wb_sheet.name not in constants.SUPPORTED_SHEET_NAMES:
                if len(wb.sheets()) == 1:
                    (
                        result_book[constants.SURVEY],
                        result_book[f"{constants.SURVEY}_header"],
                    ) = xls_to_dict_normal_sheet(wb=wb, wb_sheet=wb_sheet)
                else:
                    continue
            else:
                (
                    result_book[wb_sheet.name],
                    result_book[f"{wb_sheet.name}_header"],
                ) = xls_to_dict_normal_sheet(wb=wb, wb_sheet=wb_sheet)
        return result_book

    try:
        if isinstance(path_or_file, str | bytes | os.PathLike):
            file = open(path_or_file, mode="rb")
        else:
            file = path_or_file
        with closing(file) as wb_file:
            workbook = xlrd.open_workbook(file_contents=wb_file.read())
            try:
                return process_workbook(wb=workbook)
            finally:
                workbook.release_resources()
    except xlrd.XLRDError as read_err:
        raise PyXFormError(f"Error reading .xls file: {read_err}") from read_err


def xls_value_to_unicode(value, value_type, datemode) -> str:
    """
    Take a xls formatted value and try to make a unicode string representation.
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

    def xlsx_clean_cell(cell: pyxlCell, row_n: int, col_key: str) -> str | None:
        value = cell.value
        if isinstance(value, str):
            value = value.strip()
        if not is_empty(value):
            return xlsx_value_to_str(value)

        return None

    def xlsx_to_dict_normal_sheet(sheet: pyxlWorksheet):
        # XLSX format: max cols 16384, max rows 1048576
        first_row = (c.value for c in next(sheet.rows, []))
        headers = get_excel_column_headers(first_row=first_row)
        row_iter = sheet.iter_rows(min_row=2, max_col=len(headers))
        rows = get_excel_rows(headers=headers, rows=row_iter, cell_func=xlsx_clean_cell)
        column_header_list = [key for key in headers if key is not None]
        return rows, _list_to_dict_list(column_header_list)

    def process_workbook(wb: pyxlWorkbook):
        result_book = OrderedDict()
        for sheetname in wb.sheetnames:
            wb_sheet = wb[sheetname]
            # Note that the sheet exists but do no further processing here.
            result_book[sheetname] = []
            # Do not process sheets that have nothing to do with XLSForm.
            if sheetname not in constants.SUPPORTED_SHEET_NAMES:
                if len(wb.sheetnames) == 1:
                    (
                        result_book[constants.SURVEY],
                        result_book[f"{constants.SURVEY}_header"],
                    ) = xlsx_to_dict_normal_sheet(wb_sheet)
                else:
                    continue
            else:
                (
                    result_book[sheetname],
                    result_book[f"{sheetname}_header"],
                ) = xlsx_to_dict_normal_sheet(wb_sheet)
        return result_book

    try:
        if isinstance(path_or_file, str | bytes | os.PathLike):
            file = open(path_or_file, mode="rb")
        else:
            file = path_or_file
        with closing(file) as wb_file:
            reader = ExcelReader(wb_file, read_only=True, data_only=True)
            reader.read()
            try:
                return process_workbook(wb=reader.wb)
            finally:
                reader.wb.close()
                reader.archive.close()
    except (OSError, BadZipFile, KeyError) as read_err:
        raise PyXFormError(f"Error reading .xlsx file: {read_err}") from read_err


def xlsx_value_to_str(value) -> str:
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
    elif isinstance(value, int | datetime.datetime | datetime.time):
        return str(value)
    else:
        # ensure unicode and replace nbsp spaces with normal ones
        # to avoid this issue:
        # https://github.com/modilabs/pyxform/issues/83
        return str(value).replace(chr(160), " ")


def is_empty(value):
    if value is None:
        return True
    elif isinstance(value, str):
        if value.strip() == "":
            return True

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
                        d[k] = (replace_prefix(x, prefix) for x in v)
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
        csv_data = open(path_or_file, encoding="utf-8", newline="")
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
                _dict[f"{sheet_name}_header"] = _list_to_dict_list(current_headers)
            else:
                _d = OrderedDict()
                for key, val in zip(current_headers, content, strict=False):
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
        writer.writerow([None, *out_keys])
        for out_row in out_rows:
            writer.writerow([None, *out_row])
    return foo.getvalue()
