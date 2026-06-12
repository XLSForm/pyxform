from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.parameters import parse

from tests.pyxform_test_case import PyxformTestCase

# ( <description>, <input string>, <expected output dict> )
param_positive = [
    ("Single pair", "value=val", {"value": "val"}),
    ("Normalize keys to lowercase", "VALUE=val", {"value": "val"}),
    ("Preserve case for 'value' value", "value=VAL", {"value": "VAL"}),
    ("Preserve case for 'label' value", "label=Lb-L", {"label": "Lb-L"}),
    (
        "Normalize values to lowercase for non-case-sensitive keys",
        "other_key=VAL",
        {"other_key": "val"},
    ),
    (
        "Multiple pairs separated by space",
        "value=val label=lbl",
        {"value": "val", "label": "lbl"},
    ),
    (
        "Multiple pairs separated by comma",
        "value=val,label=lbl",
        {"value": "val", "label": "lbl"},
    ),
    (
        "Multiple pairs separated by semicolon",
        "value=val;label=lbl",
        {"value": "val", "label": "lbl"},
    ),
    (
        "Whitespace around delimiters and equals",
        "  value  =  val1  ,  label  =  lbl1  ",
        {"value": "val1", "label": "lbl1"},
    ),
    (
        "Whitespace around delimiters and equals - motivating case from pyxform/#812",
        "label = foo, value = bar",
        {"label": "foo", "value": "bar"},
    ),
    (
        "Special characters accepted in key or value",
        "value=*val3#",
        {"value": "*val3#"},
    ),
    (
        "Duplicate keys have last-write-wins dict behavior",
        "value=first value=second",
        {"value": "second"},
    ),
]

# ( <description>, <input string> )
param_negative = [
    ("Missing equals sign and value", "value"),
    ("Missing key before equals", "=val"),
    ("Missing value after equals", "value="),
    ("Whitespace only after equals", "value= "),
    ("Duplicate equals ", "value==val"),
    ("Key with no value assignment", "value=val label"),
    ("Spaces in values", "label=My Label"),
    ("Invalid delimiter", "value=val&label=Label"),
    ("No delimiter", "value=vallabel=Label"),
]


class TestParameterParser(PyxformTestCase):
    def test_parse__positive(self):
        """Should successfully parse structurally valid strings into matching dicts."""
        for description, case, expected in param_positive:
            with self.subTest(case=case, description=description):
                self.assertEqual(parse(case, row_number=1), expected)

    def test_parse__negative(self):
        """Should raise a PyXFormError for structurally invalid parameters."""
        for description, case in param_negative:
            with self.subTest(case=case, description=description):
                with self.assertRaises(PyXFormError) as err:
                    parse(case, row_number=1)
                self.assertEqual(err.exception.code, ErrorCode.SURVEY_004)

    def test_parse__empty_or_whitespace(self):
        """Should return an empty dict on empty or blank inputs."""
        for description, case in [
            ("Empty string", ""),
            ("Whitespace string", "    "),
        ]:
            with self.subTest(case=case, description=description):
                self.assertEqual(parse(case, row_number=1), {})
