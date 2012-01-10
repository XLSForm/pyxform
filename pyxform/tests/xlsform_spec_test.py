# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.

from unittest import TestCase
import pyxform
import utils
import os, sys
import pyxform.xls2json as x2j

#path_to_excel_file = "/home/user/Desktop/full_instrument_117_english_only.xls"
#path_to_excel_file = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/xlsform_spec_test.xls"
path_to_excel_file = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/MgSO4.xls"
#path_to_excel_file = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/simple_loop.xls"

class basic_test(TestCase):
    def runTest(self):
#        x = SurveyReader(utils.path_to_text_fixture("unknown_question_type.xls"))
#        print x.to_json_dict()
        survey = pyxform.create_survey_from_path(path_to_excel_file)
        directory, filename = os.path.split(path_to_excel_file)
        root_filename, ext = os.path.splitext(filename)
        path_to_xform = os.path.join(directory, root_filename + ".xml")
        survey.print_xform_to_file(path_to_xform)
        pass
    
    
#class test_variable_name_reader(TestCase):
#    def runTest(self):
#        vnr = x2j.VariableNameReader(path_to_excel_file)
#        x2j.print_pyobj_to_json(vnr.to_json_dict())
#        pass

