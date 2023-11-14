# -*- coding: utf-8 -*-
"""
Test text rows parameter.
"""
from tests.pyxform_test_case import PyxformTestCase


class TestRows(PyxformTestCase):
    def test_adding_rows_to_the_body_if_set_in_its_own_column(
        self,
    ):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | body::rows     |
            |        | text   | name     | Name  | 7              |
            """,
            xml__xpath_match=["/h:html/h:body/x:input[@ref='/data/name' and @rows='7']"],
        )

    def test_adding_rows_to_the_body_if_set_in_parameters(
        self,
    ):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | text   | name     | Name  | rows=7         |
            """,
            xml__xpath_match=["/h:html/h:body/x:input[@ref='/data/name' and @rows='7']"],
        )

    def test_throwing_error_if_rows_set_in_parameters_but_the_value_is_not_an_integer(
        self,
    ):
        parameters = ("rows=", "rows=foo", "rows=7.5")
        md = """
        | survey |        |          |       |                 |
        |        | type   | name     | label | parameters      |
        |        | text   | name     | Name  | {case}          |
        """
        for case in parameters:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    name="data",
                    md=md.format(case=case),
                    errored=True,
                    error__contains=["Parameter rows must have an integer value."],
                )
