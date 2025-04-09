"""
Test the "note" question type.
"""

from dataclasses import dataclass, field

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


@dataclass(slots=True)
class Case:
    """
    A test case spec for note output scenarios.
    """

    label: str
    match: set[str]
    xpath: str = field(default_factory=lambda: xpq.body_input_label_output_value("note"))


class TestNotes(PyxformTestCase):
    def test_instance_expression__original_problem_scenario(self):
        """Should produce expected output for scenario similar to pyxform/#646."""
        md = """
        | survey  |               |      |       |
        |         | type          | name | label |
        |         | select_one c1 | q1   | Q1    |
        |         | select_one c2 | q2   | Q2    |
        |         | text          | text | Text  |
        |         | note          | note | This is a note with a reference to ${text}. And a reference to a secondary instance: instance('c1')/root/item[name = ${q1}]/label is here, and another instance('c2')/root/item[contains(name, ${q2})]/label is here. |
        | choices |
        |         | list_name | name | label |
        |         | c1        | y    | Yes   |
        |         | c1        | n    | No    |
        |         | c2        | b    | Big   |
        |         | c2        | s    | Small |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:body/x:input[@ref='/test_name/note']/x:label[
                  contains(., 'This is a note with a reference to')
                    and contains(., '. And a reference to a secondary instance: ')
                    and contains(., 'is here, and another')
                    and contains(., 'is here.')
                ]
                """,
            ],
            # Value contains single quote so need to use xpath_exact.
            xml__xpath_exact=[
                (
                    xpq.body_input_label_output_value("note"),
                    {
                        " /test_name/text ",
                        "instance('c1')/root/item[name =  /test_name/q1 ]/label",
                        "instance('c2')/root/item[contains(name,  /test_name/q2 )]/label",
                    },
                ),
            ],
        )

    def test_instance_expression__permutations(self):
        """Should produce expected output for various combinations of instance usages."""
        md = """
        | survey  |               |      |       |
        |         | type          | name | label |
        |         | select_one c1 | q1   | Q1    |
        |         | select_one c2 | q2   | Q2    |
        |         | text          | text | Text  |
        |         | note          | note | {note} |
        | choices |
        |         | list_name | name | label |
        |         | c1        | y    | Yes   |
        |         | c1        | n    | No    |
        |         | c2        | b    | Big   |
        |         | c2        | s    | Small |
        """
        # It's a bit confusing, but although double quotes are literally HTML in entity
        # form (i.e. `&quot;`) in the output, for pyxform test comparisons they get
        # converted back, so the expected output strings are double quotes not `&quot;`.
        cases = [
            # A pyxform token.
            Case(
                "${text}",
                {" /test_name/text "},
            ),
            # Instance expression with predicate using pyxform token and equals.
            Case(
                "instance('c1')/root/item[name = ${q1}]/label",
                {"instance('c1')/root/item[name =  /test_name/q1 ]/label"},
            ),
            # Instance expression with predicate using pyxform token and equals (double quotes).
            Case(
                """instance("c1")/root/item[name = ${q1}]/label""",
                {"""instance("c1")/root/item[name =  /test_name/q1 ]/label"""},
            ),
            # Instance expression with predicate using pyxform token and function.
            Case(
                "instance('c2')/root/item[contains(name, ${q2})]/label",
                {"instance('c2')/root/item[contains(name,  /test_name/q2 )]/label"},
            ),
            # Instance expression with predicate using pyxform token and function (double quotes).
            Case(
                """instance("c2")/root/item[contains("name", ${q2})]/label""",
                {"""instance("c2")/root/item[contains("name",  /test_name/q2 )]/label"""},
            ),
            # Instance expression with predicate using pyxform token and function (mixed quotes).
            Case(
                """instance('c2')/root/item[contains("name", ${q2})]/label""",
                {"""instance('c2')/root/item[contains("name",  /test_name/q2 )]/label"""},
            ),
            # Instance expression with predicate using pyxform token and equals.
            Case(
                "instance('c2')/root/item[contains(name, instance('c1')/root/item[name = ${q1}]/label)]/label",
                {
                    "instance('c2')/root/item[contains(name, instance('c1')/root/item[name =  /test_name/q1 ]/label)]/label"
                },
            ),
            # Instance expression with predicate using pyxform token and equals (double quotes).
            Case(
                """instance("c2")/root/item[contains(name, instance("c1")/root/item[name = ${q1}]/label)]/label""",
                {
                    """instance("c2")/root/item[contains(name, instance("c1")/root/item[name =  /test_name/q1 ]/label)]/label"""
                },
            ),
            # Instance expression with predicate using pyxform token and equals (mixed quotes).
            Case(
                """instance('c2')/root/item[contains(name, instance("c1")/root/item[name = ${q1}]/label)]/label""",
                {
                    """instance('c2')/root/item[contains(name, instance("c1")/root/item[name =  /test_name/q1 ]/label)]/label"""
                },
            ),
            # Instance expression with predicate not using a pyxform token.
            Case(
                "instance('c1')/root/item[name = 'y']/label",
                {"instance('c1')/root/item[name = 'y']/label"},
            ),
            # Instance expression with predicate not using a pyxform token (double quotes).
            Case(
                """instance("c1")/root/item[name = "y"]/label""",
                {"""instance("c1")/root/item[name = "y"]/label"""},
            ),
            # Instance expression with predicate not using a pyxform token (mixed quotes).
            Case(
                """instance("c1")/root/item[name = 'y']/label""",
                {"""instance("c1")/root/item[name = 'y']/label"""},
            ),
            # Instance expression with predicate not using a pyxform token (all escaped).
            Case(
                """instance("c1")/root/item[name <> 1 and "<>&" = "1"]/label""",
                {
                    """instance("c1")/root/item[name &lt;&gt; 1 and "&lt;&gt;&amp;" = "1"]/label"""
                },
            ),
        ]
        wrap_scenarios = ("{}", "Text {}", "{} text", "Text {} text")
        # All cases together in one.
        combo_case = Case(
            " ".join(c.label for c in cases),
            {m for c in cases for m in c.match},
        )
        cases.append(combo_case)
        for c in cases:
            for fmt in wrap_scenarios:
                note_text = fmt.format(c.label)
                with self.subTest(msg=(c.label, fmt)):
                    self.assertPyxformXform(
                        md=md.format(note=note_text),
                        xml__xpath_exact=[(c.xpath, c.match)],
                        warnings_count=0,
                    )
