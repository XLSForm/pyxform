# -*- coding: utf-8 -*-
"""
Test handling setvalue of 'when' column in forms
"""

from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class WhenSetvalueTests(PyxformTestCase):
    """
    Handling 'when' column setvalue(s) tests
    """

    def test_handling_when_column_no_label_and_no_hint(self):
        md = """
        | survey |          |      |             |             |      |
        |        | type     | name | label       | calculation | when |
        |        | text     | a    | Enter text  |             |      |
        |        | dateTime | b    |             | now()       | ${a} |
        """

        self.assertPyxformXform(
            md=md,
            name="when-column",
            id_string="id",
            model__contains=["<a/>", "<b/>",],
            xml__contains=[
                '<bind nodeset="/when-column/b" type="dateTime"/>',
                '<input ref="/when-column/a">',
                '<setvalue event="xforms-value-changed" ref=" /when-column/b " value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/when-column/b" type="dateTime" calculate="now()"/>'
                '<input ref="/when-column/b">',
            ],
        )

    def test_handling_when_column_with_label_and_hint(self):
        md = """
        | survey |          |      |                    |             |      |
        |        | type     | name | label              | calculation | when |
        |        | text     | a    | Enter text         |             |      |
        |        | dateTime | c    | Date of diagnostic | now()       | ${a} |
        """

        self.assertPyxformXform(
            md=md,
            name="when-column",
            id_string="id",
            model__contains=["<a/>", "<c/>",],
            xml__contains=[
                '<bind nodeset="/when-column/c" type="dateTime"/>',
                '<input ref="/when-column/a">',
                '<input ref="/when-column/c">',
                '<setvalue event="xforms-value-changed" ref=" /when-column/c " value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/when-column/c" type="dateTime" calculate="now()"/>'
            ],
        )

    def test_handling_multiple_when_column(self):
        md = """
        | survey |          |      |            |             |      |        |
        |        | type     | name | label      | calculation | when | hint   |
        |        | text     | a    | Enter text |             |      |        |
        |        | integer  | b    |            | 1+1         | ${a} |        |
        |        | dateTime | c    |            | now()       | ${a} | A hint |
        """

        self.assertPyxformXform(
            md=md,
            name="when-column",
            id_string="id",
            model__contains=["<a/>", "<b/>", "<c/>",],
            xml__contains=[
                '<bind nodeset="/when-column/b" type="int"/>',
                '<bind nodeset="/when-column/c" type="dateTime"/>',
                '<input ref="/when-column/a">',
                '<input ref="/when-column/c">',
                '<setvalue event="xforms-value-changed" ref=" /when-column/b " value="1+1"/>',
                '<setvalue event="xforms-value-changed" ref=" /when-column/c " value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/when-column/b" type="int" calculate="1+1"/>',
                '<bind nodeset="/when-column/c" type="dateTime" calculate="now()"/>',
            ],
        )

    def test_handling_when_column_with_no_calculation(self):
        md = """
        | survey |          |      |                    |             |      |
        |        | type     | name | label              | calculation | when |
        |        | text     | a    | Enter text         |             |      |
        |        | dateTime | d    | Date of something  |             | ${a} |
        """

        self.assertPyxformXform(
            md=md,
            name="when-column",
            id_string="id",
            model__contains=["<a/>", "<d/>",],
            xml__contains=[
                '<bind nodeset="/when-column/d" type="dateTime"/>',
                '<input ref="/when-column/a">',
                '<input ref="/when-column/d">',
                '<setvalue event="xforms-value-changed" ref=" /when-column/d " value=""/>',
            ],
            xml__excludes=[
                '<bind nodeset="/when-column/d" type="dateTime" calculate=""/>'
            ],
        )

    def test_handling_when_column_with_no_calculation_no_label_no_hint(self):
        md = """
        | survey |          |      |            |             |      |
        |        | type     | name | label      | calculation | when |
        |        | text     | a    | Enter text |             |      |
        |        | decimal  | e    |            |             | ${a} |
        """

        self.assertPyxformXform(
            md=md,
            name="when-column",
            id_string="id",
            model__contains=["<a/>", "<e/>",],
            xml__contains=[
                '<bind nodeset="/when-column/e" type="decimal"/>',
                '<input ref="/when-column/a">',
                '<setvalue event="xforms-value-changed" ref=" /when-column/e " value=""/>',
            ],
            xml__excludes=[
                '<bind nodeset="/when-column/e" type="decimal" calculate=""/>',
                '<input ref="/when-column/e">',
            ],
        )

    def test_handling_when_column_in_group(self):
        md = """
        | survey |             |      |                    |             |      |
        |        | type        | name | label              | calculation | when |
        |        | text        | a    | Enter text         |             |      |
        |        | begin_group | grp  |                    |             | ${a} |
        |        | dateTime    | c    | Date of diagnostic | now()       | ${a} |
        |        | end_group   |      |                    |             |      |
        """

        self.assertPyxformXform(
            md=md,
            name="when-column",
            id_string="id",
            model__contains=["<a/>", "<grp>", "<c/>",],
            xml__contains=[
                '<bind nodeset="/when-column/grp/c" type="dateTime"/>',
                '<input ref="/when-column/a">',
                '<group ref="/when-column/grp">',
                '<input ref="/when-column/grp/c">',
                '<setvalue event="xforms-value-changed" ref=" /when-column/grp/c " value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/when-column/c" type="dateTime" calculate="now()"/>',
            ],
        )
