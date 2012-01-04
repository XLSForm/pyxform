# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.

from unittest import TestCase
import pyxform
import utils
import os, sys
from pyxform.xls2json import SurveyReader

path_to_excel_file = "/home/user/python-dev/xlsform/pyxform/tests/example_xls/xlsform_spec_test.xls"

class basic_test(TestCase):
    def runTest(self):
#        x = SurveyReader(utils.path_to_text_fixture("unknown_question_type.xls"))
#        print x.to_json_dict()
        survey = pyxform.create_survey_from_path(path_to_excel_file)
        directory, filename = os.path.split(path_to_excel_file)
        path_to_xform = os.path.join(directory, survey.id_string + ".xml")
        survey.print_xform_to_file(path_to_xform)
        pass
    