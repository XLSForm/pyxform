from django.test import TestCase, Client
from pyxform.builder import create_survey_element_from_dict, \
    create_survey_element_from_json
from pyxform.xls2json import SurveyReader, print_pyobj_to_json
from pyxform import Survey, InputQuestion
import os

class DumpAndLoadTests(TestCase):

    def setUp(self):
        self.excel_files = [
            "gps.xls",
            "include.xls",
            "specify_other.xls",
            "group.xls",
            "loop.xls",
            "text_and_integer.xls",
            "include_json.xls",
            "simple_loop.xls",
            "yes_or_no_question.xls",
            ]
        self.surveys = {}
        for filename in self.excel_files:
            path = "pyxform/tests/%s" % filename
            excel_reader = SurveyReader(path)
            d = excel_reader.to_dict()
            self.surveys[filename] = create_survey_element_from_dict(d)
    
    def test_load_from_dump(self):
        for filename, survey in self.surveys.items():
            survey.json_dump()
            path = survey.get_name() + ".json"
            survey_from_dump = create_survey_element_from_json(path)
            self.assertEqual(survey.to_dict(), survey_from_dump.to_dict())

    def tearDown(self):
        for filename, survey in self.surveys.items():
            path = survey.get_name() + ".json"
            os.remove(path)
