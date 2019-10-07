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
        |        | text    | first_name | First name | first-name${idea} |
        |        | text    | last_name  | Last name  | not-func$         |
        |        | integer | age        | Your age   | some-rando-func() |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=[
                "<first_name/>",
                "<last_name>not-func$</last_name>",
                "<age/>",
                '<setvalue event="odk-instance-first-load" ref="/dynamic/first_name" value="first-name${idea}"/>',
                '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some-rando-func()"/>',
            ],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_pretty_xml()

        self.assertContains(survey_xml, "<first_name/>", 1)
        self.assertContains(survey_xml, "<last_name>not-func$</last_name>", 1)
        self.assertContains(survey_xml, "<age/>", 1)
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some-rando-func()"/>',
            1,
        )
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/first_name" value="first-name${idea}"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/age" value="some-rando-func()"/>',
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/first_name" value="first-name${idea}"/>',
        )

    def test_handling_dynamic_default_in_repeat(self):
        """
        Should use set-value for dynamic default form inside repeat
        """
        md = """
        | survey |              |            |              |                   |
        |        | type         | name       | label        | default           |
        |        | begin repeat | household  | Households   |                   |
        |        | integer      | age        | Your age     | some-rando-func() |
        |        | text         | feeling    | Your feeling | not-func$         |
        |        | end repeat   | household  |              |                   |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=["<age/>", "<feeling>not-func$</feeling>"],
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="some-rando-func()"/>'
            ],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_pretty_xml()

        self.assertContains(survey_xml, "<feeling>not-func$</feeling>", 1)
        self.assertContains(survey_xml, "<age/>", 1)
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="some-rando-func()"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some-rando-func()"/>',
        )
