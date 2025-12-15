import re
from functools import lru_cache
from typing import Any

from lark import Lark, Token

# ncname regex adapted from eulxml https://github.com/emory-libraries/eulxml/blob/2e1a9f71ffd1fd455bd8326ec82125e333b352e0/eulxml/xpath/lexrules.py
# (C) 2010,2011 Emory University Libraries [Apache v2.0 License]
# They in turn adapted it from https://www.w3.org/TR/REC-xml/#NT-NameStartChar
# and https://www.w3.org/TR/REC-xml-names/#NT-NCName
namestartchar = (
    r"(?:[A-Z]|_|[a-z]|\xc0-\xd6]|[\xd8-\xf6]|[\xf8-\u02ff]|"
    + r"[\u0370-\u037d]|[\u037f-\u1fff]|[\u200c-\u200d]|[\u2070-\u218f]|"
    + r"[\u2c00-\u2fef]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]"
    + r"|[\U00010000-\U000EFFFF])"
)
# additional characters allowed in NCNames after the first character
namechar_extra = r"[-.0-9\xb7\u0300-\u036f\u203f-\u2040]"
ncname_regex = rf"{namestartchar}(?:{namestartchar}|{namechar_extra})*"
ncname_regex_named = rf"(?P<ncname>{ncname_regex})"
# namespaced ncname
ncname_regex_ns = rf"{ncname_regex}(?:\:{ncname_regex})?"
ncname_regex_ns_named = rf"(?P<ncname_ns>{ncname_regex_ns})"

# pyxform_ref_outer picks up possible refs, and matches unterminated refs to exclude them.
pyxform_ref_outer = r"\$\{(?P<pyxform_ref>[^}]+)\}|\$\{[^}]*$"
pyxform_ref_inner = rf"(?P<last_saved>last-saved#)?{ncname_regex_named}"
pyxform_ref_inner_last_saved_required = (
    rf"(?P<last_saved>last-saved#){ncname_regex_named}"
)
pyxform_ref = rf"(?P<pyxform_ref>\$\{{{pyxform_ref_inner}\}})"

lark_grammar = rf"""
    // Parser
    start: (token | WHITESPACE)*
    ?token: DATETIME
          | DATE
          | TIME
          | NUMBER
          | OPS_MATH
          | OPS_COMP
          | OPS_BOOL
          | OPS_UNION
          | OPEN_PAREN
          | CLOSE_PAREN
          | BRACKET
          | PARENT_REF
          | SELF_REF
          | PATH_SEP
          | SYSTEM_LITERAL
          | COMMA
          | PYXFORM_REF
          | FUNC_CALL
          | XPATH_PRED_START
          | XPATH_PRED_END
          | URI_SCHEME
          | NAME
          | PYXFORM_REF_START
          | PYXFORM_REF_END
          | OTHER

    // Lexer
    // https://www.w3.org/TR/xmlschema-2/#dateTime
    DATETIME.25: DATE "T" TIME
    DATE.24: /-?\d{{4}}-\d{{2}}-\d{{2}}/
    TIME.23: /\d{{2}}:\d{{2}}:\d{{2}}(\.\s+)?(((\+|\-)\d{{2}}:\d{{2}})|Z)?/
    NUMBER.22: /-?\d+\.\d*|-?\.\d+|-?\d+/
    // https://www.w3.org/TR/1999/REC-xpath-19991116/#exprlex
    OPS_MATH.21: /[\*\+\-]| mod | div /
    OPS_COMP.20: /\=|\!\=|\<|\>|\<=|>=/
    OPS_BOOL.19: / and | or /
    OPS_UNION.18: /\|/
    OPEN_PAREN.17: /\(/
    CLOSE_PAREN.16: /\)/
    BRACKET.15: /[\[\{{\}}]/
    PARENT_REF.14: /\.\./
    SELF_REF.13: /\./\
    // # javarosa.xpath says "//" is an "unsupported construct".
    PATH_SEP.12: /\//
    SYSTEM_LITERAL.11: /"[^"]*"|'[^']*'/
    COMMA.10: /,/
    WHITESPACE.9: /\s+/
    PYXFORM_REF.8: /\$\{{(?:last-saved#)?{ncname_regex}\}}/
    FUNC_CALL.7: /{ncname_regex_ns}\(/
    XPATH_PRED_START.6: /{ncname_regex_ns}\[/
    XPATH_PRED_END.5: /\]/
    URI_SCHEME.4: /{ncname_regex}:\/\//
    // Must be lower priority than rules containing ncname_regex.
    NAME.3: /{ncname_regex_ns}/
    PYXFORM_REF_START.2: /\$\{{/
    PYXFORM_REF_END.1: /\}}/\
    // Catch any other character so that parsing doesn't stop.
    OTHER.0: /.+?/\
"""

RE_NCNAME_NAMESPACED = re.compile(ncname_regex_ns_named)
RE_PYXFORM_REF = re.compile(pyxform_ref)
RE_PYXFORM_REF_OUTER = re.compile(pyxform_ref_outer)
RE_PYXFORM_REF_INNER = re.compile(pyxform_ref_inner)


_EXPRESSION_LEXER = Lark(
    lark_grammar, parser="lalr", start="start", propagate_positions=True
)


@lru_cache(maxsize=128)
def parse_expression(text: str) -> tuple[Token, ...]:
    """
    Parse an expression.

    Use this function instead of _EXPRESSION_LEXER to take advantage of caching.

    :param text: The expression.
    :return: The parsed tokens, and any remaining unparsed text.
    """
    return tuple(_EXPRESSION_LEXER.lex(text))


def is_xml_tag(value: str) -> bool:
    """
    Does the input string contain only a valid XML tag / element name?
    """
    return value and bool(RE_NCNAME_NAMESPACED.fullmatch(value))


def maybe_strip(value: Any) -> Any:
    """
    If the value is a string and looks like it has whitespace at either end, strip it.

    If a string was "interned" (cached) by Python, string.strip() should generally return
    the existing string if no leading/trailing whitespace was found. But strings may or
    may not be interned by Python, and there may be a large cache for many unique values
    (which is likely for XLSForms), so this function tries to avoid calling strip().
    """
    if isinstance(value, str) and value and (value[0].isspace() or value[-1].isspace()):
        return value.strip()
    return value
