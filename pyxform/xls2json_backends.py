import xlrd
from xlrd import XLRDError
from collections import defaultdict
import csv
import cStringIO
import constants
import re
from errors import PyXFormError

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
    def xls_to_dict_normal_sheet(sheet):
        result = []
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
            result.append(row_dict)
        return result
    def xls_value_from_sheet(sheet, row, column):
        value = sheet.cell_value(row, column)
        value_type = sheet.cell_type(row, column)
        if value is not None and value != "":
            return xls_value_to_unicode(value, value_type)
        else: raise PyXFormError("Empty Value")
    def xls_to_dict_cascade_sheet(sheet):
        result = []
        for column in range(1, sheet.ncols): # col 1 = headers; don't process
            # first row value for this column is the key
            col_dict = {}
            col_name = sheet.cell_value(0, column)
            col_dict["name"] = col_name 
            col_dict["choice_labels"] = []
            col_dict["prev_choice_labels"] = [] 
            for row in range(1, sheet.nrows):
                
                # pass 0: build col_dict for first time
                key = sheet.cell_value(row , 0)
                if key=="choice_label":
                    col_dict["choice_labels"].append(xls_value_from_sheet(sheet, row, column))
                    if column > 1: col_dict["prev_choice_labels"].append(xls_value_from_sheet(sheet, row, column - 1))
                else:
                    col_dict[key] = xls_value_from_sheet(sheet, row, column)

                # pass 1: make sure choice_labels are unique, while keeping the paired prev_choice_label consistent 
                def f(l, (x1,x2)):
                    if (x1,x2) in l: return l
                    else: return l + [(x1,x2)]
                zipped = reduce(f, zip(col_dict["choice_labels"], col_dict["prev_choice_labels"] or col_dict["choice_labels"]), [])
                col_dict["choice_labels"] = [a for a,b in zipped]
                if column > 1: col_dict["prev_choice_labels"] = [b for a,b in zipped]
                # end make things unique
            result.append(col_dict)

        # pass 2: explode things according to prev_choices 
        result2 = []
        def slugify(s): return re.sub(r'\W+', '_', s.lower())
        prefix = "$PREFIX$"
        for index,level in enumerate(result):
            if index==0: 
                result2.append({'lambda': {
                    "name": prefix + '_' + level['name'],
                    "label": level['label'],
                    "children": [{'name': slugify(x), 'label': x} for x in level['choice_labels']],
                    "type": "select one",
                }})
                result2.append({"stopper" : level['name']})
                continue
            calc_formula_string = "'ERROR'"
            for prev_choice_label in set(level["prev_choice_labels"]):
                prev_choice_name = slugify(prev_choice_label)
                my_name = prefix + '_' + level["name"] + "_in_" + prev_choice_name
                prev_choice_val = "${" + prefix + "_" + result[index-1]["name"] + "}"
                result2.append({'lambda': {
                    "name" : my_name, 
                    "label" : level["label"],
                    "children" : [{'name': slugify(x), 'label': x} 
                                  for (x,y) in zip(level["choice_labels"], level["prev_choice_labels"]) if y==prev_choice_label],
                    "bind": {u'relevant' : prev_choice_val + "='" + prev_choice_name + "'"},
                    "type" : "select one"
                }})
                calc_formula_string = calc_formula_string.replace("'ERROR'", "if(" + prev_choice_val + "='" + prev_choice_name + "', ${" + my_name + "}, 'ERROR')")
            result2.append({'lambda': {
                    "name" : prefix + '_' + level["name"],
                    "type" : "calculate",
                    "bind": {u'calculate' : calc_formula_string}}} )
            result2.append({"stopper" : level['name']})
        return result2
    try:
        if isinstance(path_or_file, basestring):
            workbook = xlrd.open_workbook(filename=path_or_file)
        else:
            workbook = xlrd.open_workbook(file_contents=path_or_file.read())
    except XLRDError, e:
        raise PyXFormError("Error reading .xls file: %s" % e.message)

    result = {}
    for sheet in workbook.sheets():
        if sheet.name==constants.CASCADING_CHOICES: result[sheet.name] = xls_to_dict_cascade_sheet(sheet)
        else: result[sheet.name] = xls_to_dict_normal_sheet(sheet)
    return result

def get_cascading_json(sheet_list, prefix, level):
    return_list = []
    for row in sheet_list:
        if row.has_key('stopper'):
            if row['stopper'] == level:
                return_list[-1]["name"] = prefix # last element's name IS the prefix; doesn't need level
                return return_list
            else:
                continue
        elif row.has_key('lambda'):
            def replace_prefix(d, prefix):
                for k, v in d.items():
                    if isinstance(v, basestring):
                        d[k] = v.replace('$PREFIX$', prefix)
                    elif isinstance(v, dict):
                        d[k] = replace_prefix(v, prefix)
                    elif isinstance(v, list):
                        d[k] = map(lambda x:replace_prefix(x, prefix), v)
                return d
            return_list.append(replace_prefix(row['lambda'], prefix))
    raise PyXFormError("Found a cascading_select " + level + ", but could not find " + level + "in cascades sheet.")

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
