"""
Some tests for the new (v0.9) spec is properly implemented.
"""
import os
from unittest import TestCase

import pyxform
from pyxform.errors import PyXFormError
from pyxform.utils import has_external_choices
from pyxform.validators.odk_validate import ODKValidateError, check_xform
from pyxform.xls2json import SurveyReader, parse_file_to_workbook_dict
from pyxform.xls2json_backends import xlsx_to_dict

from tests import bug_example_xls, example_xls, test_expected_output, test_output
from tests.xform_test_case.base import XFormTestCase


class GroupNames(TestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "group_name_test.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(test_output.PATH, root_filename + ".xml")
        # Do the conversion:
        warnings = []
        with self.assertRaises(PyXFormError):
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file, default_name="group_name_test", warnings=warnings
            )
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(output_path, warnings=warnings)


class NotClosedGroup(TestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "not_closed_group_test.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(test_output.PATH, root_filename + ".xml")
        # Do the conversion:
        warnings = []
        with self.assertRaises(PyXFormError):
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file,
                default_name="not_closed_group_test",
                warnings=warnings,
            )
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(output_path, warnings=warnings)


class DuplicateColumns(TestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "duplicate_columns.xlsx"
        path_to_excel_file = os.path.join(example_xls.PATH, filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(test_output.PATH, root_filename + ".xml")
        # Do the conversion:
        warnings = []
        with self.assertRaises(PyXFormError):
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file, default_name="duplicate_columns", warnings=warnings
            )
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(output_path, warnings=warnings)


class RepeatDateTest(XFormTestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "repeat_date_test.xls"
        self.get_file_path(filename)
        expected_output_path = os.path.join(
            test_expected_output.PATH, self.root_filename + ".xml"
        )

        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            self.path_to_excel_file, default_name="repeat_date_test", warnings=warnings
        )
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(self.output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with open(expected_output_path, encoding="utf-8") as expected, open(
            self.output_path, encoding="utf-8"
        ) as observed:
            self.assertXFormEqual(expected.read(), observed.read())


class XmlEscaping(XFormTestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "xml_escaping.xls"
        self.get_file_path(filename)
        expected_output_path = os.path.join(
            test_expected_output.PATH, self.root_filename + ".xml"
        )

        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            self.path_to_excel_file, default_name="xml_escaping", warnings=warnings
        )
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(self.output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with open(expected_output_path, encoding="utf-8") as expected, open(
            self.output_path, encoding="utf-8"
        ) as observed:
            self.assertXFormEqual(expected.read(), observed.read())


class DefaultTimeTest(XFormTestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "default_time_demo.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(test_output.PATH, root_filename + ".xml")
        expected_output_path = os.path.join(
            test_expected_output.PATH, root_filename + ".xml"
        )
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, default_name="default_time_demo", warnings=warnings
        )
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with open(expected_output_path, encoding="utf-8") as expected, open(
            output_path, encoding="utf-8"
        ) as observed:
            self.assertXFormEqual(expected.read(), observed.read())


class ValidateWrapper(TestCase):
    maxDiff = None

    @staticmethod
    def test_conversion(self):
        filename = "ODKValidateWarnings.xlsx"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(test_output.PATH, root_filename + ".xml")
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, default_name="ODKValidateWarnings", warnings=warnings
        )
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)


class EmptyStringOnRelevantColumnTest(TestCase):
    def test_conversion(self):
        filename = "ict_survey_fails.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        workbook_dict = pyxform.xls2json.parse_file_to_workbook_dict(path_to_excel_file)
        with self.assertRaises(KeyError):
            # bind:relevant should not be part of workbook_dict
            workbook_dict["survey"][0]["bind: relevant"].strip()


class BadChoicesSheetHeaders(TestCase):
    def test_conversion(self):
        filename = "spaces_in_choices_header.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        warnings = []
        pyxform.xls2json.parse_file_to_json(
            path_to_excel_file,
            default_name="spaces_in_choices_header",
            warnings=warnings,
        )
        # The "column with no header" warning is probably not reachable since XLS/X
        # pre-processing ignores any columns without a header.
        observed = [w for w in warnings if "Headers cannot include spaces" in w]
        self.assertEqual(1, len(observed), warnings)

    def test_values_with_spaces_are_cleaned(self):
        """
        Test that values with leading and trailing whitespaces are processed.

        This test checks that the submission_url provided is cleaned
        of leading and trailing whitespaces.
        """
        filename = "spaces_in_choices_header.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        survey_reader = SurveyReader(
            path_to_excel_file, default_name="spaces_in_choices_header"
        )
        result = survey_reader.to_json_dict()

        self.assertEqual(
            result["submission_url"], "https://odk.ona.io/random_person/submission"
        )


class TestChoiceNameAsType(TestCase):
    def test_choice_name_as_type(self):
        filename = "choice_name_as_type.xls"
        path_to_excel_file = os.path.join(example_xls.PATH, filename)
        xls_reader = SurveyReader(path_to_excel_file, default_name="choice_name_as_type")
        survey_dict = xls_reader.to_json_dict()
        self.assertTrue(has_external_choices(survey_dict))


class TestBlankSecondRow(TestCase):
    def test_blank_second_row(self):
        filename = "blank_second_row.xls"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        xls_reader = SurveyReader(path_to_excel_file, default_name="blank_second_row")
        survey_dict = xls_reader.to_json_dict()
        self.assertTrue(len(survey_dict) > 0)


class TestXLDateAmbigous(TestCase):
    """Test non standard sheet with exception is processed successfully."""

    def test_xl_date_ambigous(self):
        """Test non standard sheet with exception is processed successfully."""
        filename = "xl_date_ambiguous.xlsx"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        xls_reader = SurveyReader(path_to_excel_file, default_name="xl_date_ambiguous")
        survey_dict = xls_reader.to_json_dict()
        self.assertTrue(len(survey_dict) > 0)


class TestXLDateAmbigousNoException(TestCase):
    """Test date values that exceed the workbook datemode value.
    (This would cause an exception with xlrd, but openpyxl handles it)."""

    def test_xl_date_ambigous_no_exception(self):
        """Test standard sheet is processed successfully."""
        filename = "xl_date_ambiguous_v1.xlsx"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        survey_dict = xlsx_to_dict(path_to_excel_file)
        self.assertEqual(survey_dict["survey"][4]["default"], "1900-01-01 00:00:00")


class TestSpreadSheetFilesWithMacrosAreAllowed(TestCase):
    """Test that spreadsheets with .xlsm extension are allowed"""

    def test_xlsm_files_are_allowed(self):
        filename = "excel_with_macros.xlsm"
        path_to_excel_file = os.path.join(bug_example_xls.PATH, filename)
        result = parse_file_to_workbook_dict(path_to_excel_file)
        self.assertIsInstance(result, dict)


class TestBadCalculation(TestCase):
    """Bad calculation should not kill the application"""

    def test_bad_calculate_javarosa_error(self):
        filename = "bad_calc.xml"
        test_xml = os.path.join(test_output.PATH, filename)
        self.assertRaises(ODKValidateError, check_xform, test_xml)
