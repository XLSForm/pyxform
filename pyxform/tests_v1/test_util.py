from unittest import TestCase
from pyxform.utils import expression_is_repeated, expression_is_complex
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class RelevanceTest(PyxformTestCase):
    def test_relevance_checker_works_repeat_relevancies(self):
        """expression_is_repeated correctly flags repeated relevancies"""
        hashes = {}
        response = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11",
            hashes,
            6,
        )
        self.assertEqual("", response)

        response = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11",
            hashes,
            10,
        )
        self.assertEqual(
            "[row : 10] Duplicate expression detected. In future, it is best to store repeated logic in calculate and referring to that calculate.",
            response,
        )

        response = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11",
            hashes,
            39,
        )
        self.assertEqual(
            "[row : 39] Duplicate expression detected. In future, it is best to store repeated logic in calculate and referring to that calculate.",
            response,
        )

    def test_relevance_checker_works_complex_relevancies(self):
        """expression_is_repeated correctly flags repeated relevancies"""
        response = expression_is_complex(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 ",
            7,
        )
        self.assertEqual(
            "[row : 7] Possible complex or long logical expression detected,  This may cause stack overflows during form submission.",
            response,
        )

        response = expression_is_complex(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 ",
            5,
        )
        self.assertEqual("", response)

    def test_generates_warning_for_repeated_relevance_logic(self):
        """
        Checks that warnings are generated and appended correctly, when
        parsing an xml
        """
        md = """
            | survey |                 |                  |                     |                      |
            |        | type            | name             | label               | relevant             |
            |        | select_one      | likes-pizza      | Do you like Pizza?  |                      |
            |        | select_multiple | favorite-topping | favourite topppings | ${likes-pizza}='yes' |
            |        | text            | favorite-shop    | favourite Shop      | ${likes-pizza}='yes' |
        """
        warnings = []
        self.md_to_pyxform_survey(md_raw=md, kwargs={"warnings": warnings})
        expected_warning_message = "[row : 4] Duplicate expression detected. In future, it is best to store repeated logic in calculate and referring to that calculate."

        self.assertIn(expected_warning_message, warnings)

    def test_generates_warning_for_complex_relevance_logic(self):
        """
        Checks that a warning was generated for complex relevance expressions
        when parsing xls
        """
        md = """
                   | survey |            |               |                      |           |
                   |        | type       | name          | label                | relevant  |
                   |        | select_one | B1_1StoveType | past stove           |           |
                   |        | select_one | B1_2StoveType | present stove        |           |
                   |        | select_one | B1_3StoveType | future stove         |           |
                   |        | select_one | B1_4StoveType | possible future stove|           |
                   |        | select_one | stove_prize   | your prize           | ${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 " | 
               """
        warnings = []
        self.md_to_pyxform_survey(md_raw=md, kwargs={"warnings": warnings})
        expected_warning_message = "[row : 6] Possible complex or long logical expression detected,  This may cause stack overflows during form submission."

        self.assertIn(expected_warning_message, warnings)
