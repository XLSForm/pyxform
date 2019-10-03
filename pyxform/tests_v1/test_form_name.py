# -*- coding: utf-8 -*-
"""
Test setting form name to data.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
from pyxform.utils import unicode


class FormNameTest(PyxformTestCase):
    def test_default_to_data_when_no_name(self):
        """
        Test no form_name will default to survey name to 'data'.
        """
        survey = self.md_to_pyxform_survey(
            """
            | survey   |           |      |           |
            |          | type      | name | label     |
            |          | text      | city | City Name |
            | settings |           |      |           |
            |          | id_string | name |
            |          | some-id   | data |
            """,
            kwargs={},
            autoname=False,
        )

        # We're passing autoname false when creating the survey object.
        self.assertEqual(survey.id_string, None)
        self.assertEqual(survey.name, unicode("data"))
        self.assertEqual(survey.title, None)

        # Set required fields because we need them if we want to do xml comparison.
        survey.id_string = "some-id"
        survey.title = "data"

        self.assertPyxformXform(
            survey=survey,
            instance__contains=['<data id="some-id">'],
            model__contains=['<bind nodeset="/data/city" type="string"/>'],
            xml__contains=[
                '<input ref="/data/city">',
                "<label>City Name</label>",
                "</input>",
            ],
        )

    def test_default_to_data(self):
        """
        Test using data as the name of the form which will generate <data />.
        """
        self.assertPyxformXform(
            md="""
               | survey |      |      |           |
               |        | type | name | label     |
               |        | text | city | City Name |
               """,
            name="data",
            id_string="some-id",
            instance__contains=['<data id="some-id">'],
            model__contains=['<bind nodeset="/data/city" type="string"/>'],
            xml__contains=[
                '<input ref="/data/city">',
                "<label>City Name</label>",
                "</input>",
            ],
        )

    def test_default_form_name_to_superclass_definition(self):
        """
        Test no form_name and setting name field, should use name field.
        """

        self.assertPyxformXform(
            md="""
               | survey |      |      |           |
               |        | type | name | label     |
               |        | text | city | City Name |
               """,
            name="some-name",
            id_string="some-id",
            instance__contains=['<some-name id="some-id">'],
            model__contains=['<bind nodeset="/some-name/city" type="string"/>'],
            xml__contains=[
                '<input ref="/some-name/city">',
                "<label>City Name</label>",
                "</input>",
            ],
        )
