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
