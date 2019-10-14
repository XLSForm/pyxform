# -*- coding: utf-8 -*-
"""
Markdown table utility functions.
"""
import re


def _strp_cell(cell):
    val = cell.strip()
    if val == "":
        return None

    return val


def _extract_array(mdtablerow):
    match = re.match(r"\s*\|(.*)\|\s*", mdtablerow)
    if match:
        mtchstr = match.groups()[0]
        if re.match(r"^[\|-]+$", mtchstr):
            return False
        else:
            return [_strp_cell(c) for c in mtchstr.split("|")]

    return False


def _is_null_row(r_arr):
    for cell in r_arr:
        if cell is not None:
            return False

    return True


def md_table_to_ss_structure(mdstr):
    ss_arr = []
    for item in mdstr.split("\n"):
        arr = _extract_array(item)
        if arr:
            ss_arr.append(arr)
    sheet_name = False
    sheet_arr = False
    sheets = []
    for row in ss_arr:
        if row[0] is not None:
            if sheet_arr:
                sheets.append((sheet_name, sheet_arr))
            sheet_arr = []
            sheet_name = row[0]
        excluding_first_col = row[1:]
        if sheet_name and not _is_null_row(excluding_first_col):
            sheet_arr.append(excluding_first_col)
    sheets.append((sheet_name, sheet_arr))

    return sheets
