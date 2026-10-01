"""
## Delimited expression traceability.

Each test should reference one (or more) requirements from these lists.

- feature delimited expressions:
  - Validation
    - EDV01: an opening expression delimiter must have a matching closing delimiter.
    - EDV02: expressions must not be nested.
  - Behaviour
    - EDB01: delimited expression contents are wrapped in an XML <output/> element.
    - EDB02: whitespace in expression contents is preserved.
    - EDB03: text containing an expression is XML-escaped.
    - EDB04: escaped expression delimiters outside of an expression are unescaped.
    - EDB05: escaped expression delimiters inside of an expression are preserved.
    - EDB06: text containing an expression may contain multiple expressions.
    - EDB08: variable references inside an expression string are resolved to a XPath.
    - EDB10: variable references outside an expression are resolved and wrapped in an XML <output/> element.
    - EDB11: text strings shorter than 3 characters is returned unchanged.
    - EDB12: text without an (escaped) expression delimiter may be returned unchanged.
    - EDB13: text without an (escaped) expression may fallback to old `instance()` processing.
    - EDB14: backslashes and partial delimiter/escape sequences are preserved as text.
    - EDB15: expressions in survey translatable text/media columns are processed.
    - EDB16: expressions in choice translatable text/media are processed.
"""

from unittest import expectedFailure

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression_delimited import replace_with_output
from pyxform.question import InputQuestion
from pyxform.survey import Survey

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq

SURVEY = Survey(name="test_name")
Q1 = InputQuestion(name="q1", type="string")
Q2 = InputQuestion(name="q2", type="string")
PROXIMO = InputQuestion(name="próxiMO", type="string")
ELEMENT = InputQuestion(name="élémeNT", type="string")
SURVEY.add_children((Q1, Q2, PROXIMO, ELEMENT))
SURVEY.validate()

MD_SURVEY = """
| survey |
| | type | name    | label   |
| | text | q1      | {label} |
| | text | q2      | Q2      |
"""
MD_SURVEY_CHOICES = f"""
{MD_SURVEY}

| choices |
| | list_name | name | label |
| | c1        | n1   | N1    |
"""


class TestParsingErrors(PyxformTestCase):
    """Should raise an error when malformed expression template syntax is found."""

    def test_unclosed_template_with_trailing_content(self):
        """Unclosed template with trailing content."""
        # EDV01
        inp = "Total cost: {{ ${q1} * ${q2}"
        with self.assertRaises(PyXFormError):
            replace_with_output(inp, Q1, SURVEY)
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            errored=True,
            error__contains=[ErrorCode.INTERNAL_003.value.format(s=inp)],
        )

    def test_valid_template_followed_by_unclosed_template(self):
        """Valid template followed by unclosed template."""
        # EDV01
        inp = "User {{ ${q1} }} has pending {{ ${q2}"
        with self.assertRaises(PyXFormError):
            replace_with_output(inp, Q1, SURVEY)
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            errored=True,
            error__contains=[ErrorCode.INTERNAL_003.value.format(s=inp)],
        )

    def test_unclosed_expression_following_escaped_delimiter(self):
        """Unclosed template following escaped delimiter."""
        # EDV01
        inp = r"\{{ escaped \}} but {{ unclosed template"
        with self.assertRaises(PyXFormError):
            replace_with_output(inp, Q1, SURVEY)
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            errored=True,
            error__contains=[ErrorCode.INTERNAL_003.value.format(s=inp)],
        )

    def test_repeated_delimiters(self):
        """Doubled up delimiters inside expression."""
        # EDV01
        inp = "Value: {{{{ ${q1} }}}}"
        with self.assertRaises(PyXFormError):
            replace_with_output(inp, Q1, SURVEY)
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            errored=True,
            error__contains=[ErrorCode.INTERNAL_003.value.format(s=inp)],
        )

    def test_nested_delimiters_inside_expression(self):
        """Nested delimiters inside expression."""
        # EDV02
        inp = "Value: {{ {{ ${q1} }} }}"
        with self.assertRaises(PyXFormError):
            replace_with_output(inp, Q1, SURVEY)
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            errored=True,
            error__contains=[ErrorCode.INTERNAL_004.value.format(s=inp)],
        )


