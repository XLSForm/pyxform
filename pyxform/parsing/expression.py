import re
from functools import lru_cache
from typing import Any

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

date_regex = r"-?\d{4}-\d{2}-\d{2}"
time_regex = r"\d{2}:\d{2}:\d{2}(\.\s+)?(((\+|\-)\d{2}:\d{2})|Z)?"
date_time_regex = date_regex + "T" + time_regex

# pyxform_ref_outer picks up possible refs, and matches unterminated refs to exclude them.
pyxform_ref_outer = r"\$\{(?P<pyxform_ref>[^}]+)\}|\$\{[^}]*$"
pyxform_ref_inner = rf"(?P<last_saved>last-saved#)?{ncname_regex_named}"
pyxform_ref_inner_last_saved_required = (
    rf"(?P<last_saved>last-saved#){ncname_regex_named}"
)
pyxform_ref = rf"(?P<pyxform_ref>\$\{{{pyxform_ref_inner}\}})"

# Rule order is significant - match priority runs top to bottom.
LEXER_RULES = {
    # https://www.w3.org/TR/xmlschema-2/#dateTime
    "DATETIME": date_time_regex,
    "DATE": date_regex,
    "TIME": time_regex,
    "NUMBER": r"-?\d+\.\d*|-?\.\d+|-?\d+",
    # https://www.w3.org/TR/1999/REC-xpath-19991116/#exprlex
    "OPS_MATH": r"[\*\+\-]| mod | div ",
    "OPS_COMP": r"\=|\!\=|\<|\>|\<=|>=",
    "OPS_BOOL": r" and | or ",
    "OPS_UNION": r"\|",
    "OPEN_PAREN": r"\(",
    "CLOSE_PAREN": r"\)",
    "BRACKET": r"\[\]\{\}",
    "PARENT_REF": r"\.\.",
    "SELF_REF": r"\.",
    "PATH_SEP": r"\/",  # javarosa.xpath says "//" is an "unsupported construct".
    "SYSTEM_LITERAL": r""""[^"]*"|'[^']*'""",
    "COMMA": r",",
    "WHITESPACE": r"\s+",
    "PYXFORM_REF": pyxform_ref,
    "FUNC_CALL": ncname_regex_ns_named + r"\(",
    "XPATH_PRED_START": ncname_regex_ns_named + r"\[",
    "XPATH_PRED_END": r"\]",
    "URI_SCHEME": ncname_regex_named + r"://",
    "NAME": ncname_regex_named,  # Must be after rules containing ncname_regex.
    "PYXFORM_REF_START": r"\$\{",
    "PYXFORM_REF_END": r"\}",
    "OTHER": r".+?",  # Catch any other character so that parsing doesn't stop.
}


RE_NCNAME_NAMESPACED = re.compile(ncname_regex_ns_named)
RE_PYXFORM_REF = re.compile(pyxform_ref)
RE_PYXFORM_REF_OUTER = re.compile(pyxform_ref_outer)
RE_PYXFORM_REF_INNER = re.compile(pyxform_ref_inner)


def get_expression_lexer() -> re.Scanner:
    def get_tokenizer(name):
        def tokenizer(scan, value) -> ExpLexerToken | str:
            match = scan.match
            return ExpLexerToken(name, value, match.start(), match.end())

        return tokenizer

    lexicon = [(v, get_tokenizer(k)) for k, v in LEXER_RULES.items()]
    # re.Scanner is undocumented but has been around since at least 2003
    # https://mail.python.org/pipermail/python-dev/2003-April/035075.html
    return re.Scanner(lexicon)


class ExpLexerToken:
    __slots__ = ("end", "name", "start", "value")

    def __init__(self, name: str, value: str, start: int, end: int) -> None:
        self.name: str = name
        self.value: str = value
        self.start: int = start
        self.end: int = end


# Scanner takes a few 100ms to compile so use the shared instance.
_EXPRESSION_LEXER = get_expression_lexer()


@lru_cache(maxsize=128)
def parse_expression(text: str) -> tuple[list[ExpLexerToken], str]:
    """
    Parse an expression.

    Use this function instead of _EXPRESSION_LEXER to take advantage of caching.

    :param text: The expression.
    :return: The parsed tokens, and any remaining unparsed text.
    """
    tokens, remainder = _EXPRESSION_LEXER.scan(text)
    return tokens, remainder


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
