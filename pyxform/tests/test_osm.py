from unittest import TestCase
from pyxform.builder import create_survey_from_path
from pyxform.builder import create_survey_element_from_json
import utils
import os
import codecs


class OSMTests(TestCase):

    maxDiff = None

    def test_create_from_path(self):
        path = utils.path_to_text_fixture("osm.xlsx")
        survey = create_survey_from_path(path)
        path = os.path.join(
            os.path.dirname(__file__), 'test_expected_output', 'osm.xml')

        with codecs.open(path, encoding='utf-8') as f:
            expected_xml = f.read()
            self.assertMultiLineEqual(survey.to_xml(), expected_xml)

            survey = create_survey_element_from_json(survey.to_json())
            self.assertMultiLineEqual(survey.to_xml(), expected_xml)
