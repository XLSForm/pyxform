from unittest import TestCase
from pyxform.builder import create_survey_from_path
import utils


class SettingsTests(TestCase):

    def test_settings(self):
        path = utils.path_to_text_fixture("settings.xls")
        survey = create_survey_from_path(path)
        self.assertEqual(survey.id_string, "new_id")
        self.assertEqual(survey.title, "My Survey")
