from enum import Enum

from pyxform.parsing.expression import is_xml_tag, parse_expression

from tests.fixtures.lexer_cases import LexerCases
from tests.pyxform_test_case import PyxformTestCase

tag_positive = [
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

tag_negative = [
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
    ("name:.name", "Invalid character (in local name)"),
    ("-name:name", "Invalid character (in namespace)"),
    ("$name:@name", "Invalid character (in both names)"),
    ("name:name:name", "Invalid structure (multiple colons)"),
]


class ExpectedTokens(Enum):
    TEXT01 = (LexerCases.TEXT01, ("NAME",))
    TEXT02 = (LexerCases.TEXT02, ("NUMBER",))
    TEXT03 = (LexerCases.TEXT03, ("NAME",))
    TEXT04 = (LexerCases.TEXT04, ("URI_SCHEME", "NAME"))
    TEXT05 = (LexerCases.TEXT05, ("OPEN_PAREN", "URI_SCHEME", "NAME", "CLOSE_PAREN"))
    TEXT06 = (
        LexerCases.TEXT06,
        ("NAME", "WHITESPACE", "NAME", "WHITESPACE", "URI_SCHEME", "NAME"),
    )
    TEXT07 = (
        LexerCases.TEXT07,
        (
            "NAME",
            "WHITESPACE",
            "NAME",
            "WHITESPACE",
            "NAME",
            "OTHER",
            "WHITESPACE",
            "OTHER",
            "OTHER",
            "OTHER",
            "OTHER",
            "OTHER",
            "OTHER",
            "OTHER",
            "OTHER",
            "OTHER",
            "OPEN_PAREN",
            "CLOSE_PAREN",
            "NAME",
        ),
    )
    TEXT08 = (LexerCases.TEXT08, ("NAME", "OTHER"))
    TEXT09 = (LexerCases.TEXT09, ("NAME",))
    TEXT10 = (LexerCases.TEXT10, ("NAME",))
    TEXT11 = (LexerCases.TEXT11, ("SELF_REF", "PATH_SEP", "NAME"))

    DATETIME01 = (LexerCases.DATETIME01, ("DATE",))
    DATETIME02 = (LexerCases.DATETIME02, ("DATE",))
    DATETIME03 = (LexerCases.DATETIME03, ("TIME",))
    DATETIME04 = (LexerCases.DATETIME04, ("TIME",))
    DATETIME05 = (LexerCases.DATETIME05, ("TIME",))
    DATETIME06 = (LexerCases.DATETIME06, ("TIME",))
    DATETIME07 = (LexerCases.DATETIME07, ("TIME",))
    DATETIME08 = (LexerCases.DATETIME08, ("DATETIME",))
    DATETIME09 = (LexerCases.DATETIME09, ("DATETIME",))
    DATETIME10 = (LexerCases.DATETIME10, ("DATETIME",))
    DATETIME11 = (LexerCases.DATETIME11, ("DATETIME",))
    DATETIME12 = (LexerCases.DATETIME12, ("DATETIME",))

    GEO01 = (
        LexerCases.GEO01,
        (
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
        ),
    )
    GEO02 = (
        LexerCases.GEO02,
        (
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "OTHER",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
        ),
    )
    GEO03 = (
        LexerCases.GEO03,
        (
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "OTHER",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "OTHER",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "NUMBER",
        ),
    )

    DYNAMIC01 = (LexerCases.DYNAMIC01, ("FUNC_CALL", "CLOSE_PAREN"))
    DYNAMIC02 = (
        LexerCases.DYNAMIC02,
        (
            "FUNC_CALL",
            "SYSTEM_LITERAL",
            "COMMA",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "CLOSE_PAREN",
        ),
    )
    DYNAMIC03 = (
        LexerCases.DYNAMIC03,
        (
            "FUNC_CALL",
            "PARENT_REF",
            "PATH_SEP",
            "NAME",
            "COMMA",
            "WHITESPACE",
            "SELF_REF",
            "PATH_SEP",
            "NAME",
            "CLOSE_PAREN",
        ),
    )
    DYNAMIC04 = (LexerCases.DYNAMIC04, ("FUNC_CALL", "SYSTEM_LITERAL", "CLOSE_PAREN"))
    DYNAMIC05 = (
        LexerCases.DYNAMIC05,
        (
            "FUNC_CALL",
            "PARENT_REF",
            "PATH_SEP",
            "NAME",
            "WHITESPACE",
            "OPS_COMP",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "COMMA",
            "WHITESPACE",
            "NUMBER",
            "COMMA",
            "WHITESPACE",
            "NUMBER",
            "CLOSE_PAREN",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "FUNC_CALL",
            "NUMBER",
            "CLOSE_PAREN",
        ),
    )
    DYNAMIC06 = (
        LexerCases.DYNAMIC06,
        (
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "FUNC_CALL",
            "FUNC_CALL",
            "CLOSE_PAREN",
            "CLOSE_PAREN",
        ),
    )
    DYNAMIC07 = (
        LexerCases.DYNAMIC07,
        (
            "FUNC_CALL",
            "FUNC_CALL",
            "PARENT_REF",
            "PATH_SEP",
            "NAME",
            "WHITESPACE",
            "OPS_COMP",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "COMMA",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "COMMA",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "CLOSE_PAREN",
            "COMMA",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "CLOSE_PAREN",
        ),
    )
    DYNAMIC08 = (
        LexerCases.DYNAMIC08,
        ("NUMBER", "WHITESPACE", "OPS_MATH", "WHITESPACE", "NUMBER"),
    )
    DYNAMIC09 = (LexerCases.DYNAMIC09, ("NUMBER", "OPS_MATH", "NUMBER"))
    DYNAMIC10 = (LexerCases.DYNAMIC10, ("NUMBER", "OPS_MATH", "NUMBER"))
    DYNAMIC11 = (
        LexerCases.DYNAMIC11,
        (
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
        ),
    )
    DYNAMIC12 = (
        LexerCases.DYNAMIC12,
        (
            "NUMBER",
            "OPS_MATH",
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
        ),
    )
    DYNAMIC13 = (
        LexerCases.DYNAMIC13,
        (
            "FUNC_CALL",
            "CLOSE_PAREN",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
        ),
    )
    DYNAMIC14 = (
        LexerCases.DYNAMIC14,
        (
            "SELF_REF",
            "PATH_SEP",
            "NAME",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
        ),
    )
    DYNAMIC15 = (
        LexerCases.DYNAMIC15,
        (
            "PARENT_REF",
            "PATH_SEP",
            "NAME",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "SELF_REF",
            "PATH_SEP",
            "NAME",
        ),
    )
    DYNAMIC16 = (
        LexerCases.DYNAMIC16,
        (
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "OPS_MATH",
            "NUMBER",
            "OPS_MATH",
            "NUMBER",
        ),
    )
    DYNAMIC17 = (
        LexerCases.DYNAMIC17,
        (
            "FUNC_CALL",
            "SYSTEM_LITERAL",
            "COMMA",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "CLOSE_PAREN",
        ),
    )
    DYNAMIC18 = (LexerCases.DYNAMIC18, ("PYXFORM_REF",))
    DYNAMIC19 = (
        LexerCases.DYNAMIC19,
        ("PYXFORM_REF",),
    )
    DYNAMIC20 = (
        LexerCases.DYNAMIC20,
        ("PYXFORM_REF",),
    )
    DYNAMIC21 = (
        LexerCases.DYNAMIC21,
        (
            "FUNC_CALL",
            "PYXFORM_REF",
            "WHITESPACE",
            "OPS_COMP",
            "WHITESPACE",
            "SYSTEM_LITERAL",
            "COMMA",
            "WHITESPACE",
            "NUMBER",
            "COMMA",
            "WHITESPACE",
            "PYXFORM_REF",
            "WHITESPACE",
            "OPS_MATH",
            "WHITESPACE",
            "NUMBER",
            "CLOSE_PAREN",
        ),
    )


class TestExpression(PyxformTestCase):
    def test_is_xml_tag__positive(self):
        """Should accept positive match cases i.e. valid xml tag names."""
        for case, description in tag_positive:
            with self.subTest(case=case, description=description):
                self.assertTrue(is_xml_tag(case))

    def test_is_xml_tag__negative(self):
        """Should reject negative match cases i.e. invalid xml tag names."""
        for case, description in tag_negative:
            with self.subTest(case=case, description=description):
                self.assertFalse(is_xml_tag(case))

    def test_parse_expression(self):
        """Should find expected sequence of token types for each input."""
        for lexer_case, token_types in (i.value for i in ExpectedTokens):
            description, case = lexer_case.value
            with self.subTest(case=case, description=description):
                self.assertEqual(
                    token_types, tuple(t.type for t in parse_expression(text=case))
                )
