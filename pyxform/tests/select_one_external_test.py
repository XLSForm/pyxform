import unittest2 as unittest
import codecs
import os
import pyxform
from pyxform.utils import sheet_to_csv
from pyxform.tests.utils import XFormTestCase

DIR = os.path.dirname(__file__)


class MainTest(XFormTestCase):
    
    maxDiff = None
    
    def runTest(self):
        for filename in ["select_one_external.xlsx"]:
            path_to_excel_file = os.path.join(DIR, "example_xls", filename)
            # Get the xform output path:
            root_filename, ext = os.path.splitext(filename)
            output_path = os.path.join(
                DIR, "test_output", root_filename + ".xml")
            expected_output_path = os.path.join(
                DIR, "test_expected_output", root_filename + ".xml")
            output_csv = os.path.join(
                DIR, "test_output", root_filename + ".csv")
            # Do the conversion:
            json_survey = pyxform.xls2json.parse_file_to_json(
                path_to_excel_file)

            self.assertTrue(sheet_to_csv(
                path_to_excel_file, output_csv, "external_choices"))
            self.assertFalse(sheet_to_csv(
                path_to_excel_file, output_csv, "non-existant sheet"))

            survey = pyxform.create_survey_element_from_dict(json_survey)

            survey.print_xform_to_file(output_path)

            # Compare with the expected output:
            with codecs.open(expected_output_path, 'rb', encoding="utf-8") as\
                    expected_file:
                with codecs.open(output_path, 'rb', encoding="utf-8") as \
                        actual_file:
                    self.assertXFormEqual(
                        expected_file.read(), actual_file.read())
                
if __name__ == '__main__':
    unittest.main()