class TestOutputText(PyxformTestCase):
    """Should return unchanged text when no expression template is found."""

    def test_empty_string(self):
        """Should accept an empty string."""
        # EDB11 EDB12
        inp = ""
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        # Label required, so XPath assertion not testable.
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            errored=True,
            error__contains=["The survey element named 'q1' has no label or hint."],
        )

    def test_plain_text(self):
        """Should accept plain text."""
        # EDB12
        inp = "Welcome to the survey!"
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp})],
        )

    def test_multiline_text(self):
        """Should accept multiline text."""
        # EDB12
        inp = """Line 1\n  Line 2\twith tabs"""
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        ss_structure = {
            "survey_header": [{"type": None, "name": None, "label": None}],
            "survey": [
                {"type": "text", "name": "q1", "label": inp},
                {"type": "text", "name": "q2", "label": "Q2"},
            ],
        }
        self.assertPyxformXform(
            ss_structure=ss_structure,
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {"Line 1\n Line 2\twith tabs"})
            ],
        )

    def test_variable_references(self):
        """Should accept variable references."""
        # EDB10
        inp = "Hello ${q1}, your score is ${q2}."
        expected = """Hello <output value=" /test_name/q1 "/>, your score is <output value=" /test_name/q2 "/>."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Hello ", ", your score is ", ". "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/q1 ", " /test_name/q2 "},
                ),
            ],
        )

    def test_single_delimiter_tokens(self):
        """Should ignore single delimiter tokens."""
        # EDB12 EDB14
        inp = "Item costs $10 or {5} credits."
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp})],
        )

    def test_unclosed_opening_delimiter(self):
        """Should ignore unclosed opening delimiter."""
        # EDB11 EDB12 EDB14
        inp = "{{"
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp})],
        )

    def test_unmatched_closing_delimiter(self):
        """Should ignore unmatched closing delimiter."""
        # EDB12 EDB14
        inp = "Unmatched closing delimiter }} kept as text."
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp})],
        )

    def test_file_path_or_single_backslash(self):
        """Should ignore file paths or single backslash."""
        # EDB12 EDB14
        inp = r"C:\Users\test\file.txt \ "
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp.strip()})],
        )

    def test_partial_escape_sequence(self):
        """Should ignore partial escape sequences."""
        # EDB12 EDB14
        inp = r"\{ escaped \} but \\"
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp})],
        )


class TestOutputBasicExpressions(PyxformTestCase):
    """Should replace {{ expr }} content wrapped in an <output/> element."""

    def test_no_surrounding_text(self):
        """Should accept an expression with no surrounding text."""
        # EDB01 EDB02
        inp = "{{ 1 + 1 }}"
        expected = '<output value=" 1 + 1 "/>'
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_output_value("q1"), {" 1 + 1 "})],
        )

    def test_adjacent_templates(self):
        """Should accept adjacent templates."""
        # EDB01 EDB02 EDB06
        inp = "{{ 1 + 1 }}{{ 2 + 2 }}"
        expected = '<output value=" 1 + 1 "/><output value=" 2 + 2 "/>'
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_output_value("q1"),
                    {" 1 + 1 ", " 2 + 2 "},
                )
            ],
        )

    def test_empty_template(self):
        """Should accept an empty template."""
        # EDB01
        inp = "Empty: {{}}"
        expected = 'Empty: <output value=""/>'
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Empty: ", " "}),
                (xpq.body_input_label_output_value("q1"), {""}),
            ],
        )

    def test_no_inner_spaces(self):
        """Should accept expressions with no spaces inside the delimiters."""
        # EDB01
        inp = "Value: {{today()}}"
        expected = 'Value: <output value="today()"/>'
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Value: ", " "}),
                (xpq.body_input_label_output_value("q1"), {"today()"}),
            ],
        )

    def test_inner_spaces_not_stripped(self):
        """Should accept but not strip spaces inside expression delimiters."""
        # EDB01 EDB02
        inp = "Value: {{   count(/data/item)   }}"
        expected = 'Value: <output value="   count(/data/item)   "/>'
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Value: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" count(/data/item) "},
                ),
            ],
        )

    def test_expression_xpath_preserved(self):
        """Should accept and preserve XPath expressions."""
        # EDB01
        inp = "Selected item: {{ instance('cities')/root/item[id = 1]/name }}"
        expected = """Selected item: <output value=" instance('cities')/root/item[id = 1]/name "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Selected item: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" instance('cities')/root/item[id = 1]/name "},
                ),
            ],
        )

    def test_multiline_expression_with_internal_whitespace(self):
        """Should accept multiline expression with internal whitespace."""
        # EDB01 EDB02 EDB03 EDB08
        inp = "Result: {{\n  if(\n    ${q1} >= 18,\n    'Adult',\n    'Minor'\n  )\n}}"
        expected = """Result: <output value="\n  if(\n     /test_name/q1  &gt;= 18,\n    'Adult',\n    'Minor'\n  )\n"/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        ss_structure = {
            "survey_header": [{"type": None, "name": None, "label": None}],
            "survey": [
                {"type": "text", "name": "q1", "label": inp},
                {"type": "text", "name": "q2", "label": "Q2"},
            ],
        }
        self.assertPyxformXform(
            ss_structure=ss_structure,
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Result: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"  if(   /test_name/q1  &gt;= 18,  'Adult',  'Minor'  ) "},
                ),
            ],
        )


class TestOutputVariableResolution(PyxformTestCase):
    """Should resolve ${} variable references found inside the expression template."""

    def test_single_variable(self):
        """Should accept single variable reference."""
        # EDB01 EDB08
        inp = "Value: {{${q1}}}"
        expected = """Value: <output value=" /test_name/q1 "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Value: ", " "}),
                (xpq.body_input_label_output_value("q1"), {" /test_name/q1 "}),
            ],
        )

    def test_repeated_variable(self):
        """Should accept repeated variable references."""
        # EDB01 EDB02 EDB08
        inp = "Double: {{ ${q1} + ${q1} }}"
        expected = """Double: <output value="  /test_name/q1  +  /test_name/q1  "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Double: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"  /test_name/q1  +  /test_name/q1  "},
                ),
            ],
        )

    def test_multiple_different_variables(self):
        """Should accept multiple different variable references."""
        # EDB01 EDB02 EDB08
        inp = "Total cost: {{ ${q1} * ${q2} }} USD"
        expected = (
            """Total cost: <output value="  /test_name/q1  *  /test_name/q2  "/> USD"""
        )
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Total cost: ", " USD "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"  /test_name/q1  *  /test_name/q2  "},
                ),
            ],
        )

    def test_variable_inside_and_outside(self):
        """Should accept variable references inside and outside expression."""
        # EDB01 EDB02 EDB08 EDB10
        inp = "User ${q1}, your total is {{ ${q1} * 2 }}."
        expected = """User <output value=" /test_name/q1 "/>, your total is <output value="  /test_name/q1  * 2 "/>."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" User ", ", your total is ", ". "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/q1 ", "  /test_name/q1  * 2 "},
                ),
            ],
        )

    def test_unicode_ncname_variable_references(self):
        """Should accept variable references with a unicode NCName."""
        # EDB01 EDB02 EDB08 EDB10
        inp = "Hola ${próxiMO}, total: {{ ${élémeNT} + 1 }}"
        expected = """Hola <output value=" /test_name/próxiMO "/>, total: <output value="  /test_name/élémeNT  + 1 "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        md_extra = """
        | | text | próxiMO | PróxiMO |
        | | text | élémeNT | ÉlémeNT |
        """
        self.assertPyxformXform(
            md=(MD_SURVEY + md_extra).format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Hola ", ", total: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/próxiMO ", "  /test_name/élémeNT  + 1 "},
                ),
            ],
        )

    def test_last_saved_variables(self):
        """Should accept last-saved variable references."""
        # EDB01 EDB02 EDB08 EDB10
        inp = "Previous: ${last-saved#q1}, Calculated: {{ ${last-saved#q2} * 1.1 }}"
        expected = """Previous: <output value=" instance('__last-saved')/test_name/q1 "/>, Calculated: <output value="  instance('__last-saved')/test_name/q2  * 1.1 "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" Previous: ", ", Calculated: ", " "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {
                        " instance('__last-saved')/test_name/q1 ",
                        "  instance('__last-saved')/test_name/q2  * 1.1 ",
                    },
                ),
            ],
        )

    def test_adjacent_variables(self):
        """Should accept adjacent variable references."""
        # EDB01 EDB02 EDB08 EDB10
        inp = "${q1}{{ ${q1} * ${q2} }}${q2}"
        expected = """<output value=" /test_name/q1 "/><output value="  /test_name/q1  *  /test_name/q2  "/><output value=" /test_name/q2 "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {"\n      ", "\n        "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {
                        " /test_name/q1 ",
                        "  /test_name/q1  *  /test_name/q2  ",
                        " /test_name/q2 ",
                    },
                ),
            ],
        )


class TestOutputXpathExpressions(PyxformTestCase):
    """Should replace {{ expr }} content wrapped in an <output/> element."""

    def test_function_with_variable(self):
        """Should accept function with variable references."""
        # EDB01 EDB02 EDB08
        inp = "Welcome {{ coalesce(upper-case(${q1}), 'Guest') }}!"
        expected = """Welcome <output value=" coalesce(upper-case( /test_name/q1 ), 'Guest') "/>!"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Welcome ", "! "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" coalesce(upper-case( /test_name/q1 ), 'Guest') "},
                ),
            ],
        )

    def test_operator_escaping(self):
        """Should escape XML characters."""
        # EDB01 EDB02 EDB03 EDB08
        inp = "Valid: {{ ${q1} < 10 and ${q2} <= 20 }}"
        expected = """Valid: <output value="  /test_name/q1  &lt; 10 and  /test_name/q2  &lt;= 20 "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Valid: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"  /test_name/q1  &lt; 10 and  /test_name/q2  &lt;= 20 "},
                ),
            ],
        )

    def test_literal_ampersand_escaping(self):
        """Should escape XML characters."""
        # EDB01 EDB02 EDB03 EDB08
        inp = "Menu: {{ concat('Fish & Chips: ', ${q1}) }}"
        expected = (
            """Menu: <output value=" concat('Fish &amp; Chips: ',  /test_name/q1 ) "/>"""
        )
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Menu: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" concat('Fish &amp; Chips: ',  /test_name/q1 ) "},
                ),
            ],
        )

    def test_secondary_instance_lookup_with_predicate_filtering(self):
        """Should accept secondary instance lookups with predicate filtering."""
        # EDB01 EDB02 EDB08
        inp = "Facility: {{ instance('facilities')/root/item[id=${q1}]/label }}"
        expected = """Facility: <output value=" instance('facilities')/root/item[id= /test_name/q1 ]/label "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Facility: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" instance('facilities')/root/item[id= /test_name/q1 ]/label "},
                ),
            ],
        )

    def test_complex_nested_functions_with_operators_and_variable_references(self):
        """Should accept complex nested functions with operators and variable references."""
        # EDB01 EDB02 EDB03 EDB08
        inp = "Score: {{ if(${q1} >= 80, concat('PASS: ', round(${q1} * 1.1, 2), '%'), if(${q1} >= 50, 'RETRY', 'FAIL')) }}"
        expected = """Score: <output value=" if( /test_name/q1  &gt;= 80, concat('PASS: ', round( /test_name/q1  * 1.1, 2), '%'), if( /test_name/q1  &gt;= 50, 'RETRY', 'FAIL')) "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Score: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {
                        """ if( /test_name/q1  &gt;= 80, concat('PASS: ', round( /test_name/q1  * 1.1, 2), '%'), if( /test_name/q1  &gt;= 50, 'RETRY', 'FAIL')) """
                    },
                ),
            ],
        )

    def test_date_formatting_string(self):
        """Should accept and preserve date formatting specifiers."""
        # EDB01 EDB02 EDB08
        inp = "Visit scheduled for {{ format-date(${q1}, '%A, %b %e, %Y') }}."
        expected = """Visit scheduled for <output value=" format-date( /test_name/q1 , '%A, %b %e, %Y') "/>."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Visit scheduled for ", ". "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" format-date( /test_name/q1 , '%A, %b %e, %Y') "},
                ),
            ],
        )

    def test_indexed_repeat_lookup(self):
        """Should accept indexed repeat lookups."""
        # EDB01 EDB02 EDB08
        inp = "Primary Contact: {{ indexed-repeat(${q1}, ${q2}, 1) }}"
        expected = """Primary Contact: <output value=" indexed-repeat( /test_name/q1 ,  /test_name/q2 , 1) "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Primary Contact: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" indexed-repeat( /test_name/q1 ,  /test_name/q2 , 1) "},
                ),
            ],
        )

    def test_multiple_expressions(self):
        """Should accept multiple expressions and emit each in output elements."""
        # EDB01 EDB02 EDB06 EDB08
        # pyxform/#844 alternative strategy with new feature.
        inp = """Thing's label: {{instance('c1')/root/item[name=${q1} or true()]/label}} Thing's denomination: {{instance('c1')/root/item[name=${q1}]/denomination}} and more stuff."""
        expected = """Thing's label: <output value="instance('c1')/root/item[name= /test_name/q1  or true()]/label"/> Thing's denomination: <output value="instance('c1')/root/item[name= /test_name/q1 ]/denomination"/> and more stuff."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {
                        " Thing's label: ",
                        " Thing's denomination: ",
                        " and more stuff. ",
                    },
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {
                        "instance('c1')/root/item[name= /test_name/q1  or true()]/label",
                        "instance('c1')/root/item[name= /test_name/q1 ]/denomination",
                    },
                ),
            ],
        )


