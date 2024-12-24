import re
from functools import lru_cache


def get_lexer_rules():
    # ncname regex adapted from eulxml https://github.com/emory-libraries/eulxml/blob/2e1a9f71ffd1fd455bd8326ec82125e333b352e0/eulxml/xpath/lexrules.py
    # (C) 2010,2011 Emory University Libraries [Apache v2.0 License]
    # They in turn adapted it from https://www.w3.org/TR/REC-xml/#NT-NameStartChar
    # and https://www.w3.org/TR/REC-xml-names/#NT-NCName
    namestartchar = (
        r"([A-Z]|_|[a-z]|\xc0-\xd6]|[\xd8-\xf6]|[\xf8-\u02ff]|"
        + r"[\u0370-\u037d]|[\u037f-\u1fff]|[\u200c-\u200d]|[\u2070-\u218f]|"
        + r"[\u2c00-\u2fef]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]"
        + r"|[\U00010000-\U000EFFFF])"
    )
    # additional characters allowed in NCNames after the first character
    namechar_extra = r"[-.0-9\xb7\u0300-\u036f\u203f-\u2040]"
    ncname_regex = (
        r"(" + namestartchar + r")(" + namestartchar + r"|" + namechar_extra + r")*"
    )
    ncname_regex = ncname_regex + r"(:" + ncname_regex + r")?"

    date_regex = r"-?\d{4}-\d{2}-\d{2}"
    time_regex = r"\d{2}:\d{2}:\d{2}(\.\s+)?(((\+|\-)\d{2}:\d{2})|Z)?"
    date_time_regex = date_regex + "T" + time_regex

    # Rule order is significant - match priority runs top to bottom.
    return {
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
        "PYXFORM_REF": r"\$\{(last-saved#)?" + ncname_regex + r"\}",
        "FUNC_CALL": ncname_regex + r"\(",
        "XPATH_PRED_START": ncname_regex + r"\[",
        "XPATH_PRED_END": r"\]",
        "URI_SCHEME": ncname_regex + r"://",
        "NAME": ncname_regex,  # Must be after rules containing ncname_regex.
        "PYXFORM_REF_START": r"\$\{",
        "PYXFORM_REF_END": r"\}",
        "OTHER": r".+?",  # Catch any other character so that parsing doesn't stop.
    }


LEXER_RULES = get_lexer_rules()
RE_ONLY_NCNAME = re.compile(rf"""^{LEXER_RULES["NAME"]}$""")
RE_ONLY_PYXFORM_REF = re.compile(rf"""^{LEXER_RULES["PYXFORM_REF"]}$""")
RE_ANY_PYXFORM_REF = re.compile(LEXER_RULES["PYXFORM_REF"])


def get_expression_lexer() -> re.Scanner:
    def get_tokenizer(name):
        def tokenizer(scan, value) -> ExpLexerToken | str:
            return ExpLexerToken(name, value, scan.match.start(), scan.match.end())

        return tokenizer

    lexicon = [(v, get_tokenizer(k)) for k, v in LEXER_RULES.items()]
    # re.Scanner is undocumented but has been around since at least 2003
    # https://mail.python.org/pipermail/python-dev/2003-April/035075.html
    return re.Scanner(lexicon)


class ExpLexerToken:
    __slots__ = ("name", "value", "start", "end")

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


def is_pyxform_reference(value: str) -> bool:
    """
    Does the input string contain only a valid Pyxform reference? e.g. ${my_question}
    """
    # Needs 3 characters for "${}", plus a name inside.
    return value and len(value) > 3 and bool(RE_ONLY_PYXFORM_REF.match(value))


def is_xml_tag(value: str) -> bool:
    """
    Does the input string contain only a valid XML tag / element name?
    """
    return value and bool(RE_ONLY_NCNAME.match(value))


def has_last_saved(value: str) -> bool:
    """
    Does the input string contain a valid '#last-saved' Pyxform reference? e.g. ${last-saved#my_question}
    """
    # Needs 14 characters for "${last-saved#}", plus a name inside.
    return (
        value
        and len(value) > 14
        and "${last-saved#" in value
        and RE_ANY_PYXFORM_REF.search(value)
    )
