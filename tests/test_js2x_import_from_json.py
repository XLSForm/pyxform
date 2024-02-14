"""
Testing our ability to import from a JSON text file.
"""
from unittest import TestCase

from pyxform.builder import (
    create_survey_element_from_dict,
    create_survey_element_from_json,
)


class TestJson2XformJsonImport(TestCase):
    def test_simple_questions_can_be_imported_from_json(self):
        json_text = {
            "type": "survey",
            "name": "Exchange rate",
            "children": [
                {
                    "label": {"French": "Combien?", "English": "How many?"},
                    "type": "decimal",
                    "name": "exchange_rate",
                }
            ],
        }
        s = create_survey_element_from_dict(json_text)

        self.assertEqual(s.children[0].type, "decimal")

    def test_question_type_that_accepts_parameters__without_parameters__to_xml(self):
        """Should be able to round-trip survey using a un-parameterised question without error."""
        # Per https://github.com/XLSForm/pyxform/issues/605
        # Underlying issue was that the SurveyElement.FIELDS default for "parameters" was
        # a string, but in MultipleChoiceQuestion.build_xml a dict is assumed, because
        # xls2json.parse_parameters always returns a dict.
        js = """
        {
            "type": "survey",
            "name": "ExchangeRate",
            "children": [
                {
                    "itemset": "pain_locations.xml",
                    "label": "Location of worst pain this week.",
                    "name": "pweek",
                    "type": "select one"
                }
            ]
        }
        """
        create_survey_element_from_json(str_or_path=js).to_xml()
