# -*- coding: utf-8 -*-
"""
Test handling setvalue of 'trigger' column in forms
"""

from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TriggerSetvalueTests(PyxformTestCase):
    def test_trigger_reference_to_nonexistent_node_gives_error(self):
        self.assertPyxformXform(
            name="trigger-missing-ref",
            md="""
            | survey |          |      |             |             |         |
            |        | type     | name | label       | calculation | trigger |
            |        | dateTime | b    |             | now()       | ${a}    |
            """,
            errored=True,
            error__contains=[
                "There has been a problem trying to replace ${a} with the XPath to the survey element named 'a'. There is no survey element with this name."
            ],
        )

    def test_trigger_with_something_other_than_node_ref_gives_error(self):
        self.assertPyxformXform(
            name="trigger-invalid-ref",
            md="""
            | survey |          |      |             |             |         |
            |        | type     | name | label       | calculation | trigger |
            |        | dateTime | b    |             | now()       | 6       |
            """,
            errored=True,
            error__contains=[
                "Only references to other fields are allowed in the 'trigger' column."
            ],
        )

    def test_handling_trigger_column_no_label_and_no_hint(self):
        md = """
        | survey |          |      |             |             |         |
        |        | type     | name | label       | calculation | trigger |
        |        | text     | a    | Enter text  |             |         |
        |        | dateTime | b    |             | now()       | ${a}    |
        """
        self.assertPyxformXform(
            md=md,
            name="trigger-column",
            id_string="id",
            model__contains=["<a/>", "<b/>",],
            xml__contains=[
                '<bind nodeset="/trigger-column/b" type="dateTime"/>',
                '<input ref="/trigger-column/a">',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/b" value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/trigger-column/b" type="dateTime" calculate="now()"/>'
                '<input ref="/trigger-column/b">',
            ],
        )

    def test_handling_trigger_column_with_label_and_hint(self):
        md = """
        | survey |          |      |                    |             |         |
        |        | type     | name | label              | calculation | trigger |
        |        | text     | a    | Enter text         |             |         |
        |        | dateTime | c    | Date of diagnostic | now()       | ${a}    |
        """

        self.assertPyxformXform(
            md=md,
            name="trigger-column",
            id_string="id",
            model__contains=["<a/>", "<c/>",],
            xml__contains=[
                '<bind nodeset="/trigger-column/c" type="dateTime"/>',
                '<input ref="/trigger-column/a">',
                '<input ref="/trigger-column/c">',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/c" value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/trigger-column/c" type="dateTime" calculate="now()"/>'
            ],
        )

    def test_handling_multiple_trigger_column(self):
        md = """
        | survey |          |      |            |             |         |        |
        |        | type     | name | label      | calculation | trigger | hint   |
        |        | text     | a    | Enter text |             |         |        |
        |        | integer  | b    |            | 1+1         | ${a}    |        |
        |        | dateTime | c    |            | now()       | ${a}    | A hint |
        """

        self.assertPyxformXform(
            md=md,
            name="trigger-column",
            id_string="id",
            model__contains=["<a/>", "<b/>", "<c/>",],
            xml__contains=[
                '<bind nodeset="/trigger-column/b" type="int"/>',
                '<bind nodeset="/trigger-column/c" type="dateTime"/>',
                '<input ref="/trigger-column/a">',
                '<input ref="/trigger-column/c">',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/b" value="1+1"/>',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/c" value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/trigger-column/b" type="int" calculate="1+1"/>',
                '<bind nodeset="/trigger-column/c" type="dateTime" calculate="now()"/>',
            ],
        )

    def test_handling_trigger_column_with_no_calculation(self):
        md = """
        | survey |          |      |                    |             |         |
        |        | type     | name | label              | calculation | trigger |
        |        | text     | a    | Enter text         |             |         |
        |        | dateTime | d    | Date of something  |             | ${a}    |
        """

        self.assertPyxformXform(
            md=md,
            name="trigger-column",
            id_string="id",
            model__contains=["<a/>", "<d/>",],
            xml__contains=[
                '<bind nodeset="/trigger-column/d" type="dateTime"/>',
                '<input ref="/trigger-column/a">',
                '<input ref="/trigger-column/d">',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/d"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/trigger-column/d" type="dateTime" calculate=""/>'
            ],
        )

    def test_handling_trigger_column_with_no_calculation_no_label_no_hint(self):
        md = """
        | survey |          |      |            |             |         |
        |        | type     | name | label      | calculation | trigger |
        |        | text     | a    | Enter text |             |         |
        |        | decimal  | e    |            |             | ${a}    |
        """

        self.assertPyxformXform(
            md=md,
            name="trigger-column",
            id_string="id",
            model__contains=["<a/>", "<e/>",],
            xml__contains=[
                '<bind nodeset="/trigger-column/e" type="decimal"/>',
                '<input ref="/trigger-column/a">',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/e"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/trigger-column/e" type="decimal" calculate=""/>',
                '<input ref="/trigger-column/e">',
            ],
        )

    def test_trigger_refer_to_hidden_node_ref_gives_error(self):
        self.assertPyxformXform(
            name="trigger-invalid-ref",
            md="""
            | survey |           |        |                      |         |             |
            |        | type      | name   | label                | trigger | calculation |
            |        | calculate | one    |                      |         | 5 + 4       |
            |        | calculate | one-ts |                      | ${one}  | now()       |
            |        | note      | note   | timestamp: ${one-ts} |         |             |
            """,
            errored=True,
            error__contains=[
                "The question ${one} is not user-visible so it can't be used as a calculation trigger for question ${one-ts}.",
            ],
        )

    def test_when_trigger_refers_to_calculate_with_label_error_is_shown(self):
        self.assertPyxformXform(
            name="trigger-invalid-ref",
            md="""
            | survey |           |        |                      |         |             |
            |        | type      | name   | label                | trigger | calculation |
            |        | calculate | one    | A label              |         | 5 + 4       |
            |        | calculate | one-ts |                      | ${one}  | now()       |
            """,
            errored=True,
            error__contains=[
                "The question ${one} is not user-visible so it can't be used as a calculation trigger for question ${one-ts}.",
            ],
        )

    def test_typed_calculate_cant_be_trigger(self):
        self.assertPyxformXform(
            name="trigger-invalid-ref",
            md="""
                | survey |           |        |         |             |
                |        | type      | name   | trigger | calculation |
                |        | integer   | two    |         | 1 + 1       |
                |        | integer   | two-ts | ${two}  | now()       | 
                """,
            errored=True,
            error__contains=[
                "The question ${two} is not user-visible so it can't be used as a calculation trigger for question ${two-ts}."
            ],
        )

    def test_handling_trigger_column_in_group(self):
        md = """
        | survey |             |      |                    |             |         |
        |        | type        | name | label              | calculation | trigger |
        |        | text        | a    | Enter text         |             |         |
        |        | begin_group | grp  |                    |             | ${a}    |
        |        | dateTime    | c    | Date of diagnostic | now()       | ${a}    |
        |        | end_group   |      |                    |             |         |
        """

        self.assertPyxformXform(
            md=md,
            name="trigger-column",
            id_string="id",
            model__contains=["<a/>", "<grp>", "<c/>",],
            xml__contains=[
                '<bind nodeset="/trigger-column/grp/c" type="dateTime"/>',
                '<input ref="/trigger-column/a">',
                '<group ref="/trigger-column/grp">',
                '<input ref="/trigger-column/grp/c">',
                '<setvalue event="xforms-value-changed" ref="/trigger-column/grp/c" value="now()"/>',
            ],
            xml__excludes=[
                '<bind nodeset="/trigger-column/c" type="dateTime" calculate="now()"/>',
            ],
        )

    def test_calculation_with_trigger_column_should_have_expanded_xpath(self):
        self.assertPyxformXform(
            name="trigger-column",
            md="""
            | survey |          |      |             |                         |         |
            |        | type     | name | label       | calculation             | trigger |
            |        | dateTime | a    | A date      |                         |         |
            |        | integer  | b    |             | decimal-date-time(${a}) | ${a}    |
            """,
            xml__contains=[
                '<setvalue event="xforms-value-changed" ref="/trigger-column/b" value="decimal-date-time( /trigger-column/a )"/>'
            ],
        )

    def test_trigger_with_trigger_of_type_select_nests_setvalue_in_select(self):
        self.assertPyxformXform(
            name="trigger-select_trigger",
            md="""
            | survey |                    |      |             |                    |         |
            |        | type               | name | label       | calculation        | trigger |
            |        | select_one choices | a    | Some choice |                    |         |
            |        | integer            | b    |             | string-length(${a})| ${a}    |
            | choices|                    |      |             |                    |         |
            |        | list_name          | name | label       |
            |        | choices            | a    | A           |
            |        | choices            | aa   | AA          |
            """,
            xml__contains=[
                '<setvalue event="xforms-value-changed" ref="/trigger-select_trigger/b" value="string-length( /trigger-select_trigger/a )"/>\n    </select1>'
            ],
        )

    def test_trigger_column_in_repeat_should_have_expanded_xpath(self):
        self.assertPyxformXform(
            name="trigger-column",
            md="""
            | survey |              |       |                        |              |         |
            |        | type         | name  | label                  | calculation  | trigger |
            |        | begin repeat | rep   |                        |              |         |
            |        | dateTime     | one   | Enter text             |              |         |
            |        | dateTime     | three | Enter text (triggered) | now()        | ${one}  |
            |        | end repeat   |       |                        |              |         |
            """,
            xml__contains=[
                '<setvalue event="xforms-value-changed" ref="/trigger-column/rep/three" value="now()"/>'
            ],
        )

    def test_trigger_column_in_repeat_should_have_expanded_xpath_in_value(self):
        self.assertPyxformXform(
            name="trigger-column",
            md="""
            | survey |              |       |                        |                        |         |
            |        | type         | name  | label                  | calculation            | trigger |
            |        | begin repeat | rep   |                        |                        |         |
            |        | dateTime     | one   | Enter text             |                        |         |
            |        | dateTime     | three | Enter text (triggered) | string-length(${one})  | ${one}  |
            |        | end repeat   |       |                        |                        |         |
            """,
            xml__contains=[
                '<setvalue event="xforms-value-changed" ref="/trigger-column/rep/three" value="string-length( ../one )"/>'
            ],
        )
