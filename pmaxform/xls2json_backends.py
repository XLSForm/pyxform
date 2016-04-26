"""
XLS-to-dict and csv-to-dict are essentially backends for xls2json.
"""
import xlrd
from xlrd import XLRDError
import csv
import cStringIO
import constants
import re
import datetime
from errors import PyXFormError


def _list_to_dict_list(list_items):
    """
    Takes a list and creates a dict with the list values as keys.
    Returns a list of the created dict or an empty list
    """
    if list_items:
        k = {}
        for item in list_items:
            k[u'%s' % item] = u''
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
        if isinstance(path_or_file, basestring):
            workbook = xlrd.open_workbook(filename=path_or_file)
        else:
            workbook = xlrd.open_workbook(file_contents=path_or_file.read())
    except XLRDError, e:
        raise PyXFormError("Error reading .xls file: %s" % e.message)

    def xls_value_to_unicode(value, value_type):
        """
        Take a xls formatted value and try to make a unicode string
        representation.
        """
        if value_type == xlrd.XL_CELL_BOOLEAN:
            return u"TRUE" if value else u"FALSE"
        elif value_type == xlrd.XL_CELL_NUMBER:
            #Try to display as an int if possible.
            int_value = int(value)
            if int_value == value:
                return unicode(int_value)
            else:
                return unicode(value)
        elif value_type is xlrd.XL_CELL_DATE:
            #Warn that it is better to single quote as a string.
            #error_location = cellFormatString % (ss_row_idx, ss_col_idx)
            #raise Exception(
            #   "Cannot handle excel formatted date at " + error_location)
            datetime_or_time_only = xlrd.xldate_as_tuple(
                value, workbook.datemode)
            if datetime_or_time_only[:3] == (0, 0, 0):
                # must be time only
                return unicode(datetime.time(*datetime_or_time_only[3:]))
            return unicode(datetime.datetime(*datetime_or_time_only))
        else:
            #ensure unicode and replace nbsp spaces with normal ones
            #to avoid this issue:
            #https://github.com/modilabs/pyxform/issues/83
            return unicode(value).replace(unichr(160), ' ')

    def xls_to_dict_normal_sheet(sheet):
        def iswhitespace(string):
            return (
                isinstance(string, basestring) and len(string.strip()) == 0)

        #Check for duplicate column headers
        column_header_set = set()
        for column in range(0, sheet.ncols):
            column_header = sheet.cell_value(0, column)
            if column_header in column_header_set:
                raise PyXFormError(
                    u"Duplicate column header: %s" % column_header)
            # xls file with 3 columns mostly have a 3 more columns that are
            # blank by default or something, skip during check
            if column_header is not None:
                if not iswhitespace(column_header):
                    column_header_set.add(column_header)

        result = []
        for row in range(1, sheet.nrows):
            row_dict = {}
            for column in range(0, sheet.ncols):
                #Changing to cell_value function
                # convert to string, in case it is not string
                key = u"%s" % sheet.cell_value(0, column)
                key = key.strip()
                value = sheet.cell_value(row, column)
                # remove whitespace at the beginning and end of value
                if isinstance(value, basestring):
                    value = value.strip()
                value_type = sheet.cell_type(row, column)
                if value is not None:
                    if not iswhitespace(value):
                        row_dict[key] = xls_value_to_unicode(value, value_type)
