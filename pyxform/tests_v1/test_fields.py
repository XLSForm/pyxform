# -*- coding: utf-8 -*-
"""
Test duplicate survey question field name.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


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
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | b        | option b |
            |         | list            | b        | option c |
            | settings |                |          |          |
            |          | id_string      | allow_choice_duplicates   |
            |          | Duplicates     | Yes                       |
            """

        expected = """
    <select1 ref="/pyxform_autotestname/S1">
      <label>s1</label>
      <item>
        <label>option a</label>
        <value>a</value>
      </item>
      <item>
        <label>option b</label>
        <value>b</value>
      </item>
      <item>
        <label>option c</label>
        <value>b</value>
      </item>
    </select1>
"""
        self.assertPyxformXform(md=md, xml__contains=[expected])

    def test_choice_list_without_duplicates_is_successful(self):
        md = """
            | survey  |                 |          |       |
            |         | type            | name     | label |
            |         | select_one list | S1       | s1    |
            | choices |                 |          |       |
            |         | list name       | name     | label  |
            |         | list            | option a | a      |
            |         | list            | option b | b      |
            | settings |                |          |        |
            |          | id_string    | allow_choice_duplicates   |
            |          | Duplicates   | Yes                       |
            """

        expected = """
    <select1 ref="/pyxform_autotestname/S1">
      <label>s1</label>
      <item>
        <label>a</label>
        <value>option a</value>
      </item>
      <item>
        <label>b</label>
        <value>option b</value>
      </item>
    </select1>
"""
        self.assertPyxformXform(md=md, xml__contains=[expected])

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
