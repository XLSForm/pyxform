from pyxform.parsing.expression import is_xml_tag

from tests.pyxform_test_case import PyxformTestCase

positive = [
    ("A", "Single uppercase letter"),
    ("ab", "Lowercase letters"),
    ("_u", "Leading underscore"),
    ("A12", "Leading uppercase letter with digit"),
    ("A-1.23", "Leading uppercase letter with hyphen, period, and digit"),
    ("Name123-456", "Mixed case, digits, hyphen"),
    ("𐐀n", "Leading unicode"),
    ("Αλ", "Following unicode"),
    ("name:name", "NCName, colon, NCName"),
    ("name_with_colon:_and_extras", "NCName, colon, NCName (non-letter characters)"),
    # Other special character tokens are excluded by ncname_regex.
    ("nameor", "Contains another parser token (or)"),
    ("nameand", "Contains another parser token (and)"),
    ("namemod", "Contains another parser token (mod)"),
    ("namediv", "Contains another parser token (div)"),
]

negative = [
    ("", "Empty string"),
    (" ", "Space"),
    ("123name", "Leading digit"),
    ("-name", "Leading hyphen"),
    (".name", "Leading period"),
    (":name", "Leading colon"),
    ("name$", "Invalid character ($)"),
    ("name with space", "Invalid character (space)"),
    ("na@me", "Invalid character (@)"),
    ("na#me", "Invalid character (#)"),
    ("name:name:name", "Invalid structure (multiple colons)"),
]


class TestExpression(PyxformTestCase):
    def test_is_xml_tag__positive(self):
        """Should accept positive match cases i.e. valid xml tag names."""
        for case, description in positive:
            with self.subTest(case=case, description=description):
                self.assertTrue(is_xml_tag(case))

    def test_is_xml_tag__negative(self):
        """Should reject negative match cases i.e. invalid xml tag names."""
        for case, description in negative:
            with self.subTest(case=case, description=description):
                self.assertFalse(is_xml_tag(case))
