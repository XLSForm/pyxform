# -*- coding: utf-8 -*-
"""
Some tests for the new (v0.9) spec is properly implemented.
"""
import os
from unittest import TestCase

from pyxform import builder, xls2json
from pyxform.errors import PyXFormError
from tests import example_xls, test_expected_output
from tests.xform_test_case.base import XFormTestCase


class TestXFormConversion(XFormTestCase):
    maxDiff = None

    def compare_xform(self, file_name: str, set_default_name: bool = True):
        self.get_file_path(file_name)
        expected_output_path = os.path.join(
            test_expected_output.PATH, self.root_filename + ".xml"
        )
        # Do the conversion:
        warnings = []
        if set_default_name:
            json_survey = xls2json.parse_file_to_json(
                self.path_to_excel_file,
                default_name=self.root_filename,
                warnings=warnings,
            )
        else:
            json_survey = xls2json.parse_file_to_json(
                self.path_to_excel_file,
                warnings=warnings,
            )
        survey = builder.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(self.output_path, warnings=warnings)
        # Compare with the expected output:
        with open(expected_output_path, "r", encoding="utf-8") as ef, open(
            self.output_path, "r", encoding="utf-8"
        ) as af:
            expected = ef.read()
            observed = af.read()
        self.assertXFormEqual(expected, observed)

    def test_xlsform_spec(self):
        self.compare_xform(file_name="xlsform_spec_test.xlsx")

    def test_flat_xlsform(self):
        self.compare_xform(file_name="flat_xlsform_test.xlsx")

    def test_widgets(self):
        self.compare_xform(file_name="widgets.xls")

    def test_pull_data(self):
        self.compare_xform(file_name="pull_data.xlsx")

    def test_search_and_select(self):
        self.compare_xform(file_name="search_and_select.xlsx")

    def test_default_survey_sheet(self):
        self.compare_xform(file_name="survey_no_name.xlsx", set_default_name=False)


class TestCalculateWithoutCalculation(TestCase):
    """
    Just checks that calculate field without calculation raises a PyXFormError.
    """

    def runTest(self):
        filename = "calculate_without_calculation.xls"
        path_to_excel_file = os.path.join(example_xls.PATH, filename)
        self.assertRaises(PyXFormError, xls2json.parse_file_to_json, path_to_excel_file)