#            Taking this condition out so I can get accurate row numbers.
#            TODO: Do the same for csvs
#            if row_dict != {}:
            result.append(row_dict)
        return result, _list_to_dict_list(column_header_set)

    def xls_value_from_sheet(sheet, row, column):
        value = sheet.cell_value(row, column)
        value_type = sheet.cell_type(row, column)
        if value is not None and value != "":
            return xls_value_to_unicode(value, value_type)
        else:
            raise PyXFormError("Empty Value")

    def xls_to_dict_cascade_sheet(sheet):
        result = []
        for column in range(1, sheet.ncols):  # col 1 = headers; don't process
            # first row value for this column is the key
            col_dict = {}
            col_name = sheet.cell_value(0, column)
            col_dict["name"] = col_name
            col_dict["choice_labels"] = []
            col_dict["prev_choice_labels"] = []
            for row in range(1, sheet.nrows):

                # pass 0: build col_dict for first time
                key = sheet.cell_value(row, 0)
                if key == "choice_label":
                    col_dict["choice_labels"].append(
                        xls_value_from_sheet(sheet, row, column))
                    if column > 1:
                        col_dict["prev_choice_labels"].append(
                            xls_value_from_sheet(sheet, row, column - 1))
                else:
                    col_dict[key] = xls_value_from_sheet(sheet, row, column)

                # pass 1: make sure choice_labels are unique,
                # while keeping the paired prev_choice_label consistent
                def f(l, (x1, x2)):
                    if (x1, x2) in l:
                        return l
                    else:
                        return l + [(x1, x2)]
                zipped = reduce(
                    f,
                    zip(col_dict["choice_labels"],
                        col_dict["prev_choice_labels"]
                        or col_dict["choice_labels"]), [])
                col_dict["choice_labels"] = [a for a, b in zipped]
                if column > 1:
                    col_dict["prev_choice_labels"] = [b for a, b in zipped]
                # end make things unique
            result.append(col_dict)

        # pass 2: explode things according to prev_choices
        result2 = []

        def slugify(s):
            return re.sub(r'\W+', '_', s.lower())
        prefix = "$PREFIX$"
        for index, level in enumerate(result):
            if index == 0:
                result2.append({'lambda': {
                    "name": prefix + '_' + level['name'],
                    "label": level['label'],
                    "children": [
                        {'name': slugify(x),
                         'label': x} for x in level['choice_labels']],
                    "type": "select one",
                }})
                result2.append({"stopper": level['name']})
                continue
            calc_formula_string = "'ERROR'"
            for prev_choice_label in set(level["prev_choice_labels"]):
                prev_choice_name = slugify(prev_choice_label)
                my_name = \
                    prefix + '_' + level["name"] + "_in_" + prev_choice_name
                prev_choice_val = \
                    "${" + prefix + "_" + result[index - 1]["name"] + "}"
                result2.append({'lambda': {
                    "name": my_name,
                    "label": level["label"],
                    "children": [
                        {'name': slugify(x), 'label': x}
                        for (x, y) in zip(
                            level["choice_labels"],
                            level["prev_choice_labels"])
                        if y == prev_choice_label],
                    "bind": {
                        u'relevant':
                        prev_choice_val + "='" + prev_choice_name + "'"},
                    "type": "select one"
                }})
                calc_formula_string = calc_formula_string.replace(
                    "'ERROR'",
                    "if(" + prev_choice_val + "='" + prev_choice_name
                    + "', ${" + my_name + "}, 'ERROR')")
            result2.append({'lambda': {
                "name": prefix + '_' + level["name"],
                "type": "calculate",
                "bind": {u'calculate': calc_formula_string}}})
            result2.append({"stopper": level['name']})
        return result2

    def _xls_to_dict_cascade_sheet(sheet):
        result = []
        rs_dict = {}  # tmp dict to hold entire structure

        def slugify(s):
            return re.sub(r'\W+', '_', s.strip().lower())
        prefix = "$PREFIX$"
        # get col headers and position first, ignore first column
        for column in range(1, sheet.ncols):
            col_name = sheet.cell_value(0, column)
            rs_dict[col_name] = {
                'pos': column,
                'data': [],
                'itemset': col_name,
                'type': constants.SELECT_ONE,
                'name':
                prefix if (column == sheet.ncols - 1) else u''.join(
                        [prefix, '_', col_name]),
                'label': sheet.cell_value(1, column)}
            if column > 1:
                rs_dict[col_name]['parent'] = sheet.cell_value(0, column - 1)
            else:
                rs_dict[col_name]['choices'] = []
            choice_filter = ''
            for a in range(1, column):
                prev_col_name = sheet.cell_value(0, a)
                if choice_filter != '':
                    choice_filter += ' and %s=${%s_%s}' %\
                                     (prev_col_name, prefix, prev_col_name)
                else:
                    choice_filter += '%s=${%s_%s}' % \
                                     (prev_col_name, prefix, prev_col_name)
            rs_dict[col_name]['choice_filter'] = choice_filter
        # get data, use new cascade dict structure, data starts on 3 row
        for row in range(2, sheet.nrows):
            # go through each header aka column
            for col_name in rs_dict:
                column = rs_dict[col_name]['pos']
                cell_data = xls_value_from_sheet(sheet, row, column)
                try:
                    rs_dict[col_name]['data'].index(slugify(cell_data))
                except ValueError:
                    rs_dict[col_name]['data'].append(slugify(cell_data))
                    if 'choices' in rs_dict[col_name]:
                        l = {'name': slugify(cell_data), 'label': cell_data}
                        rs_dict[col_name]['choices'].append(l)
                data = {
                    'name': slugify(cell_data),
                    'label': cell_data.strip(),
                    constants.LIST_NAME: col_name
                }
                for prev_column in range(1, column):
                    prev_col_name = sheet.cell_value(0, prev_column)
                    data[prev_col_name] = slugify(xls_value_from_sheet(
                        sheet, row, prev_column))
                result.append(data)
        # order
        kl = []
        for column in range(1, sheet.ncols):
            col_name = sheet.cell_value(0, column)
            if 'parent' in rs_dict[col_name]:
                rs_dict[col_name].pop('parent')
            if 'pos' in rs_dict[col_name]:
                rs_dict[col_name].pop('pos')
            if 'data' in rs_dict[col_name]:
                rs_dict[col_name].pop('data')
            kl.append(rs_dict[col_name])

    # create list with no duplicates
        choices = []
        for rec in result:
            c = 0
            for check in result:
                if rec == check:
                    c += 1
            if c == 1:
                choices.append(rec)
            else:
                try:
                    choices.index(rec)
                except ValueError:
                    choices.append(rec)
        return [{'choices': choices, 'questions': kl}]

    result = {}
    for sheet in workbook.sheets():
        if sheet.name == constants.CASCADING_CHOICES:
            result[sheet.name] = _xls_to_dict_cascade_sheet(sheet)
        else:
            result[sheet.name], result[u"%s_header" % sheet.name] = \
                xls_to_dict_normal_sheet(sheet)
    return result


