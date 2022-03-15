# -*- coding: utf-8 -*-
"""
Test handling dynamic default in forms
"""
from collections import namedtuple

from pyxform import utils
from tests.pyxform_test_case import PyxformTestCase


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
        |        | integer | age        | Your age   | random() |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=[
                "<last_name>not_func$</last_name>",
                "<age/>",
                '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="random()"/>',
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
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="random()"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/age" value="random()"/>',
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
        |        | integer      | age        | Your age     | random() |
        |        | text         | feeling    | Your feeling | not_func$         |
        |        | end repeat   | household  |              |                   |
        """

        self.assertPyxformXform(
            md=md,
            name="dynamic",
            id_string="id",
            model__contains=["<age/>", "<feeling>not_func$</feeling>"],
            model__excludes=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="random()"/>'
            ],
            xml__contains=[
                '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="random()"/>'
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
            '<setvalue event="odk-instance-first-load odk-new-repeat" ref="/dynamic/household/age" value="random()"/>',
            1,
        )
        self.assertNotContains(
            survey_xml,
            '<setvalue event="odk-instance-first-load" ref="/dynamic/age" value="random()"/>',
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
        |        | integer | expr_3     | Third expr  | random() + 2 * 5    |
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
                '<setvalue event="odk-instance-first-load" ref="/dynamic/expr_3" value="random() + 2 * 5"/>',
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

        self.assertTrue(len(warnings) == 0)

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

    def test_dynamic_default_select_choice_name_with_hyphen(self):
        # Repro for https://github.com/XLSForm/pyxform/issues/495
        md = """
        | survey  |               |      |         |         |
        |         | type          | name | label   | default |
        |         | select_one c1 | s1   | Select1 | a-2     |
        |         | select_one c2 | s2   | Select2 | 1-1     |
        |         | select_one c3 | s3   | Select3 | a-b     |
        | choices |           |      |            |
        |         | list_name | name | label      |
        |         | c1        | a-1  | Choice A-1 |
        |         | c1        | a-2  | Choice A-2 |
        |         | c2        | 1-1  | Choice 1-1 |
        |         | c2        | 2-2  | Choice 1-2 |
        |         | c3        | a-b  | Choice A-B |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            run_odk_validate=True,
        )


