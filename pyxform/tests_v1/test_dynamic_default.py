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
        |        | text    | last_name  | Last name  | not_func$         |
        |        | integer | age        | Your age   | some_rando_func() |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=[
                "<last_name>not_func$</last_name>",
                "<age/>",
                '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some_rando_func()"/>',
            ],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_pretty_xml()

        self.assertContains(survey_xml, "<last_name>not_func$</last_name>", 1)
        self.assertContains(survey_xml, "<age/>", 1)
        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="some_rando_func()"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/age" value="some_rando_func()"/>',
        )

    def test_static_defaults(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |              |          |       |                   |
            |        | type         | name     | label | default           |
            |        | integer      | foo      | Foo   | foo               |
            |        | begin repeat | repeat   |       |                   |
            |        | integer      | bar      | Bar   | 12                |
            |        | end repeat   | repeat   |       |                   |
            """,
            model__contains=["<foo>foo</foo>", "<bar>12</bar>"],
            model__excludes=["setvalue"],
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
            model__excludes=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="some_rando_func()"/>'
            ],
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="some_rando_func()"/>'
            ],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_pretty_xml()

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

    def test_dynamic_default_in_group(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |            |          |       |                   |
            |        | type       | name     | label | default           |
            |        | integer    | foo      | Foo   |                   |
            |        | begin group| group    |       |                   |
            |        | integer    | bar      | Bar   | ${foo}            |
            |        | end group  | group    |       |                   |
            """,
            model__contains=[
                '<setvalue event="odk-instance-first-load" ref="/dynamic/group/bar" value=" /dynamic/foo "/>'
            ],
        )

    def test_sibling_dynamic_default_in_group(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |              |          |       |                   |
            |        | type         | name     | label | default           |
            |        | begin group  | group    |       |                   |
            |        | integer      | foo      | Foo   |                   |
            |        | integer      | bar      | Bar   | ${foo}            |
            |        | end group    | group    |       |                   |
            """,
            model__contains=[
                '<setvalue event="odk-instance-first-load" ref="/dynamic/group/bar" value=" /dynamic/group/foo "/>'
            ],
        )

    def test_sibling_dynamic_default_in_repeat(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |              |          |       |                   |
            |        | type         | name     | label | default           |
            |        | begin repeat | repeat   |       |                   |
            |        | integer      | foo      | Foo   |                   |
            |        | integer      | bar      | Bar   | ${foo}            |
            |        | end repeat   | repeat   |       |                   |
            """,
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/repeat/bar" value=" ../foo "/>'
            ],
            model__excludes=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/repeat/bar" value=" ../foo "/>'
            ],
        )

    def test_dynamic_default_in_group_nested_in_repeat(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |              |          |       |                   |
            |        | type         | name     | label | default           |
            |        | begin repeat | repeat   |       |                   |
            |        | begin group  | group    |       |                   |
            |        | integer      | foo      | Foo   |                   |
            |        | integer      | bar      | Bar   | ${foo}            |
            |        | end group    | group    |       |                   |
            |        | end repeat   | repeat   |       |                   |
            """,
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/repeat/group/bar" value=" ../foo "/>'
            ],
            model__excludes=['<setvalue event="odk-instance-first-load'],
        )

    def test_dynamic_defaults_in_nested_repeat(self):
        md = """
            | survey |              |          |       |                   |
            |        | type         | name     | label | default           |
            |        | begin repeat | outer    |       |                   |
            |        | date         | date     | Date  | now()             |
            |        | integer      | foo      | Foo   |                   |
            |        | begin repeat | inner    |       |                   |
            |        | integer      | bar      | Bar   | ${foo}            |
            |        | end repeat   | inner    |       |                   |
            |        | end repeat   | outer    |       |                   |
            """

        self.assertPyxformXform(
            name="dynamic",
            md=md,
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/outer/inner/bar" value=" ../../foo "/>',
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/outer/date" value="now()"/>',
            ],
            model__excludes=['<setvalue event="odk-instance-first-load'],
        )

        survey = self.md_to_pyxform_survey(
            md_raw=md,
            kwargs={"id_string": "id", "name": "dynamic", "title": "some-title"},
            autoname=False,
        )
        survey_xml = survey._to_pretty_xml()

        self.assertContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/outer/inner/bar" value=" ../../foo "/>',
            1,
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

    def test_dynamic_default_with_nested_expression(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |         |               |               |                   |
            |        | type    | name          | label         | default           |
            |        | integer | patient_count | Patient count | if(${last-saved#patient_count} = '', 0, ${last-saved#patient_count} + 1) |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                '<setvalue event="odk-instance-first-load" ref="/dynamic/patient_count" '
                "value=\"if( instance('__last-saved')/dynamic/patient_count  = '', 0,  "
                "instance('__last-saved')/dynamic/patient_count  + 1)\"/>",
            ],
        )

    def test_dynamic_default_with_reference(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |            |          |       |                   |
            |        | type       | name     | label | default           |
            |        | integer    | foo      | Foo   |                   |
            |        | integer    | bar      | Bar   | ${foo}            |
            """,
            xml__contains=[
                '<setvalue event="odk-instance-first-load" ref="/dynamic/bar" value=" /dynamic/foo "/>'
            ],
        )

    def test_dynamic_default_warns(self):
        warnings = []

        self.md_to_pyxform_survey(
            """
            | survey |      |         |       |         |
            |        | type | name    | label | default |
            |        | text | foo     | Foo   |         |
            |        | text | bar     | Bar   | ${foo}  |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue(
            "Not all form filling software and versions support dynamic defaults"
            in warnings[0]
        )

    def test_default_date_not_considered_dynamic(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |            |          |       |                   |
            |        | type       | name     | label | default           |
            |        | date       | foo      | Foo   | 2020-01-01        |
            """,
            xml__contains=["<foo>2020-01-01</foo>"],
        )

    def test_dynamic_default_on_calculate(self):
        self.assertPyxformXform(
            name="dynamic",
            md="""
            | survey |            |          |       |             |                      |
            |        | type       | name     | label | calculation | default              |
            |        | calculate  | r        |       |             | random() + 0.5       |
            |        | calculate  | one      |       |             | if(${r} < 1,'A','B') |
            """,
            xml__contains=[
                """<setvalue event="odk-instance-first-load" ref="/dynamic/r" value="random() + 0.5"/>""",
                """<setvalue event="odk-instance-first-load" ref="/dynamic/one" value="if( /dynamic/r  &lt; 1,'A','B')"/>""",
            ],
        )