def get_cascading_json(sheet_list, prefix, level):
    return_list = []
    for row in sheet_list:
        if 'stopper' in row:
            if row['stopper'] == level:
                # last element's name IS the prefix; doesn't need level
                return_list[-1]["name"] = prefix
                return return_list
            else:
                continue
        elif 'lambda' in row:
            def replace_prefix(d, prefix):
                for k, v in d.items():
                    if isinstance(v, basestring):
                        d[k] = v.replace('$PREFIX$', prefix)
                    elif isinstance(v, dict):
                        d[k] = replace_prefix(v, prefix)
                    elif isinstance(v, list):
                        d[k] = map(lambda x: replace_prefix(x, prefix), v)
                return d
            return_list.append(replace_prefix(row['lambda'], prefix))
    raise PyXFormError(
        "Found a cascading_select " + level + ", but could not"
        " find " + level + "in cascades sheet.")


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
            if reduce(lambda x, y: x + y, content) == '':
                # content is a list of empty strings
                content = None
            return (s_or_c, content)

    reader = csv.reader(csv_data.split("\n"))
    sheet_name = None
    current_headers = None
    for ascii_row in reader:
        row = [unicode(cell, "utf-8") for cell in ascii_row]
        survey_or_choices, content = first_column_as_sheet_name(row)
        if survey_or_choices is not None:
            sheet_name = survey_or_choices
            if sheet_name not in _dict:
                _dict[unicode(sheet_name)] = []
            current_headers = None
        if content is not None:
            if current_headers is None:
                current_headers = content
                _dict[u"%s_header" % sheet_name] = \
                    _list_to_dict_list(current_headers)
            else:
                _d = {}
                for key, val in zip(current_headers, content):
                    if val != "":
                        #Slight modification so values are striped
                        #this is because csvs often spaces following commas
                        #(but the csv reader might already handle that.)
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
    writer = csv.writer(
        foo, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
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
