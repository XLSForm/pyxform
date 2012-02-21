import xlrd
from collections import defaultdict
import csv
import cStringIO

"""
XLS-to-dict and csv-to-dict are essentially backends for xls2json.
"""


def xls_value_to_unicode(value, value_type):
    """
    Take a xls formatted value and try to make a unicode string representation.
    """
    if value_type == xlrd.XL_CELL_BOOLEAN:
        return u"TRUE" if value else u"FALSE"
    if value_type == xlrd.XL_CELL_NUMBER:
        #Try to display as an int if possible.
        int_value = int(value)
        if int_value == value:
            return unicode(int_value)
        else:
            return unicode(value)
    else:
        return unicode(value).strip()
        

def xls_to_dict(path_or_file):
    """
    Return a Python dictionary with a key for each worksheet
    name. For each sheet there is a list of dictionaries, each
    dictionary corresponds to a single row in the worksheet. A
    dictionary has keys taken from the column headers and values
    equal to the cell value for that row and column.
    All the keys and leaf elements are unicode text.
    """
    if isinstance(path_or_file, basestring):
        workbook = xlrd.open_workbook(filename=path_or_file)
    else:
        workbook = xlrd.open_workbook(file_contents=path_or_file.read())

    result = {}
    for sheet in workbook.sheets():
        result[sheet.name] = []
        for row in range(1, sheet.nrows):
            row_dict = {}
            for column in range(0, sheet.ncols):
                #Changing to cell_value function
                key = sheet.cell_value(0, column)#.value
                value = sheet.cell_value(row, column)#.value
                value_type = sheet.cell_type(row, column)
                if value is not None and value != "":
                    row_dict[key] = xls_value_to_unicode(value, value_type)
#            Taking this condition out so I can get accurate row numbers.
#            TODO: Do the same for csvs
#            if row_dict != {}:
            result[sheet.name].append(row_dict)
    return result

def csv_to_dict(path_or_file):
    if isinstance(path_or_file, basestring):
        with open(path_or_file) as f:
            csv_data = f.read()
    else:
        csv_data = path_or_file.read()

    _dict = {}
    def first_column_as_sheet_name(row):
        if len(row) == 0:
            return (None, None)
        elif len(row) == 1:
            return (row[0], None)
        else:
            s_or_c = row[0]
            content = row[1:]
            if s_or_c == '':
                s_or_c = None
            #concatenate all the strings in content
            if reduce(lambda x, y: x+y, content) == '':
                # content is a list of empty strings
                content = None
            return (s_or_c, content)

    reader = csv.reader(csv_data.split("\n"))
    sheet_name = None
    current_headers = None
    for row in reader:
        survey_or_choices, content = first_column_as_sheet_name(row)
        if survey_or_choices != None:
            sheet_name = survey_or_choices
            if sheet_name not in _dict:
                _dict[unicode(sheet_name)] = []
            current_headers = None
        if content != None:
            if current_headers == None:
                current_headers = content
            else:
                _d = {}
                for key, val in zip(current_headers, content):
                    if val != "":
                        #Slight modification so values are striped
                        #this is because csvs often spaces following commas (but the csv reader might already handle that.)
                        _d[unicode(key)] = unicode(val.strip())
                _dict[sheet_name].append(_d)
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
    foo = cStringIO.StringIO()
    writer = csv.writer(foo, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
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
