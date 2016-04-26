"""
Some tests for the new (v0.9) spec is properly implemented.  
"""
import unittest2 as unittest
import codecs
import os
import sys
#Hack to make sure that pyxform is on the python import path
parentdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,parentdir)
import pyxform

DIR = os.path.dirname(__file__)

class main_test(unittest.TestCase):
    
    maxDiff = None
    
    def runTest(self):
        filename = "or_other.xlsx"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        #Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".xml")
        expected_output_path = os.path.join(DIR, "test_expected_output", root_filename + ".xml")
        #Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(path_to_excel_file, warnings=warnings)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(output_path, warnings=warnings)
        #print warnings
        #Compare with the expected output:
        with codecs.open(expected_output_path, 'rb', encoding="utf-8") as expected_file:
            with codecs.open(output_path, 'rb', encoding="utf-8") as actual_file:
                self.assertMultiLineEqual(expected_file.read(), actual_file.read())

if __name__ == '__main__':
    unittest.main()
