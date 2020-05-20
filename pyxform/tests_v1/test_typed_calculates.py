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
                '<bind calculate="2 * 2" nodeset="/calculate-type/a" type="string"/>'
            ],
        )

    def test_other_xls_type_with_calculation_is_passed_through(self):
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

    def test_other_xls_type_with_calculation_and_no_label_has_no_control(self):
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
