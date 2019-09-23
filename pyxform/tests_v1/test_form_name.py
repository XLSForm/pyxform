# -*- coding: utf-8 -*-
"""
Test setting form name to data.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase

class FormNameTest(PyxformTestCase):

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
            name='data',
            id_string='some-id',
            instance__contains=['<data id="some-id">'],
            model__contains=['<bind nodeset="/data/city" type="string"/>'],
            xml__contains=[
                '<input ref="/data/city">',
                '<label>City Name</label>',
                '</input>',
            ],
        )

    def test_default_to_data_when_no_name(self):
        """
        Test no form_name and skipping name field, default to 'data'.
        """

        self.assertPyxformXform(
            md="""
               | survey |      |      |           |
               |        | type | name | label     |
               |        | text | city | City Name |
               """,
            skip_name=True,
            id_string='some-id',
            instance__contains=['<data id="some-id">'],
            model__contains=['<bind nodeset="/data/city" type="string"/>'],
            xml__contains=[
                '<input ref="/data/city">',
                '<label>City Name</label>',
                '</input>',
            ],
        )

    def test_default_form_name_to_superclass_definition(self):
        """
        Test no form_name and not skipping name field, default to super class definition.
        """

        self.assertPyxformXform(
            md="""
               | survey |      |      |           |
               |        | type | name | label     |
               |        | text | city | City Name |
               """,
            id_string='some-id',
            instance__contains=['<pyxform_autotestname id="some-id">'],
            model__contains=['<bind nodeset="/pyxform_autotestname/city" type="string"/>'],
            xml__contains=[
                '<input ref="/pyxform_autotestname/city">',
                '<label>City Name</label>',
                '</input>',
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
            name='some-name',
            id_string='some-id',
            instance__contains=['<some-name id="some-id">'],
            model__contains=['<bind nodeset="/some-name/city" type="string"/>'],
            xml__contains=[
                '<input ref="/some-name/city">',
                '<label>City Name</label>',
                '</input>',
            ],
        )
