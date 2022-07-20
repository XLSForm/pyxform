# -*- coding: utf-8 -*-
"""
Test duplicate survey question field name.
"""
from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


class FieldsTests(PyxformTestCase):
    """
    Test XLSForm Fields
    """

    def test_duplicate_fields(self):
        """
        Ensure that duplicate field names are not allowed
        """
        self.assertPyxformXform(
            name="duplicatefields",
            md="""
            | Survey |         |         |               |
            |        | Type    | Name    | Label         |
            |        | integer | age     | the age       |
            |        | integer | age     | the age       |
            """,
            errored=True,
            error__contains=["There are more than one survey elements named 'age'"],
        )

    def test_duplicate_fields_diff_cases(self):
        """
        Ensure that duplicate field names with different cases are not allowed
        """
        self.assertPyxformXform(
            name="duplicatefieldsdiffcases",
            md="""
            | Survey |         |         |               |
            |        | Type    | Name    | Label         |
            |        | integer | age     | the age       |
            |        | integer | Age     | the age       |
            """,
            errored=True,
            error__contains=["There are more than one survey elements named 'age'"],
        )

    def test_duplicate_choices_without_setting(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | b        | option b |
            |         | list            | b        | option c |
            """,
            errored=True,
            error__contains=[
                "The name column for the 'list' choice list contains these duplicates: 'b'"
            ],  # noqa
        )

    def test_multiple_duplicate_choices_without_setting(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | a        | option b |
            |         | list            | b        | option c |
            |         | list            | b        | option d |
            """,
            errored=True,
            error__contains=[
                "The name column for the 'list' choice list contains these duplicates: 'a', 'b'"
            ],  # noqa
        )

    def test_duplicate_choices_with_setting_not_set_to_yes(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | b        | option b |
            |         | list            | b        | option c |
            | settings |                |          |          |
            |          | id_string    | allow_choice_duplicates   |
            |          | Duplicates   | Bob                       |
            """,
            errored=True,
            error__contains=[
                "The name column for the 'list' choice list contains these duplicates: 'b'"
            ],  # noqa
        )

    def test_duplicate_choices_with_allow_choice_duplicates_setting(self):
        md = """
            | survey  |                 |      |       |
            |         | type            | name | label |
            |         | select_one list | S1   | s1    |
            | choices |                 |      |       |
            |         | list name       | name | label |
            |         | list            | a    | A     |
            |         | list            | b    | B     |
            |         | list            | b    | C     |
            | settings |                |                         |
            |          | id_string      | allow_choice_duplicates |
            |          | Duplicates     | Yes                     |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_instance_choices_label(
                    "list", (("a", "A"), ("b", "B"), ("b", "C"))
                ),
                xpq.body_select1_itemset("S1"),
            ],
        )

    def test_choice_list_without_duplicates_is_successful(self):
        md = """
            | survey  |                 |      |       |
            |         | type            | name | label |
            |         | select_one list | S1   | s1    |
            | choices |                 |      |       |
            |         | list name       | name | label |
            |         | list            | a    | A     |
            |         | list            | b    | B     |
            | settings |              |                         |
            |          | id_string    | allow_choice_duplicates |
            |          | Duplicates   | Yes                     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_instance_choices_label("list", (("a", "A"), ("b", "B"))),
                xpq.body_select1_itemset("S1"),
            ],
        )

    def test_duplicate_form_name_in_section_name(self):
        """
        Ensure that the section name cannot be the same as form name
        """
        self.assertPyxformXform(
            name="foo",
            md="""
            | Survey   |             |         |               |
            |          | Type        | Name    | Label         |
            |          | begin group | foo     | A group       |
            |          | text        | a       | Enter text    |
            |          | end group   |         |               |
            """,
            errored=True,
            error__contains=['The name "foo" is the same as the form name'],
        )

    def test_field_name_may_match_form_name(self):
        """
        Unlike section names, it's okay for a field name to match the form
        name, which becomes the XML root node name
        """
        self.assertPyxformXform(
            name="activity",
            md="""
            | survey  |             |          |                   |
            |         | type        | name     | label             |
            |         | date        | date     | Observation date  |
            |         | text        | activity | Describe activity |
            """,
            errored=False,
        )
