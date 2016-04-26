from unittest import TestCase
from pyxform.builder import create_survey_from_path
import utils


class TutorialTests(TestCase):

    def test_create_from_path(self):
        path = utils.path_to_text_fixture("tutorial.xls")
        survey = create_survey_from_path(path)
        #print survey.to_xml()
