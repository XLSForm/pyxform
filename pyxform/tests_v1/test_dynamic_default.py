# -*- coding: utf-8 -*-
"""
Test handling dynamic default in forms
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class DynamicDefaultTests(PyxformTestCase):
    """
    Handling dynamic defaults
    """

    def test_handling_dynamic_default(self):
        """
        Should use set-value for dynamic default form
        """
        md = """
        | survey |         |            |            |                   |
        |        | type    | name       | label      | default           |
        |        | text    | first_name | First name | first_name${idea} |
        |        | text    | last_name  | Last name  | not_func$         |
        |        | integer | age        | Your age   | some_rando_func() |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=[
                "<first_name/>",
                "<last_name>not_func$</last_name>",
                "<age/>",
                '<setvalue event="odk-instance-first-load" ref="/dynamic/first_name" value="first_name${idea}"/>',
                '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some_rando_func()"/>',
            ],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_testable_xml()

        self.assertContains(survey_xml, "<first_name/>", 1)
        self.assertContains(survey_xml, "<last_name>not_func$</last_name>", 1)
        self.assertContains(survey_xml, "<age/>", 1)
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some_rando_func()"/>',
            1,
        )
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/first_name" value="first_name${idea}"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/age" value="some_rando_func()"/>',
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/first_name" value="first_name${idea}"/>',
        )

    def test_handling_dynamic_default_in_repeat(self):
        """
        Should use set-value for dynamic default form inside repeat
        """
        md = """
        | survey |              |            |              |                   |
        |        | type         | name       | label        | default           |
        |        | begin repeat | household  | Households   |                   |
        |        | integer      | age        | Your age     | some_rando_func() |
        |        | text         | feeling    | Your feeling | not_func$         |
        |        | end repeat   | household  |              |                   |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=["<age/>", "<feeling>not_func$</feeling>"],
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="some_rando_func()"/>'
            ],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_testable_xml()

        self.assertContains(survey_xml, "<feeling>not_func$</feeling>", 2)
        self.assertContains(survey_xml, "<age/>", 2)
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="some_rando_func()"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some_rando_func()"/>',
        )

    def test_handling_arithmetic_expression(self):
        """
        Should use set-value for dynamic default form
        """
        md = """
        | survey |         |            |             |                   |
        |        | type    | name       | label       | default           |
        |        | text    | expr_1     | First expr  | 2 + 3 * 4         |
        |        | text    | expr_2     | Second expr | 5 div 5 - 5       |
        |        | integer | expr_3     | Third expr  | expr() + 2 * 5    |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=[
                "<expr_1/>",
                "<expr_2/>",
                "<expr_3/>",
                '<setvalue event="odk-instance-first-load" ref="/dynamic/expr_1" value="2 + 3 * 4"/>',
                '<setvalue event="odk-instance-first-load" ref="/dynamic/expr_2" value="5 div 5 - 5"/>',
                '<setvalue event="odk-instance-first-load" ref="/dynamic/expr_3" value="expr() + 2 * 5"/>',
            ],
        )

    def test_handling_arithmetic_text(self):
        """
        Should use set-value for dynamic default form with arithmetic text
        """
        md = """
        | survey |         |            |             |         |
        |        | type    | name       | label       | default |
        |        | text    | expr_1     | First expr  | 3 mod 3 |
        |        | text    | expr_2     | Second expr | 5 div 5 |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=[
                "<expr_1/>",
                "<expr_2/>",
                '<setvalue event="odk-instance-first-load" ref="/dynamic/expr_1" value="3 mod 3"/>',
                '<setvalue event="odk-instance-first-load" ref="/dynamic/expr_2" value="5 div 5"/>',
            ],
        )
