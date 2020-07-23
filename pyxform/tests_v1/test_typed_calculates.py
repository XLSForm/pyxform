# -*- coding: utf-8 -*-
"""
Test that any row with a calculation becomes a calculate of the row's type or of type string if the type is "calculate". A hint or label
error should only be thrown for a row without a calculation.
"""

from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TypedCalculatesTest(PyxformTestCase):
    def test_xls_type_calculate_has_type_string(self):
        self.assertPyxformXform(
            name="calculate-type",
            md="""
            | survey |          |      |             |             |
            |        | type     | name | label       | calculation |
            |        | calculate| a    |             | 2 * 2       |
            """,
            xml__contains=[
                '<bind calculate="2 * 2" nodeset="/calculate-type/a" type="string"/>',
            ],
        )

    def test_xls_type_calculate_with_label_has_no_body(self):
        self.assertPyxformXform(
            name="calculate-type",
            md="""
                | survey |          |      |             |             |
                |        | type     | name | label       | calculation |
                |        | calculate| a    | A           | 2 * 2       |
                """,
            xml__contains=[
                '<bind calculate="2 * 2" nodeset="/calculate-type/a" type="string"/>',
                "<h:body/>",
            ],
        )

    def test_non_calculate_type_with_calculation_is_bind_type(self):
        self.assertPyxformXform(
            name="non-calculate-type",
            md="""
            | survey |          |      |             |             |
            |        | type     | name | label       | calculation |
            |        | integer  | a    |             | 2 * 2       |
            """,
            xml__contains=[
                '<bind calculate="2 * 2" nodeset="/non-calculate-type/a" type="int"/>'
            ],
        )

    def test_non_calculate_type_with_calculation_and_no_label_has_no_control(self):
        self.assertPyxformXform(
            name="no-label",
            md="""
                | survey |          |      |             |             |
                |        | type     | name | label       | calculation |
                |        | integer  | a    |             | 2 * 2       |
                """,
            instance__contains=["<a/>"],
            xml__excludes=["input"],
        )

    def test_non_calculate_type_with_calculation_no_warns(self):
        warnings = []

        self.md_to_pyxform_survey(
            """
            | survey |           |      |             |      |             |
            |        | type      | name | label       | hint | calculation |
            |        | dateTime  | a    |             |      | now()       |
            |        | integer   | b    |             |      | 1 div 1     |
            |        | note      | note | Hello World |      |             |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 0)

    def test_non_calculate_type_with_hint_and_no_calculation_warns(self):
        warnings = []

        self.md_to_pyxform_survey(
            """
            | survey |           |      |             |           |             |
            |        | type      | name | label       | hint      | calculation |
            |        | dateTime  | a    |             |           | now()       |
            |        | integer   | b    |             | Some hint |             |
            |        | note      | note | Hello World |           |             |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue("Question has no label" in warnings[0])

    def test_non_calculate_type_with_calculation_and_dynamic_default_warns(self):
        warnings = []

        self.md_to_pyxform_survey(
            """
            | survey |           |      |             |      |             |         |
            |        | type      | name | label       | hint | calculation | default |
            |        | dateTime  | a    |             |      | now()       |         |
            |        | integer   | b    |             |      | 1 div 1     | $(a)    |
            |        | note      | note | Hello World |      |             |         |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue("This form definition contains dynamic defaults" in warnings[0])

    def test_non_calculate_type_with_calculation_and_default_no_warns(self):
        warnings = []

        self.md_to_pyxform_survey(
            """
            | survey |           |      |             |      |             |         |
            |        | type      | name | label       | hint | calculation | default |
            |        | dateTime  | a    |             |      | now()       |         |
            |        | integer   | b    |             |      | 1 div 1     | 1       |
            |        | note      | note | Hello World |      |             |         |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 0)

    def test_select_type_with_calculation_and_no_label_has_no_control(self):
        self.assertPyxformXform(
            name="calculate-select",
            md="""
                | survey  |                   |      |       |                  |
                |         | type              | name | label | calculation      |
                |         | select_one yes_no | a    |       | concat('a', 'b') |
                | choices |                   |      |       |                  |
                |         | list_name         | name | label |                  |
                |         | yes_no            | yes  | Yes   |                  |
                |         | yes_no            | no   | No    |                  |
                """,
            xml__contains=[
                '<bind calculate="concat(\'a\', \'b\')" nodeset="/calculate-select/a" type="string"/>'
            ],
            instance__contains=["<a/>"],
            xml__excludes=["<select1>"],
        )

    def test_row_without_label_or_calculation_throws_error(self):
        self.assertPyxformXform(
            name="no-label",
            md="""
        | survey |          |      |             |
        |        | type     | name | label       |
        |        | integer  | a    |             |
        """,
            errored=True,
            error__contains="The survey element named 'a' has no label or hint.",
        )

    def test_calculate_without_calculation_without_default(self):
        self.assertPyxformXform(
            name="calculate-without-calculation-without-default",
            md="""
        | survey |            |      |             |             |         |
        |        | type       | name | label       | calculation | default |
        |        | calculate  | a    |             |             |         |
        """,
            errored=True,
            error__contains="Missing calculation",
        )

    def test_calculate_without_calculation_with_default_without_dynamic_default(self):
        self.assertPyxformXform(
            name="calculate-without-calculation-with-default-without-dynamic-default",
            md="""
        | survey |            |      |             |             |         |
        |        | type       | name | label       | calculation | default |
        |        | calculate  | a    |             |             | foo     |
        """,
            errored=True,
            error__contains="Missing calculation",
        )

    def test_calculate_without_calculation_with_dynamic_default(self):
        self.assertPyxformXform(
            name="calculate-without-calculation-with-dynamic-default",
            md="""
        | survey |            |      |             |             |          |
        |        | type       | name | label       | calculation | default  |
        |        | calculate  | a    |             |             | random() |
        """,
            errored=False,
            instance__contains=["<a/>"],
        )
