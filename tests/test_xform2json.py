# -*- coding: utf-8 -*-
"""
Test XForm2JSON functionality
"""
import json

from pyxform.builder import create_survey_element_from_dict
from tests.pyxform_test_case import PyxformTestCase


class TestXForm2JSON(PyxformTestCase):
    """
    Test xform2json module
    """

    def test_convert_toJSON_multi_language(self):
        """
        Test that it's possible to convert XLSForms with multiple languages
        to JSON and back into XML without losing any of the required information
        """
        md = """
        | survey  |
        |         | type                   | name  | label:Eng  | label:Fr |
        |         | text                   | name  | Name       | Prénom   |
        |         | select_multiple fruits | fruit | Fruit      | Fruit    |
        |         |                        |       |            |          |
        | choices | list name              | name  | label:Eng  | label:Fr |
        |         | fruits                 | 1     | Mango      | Mangue   |
        |         | fruits                 | 2     | Orange     | Orange   |
        |         | fruits                 | 3     | Apple      | Pomme    |
        """

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "multi-language", "title": "some-title"},
            autoname=False,
        )
        expected = survey.to_xml()
        generated_json = survey.to_json()

        survey_from_builder = create_survey_element_from_dict(json.loads(generated_json))
        observed = survey_from_builder.to_xml()

        self.assertEqual(expected, observed)
