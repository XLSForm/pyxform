# -*- coding: utf-8 -*-
"""
BindConversionsTest - test bind conversions.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class BindConversionsTest(PyxformTestCase):
    """
    BindConversionsTest - test bind conversions
    """

    def test_bind_readonly_conversion(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |      |       |          |
            |        | type  | name | label | readonly |
            |        | text  | text | text  | yes      |
            """,
            xml__contains=['<bind nodeset="/data/text" readonly="true()"'],
        )

    def test_bind_required_conversion(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |      |       |          |
            |        | type  | name | label | required |
            |        | text  | text | text  | FALSE    |
            """,
            xml__contains=['<bind nodeset="/data/text" required="false()"'],
        )

    def test_bind_required_message_with_reference(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |      |       |            |                    |
            |        | type  | name | label | required   | required_message |
            |        | int   | foo  | foo   |            |                    |
            |        | text  | text | text  | true()     | required, ${foo}   |
            """,
            xml__contains=[
                '<bind nodeset="/data/text" required="true()" type="string" jr:requiredMsg="jr:itext(\'/data/text:jr:requiredMsg\')"',
                '<value> required, <output value=" /data/foo "/> </value>',
            ],
        )

    def test_bind_constraint_conversion(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |      |       |                    |
            |        | type  | name | label | constraint_message |
            |        | text  | text | text  | yes                |
            """,
            xml__contains=[
                '<bind nodeset="/data/text" type="string" jr:constraintMsg="yes"'
            ],
        )

    def test_bind_constraint_message_with_reference(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |      |       |                      |                    |
            |        | type  | name | label | constraint           | constraint_message |
            |        | int   | foo  | foo   |                      |                    |
            |        | text  | text | text  | string-length(.) > 1 | too short ${foo}   |
            """,
            xml__contains=[
                '<bind constraint="string-length(.) &gt; 1" nodeset="/data/text" type="string" jr:constraintMsg="jr:itext(\'/data/text:jr:constraintMsg\')"',
                '<value> too short <output value=" /data/foo "/> </value>',
            ],
        )

    def test_bind_custom_conversion(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |      |       |           |
            |        | type  | name | label | bind::foo |
            |        | text  | text | text  | bar       |
            """,
            xml__contains=['<bind foo="bar" nodeset="/data/text" type="string"'],
        )
