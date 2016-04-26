"""
Some tests for the new (v0.9) spec is properly implemented.
"""
import unittest2 as unittest
import codecs
import os
import sys

# Hack to make sure that pyxform is on the python import path
parentdir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parentdir)
import pyxform
from pyxform.utils import has_external_choices
from pyxform.xls2json import SurveyReader

DIR = os.path.dirname(__file__)


class group_names(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "group_name_test.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        with self.assertRaises(Exception):
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file, warnings=warnings)
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(output_path, warnings=warnings)


class duplicate_columns(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "duplicate_columns.xlsx"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        with self.assertRaises(Exception):
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file, warnings=warnings)
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(output_path, warnings=warnings)


class repeat_date_test(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "repeat_date_test.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        expected_output_path = os.path.join(
            DIR, "test_expected_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with codecs.open(
                expected_output_path, 'rb', encoding="utf-8") as expected_file:
            with codecs.open(
                    output_path, 'rb', encoding="utf-8") as actual_file:
                self.assertMultiLineEqual(
                    expected_file.read(), actual_file.read())


class xml_escaping(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "xml_escaping.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        expected_output_path = os.path.join(
            DIR, "test_expected_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with codecs.open(
                expected_output_path, 'rb', encoding="utf-8") as expected_file:
            with codecs.open(
                    output_path, 'rb', encoding="utf-8") as actual_file:
                self.assertMultiLineEqual(
                    expected_file.read(), actual_file.read())


class DefaultTimeTest(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "default_time_demo.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        expected_output_path = os.path.join(
            DIR, "test_expected_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with codecs.open(
                expected_output_path, 'rb', encoding="utf-8") as expected_file:
            with codecs.open(
                    output_path, 'rb', encoding="utf-8") as actual_file:
                self.assertMultiLineEqual(
                    expected_file.read(), actual_file.read())


class cascade_old_format(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "cascades_old.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)


class validate_wrapper(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "ODKValidateWarnings.xlsx"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)


class cascade_old_format_index_error(unittest.TestCase):

    maxDiff = None

    def runTest(self):
        filename = "cascades_old_with_no_cascade_sheet.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        # Do the conversion:
        warnings = []
        with self.assertRaises(pyxform.errors.PyXFormError):
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file, warnings=warnings)
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(output_path, warnings=warnings)


class EmptyStringOnRelevantColumnTest(unittest.TestCase):

    def runTest(self):
        filename = "ict_survey_fails.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        workbook_dict = pyxform.xls2json.parse_file_to_workbook_dict(
            path_to_excel_file)
        with self.assertRaises(KeyError):
            # bind:relevant should not be part of workbook_dict
            workbook_dict['survey'][0][u'bind: relevant'].strip()


class MissingOrBadlyNamedChoicesTest(unittest.TestCase):

    def runTest(self):
        filename = "badly_named_choices_sheet.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        workbook_dict = pyxform.xls2json.parse_file_to_workbook_dict(
            path_to_excel_file)
        with self.assertRaises(pyxform.errors.PyXFormError):
            pyxform.xls2json.workbook_to_json(workbook_dict)


class BadChoicesSheetHeaders(unittest.TestCase):

    def runTest(self):
        filename = "spaces_in_choices_header.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        warnings = []
        pyxform.xls2json.parse_file_to_json(path_to_excel_file,
                                            warnings=warnings)
        self.assertEquals(len(warnings), 2,
                          "Found " + str(len(warnings)) + " warnings")


class MissingHeaderColumnsTest(unittest.TestCase):
    def test_choices_headers_missing(self):
        filename = "no_header_on_choices_sheet.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        workbook_dict = pyxform.xls2json.parse_file_to_workbook_dict(
            path_to_excel_file)
        with self.assertRaises(pyxform.errors.PyXFormError):
            pyxform.xls2json.workbook_to_json(workbook_dict)

    def test_survey_headers_missing(self):
        filename = "no_header_on_survey_sheet.xls"
        path_to_excel_file = os.path.join(DIR, "bug_example_xls", filename)
        workbook_dict = pyxform.xls2json.parse_file_to_workbook_dict(
            path_to_excel_file)
        with self.assertRaises(pyxform.errors.PyXFormError):
            pyxform.xls2json.workbook_to_json(workbook_dict)


class TestChoiceNameAsType(unittest.TestCase):
    def test_choice_name_as_type(self):
        filename = "choice_name_as_type.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        xls_reader = SurveyReader(path_to_excel_file)
        survey_dict = xls_reader.to_json_dict()
        self.assertTrue(has_external_choices(survey_dict))


if __name__ == '__main__':
    unittest.main()
