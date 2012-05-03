"""
Some tests for the new (v0.9) spec is properly implemented.  
"""

from unittest2 import TestCase
import pyxform
from pyxform import xls2json
import os, sys
import utils
import codecs

class main_test(TestCase):
    
    maxDiff = None
    
    def runTest(self):
       
        path_to_excel_file = utils.path_to_text_fixture("xlsform_spec_test.xls")
        
        #Get the xform output path:
        directory, filename = os.path.split(path_to_excel_file)
        root_filename, ext = os.path.splitext(filename)
        path_to_xform = os.path.join(directory, root_filename + ".xml")

        #Do the conversion:
        json_survey = xls2json.parse_file_to_json(path_to_excel_file)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(path_to_xform)
        
        #Compare with the expected output:
        expected_path = utils.path_to_text_fixture("spec_test_expected_output.xml")
        with codecs.open(expected_path, 'rb', encoding="utf-8") as expected_file:
            self.assertMultiLineEqual(expected_file.read(), survey.to_xml())

class warnings_test(TestCase):
    """
    Just checks that the number of warnings thrown when reading warnings.xls doesn't change.
    """
    def runTest(self):
        
        path_to_excel_file = utils.path_to_text_fixture("warnings.xls")
        
        warnings = []
        xls2json.parse_file_to_json(path_to_excel_file, warnings=warnings)
        #print '\n'.join(warnings)
        self.assertEquals(len(warnings), 17, "Found " + str(len(warnings)) + " warnings")