class DynamicDefaultUnitTests(PyxformTestCase):
    """
    Similar scope to DynamicDefaultTests but separated cases for testing parse step.
    """

    Case = namedtuple("Case", ["is_dynamic", "q_type", "q_default", "q_label_fr"])

    def setUp(self) -> None:
        self.case_data = (
            # TEXT
            # Literal text containing URI; https://github.com/XLSForm/pyxform/issues/533
            self.Case(False, "text", """https://my-site.com""", ""),
            # Literal text containing brackets.
            # French translation "Oui" here to satisfy Validate for jr:itext call below.
            self.Case(False, "text", """(https://mysite.com)""", "Oui"),
            # Literal text containing URI.
            self.Case(False, "text", """go to https://mysite.com""", ""),
            # Literal text containing various non-operator symbols.
            self.Case(False, "text", """Repeat after me: ~!@#$%^&()_""", ""),
            # DATE(TIME)
            # Literal date.
            self.Case(False, "date", """2022-03-14""", ""),
            # Literal date, BCE.
            self.Case(False, "date", """-2022-03-14""", ""),
            # Literal time.
            self.Case(False, "time", """01:02:55""", ""),
            # Literal time, UTC.
            self.Case(False, "time", """01:02:55Z""", ""),
            # Literal time, UTC + 0.
            self.Case(False, "time", """01:02:55+00:00""", ""),
            # Literal time, UTC + 10.
            self.Case(False, "time", """01:02:55+10:00""", ""),
            # Literal time, UTC - 7.
            self.Case(False, "time", """01:02:55-07:00""", ""),
            # Literal datetime.
            self.Case(False, "date", """2022-03-14T01:02:55""", ""),
            # Literal datetime, UTC.
            self.Case(False, "dateTime", """2022-03-14T01:02:55Z""", ""),
            # Literal datetime, UTC + 0.
            self.Case(False, "dateTime", """2022-03-14T01:02:55+00:00""", ""),
            # Literal datetime, UTC + 10.
            self.Case(False, "dateTime", """2022-03-14T01:02:55+10:00""", ""),
            # Literal datetime, UTC - 7.
            self.Case(False, "dateTime", """2022-03-14T01:02:55-07:00""", ""),
            # GEO*
            # Literal geopoint.
            self.Case(False, "geopoint", """32.7377112 -117.1288399 14 5.01""", ""),
            # Literal geotrace.
            self.Case(
                False,
                "geotrace",
                "32.7377112 -117.1288399 14 5.01;" + "32.7897897 -117.9876543 14 5.01",
                "",
            ),
            # Literal geoshape.
            self.Case(
                False,
                "geoshape",
                "32.7377112 -117.1288399 14 5.01;"
                + "32.7897897 -117.9876543 14 5.01;"
                + "32.1231231 -117.1145877 14 5.01",
                "",
            ),
            # DYNAMIC
            # Function with mixture of quotes.
            self.Case(True, "text", """ends-with('mystr', "str")""", ""),
            # Function with node paths.
            self.Case(True, "text", """ends-with(../t2, ./t4)""", ""),
            # Namespaced function. Although jr:itext probably not valid in a default.
            self.Case(True, "text", """jr:itext('/test/q1:label')""", ""),
            # Compound expression with functions, operators, numeric/string literals.
            self.Case(True, "text", """if(../t2 = 'test', 1, 2) + 15 - int(1.2)""", ""),
            # Compound expression with a literal first.
            self.Case(True, "text", """1 + decimal-date-time(now())""", ""),
            # Nested function calls.
            self.Case(
                True,
                "text",
                """concat(if(../t1 = "this", 'go', "to"), "https://mysite.com")""",
                "",
            ),
            # Node paths with operator.
            self.Case(True, "text", """../t2 - ./t4""", ""),
            # Math expression.
            self.Case(True, "text", """1 + 2 - 3 * 4 div 5 mod 6""", ""),
        )
        # Additional cases needing different approach for markdown / xpath assertions.
        self.case_data_extras = (
            # TODO: pyxform references appear in result as resolved XPaths
            # Pyxform reference.
            self.Case(True, "text", """${q0}""", ""),
            # Pyxform reference, with last-saved.
            self.Case(True, "text", """${last-saved#q0}""", ""),
            # TODO: Pipe character is interpreted as column delimiter
            # Union expression.
            self.Case(True, "text", """../t2 | ./t4""", ""),
        )

    def test_default_is_dynamic_return_value(self):
        """Should find expected return value for each case passed to default_is_dynamic."""
        for c in (*self.case_data, *self.case_data_extras):
            with self.subTest(msg=repr(c)):
                self.assertEqual(
                    c.is_dynamic,
                    utils.default_is_dynamic(
                        element_default=c.q_default, element_type=c.q_type
                    ),
                )

    def test_dynamic_default_xform_structure(self):
        """Should find non-dynamic values in instance, and dynamic values in setvalue."""
        cases_enum = list(enumerate(self.case_data))
        md_head = """
        | survey |            |          |          |               |                    |
        |        | type       | name     | label    | default       | label::French (fr) |
        """
        md_row = """
        |        | {c.q_type} | q{q_num} | Q{q_num} | {c.q_default} | {c.q_label_fr}     |
        """
        md = md_head + "".join(
            md_row.strip("\n").format(q_num=q_num, c=c) for q_num, c in cases_enum
        )

        def xp_model(qnum, case):
            """Non-dynamic values in instance, and dynamic values in setvalue."""
            q_default = case.q_default.replace('"', "&quot;")
            if case.is_dynamic:
                # Comparison to attribute string containing single-quote doesn't work but
                # can at least check the original default string length is a match.
                if "'" in q_default:
                    value_cmp = f""" string-length(@value)={len(case.q_default)} """
                else:
                    value_cmp = f""" @value="{q_default}" """
                return fr"""
                /h:html/h:head/x:model
                  /x:instance/x:test[@id="test"]/x:q{qnum}[
                    not(text())
                    and ancestor::x:model/x:setvalue[
                      @ref="/test/q{qnum}"
                      and {value_cmp}
                    ]
                  ]
                """
            else:
                return fr"""
                /h:html/h:head/x:model
                  /x:instance/x:test[@id="test"]/x:q{qnum}[
                    text()="{q_default}"
                    and not(ancestor::x:model/x:setvalue[@ref="/test/q{qnum}"])
                  ]
                """

        def xp_body(qnum, case):
            """All items are 'input' type, translations refer to itext."""
            if case.q_label_fr == "":
                label_cmp = f""" ./x:label[text()="Q{qnum}"] """
            else:
                label_cmp = f""" ./x:label[@ref="jr:itext('/test/q{qnum}:label')"] """
            return f"""
              /h:html/h:body/x:input[
                @ref="/test/q{qnum}"
                and {label_cmp}
              ]
            """

        self.assertPyxformXform(
            name="test",
            id_string="test",
            md=md,
            run_odk_validate=True,
            xml__xpath_match=[
                xp  # Get both XPath types for each Case.
                for q_num, c in cases_enum
                for xp in (xp_model(q_num, c), xp_body(q_num, c))
            ],
        )
