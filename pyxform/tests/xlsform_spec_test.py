"""
Some tests for the new (v0.9) spec is properly implemented.  
"""
from unittest2 import TestCase
import pyxform
from pyxform import xls2json
import os, codecs

DIR = os.path.dirname(__file__)

class main_test(TestCase):
    
    maxDiff = None
    
    def runTest(self):
        filename = "xlsform_spec_test.xlsx"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        #Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        expected_output_path = os.path.join(DIR, "test_expected_output", root_filename + ".xml")
        #Do the conversion:
        warnings = []
        json_survey = xls2json.parse_file_to_json(path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)
        #print warnings
        #Compare with the expected output:
        with codecs.open(expected_output_path, 'rb', encoding="utf-8") as expected_file:
            with codecs.open(output_path, 'rb', encoding="utf-8") as actual_file:
                self.assertMultiLineEqual(expected_file.read(), actual_file.read())

class warnings_test(TestCase):
    """
    Just checks that the number of warnings thrown when reading warnings.xls doesn't change.
    """
    def runTest(self):
        filename = "warnings.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        warnings = []
        xls2json.parse_file_to_json(path_to_excel_file, warnings=warnings)
        #print '\n'.join(warnings)
        self.assertEquals(len(warnings), 21, "Found " + str(len(warnings)) + " warnings")
