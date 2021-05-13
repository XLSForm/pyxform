# -*- coding: utf-8 -*-
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
from pyxform.utils import unicode


class ChoicesSheetTest(PyxformTestCase):
    def test_numeric_choice_names__for_static_selects__allowed(self):
        """
        Test numeric choice names for static selects.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |
            |          | type               | name | label |
            |          | select_one choices | a    | A     |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    | One   |
            |          | choices            | 2    | Two   |
            """,
            xml__contains=["<value>1</value>"],
        )

    def test_numeric_choice_names__for_dynamic_selects__allowed(self):
        """
        Test numeric choice names for dynamic selects.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |               |
            |          | type               | name | label | choice_filter |
            |          | select_one choices | a    | A     | true()        |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    | One   |
            |          | choices            | 2    | Two   |
            """,
            xml__contains=['<instance id="choices">', "<item>", "<name>1</name>"],
        )

    def test_choices_without_labels__for_static_selects__allowed(self):
        """
        Test choices without labels for static selects. Validate will NOT fail.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |
            |          | type               | name | label |
            |          | select_one choices | a    | A     |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    |       |
            |          | choices            | 2    |       |
            """,
            xml__contains=["<value>1</value>"],
        )

    def test_choices_without_labels__for_dynamic_selects__allowed_by_pyxform(self):
        """
        Test choices without labels for dynamic selects. Validate will fail.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |               |
            |          | type               | name | label | choice_filter |
            |          | select_one choices | a    | A     | true()        |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    |       |
            |          | choices            | 2    |       |
            """,
            run_odk_validate=False,
            xml__contains=['<instance id="choices">', "<item>", "<name>1</name>"],
        )
