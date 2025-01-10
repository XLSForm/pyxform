"""
Test xls2json_backends module functionality.
"""

import datetime
import os
from unittest import TestCase

import openpyxl
import xlrd
from pyxform.xls2json_backends import (
    csv_to_dict,
    md_to_dict,
    xls_to_dict,
    xls_value_to_unicode,
    xlsx_to_dict,
    xlsx_value_to_str,
)

from tests import bug_example_xls, utils


class TestXLS2JSONBackends(TestCase):
    """
    Test xls2json_backends module.
    """

    maxDiff = None

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
        """Should get the same data from equivalent files using each file type reader."""
        equivalent_fixtures = [
            "group",
            "include",
            "include_json",
            "loop",
            "specify_other",
            "text_and_integer",
            "yes_or_no_question",
        ]
        for fixture in equivalent_fixtures:
            xlsx_inp = xlsx_to_dict(utils.path_to_text_fixture(f"{fixture}.xlsx"))
            xls_inp = xls_to_dict(utils.path_to_text_fixture(f"{fixture}.xls"))
            csv_inp = csv_to_dict(utils.path_to_text_fixture(f"{fixture}.csv"))
            md_inp = md_to_dict(utils.path_to_text_fixture(f"{fixture}.md"))

            self.assertEqual(xlsx_inp, xls_inp)
            self.assertEqual(xlsx_inp, csv_inp)
            self.assertEqual(xlsx_inp, md_inp)

    def test_xls_with_many_empty_cells(self):
        """Should quickly produce expected data, and find large input sheet dimensions."""
        # Test fixture produced by adding data at cells IV1 and A19999.
        xls_path = os.path.join(bug_example_xls.PATH, "extra_columns.xls")
        before = datetime.datetime.now(datetime.timezone.utc)
        xls_data = xls_to_dict(xls_path)
        after = datetime.datetime.now(datetime.timezone.utc)
        self.assertLess((after - before).total_seconds(), 5)
        wb = xlrd.open_workbook(filename=xls_path)

        survey_headers = [
            "type",
            "name",
            "label",
        ]
        self.assertEqual(survey_headers, list(xls_data["survey_header"][0].keys()))
        self.assertEqual(3, len(xls_data["survey"]))
        self.assertEqual("b", xls_data["survey"][2]["name"])
        survey = wb["survey"]
        self.assertTupleEqual((19999, 256), (survey.nrows, survey.ncols))

        wb.release_resources()

    def test_xlsx_with_many_empty_cells(self):
        """Should quickly produce expected data, and find large input sheet dimensions."""
        # Test fixture produced (presumably) by a LibreOffice serialisation bug.
        xlsx_path = os.path.join(bug_example_xls.PATH, "UCL_Biomass_Plot_Form.xlsx")
        before = datetime.datetime.now(datetime.timezone.utc)
        xlsx_data = xlsx_to_dict(xlsx_path)
        after = datetime.datetime.now(datetime.timezone.utc)
        self.assertLess((after - before).total_seconds(), 5)
        wb = openpyxl.open(filename=xlsx_path, read_only=True, data_only=True)

        survey_headers = [
            "type",
            "name",
            "label::Swahili (sw)",
            "label::English (en)",
            "hint::Swahili (sw)",
            "hint::English (en)",
            "required",
            "relevant",
            "constraint",
            "constraint_message::Swahili (sw)",
            "constraint_message::English (en)",
            "choice_filter",
            "appearance",
            "calculation",
            "repeat_count",
            "parameters",
        ]
        # Expected headers, rows, and last row contains expected data.
        self.assertEqual(survey_headers, list(xlsx_data["survey_header"][0].keys()))
        self.assertEqual(90, len(xlsx_data["survey"]))
        self.assertEqual("deviceid", xlsx_data["survey"][89]["type"])
        survey = wb["survey"]
        self.assertTupleEqual((1048576, 1024), (survey.max_row, survey.max_column))

        choices_headers = [
            "list_name",
            "name",
            "label::Swahili (sw)",
            "label::English (en)",
        ]
        self.assertEqual(choices_headers, list(xlsx_data["choices_header"][0].keys()))
        self.assertEqual(27, len(xlsx_data["choices"]))
        self.assertEqual("Mwingine", xlsx_data["choices"][26]["label::Swahili (sw)"])
        choices = wb["choices"]
        self.assertTupleEqual((1048576, 4), (choices.max_row, choices.max_column))

        settings_headers = [
            "default_language",
            "version",
        ]
        self.assertEqual(settings_headers, list(xlsx_data["settings_header"][0].keys()))
        self.assertEqual(1, len(xlsx_data["settings"]))
        self.assertEqual("Swahili (sw)", xlsx_data["settings"][0]["default_language"])
        settings = wb["settings"]
        self.assertTupleEqual((2, 2), (settings.max_row, settings.max_column))

        wb.close()
