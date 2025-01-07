"""
Test handling dynamic default in forms
"""

from dataclasses import dataclass
from os import getpid
from time import perf_counter
from unittest import skip
from unittest.mock import patch

from psutil import Process
from pyxform import utils
from pyxform.xls2json_backends import SupportedFileTypes
from pyxform.xls2xform import convert

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


@dataclass(slots=True)
class Case:
    """
    A test case spec for dynamic default scenarios.

    - is_dynamic: If true, the default should result in treatment as a dynamic default.
    - q_type: The question type, e.g. text, integer, select_one, etc.
    - q_default: The default value.
    - q_value: The rendered default value. Can be different to the input default, for
        example Pyxform references are input as ${q1} but rendered as "/instance/q1".
    - q_label_fr: For itext cases, a French question label.
    """

    is_dynamic: bool
    q_type: str
    q_default: str = ""
    q_value: str | None = None
    q_label_fr: str = ""


class XPathHelper:
    """
    XPath expressions for dynamic defaults assertions.
    """

    @staticmethod
    def model_setvalue(q_num: int):
        """Get the setvalue element's value attribute."""
        return rf"""
        /h:html/h:head/x:model/x:setvalue[
          @ref="/test_name/q{q_num}"
          and @event='odk-instance-first-load'
        ]/@value
        """

    @staticmethod
    def model(q_num: int, case: Case):
        """
        Expected structure for model elements.

        Expect non-dynamic values in the instance, and dynamic values in a setvalue.

        For default values that include a single quote, it's not really possible to use
        a XPath expression with xpath_match. Testing for the same string length is
        problematic as well due to substitution of &quot; for single quote. Instead,
        use the model_setvalue XPath with xml__xpath_exact, which compares the value
        containing single quotes outside of a XPath context.
        """
        q_default_final = utils.coalesce(case.q_value, case.q_default)

        if case.q_type in ("calculate", "select_one", "text"):
            q_bind = "string"
        elif case.q_type == "integer":
            q_bind = "int"
        else:
            q_bind = case.q_type

        if case.is_dynamic:
            if "'" in q_default_final:
                value_cmp = ""
            else:
                value_cmp = f"""and @value="{q_default_final}" """
            return rf"""
            /h:html/h:head/x:model
              /x:instance/x:test_name[@id="data"]/x:q{q_num}[
                not(text())
                and ancestor::x:model/x:bind[
                  @nodeset='/test_name/q{q_num}'
                  and @type='{q_bind}'
                ]
                and ancestor::x:model/x:setvalue[
                  @ref="/test_name/q{q_num}"
                  and @event='odk-instance-first-load'
                  {value_cmp}
                ]
              ]
            """
        else:
            if 0 == len(q_default_final):
                q_default_cmp = """and not(text()) """
            elif "'" in q_default_final:
                q_default_cmp = ""
            else:
                q_default_cmp = f"""and text()='{q_default_final}' """
            return rf"""
            /h:html/h:head/x:model
              /x:instance/x:test_name[@id="data"]/x:q{q_num}[
                ancestor::x:model/x:bind[
                  @nodeset='/test_name/q{q_num}'
                  and @type='{q_bind}'
                ]
                and not(ancestor::x:model/x:setvalue[@ref="/test_name/q{q_num}"])
                {q_default_cmp}
              ]
            """

    @staticmethod
    def body_input(qnum: int, case: Case):
        """Expected structure for body elements for input types."""
        if case.q_label_fr == "":
            label_cmp = f""" ./x:label[text()="Q{qnum}"] """
        else:
            label_cmp = f""" ./x:label[@ref="jr:itext('/test_name/q{qnum}:label')"] """
        return f"""
          /h:html/h:body/x:input[
            @ref="/test_name/q{qnum}"
            and {label_cmp}
          ]
        """

    @staticmethod
    def body_select1(q_num: int, choices: tuple[tuple[str, str], ...]):
        """Expected structure for body elements for select1 types."""
        choices_xp = "\n              and ".join(
            (
                f"./x:item/x:value/text() = '{cv}' and ./x:item/x:label/text() = '{cl}'"
                for cv, cl in choices
            )
        )
        return rf"""
        /h:html/h:body/x:select1[
          @ref = '/test/q{q_num}'
          and ./x:label/text() = 'Select{q_num}'
          and {choices_xp}
        ]
        """


