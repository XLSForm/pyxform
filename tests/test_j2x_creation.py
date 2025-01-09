"""
Testing creation of Surveys using verbose methods
"""

from unittest import TestCase

from pyxform import MultipleChoiceQuestion, Survey, create_survey_from_xls

from tests import utils


class Json2XformVerboseSurveyCreationTests(TestCase):
    def test_survey_can_be_created_in_a_slightly_less_verbose_manner(self):
        choices = {
            "test": [
                {"name": "red", "label": "Red"},
                {"name": "blue", "label": "Blue"},
            ]
        }
        s = Survey(name="Roses_are_Red", choices=choices)
        q = MultipleChoiceQuestion(
            name="Favorite_Color",
            type="select one",
            list_name="test",
        )
        s.add_child(q)

        expected_dict = {
            "name": "Roses_are_Red",
            "type": "survey",
            "children": [
                {"name": "Favorite_Color", "type": "select one", "list_name": "test"}
            ],
            "choices": choices,
        }

        self.assertEqual(expected_dict, s.to_json_dict())

    def test_allow_surveys_with_comment_rows(self):
        """assume that a survey with rows that don't have name, type, or label
        headings raise warning only"""
        path = utils.path_to_text_fixture("allow_comment_rows_test.xls")
        survey = create_survey_from_xls(path)
        expected_dict = {
            "children": [
                {
                    "label": {"English": "First and last name of farmer"},
                    "name": "farmer_name",
                    "type": "text",
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
            "default_language": "default",
            "id_string": "allow_comment_rows_test",
            "name": "data",
            "sms_keyword": "allow_comment_rows_test",
            "title": "allow_comment_rows_test",
            "type": "survey",
        }
        self.assertEqual(expected_dict, survey.to_json_dict())
