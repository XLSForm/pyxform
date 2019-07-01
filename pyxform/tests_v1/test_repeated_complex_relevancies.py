from unittest import TestCase
from pyxform.xls2json import expression_is_repeated, expression_is_complex


class RelevanceTest(TestCase):
    def test_relevance_checker_works_repeat_relevancies(self):
        """expression_is_repeated correctly flags repeated relevancies"""
        errors = []
        hashes = {}
        errors_list = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11",
            6,
            hashes,
        )
        errors.extend(errors_list)
        errors_list = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11",
            10,
            hashes,
        )
        errors.extend(errors_list)
        errors_list = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11",
            39,
            hashes,
        )
        errors.extend(errors_list)
        expected_error_message = """11, 40: Duplicate relevancies detected.
        In future, its best to store repeated logic in calculate 
        and referring to that calculate."""
        self.assertListEqual([expected_error_message], errors_list)

    def test_relevance_checker_works_complex_relevancies(self):
        """expression_is_repeated correctly flags repeated relevancies"""
        errors = []
        hashes = {}
        errors_list = expression_is_complex(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 ",
            6,
            hashes,
        )
        expected_error_message = """7: Possible complex or long logical expression detected .
        This mat cause stack overflows during form submission."""
        errors.extend(errors_list)
        self.assertListEqual([expected_error_message], errors)

    def test_relevance_checker_both_complex_and_repeated(self):
        """relevance-checker function correctly checks for both
        complex and repeated logical expressions"""
        errors = []
        hashes = {}
        errors_list = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 ",
            6,
            hashes,
        )
        errors.extend(errors_list)
        errors_list = expression_is_complex(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 ",
            6,
            hashes,
        )
        errors.extend(errors_list)
        errors_list = expression_is_repeated(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 ",
            10,
            hashes,
        )
        errors.extend(errors_list)
        errors_list = expression_is_complex(
            "${B1_1StoveType}=23 or ${B1_1StoveType}=9 or ${B1_1StoveType}=10 or ${B1_1StoveType}=11 or ${B1_1StoveType}=12 or ${B1_1StoveType}=13 or ${B1_1StoveType}=14 or ${B1_1StoveType}=15 or ${B1_1StoveType}=16 or ${B1_1StoveType}=17 or ${B1_1StoveType}=18 or ${B1_1StoveType}=19 or ${B1_1StoveType}=20 or ${B1_1StoveType}=21 or ${B1_1StoveType}=22 or ${B1_2StoveType}=23 or ${B1_2StoveType}=9 or ${B1_2StoveType}=10 or ${B1_2StoveType}=11 or ${B1_2StoveType}=12 or ${B1_2StoveType}=13 or ${B1_2StoveType}=14 or ${B1_2StoveType}=15 or ${B1_2StoveType}=16 or ${B1_2StoveType}=17 or ${B1_2StoveType}=18 or ${B1_2StoveType}=19 or ${B1_2StoveType}=20 or ${B1_2StoveType}=21 or ${B1_2StoveType}=22 or ${B1_3StoveType}=23 or ${B1_3StoveType}=9 or ${B1_3StoveType}=10 or ${B1_3StoveType}=11 or ${B1_3StoveType}=12 or ${B1_3StoveType}=13 or ${B1_3StoveType}=14 or ${B1_3StoveType}=15 or ${B1_3StoveType}=16 or ${B1_3StoveType}=17 or ${B1_3StoveType}=18 or ${B1_3StoveType}=19 or ${B1_3StoveType}=20 or ${B1_3StoveType}=21 or ${B1_3StoveType}=22 or ${B1_4StoveType}=23 or ${B1_4StoveType}=9 or ${B1_4StoveType}=10 or ${B1_4StoveType}=11 or ${B1_4StoveType}=12 or ${B1_4StoveType}=13 or ${B1_4StoveType}=14 or ${B1_4StoveType}=15 or ${B1_4StoveType}=16 or ${B1_4StoveType}=17 or ${B1_4StoveType}=18 or ${B1_4StoveType}=19 or ${B1_4StoveType}=20 or ${B1_4StoveType}=21 or ${B1_4StoveType}=22 ",
            39,
            hashes,
        )
        errors.extend(errors_list)
        expected_error_message1 = """11: Duplicate relevancies detected.
                In future, its best to store repeated logic in calculate 
                and referring to that calculate."""
        expected_error_message2 = """7, 40: Possible complex or long logical expression detected .
                This may cause stack overflows during form submission."""
        self.assertTrue(expected_error_message1 in errors)
        self.assertTrue(expected_error_message2 in errors)