class TestOutputDelimiterEscaping(PyxformTestCase):
    """Should detect and resolve escaped delimiters when an expression template is found."""

    def test_escaped_delimiters(self):
        """Should accept escaped delimiters."""
        # EDB04 EDB10
        inp = r"Literal \{{ ${q1} \}} display."
        expected = """Literal {{ <output value=" /test_name/q1 "/> }} display."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" Literal {{ ", " }} display. "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/q1 "},
                ),
            ],
        )

    def test_escaped_closing_delimiter_outside_expression(self):
        """Should accept escaped closing delimiter outside an expression."""
        # EDB04
        inp = r"Hello \}} there"
        expected = """Hello }} there"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_escaped_opening_delimiter_outside_expression(self):
        """Should accept escaped opening delimiter outside an expression."""
        # EDB04
        inp = r"Hello \{{ there"
        expected = r"Hello {{ there"
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_escaped_closing_delimiter_inside_expression(self):
        """Should accept escaped closing delimiter inside an expression."""
        # EDB01 EDB05
        inp = r"Result: {{ concat('foo', '\}}') }}"
        expected = """Result: <output value=" concat('foo', '}}') "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Result: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" concat('foo', '}}') "},
                ),
            ],
        )

    def test_escaped_opening_delimiter_inside_expression(self):
        """Should accept escaped opening delimiter inside an expression."""
        # EDB01 EDB05 EDB08
        inp = r"Result: {{ concat('\{{', ${q1}) }}"
        expected = """Result: <output value=" concat('{{',  /test_name/q1 ) "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Result: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" concat('{{',  /test_name/q1 ) "},
                ),
            ],
        )

    def test_escaped_delimiter_with_expression(self):
        """Should accept string with escaped an unescaped delimiters."""
        # EDB01 EDB04 EDB08 EDB10
        inp = r"User ${q1}: \{{ literal \}} evaluates to {{ ${q2} * 100 }}%"
        expected = """User <output value=" /test_name/q1 "/>: {{ literal }} evaluates to <output value="  /test_name/q2  * 100 "/>%"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" User ", ": {{ literal }} evaluates to ", "% "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/q1 ", "  /test_name/q2  * 100 "},
                ),
            ],
        )

    def test_adjacent_escaped_delimiters(self):
        """Should ignore adjacent escaped delimiters."""
        # EDB04
        inp = r"\{{\{{\}}\}}"
        expected = r"{{{{}}}}"
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_double_escaped_delimiters(self):
        """Should ignore double-escaped delimiters."""
        # EDB04
        inp = r"\\{{\\}}"
        expected = r"\{{\}}"
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_escaped_delimiters_multiline(self):
        """Should ignore escaped delimiters in multi-line strings."""
        # EDB04
        inp = "Line 1: \\{{\nLine 2: \\}}"
        expected = "Line 1: {{\nLine 2: }}"
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        ss_structure = {
            "survey_header": [{"type": None, "name": None, "label": None}],
            "survey": [
                {"type": "text", "name": "q1", "label": inp},
                {"type": "text", "name": "q2", "label": "Q2"},
            ],
        }
        self.assertPyxformXform(
            ss_structure=ss_structure,
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_escaped_delimiters_adjacent_variable_references(self):
        """Should ignore escaped delimiters adjacent to variable references."""
        # EDB04 EDB10
        inp = r"${q1}\{{ ${q2} \}}${q1}"
        expected = """<output value=" /test_name/q1 "/>{{ <output value=" /test_name/q2 "/> }}<output value=" /test_name/q1 "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {"{{ ", " }}", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/q1 ", " /test_name/q2 "},
                ),
            ],
        )


