"""
Some tests for the new (v0.9) spec is properly implemented.  
"""

from lxml import etree
from formencode.doctest_xml_compare import xml_compare
from unittest import TestCase
import pyxform
from pyxform import xls2json
import os, sys
import utils
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
        filename = "xlsform_spec_test.xlsx"
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
        expected_path = utils.path_to_text_fixture("spec_test_expected_output.xml")
        with codecs.open(expected_path, 'rb', encoding="utf-8") as expected_file:
            expected = etree.fromstring(expected_file.read())
            result = etree.fromstring(survey.to_xml())
            self.assertTrue(xml_compare(expected, result))


class warnings_test(unittest.TestCase):
    """
    Just checks that the number of warnings thrown when reading warnings.xls doesn't change.
    """
    def runTest(self):
        filename = "warnings.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        warnings = []
        pyxform.xls2json.parse_file_to_json(path_to_excel_file, warnings=warnings)
        #print '\n'.join(warnings)
        self.assertEquals(len(warnings), 17, "Found " + str(len(warnings)) + " warnings")
