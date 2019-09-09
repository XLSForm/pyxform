# -*- coding: utf-8 -*-
"""
Test Selects syntax.
"""

from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class SelectTest(PyxformTestCase):
    def test_select_one_no_spaces(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |         |       |
            |        | type               | name    | label |
            |        | select_one choices | select  | Select|
            | choices|                    |         |       |
            |        | list_name          | name    | label |
            |        | choices            | a       | a     |
            |        | choices            | b       | a     |

            """,
            xml__contains=[
                '<select1 ref="/data/select">',
                "<value>a</value>",
                "<value>b</value>",
                "</select1>",
            ],
        )

    def test_select_one_spaces(self):
        survey, warnings = self.md_to_pyxform_survey(
            """
            | survey |                    |         |       |
            |        | type               | name    | label |
            |        | select_one choices | select  | Select|
            | choices|                    |         |       |
            |        | list_name          | name    | label |
            |        | choices            | a a     | a a   |
            |        | choices            | b b     | b b   |
            """, return_warnings=True
        )

        # self.assertTrue(len(warnings) == 2)
        # self.assertTrue(
        #     "Choice names with spaces will soon be disallowed" in warnings[0]
        # )

    def test_select_multiple_no_spaces(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                         |         |       |
            |        | type                    | name    | label |
            |        | select_multiple choices | select  | Select|
            | choices|                         |         |       |
            |        | list_name               | name    | label |
            |        | choices                 | a       | a     |
            |        | choices                 | b       | a     |

            """,
            xml__contains=[
                '<select ref="/data/select">',
                "<value>a</value>",
                "<value>b</value>",
                "</select>",
            ],
        )

    def test_select_multiple_spaces(self):
        self.assertPyxformXform(
            name="data",
            errored="true",
            md="""
            | survey |                         |         |       |
            |        | type                    | name    | label |
            |        | select_multiple choices | select  | Select|
            | choices|                         |         |       |
            |        | list_name               | name    | label |
            |        | choices                 | a a     | a a   |
            |        | choices                 | b b     | b b   |

            """,
            error__contains=[
                "Choice names with spaces cannot be added to select multiples."
            ],
        )