class TestOutputDelimiterAmbiguity(PyxformTestCase):
    """Should preserve single delimiter token sequences."""

    def test_single_delimiter_tokens_in_expression_in_single_quotes(self):
        """Should ignore single delimiter tokens in single quotes in an expression."""
        # EDB01 EDB08 EDB14
        inp = "Output: {{ concat('Val: $', ${q1}, ' {tax incl.}') }}"
        expected = """Output: <output value=" concat('Val: $',  /test_name/q1 , ' {tax incl.}') "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Output: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" concat('Val: $',  /test_name/q1 , ' {tax incl.}') "},
                ),
            ],
        )

    def test_single_delimiter_tokens_in_expression_in_double_quotes(self):
        """Should ignore single delimiter tokens in double quotes in an expression."""
        # EDB01 EDB03 EDB08 EDB14
        inp = 'Output: {{ concat("Val: $", ${q1}, " {tax incl.}") }}'
        expected = """Output: <output value=" concat(&quot;Val: $&quot;,  /test_name/q1 , &quot; {tax incl.}&quot;) "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Output: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {""" concat("Val: $",  /test_name/q1 , " {tax incl.}") """},
                ),
            ],
        )

    def test_single_delimiter_tokens_in_expression_in_xpath(self):
        """Should ignore single delimiter tokens in XPath in an expression."""
        # EDB01 EDB03 EDB08 EDB14
        inp = "Data: {{ instance('items')/root/item[code = 'x}y' and ${q1} > 0]/name }}"
        expected = """Data: <output value=" instance('items')/root/item[code = 'x}y' and  /test_name/q1  &gt; 0]/name "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Data: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {
                        " instance('items')/root/item[code = 'x}y' and  /test_name/q1  &gt; 0]/name "
                    },
                ),
            ],
        )

    def test_triple_delimiter_tokens(self):
        """Should ignore extra delimiter tokens and accept outer pair of delimiter tokens."""
        # EDB01 EDB08 EDB14
        inp = "Triple open: {{{ ${q1} }}}"
        expected = 'Triple open: <output value="{  /test_name/q1  }"/>'
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Triple open: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"{  /test_name/q1  }"},
                ),
            ],
        )

    def test_triple_closing_delimiter(self):
        """Should ignore extra delimiter token and accept outer closing delimiter."""
        # EDB01 EDB08 EDB14
        inp = "Triple close: {{ ${q1} }}}"
        expected = """Triple close: <output value="  /test_name/q1  }"/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Triple close: ", " "}),
                (xpq.body_input_label_output_value("q1"), {"  /test_name/q1  }"}),
            ],
        )

    def test_extra_closing_delimiter_near_expression_end(self):
        """Should ignore single quote near accepted closing delimiter."""
        # EDB01 EDB08 EDB14
        inp = "Ending brace: {{ concat(${q1}, '}') }}"
        expected = """Ending brace: <output value=" concat( /test_name/q1 , '}') "/>"""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Ending brace: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" concat( /test_name/q1 , '}') "},
                ),
            ],
        )

    def test_backlash_inside_expression(self):
        """Should ignore backslash inside expression not adjacent to delimiter."""
        # EDB01 EDB08 EDB14
        inp = r"Path: {{ concat('C:\temp\node', ${q1}) }}"
        expected = (
            r"""Path: <output value=" concat('C:\temp\node',  /test_name/q1 ) "/>"""
        )
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY.format(label=inp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Path: ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    {r" concat('C:\temp\node',  /test_name/q1 ) "},
                ),
            ],
        )