xp = XPathHelper()


class TestDynamicDefault(PyxformTestCase):
    """
    Handling dynamic defaults.
    """

    def test_static_default_in_repeat(self):
        """Should use instance repeat template and first row for static default inside a repeat."""
        md = """
        | survey |              |      |       |         |
        |        | type         | name | label | default |
        |        | integer      | q0   | Foo   | foo     |
        |        | begin repeat | r1   |       |         |
        |        | integer      | q1   | Bar   | 12      |
        |        | end repeat   | r1   |       |         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xp.model(0, Case(False, "integer", "foo")),
                # Repeat template and first row.
                """
                /h:html/h:head/x:model/x:instance/x:test_name[
                  @id="data"
                  and ./x:r1[@jr:template='']
                  and ./x:r1[not(@jr:template)]
                ]
                """,
                # q1 static default value in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:q1[text()='12']
                """,
                # q1 static default value in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:q1[text()='12']
                """,
            ],
        )

    def test_dynamic_default_in_repeat(self):
        """Should use body setvalue for dynamic default form inside a repeat."""
        md = """
        | survey |              |      |              |           |
        |        | type         | name | label        | default   |
        |        | begin repeat | r1   | Households   |           |
        |        | integer      | q0   | Your age     | random()  |
        |        | text         | q1   | Your feeling | not_func$ |
        |        | end repeat   | r1   |              |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Repeat template and first row.
                """
                /h:html/h:head/x:model/x:instance/x:test_name[
                  @id="data"
                  and ./x:r1[@jr:template='']
                  and ./x:r1[not(@jr:template)]
                ]
                """,
                # q0 dynamic default value not in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q0' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:q0[not(text())]
                """,
                # q0 dynamic default value not in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q0' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:q0[not(text())]
                """,
                # q0 dynamic default value not in model setvalue.
                """
                /h:html/h:head/x:model[not(./x:setvalue[@ref='data/r1/q0'])]
                """,
                # q0 dynamic default value in body group setvalue, with 2 events.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[@nodeset='/test_name/r1']
                  /x:setvalue[
                    @event='odk-instance-first-load odk-new-repeat'
                    and @ref='/test_name/r1/q0'
                    and @value='random()'
                  ]
                """,
                # q1 static default value in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='string']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:q1[text()='not_func$']
                """,
                # q1 static default value in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='string']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:q1[text()='not_func$']
                """,
            ],
        )

    def test_dynamic_default_in_group(self):
        """Should use model setvalue for dynamic default form inside a group."""
        md = """
        | survey |             |      |       |         |
        |        | type        | name | label | default |
        |        | integer     | q0   | Foo   |         |
        |        | begin group | g1   |       |         |
        |        | integer     | q1   | Bar   | ${q0}   |
        |        | end group   | g1   |       |         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # q0 element in instance.
                """/h:html/h:head/x:model/x:instance/x:test_name[@id="data"]/x:q0""",
                # Group element in instance.
                """/h:html/h:head/x:model/x:instance/x:test_name[@id="data"]/x:g1""",
                # q1 dynamic default not in instance.
                """/h:html/h:head/x:model/x:instance/x:test_name[@id="data"]/x:g1/x:q1[not(text())]""",
                # q1 dynamic default value in model setvalue, with 1 event.
                """
                /h:html/h:head/x:model/x:setvalue[
                  @event="odk-instance-first-load"
                  and @ref='/test_name/g1/q1'
                  and @value=' /test_name/q0 '
                ]
                """,
                # q1 dynamic default value not in body group setvalue.
                """
                /h:html/h:body/x:group[
                  @ref='/test_name/g1'
                  and not(child::setvalue[@ref='/test_name/g1/q1'])
                ]
                """,
            ],
        )

    def test_sibling_dynamic_default_in_group(self):
        """Should use model setvalue for dynamic default form inside a group."""
        md = """
        | survey |              |      |       |         |
        |        | type         | name | label | default |
        |        | begin group  | g1   |       |         |
        |        | integer      | q0   | Foo   |         |
        |        | integer      | q1   | Bar   | ${q0}   |
        |        | end group    | g1   |       |         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Group element in instance.
                """/h:html/h:head/x:model/x:instance/x:test_name[@id="data"]/x:g1""",
                # q0 element in group.
                """/h:html/h:head/x:model/x:instance/x:test_name[@id="data"]/x:g1/x:q0""",
                # q1 dynamic default not in instance.
                """/h:html/h:head/x:model/x:instance/x:test_name[@id="data"]/x:g1/x:q1[not(text())]""",
                # q1 dynamic default value in model setvalue, with 1 event.
                """
                /h:html/h:head/x:model/x:setvalue[
                  @event="odk-instance-first-load"
                  and @ref='/test_name/g1/q1'
                  and @value=' /test_name/g1/q0 '
                ]
                """,
                # q1 dynamic default value not in body group setvalue.
                """
                /h:html/h:body/x:group[
                  @ref='/test_name/g1'
                  and not(child::setvalue[@ref='/test_name/g1/q1'])
                ]
                """,
            ],
        )

    def test_sibling_dynamic_default_in_repeat(self):
        """Should use body setvalue for dynamic default form inside a repeat."""
        md = """
        | survey |              |      |       |         |
        |        | type         | name | label | default |
        |        | begin repeat | r1   |       |         |
        |        | integer      | q0   | Foo   |         |
        |        | integer      | q1   | Bar   | ${q0}   |
        |        | end repeat   | r1   |       |         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Repeat template and first row.
                """
                /h:html/h:head/x:model/x:instance/x:test_name[
                  @id="data"
                  and ./x:r1[@jr:template='']
                  and ./x:r1[not(@jr:template)]
                ]
                """,
                # q0 element in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q0' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:q0
                """,
                # q0 element in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q0' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:q0
                """,
                # q1 dynamic default value not in model setvalue.
                """
                /h:html/h:head/x:model[not(./x:setvalue[@ref='data/r1/q1'])]
                """,
                # q1 dynamic default value in body group setvalue, with 2 events.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[@nodeset='/test_name/r1']
                  /x:setvalue[
                    @event='odk-instance-first-load odk-new-repeat'
                    and @ref='/test_name/r1/q1'
                    and @value=' ../q0 '
                  ]
                """,
            ],
        )

    def test_dynamic_default_in_group_nested_in_repeat(self):
        """Should use body setvalue for dynamic default form inside a group and repeat."""
        md = """
        | survey |              |      |       |         |
        |        | type         | name | label | default |
        |        | begin repeat | r1   |       |         |
        |        | begin group  | g1   |       |         |
        |        | integer      | q0   | Foo   |         |
        |        | integer      | q1   | Bar   | ${q0}   |
        |        | end group    | g1   |       |         |
        |        | end repeat   | r1   |       |         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Repeat template and first row contains the group.
                """
                /h:html/h:head/x:model/x:instance/x:test_name[
                  @id="data"
                  and ./x:r1[@jr:template='']/x:g1
                  and ./x:r1[not(@jr:template)]/x:g1
                ]
                """,
                # q0 element in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/g1/q0' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:g1/x:q0
                """,
                # q0 element in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/g1/q0' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:g1/x:q0
                """,
                # q1 dynamic default value not in model setvalue.
                """
                /h:html/h:head/x:model[not(./x:setvalue[@ref='data/r1/g1/q1'])]
                """,
                # q1 dynamic default value in body group setvalue, with 2 events.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[@nodeset='/test_name/r1']
                  /x:setvalue[
                    @event='odk-instance-first-load odk-new-repeat'
                    and @ref='/test_name/r1/g1/q1'
                    and @value=' ../q0 '
                  ]
                """,
            ],
        )

    def test_dynamic_default_in_repeat_nested_in_repeat(self):
        """Should use body setvalue for dynamic default form inside 2 levels of repeat."""
        md = """
        | survey |              |      |       |         |
        |        | type         | name | label | default |
        |        | begin repeat | r1   |       |         |
        |        | date         | q0   | Date  | now()   |
        |        | integer      | q1   | Foo   |         |
        |        | begin repeat | r2   |       |         |
        |        | integer      | q2   | Bar   | ${q1}   |
        |        | end repeat   | r2   |       |         |
        |        | end repeat   | r1   |       |         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Repeat templates and first rows.
                """
                /h:html/h:head/x:model/x:instance/x:test_name[
                  @id="data"
                  and ./x:r1[@jr:template='']/x:r2[@jr:template='']
                  and ./x:r1[not(@jr:template)]/x:r2[not(@jr:template)]
                ]
                """,
                # q0 element in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q0' and @type='date']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:q0
                """,
                # q0 element in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q0' and @type='date']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:q0
                """,
                # q0 dynamic default value not in model setvalue.
                """
                /h:html/h:head/x:model[not(./x:setvalue[@ref='data/r1/q0'])]
                """,
                # q0 dynamic default value in body group setvalue, with 2 events.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[@nodeset='/test_name/r1']
                  /x:setvalue[
                    @event='odk-instance-first-load odk-new-repeat'
                    and @ref='/test_name/r1/q0'
                    and @value='now()'
                  ]
                """,
                # q1 element in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:q1
                """,
                # q1 element in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:q1
                """,
                # q2 element in repeat template.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[@jr:template='']/x:r2[@jr:template='']/x:q2
                """,
                # q2 element in repeat row.
                """
                /h:html/h:head/x:model[
                  ./x:bind[@nodeset='/test_name/r1/q1' and @type='int']
                ]/x:instance/x:test_name[@id="data"]/x:r1[not(@jr:template)]/x:r2[not(@jr:template)]/x:q2
                """,
                # q2 dynamic default value not in model setvalue.
                """
                /h:html/h:head/x:model[not(./x:setvalue[@ref='data/r1/r2/q2'])]
                """,
                # q2 dynamic default value in body group setvalue, with 2 events.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[@nodeset='/test_name/r1']
                  /x:group[@ref='/test_name/r1/r2']/x:repeat[@nodeset='/test_name/r1/r2']
                    /x:setvalue[
                      @event='odk-instance-first-load odk-new-repeat'
                      and @ref='/test_name/r1/r2/q2'
                      and @value=' ../../q1 '
                    ]
                """,
            ],
        )

    def test_dynamic_default_does_not_warn(self):
        """Pyxform used to warn about client compatibility, but now it shouldn't."""
        self.assertPyxformXform(
            md="""
            | survey |      |         |       |         |
            |        | type | name    | label | default |
            |        | text | foo     | Foo   |         |
            |        | text | bar     | Bar   | ${foo}  |
            """,
            warnings_count=0,
        )

    def test_dynamic_default_on_calculate(self):
        self.assertPyxformXform(
            md="""
            | survey |            |      |       |             |                      |
            |        | type       | name | label | calculation | default              |
            |        | calculate  | q1   |       |             | random() + 0.5       |
            |        | calculate  | q2   |       |             | if(${q1} < 1,'A','B') |
            """,
            xml__xpath_match=[
                xp.model(1, Case(True, "calculate", "random() + 0.5")),
                xp.model(2, Case(True, "calculate", "if( /test_name/q1  < 1,'A','B')")),
                # Nothing in body since both questions are calculations.
                "/h:html/h:body[not(text) and count(./*) = 0]",
            ],
        )

    def test_dynamic_default_select_choice_name_with_hyphen(self):
        # Repro for https://github.com/XLSForm/pyxform/issues/495
        md = """
        | survey  |               |      |         |         |
        |         | type          | name | label   | default |
        |         | select_one c1 | q1   | Select1 | a-2     |
        |         | select_one c2 | q2   | Select2 | 1-1     |
        |         | select_one c3 | q3   | Select3 | a-b     |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | c1        | a-1  | C A-1 |
        |         | c1        | a-2  | C A-2 |
        |         | c2        | 1-1  | C 1-1 |
        |         | c2        | 2-2  | C 1-2 |
        |         | c3        | a-b  | C A-B |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xp.model(1, Case(False, "select_one", "a-2")),
                xp.model(2, Case(False, "select_one", "1-1")),
                xp.model(3, Case(False, "select_one", "a-b")),
                xpc.model_instance_choices_label(
                    "c1", (("a-1", "C A-1"), ("a-2", "C A-2"))
                ),
                xpc.model_instance_choices_label(
                    "c2", (("1-1", "C 1-1"), ("2-2", "C 1-2"))
                ),
                xpc.model_instance_choices_label("c3", (("a-b", "C A-B"),)),
                xpq.body_select1_itemset("q1"),
                xpq.body_select1_itemset("q2"),
                xpq.body_select1_itemset("q3"),
            ],
        )


class TestDynamicDefaultSimpleInput(PyxformTestCase):
    """
    Dynamic default test cases using simple input-bound question types, i.e. not using
    selects, groups, or repeats.
    """

    def setUp(self) -> None:
        self.case_data = (
            # --------
            # TEXT
            # --------
            # Literal with just alpha characters.
            Case(False, "integer", """foo"""),
            # Literal with numeric characters.
            Case(False, "integer", """123"""),
            # Literal with alphanumeric characters.
            Case(False, "text", """bar123"""),
            # Literal text containing URI; https://github.com/XLSForm/pyxform/issues/533
            Case(False, "text", """https://my-site.com"""),
            # Literal text containing brackets.
            Case(False, "text", """(https://mysite.com)"""),
            # Literal text containing URI.
            Case(False, "text", """go to https://mysite.com"""),
            # Literal text containing various non-operator symbols.
            Case(False, "text", """Repeat after me: '~!@#$%^&()_"""),
            Case(False, "text", """not_func$"""),
            # Names that look like a math expression.
            Case(False, "text", """f-g"""),
            Case(False, "text", """f-4"""),
            # Name that looks like a math expression, in a node ref.
            Case(False, "text", """./f-4"""),
            # --------
            # INTEGER
            # --------
            # Names that look like a math expression.
            Case(False, "integer", """f-g"""),
            Case(False, "integer", """f-4"""),
            # --------
            # DATE(TIME)
            # --------
            # Literal date.
            Case(False, "date", """2022-03-14"""),
            # Literal date, BCE.
            Case(False, "date", """-2022-03-14"""),
            # Literal time.
            Case(False, "time", """01:02:55"""),
            # Literal time, UTC.
            Case(False, "time", """01:02:55Z"""),
            # Literal time, UTC + 0.
            Case(False, "time", """01:02:55+00:00"""),
            # Literal time, UTC + 10.
            Case(False, "time", """01:02:55+10:00"""),
            # Literal time, UTC - 7.
            Case(False, "time", """01:02:55-07:00"""),
            # Literal datetime.
            Case(False, "date", """2022-03-14T01:02:55"""),
            # Literal datetime, UTC.
            Case(False, "dateTime", """2022-03-14T01:02:55Z"""),
            # Literal datetime, UTC + 0.
            Case(False, "dateTime", """2022-03-14T01:02:55+00:00"""),
            # Literal datetime, UTC + 10.
            Case(False, "dateTime", """2022-03-14T01:02:55+10:00"""),
            # Literal datetime, UTC - 7.
            Case(False, "dateTime", """2022-03-14T01:02:55-07:00"""),
            # --------
            # GEO*
            # --------
            # Literal geopoint.
            Case(False, "geopoint", """32.7377112 -117.1288399 14 5.01"""),
            # Literal geotrace.
            Case(
                False,
                "geotrace",
                "32.7377112 -117.1288399 14 5.01;" + "32.7897897 -117.9876543 14 5.01",
            ),
            # Literal geoshape.
            Case(
                False,
                "geoshape",
                "32.7377112 -117.1288399 14 5.01;"
                + "32.7897897 -117.9876543 14 5.01;"
                + "32.1231231 -117.1145877 14 5.01",
            ),
            # --------
            # DYNAMIC
            # --------
            # Function call with no args.
            Case(True, "integer", """random()"""),
            # Function with mixture of quotes.
            Case(True, "text", """ends-with('mystr', "str")"""),
            # Function with node paths.
            Case(True, "text", """ends-with(../t2, ./t4)"""),
            # Namespaced function. Although jr:itext probably does nothing?
            Case(True, "text", """jr:itext('/test/ref_text:label')"""),
            # Compound expression with functions, operators, numeric/string literals.
            Case(True, "text", """if(../t2 = 'test', 1, 2) + 15 - int(1.2)"""),
            # Compound expression with a literal first.
            Case(True, "text", """1 + decimal-date-time(now())"""),
            # Nested function calls.
            Case(
                True,
                "text",
                """concat(if(../t1 = "this", 'go', "to"), "https://mysite.com")""",
            ),
            # Two constants in a math expression.
            Case(True, "integer", """7 - 4"""),
            Case(True, "text", """3 mod 3"""),
            Case(True, "text", """5 div 5"""),
            # 3 or more constants in a math expression.
            Case(True, "text", """2 + 3 * 4"""),
            Case(True, "text", """5 div 5 - 5"""),
            # Two constants, with a function call.
            Case(True, "integer", """random() + 2 * 5"""),
            # Node path with operator and constant.
            Case(True, "text", """./f - 4"""),
            # Two node paths with operator.
            Case(True, "text", """../t2 - ./t4"""),
            # Math expression.
            Case(True, "text", """1 + 2 - 3 * 4 div 5 mod 6"""),
            # Function with date type result.
            Case(True, "date", """concat('2022-03', '-14')"""),
            # Pyxform reference.
            Case(True, "text", "${ref_text}", q_value=" /test_name/ref_text "),
            Case(True, "integer", "${ref_int}", q_value=" /test_name/ref_int "),
            # Pyxform reference, with last-saved.
            Case(
                True,
                "text",
                "${last-saved#ref_text}",
                q_value=" instance('__last-saved')/test_name/ref_text ",
            ),
            # Pyxform reference, with last-saved, inside a function.
            Case(
                True,
                "integer",
                "if(${last-saved#ref_int} = '', 0, ${last-saved#ref_int} + 1)",
                q_value="if( instance('__last-saved')/test_name/ref_int  = '', 0,"
                "  instance('__last-saved')/test_name/ref_int  + 1)",
            ),
        )
        # Additional cases passed through default_is_dynamic only, not markdown->xform test.
        self.case_data_extras = (
            # Union expression.
            # Rejected by ODK Validate: https://github.com/getodk/xforms-spec/issues/293
            Case(True, "text", r"""../t2 \| ./t4"""),
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
        # Ref_* items here for the above Cases to use in Pyxform ${references}.
        md_head = """
        | survey |            |          |          |               |                    |
        |        | type       | name     | label    | default       | label::French (fr) |
        |        | text       | ref_text | RefText  |               | Oui                |
        |        | integer    | ref_int  | RefInt   |               |                    |
        """
        md_row = """
        |        | {c.q_type} | q{q_num} | Q{q_num} | {c.q_default} | {c.q_label_fr}     |
        """
        md = md_head + "".join(
            md_row.strip("\n").format(q_num=q_num, c=c) for q_num, c in cases_enum
        )
        self.assertPyxformXform(
            md=md,
            # Exclude if single quote in value, to avoid comparison and escaping issues.
            xml__xpath_match=[
                xpaths
                for q_num, c in cases_enum
                for xpaths in (xp.model(q_num, c), xp.body_input(q_num, c))
                if "'" not in utils.coalesce(c.q_value, "")
            ],
            # For values with single quote, use comparison outside of XPath context.
            xml__xpath_exact=[
                (xp.model_setvalue(q_num), {c.q_value})
                for q_num, c in cases_enum
                if "'" in utils.coalesce(c.q_value, "")
            ],
        )

    @skip("Slow performance test. Un-skip to run as needed.")
    def test_dynamic_default_performance__time(self):
        """
        Should find the dynamic default check costs little extra relative time large forms.

        Results with Python 3.10.14 on VM with 2vCPU (i7-7700HQ) 1GB RAM, x questions
        each, average of 10 runs (seconds), with and without the check, per question:
        | num   | with   | without | peak RSS MB |
        |   500 | 0.1626 |  0.1886 |          60 |
        |  1000 | 0.3330 |  0.3916 |          63 |
        |  2000 | 0.8675 |  0.7823 |          70 |
        |  5000 | 1.7051 |  1.5653 |          91 |
        | 10000 | 3.1097 |  3.8525 |         137 |
        """
        survey_header = """
        | survey |            |          |          |               |
        |        | type       | name     | label    | default       |
        """
        question = """
        |        | text       | q{i}     | Q{i}     | if(../t2 = 'test', 1, 2) + 15 - int(1.2) |
        """
        process = Process(getpid())
        for count in (500, 1000, 2000):
            questions = "\n".join(question.format(i=i) for i in range(count))
            md = "".join((survey_header, questions))

            def run(name, case):
                runs = 0
                results = []
                peak_memory_usage = process.memory_info().rss
                while runs < 10:
                    start = perf_counter()
                    convert(xlsform=case, file_type=SupportedFileTypes.md.value)
                    results.append(perf_counter() - start)
                    peak_memory_usage = max(process.memory_info().rss, peak_memory_usage)
                    runs += 1
                print(
                    name,
                    round(sum(results) / len(results), 4),
                    f"| Peak RSS: {peak_memory_usage}",
                )

            run(name=f"questions={count}, with check (seconds):", case=md)

            with patch("pyxform.utils.default_is_dynamic", return_value=True):
                run(name=f"questions={count}, without check (seconds):", case=md)

    def test_dynamic_default_performance__memory(self):
        """
        Should find the dynamic default check costs little extra RAM for large forms.

        Not very accurate since assertPyxformXform does lots of other things that add to
        memory usage, and the test measures the current process usage which is atypical of
        actual usage. If at some stage Pyxform can write XLSX or process markdown, a more
        accurate test could call subprocess and compare memory usage from repeat runs.
        """
        survey_header = """
        | survey |            |          |          |               |
        |        | type       | name     | label    | default       |
        """
        question = """
        |        | text       | q{i}     | Q{i}     | if(../t2 = 'test', 1, 2) + 15 - int(1.2) |
        """
        questions = "\n".join(question.format(i=i) for i in range(1, 2000))
        md = "".join((survey_header, questions))
        process = Process(getpid())
        pre_mem = process.memory_info().rss
        self.assertPyxformXform(md=md)
        post_mem = process.memory_info().rss
        self.assertLess(post_mem, pre_mem * 2)
