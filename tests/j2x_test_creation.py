"""
Testing creation of Surveys using verbose methods
"""
from unittest import TestCase

from pyxform import MultipleChoiceQuestion, Survey, create_survey_from_xls

from tests import utils


class Json2XformVerboseSurveyCreationTests(TestCase):
    def test_survey_can_be_created_in_a_verbose_manner(self):
        s = Survey()
        s.name = "simple_survey"

        q = MultipleChoiceQuestion()
        q.name = "cow_color"
        q.type = "select one"

        q.add_choice(label="Green", name="green")
        s.add_child(q)

        expected_dict = {
            "name": "simple_survey",
            "children": [
                {
                    "name": "cow_color",
                    "type": "select one",
                    "children": [{"label": "Green", "name": "green"}],
                }
            ],
        }
        self.maxDiff = None
        self.assertEqual(s.to_json_dict(), expected_dict)

    def test_survey_can_be_created_in_a_slightly_less_verbose_manner(self):
        option_dict_array = [
            {"name": "red", "label": "Red"},
            {"name": "blue", "label": "Blue"},
        ]

        q = MultipleChoiceQuestion(name="Favorite_Color", choices=option_dict_array)
        q.type = "select one"
        s = Survey(name="Roses_are_Red", children=[q])

        expected_dict = {
            "name": "Roses_are_Red",
            "children": [
                {
                    "name": "Favorite_Color",
                    "type": "select one",
                    "children": [
                        {"label": "Red", "name": "red"},
                        {"label": "Blue", "name": "blue"},
                    ],
                }
            ],
        }

        self.assertEqual(s.to_json_dict(), expected_dict)

    def allow_surveys_with_comment_rows(self):
        """assume that a survey with rows that don't have name, type, or label
        headings raise warning only"""
        path = utils.path_to_text_fixture("allow_comment_rows_test.xls")
        survey = create_survey_from_xls(path)
        expected_dict = {
            "default_language": "default",
            "id_string": "allow_comment_rows_test",
            "children": [
                {
                    "name": "farmer_name",
                    "label": {"English": "First and last name of farmer"},
                    "type": "text",
                }
            ],
            "name": "allow_comment_rows_test",
            "_translations": {
                "English": {
                    "/allow_comment_rows_test/farmer_name:label": {
                        "long": "First and last name of farmer"
                    }
                }
            },
            "title": "allow_comment_rows_test",
            "_xpath": {
                "allow_comment_rows_test": "/allow_comment_rows_test",
                "farmer_name": "/allow_comment_rows_test/farmer_name",
            },
            "type": "survey",
        }
        self.assertEquals(survey.to_json_dict(), expected_dict)