class TestOutputFallbackInstanceExpression(PyxformTestCase):
    """Should attempt to process `instance()` expressions if no expression delimiter found."""

    def test_ignored_when__delimited_expression(self):
        """Should ignore instance() in text adjacent to delimited expression."""
        # EDB01 EDB13
        inp = "Lookup {{instance('c1')/root/item[./text() = 'OK!']}} instance('c1')/root/item[./text() = 'OK!'] ."
        expected = """Lookup <output value="instance('c1')/root/item[./text() = 'OK!']"/> instance('c1')/root/item[./text() = 'OK!'] ."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" Lookup ", " instance('c1')/root/item[./text() = 'OK!'] . "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"instance('c1')/root/item[./text() = 'OK!']"},
                ),
            ],
        )

    def test_ignored_when__escaped_opening_delimiter(self):
        """Should ignore instance() in text adjacent to escaped expression opening delimiter."""
        # EDB04 EDB13
        inp = r"Lookup \{{ instance('c1')/root/item[./text() = 'OK!'] ."
        expected = """Lookup {{ instance('c1')/root/item[./text() = 'OK!'] ."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_ignored_when__escaped_closing_delimiter(self):
        """Should ignore instance() in text adjacent to escaped expression closing delimiter."""
        # EDB04 EDB13
        inp = r"Lookup \}} instance('c1')/root/item[./text() = 'OK!'] ."
        expected = """Lookup }} instance('c1')/root/item[./text() = 'OK!'] ."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {expected})],
        )

    def test_instance_expression(self):
        """Should process instance() with no other <output/> triggers present."""
        # EDB13
        inp = "Lookup instance('c1')/root/item[./text() = 'OK!'] ."
        expected = (
            """Lookup <output value="instance('c1')/root/item[./text() = 'OK!']"/> ."""
        )
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" Lookup ", " . "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"instance('c1')/root/item[./text() = 'OK!']"},
                ),
            ],
        )

    def test_instance_expression_adjacent_to_variable_reference(self):
        """Should process instance() with variable reference adjacent to the expression."""
        # EDB10 EDB13
        inp = "Lookup ${q2} instance('c1')/root/item[./text() = 'OK!'] ."
        expected = """Lookup <output value=" /test_name/q2 "/> <output value="instance('c1')/root/item[./text() = 'OK!']"/> ."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" Lookup ", " ", " . "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {" /test_name/q2 ", "instance('c1')/root/item[./text() = 'OK!']"},
                ),
            ],
        )

    def test_instance_expression_containing_variable_reference(self):
        """Should process instance() with variable reference inside of the expression."""
        # EDB10 EDB13
        inp = "Lookup instance('c1')/root/item[${q2} = 'OK!'] ."
        expected = """Lookup <output value="instance('c1')/root/item[ /test_name/q2  = 'OK!']"/> ."""
        self.assertEqual(expected, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[
                (
                    xpq.body_input_label_text("q1"),
                    {" Lookup ", " . "},
                ),
                (
                    xpq.body_input_label_output_value("q1"),
                    {"instance('c1')/root/item[ /test_name/q2  = 'OK!']"},
                ),
            ],
        )

    def test_no_processing(self):
        """Should not modify text with no <output/> triggers present."""
        # EDB12
        inp = "Lookup at the sky."
        self.assertEqual(inp, replace_with_output(inp, Q1, SURVEY))
        self.assertPyxformXform(
            md=MD_SURVEY_CHOICES.format(label=inp),
            xml__xpath_exact=[(xpq.body_input_label_text("q1"), {inp})],
        )


