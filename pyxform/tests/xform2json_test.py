from pyxform.builder import create_survey_from_path
from pyxform.xform2json import create_survey_element_from_xml
import os
import utils


class DumpAndLoadXForm2JsonTests(utils.XFormTestCase):

    maxDiff = None

    def setUp(self):
        self.excel_files = [
            "gps.xls",
            #"include.xls",
            "specify_other.xls",
            "loop.xls",
            "text_and_integer.xls",
            # todo: this is looking for json that is created (and
            # deleted) by another test, is should just add that json
            # to the directory.
            # "include_json.xls",
            "simple_loop.xls",
            "yes_or_no_question.xls",
            "xlsform_spec_test.xlsx",
            "group.xls",
        ]
        self.surveys = {}
        self.this_directory = os.path.dirname(__file__)
        for filename in self.excel_files:
            path = utils.path_to_text_fixture(filename)
            try:
                self.surveys[filename] = create_survey_from_path(path)
            except Exception as e:
                print("Error on : " + filename)
                raise e

    def test_load_from_dump(self):
        for filename, survey in self.surveys.items():
            survey.json_dump()
            survey_from_dump = create_survey_element_from_xml(survey.to_xml())
            self.assertXFormEqual(
                survey.to_xml(), survey_from_dump.to_xml())

    def tearDown(self):
        for filename, survey in self.surveys.items():
            path = survey.name + ".json"
            if os.path.exists(path):
                os.remove(path)
