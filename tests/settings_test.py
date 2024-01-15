# -*- coding: utf-8 -*-
"""
Test settings sheet syntax.
"""

from unittest import TestCase

from pyxform.builder import create_survey_from_path
from pyxform.xls2json import SurveyReader

from tests import utils


class SettingsTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.path = utils.path_to_text_fixture("settings.xls")

    def test_survey_reader(self):
        survey_reader = SurveyReader(self.path, default_name="settings")
        expected_dict = {
            "id_string": "new_id",
            "sms_keyword": "new_id",
            "default_language": "default",
            "name": "settings",
            "title": "My Survey",
            "type": "survey",
            "attribute": {
                "my_number": "1234567890",
                "my_string": "lor\xe9m ipsum",
            },
            "children": [
                {
                    "name": "your_name",
                    "label": {"english": "What is your name?"},
                    "type": "text",
                },
                {
                    "name": "your_age",
                    "label": {"english": "How many years old are you?"},
                    "type": "integer",
                },
                {
                    "children": [
                        {
                            "bind": {"jr:preload": "uid", "readonly": "true()"},
                            "name": "instanceID",
                            "type": "calculate",
                        }
                    ],
                    "control": {"bodyless": True},
                    "name": "meta",
                    "type": "group",
                },
            ],
        }
        self.assertEqual(survey_reader.to_json_dict(), expected_dict)

    def test_settings(self):
        survey = create_survey_from_path(self.path)
        self.assertEqual(survey.id_string, "new_id")
        self.assertEqual(survey.title, "My Survey")