class TestOutputSupportedColumns(PyxformTestCase):
    """
    Should allow expression usage in all translatable text/media columns.

    For the media columns, the `jr://` prefix makes the test cases look strange but there
    probably are meaningful use cases for dynamically setting the image name.
    """

    def setUp(self):
        # Test expression with a delimited expression, and variable refs inside and out.
        self.exp = "Test q1 ${q1}: {{ ${q1} + 1}}"
        # Expected contents of the corresponding <output/> elements @value attribute.
        self.outputs = {" /test_name/q1 ", "  /test_name/q1  + 1"}

    def test_survey_label_default(self):
        """Should emit the processed label in the body control."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (xpq.body_input_label_text("q1"), {" Test q1 ", ": ", " "}),
                (
                    xpq.body_input_label_output_value("q1"),
                    self.outputs,
                ),
            ],
        )

    def test_survey_hint_default(self):
        """Should emit the processed hint in the body control."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | hint  |
        | | text | q1   | Q1    | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    """/h:html/h:body/x:input[@ref='/test_name/q1']/x:hint/text()""",
                    {" Test q1 ", ": ", " "},
                ),
                (
                    """/h:html/h:body/x:input[@ref='/test_name/q1']/x:hint/x:output/@value""",
                    self.outputs,
                ),
            ],
        )

    def test_survey_label_itext(self):
        """Should emit the processed label in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label::English (en) |
        | | text | q1   | {exp}               |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "English (en)", "label", "/text()"),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "English (en)", "label", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_hint_itext(self):
        """Should emit the processed hint in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | hint::English (en) |
        | | text | q1   | Q1    | {exp}              |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "English (en)", "hint", "/text()"),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "English (en)", "hint", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_guidance_hint(self):
        """Should emit the processed guidance hint in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | guidance_hint |
        | | text | q1   | Q1    | {exp}         |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "default", "guidance", "/text()"),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "guidance", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_constraint_message(self):
        """Should emit the processed constraint message in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | constraint    | constraint_message |
        | | text | q1   | Q1    | length(.) > 0 | {exp}              |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "constraint_msg", "/text()"
                    ),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "constraint_msg", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_required_message(self):
        """Should emit the processed required message in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | required_message |
        | | text | q1   | Q1    | {exp}            |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "required_msg", "/text()"
                    ),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "required_msg", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_image(self):
        """Should emit the processed image file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | image |
        | | text | q1   | Q1    | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "default", "image", "/text()"),
                    {" jr://images/Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "image", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_big_image(self):
        """Should emit the processed big-image file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | image  | big-image |
        | | text | q1   | Q1    | q1.png | {exp}     |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "default", "big-image", "/text()"),
                    {" jr://images/Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "big-image", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_audio(self):
        """Should emit the processed audio file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | audio |
        | | text | q1   | Q1    | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "default", "audio", "/text()"),
                    {" jr://audio/Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "audio", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_survey_video(self):
        """Should emit the processed video file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB15
        md = """
        | survey |
        | | type | name | label | video |
        | | text | q1   | Q1    | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpq.model_itext_form_value("q1", "default", "video", "/text()"),
                    {" jr://video/Test q1 ", ": ", " "},
                ),
                (
                    xpq.model_itext_form_value(
                        "q1", "default", "video", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_choice_label_default(self):
        """Should emit the processed label in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value("c1-0", "default", "label", "/text()"),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "default", "label", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_choice_label_itext(self):
        """Should emit the processed label in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | label::English (en) |
        | | c1        | n1   | {exp}               |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value(
                        "c1-0", "English (en)", "label", "/text()"
                    ),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "English (en)", "label", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_choice_image(self):
        """Should emit the processed image file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | image |
        | | c1        | n1   | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value("c1-0", "default", "image", "/text()"),
                    {" jr://images/Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "default", "image", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_choice_big_image(self):
        """Should emit the processed big-image file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | image  | big-image |
        | | c1        | n1   | n1.png | {exp}     |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value("c1-0", "default", "big-image", "/text()"),
                    {" jr://images/Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "default", "big-image", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_choice_audio(self):
        """Should emit the processed audio file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | audio |
        | | c1        | n1   | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value("c1-0", "default", "audio", "/text()"),
                    {" jr://audio/Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "default", "audio", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    def test_choice_video(self):
        """Should emit the processed video file name in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | video |
        | | c1        | n1   | {exp} |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value("c1-0", "default", "video", "/text()"),
                    {" jr://video/Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "default", "video", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )

    # Not (yet?) supported: `geometry` is not placed in itext and not translatable.
    @expectedFailure
    def test_choice_geometry(self):
        """Should emit the processed geometry value in the model itext."""
        # EDB01 EDB08 EDB10 EDB16
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | choices |
        | | list_name | name | geometry |
        | | c1        | n1   | {exp}    |
        """
        self.assertPyxformXform(
            md=md.format(exp=self.exp),
            xml__xpath_exact=[
                (
                    xpc.model_itext_form_value("c1-0", "default", "geometry", "/text()"),
                    {" Test q1 ", ": ", " "},
                ),
                (
                    xpc.model_itext_form_value(
                        "c1-0", "default", "geometry", "/x:output/@value"
                    ),
                    self.outputs,
                ),
            ],
        )
