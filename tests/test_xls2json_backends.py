# -*- coding: utf-8 -*-
"""
Test xls2json_backends module functionality.
"""
from unittest import TestCase

import openpyxl
import xlrd

from pyxform.xls2json_backends import (
    xls_to_dict,
    xls_value_to_unicode,
    xlsx_to_dict,
    xlsx_value_to_str,
)
from tests import utils


class TestXLS2JSONBackends(TestCase):
    """
    Test xls2json_backends module.
    """

    def test_xls_value_to_unicode(self):
        """
        Test external choices sheet with numeric values is processed successfully.

        The test ensures that the integer values within the external choices sheet
        are returned as they were initially received.
        """
        value = 32.0
        value_type = xlrd.XL_CELL_NUMBER
        datemode = 1
        csv_data = xls_value_to_unicode(value, value_type, datemode)
        expected_output = "32"
        self.assertEqual(csv_data, expected_output)

        # Test that the decimal value is not changed during conversion.
        value = 46.9
        csv_data = xls_value_to_unicode(value, value_type, datemode)
        expected_output = "46.9"
        self.assertEqual(csv_data, expected_output)

    def test_xlsx_value_to_str(self):
        value = 32.0
        csv_data = xlsx_value_to_str(value)
        expected_output = "32"
        self.assertEqual(csv_data, expected_output)

        # Test that the decimal value is not changed during conversion.
        value = 46.9
        csv_data = xlsx_value_to_str(value)
        expected_output = "46.9"
        self.assertEqual(csv_data, expected_output)

    def test_defusedxml_enabled(self):
        self.assertTrue(openpyxl.DEFUSEDXML)

    def test_equivalency(self):
        equivalent_fixtures = [
            "group",
            "loop",
            "specify_other",
            "include",
            "text_and_integer",
            "include_json",
            "yes_or_no_question",
        ]
        for fixture in equivalent_fixtures:
            xls_path = utils.path_to_text_fixture("%s.xls" % fixture)
            xlsx_path = utils.path_to_text_fixture("%s.xlsx" % fixture)
            xls_inp = xls_to_dict(xls_path)
            xlsx_inp = xlsx_to_dict(xlsx_path)
            self.maxDiff = None
            self.assertEqual(xls_inp, xlsx_inp)
