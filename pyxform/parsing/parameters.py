from lark import Lark, Token, Transformer
from lark.exceptions import LarkError

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import maybe_strip

# Label and value are used to match against user-specified files so case should be preserved.
CASE_SENSITIVE_VALUES = {"label", "value"}

PARAMETER_GRAMMAR = r"""
    start: pair*
    pair: TOKEN "=" TOKEN
    // Anything that's not a delimiter.
    TOKEN: /[^\s=,;]+/
    // Delimiters between key-value pairs.
    %ignore /[\s,;]+/
"""

_PARAMETER_PARSER = Lark(PARAMETER_GRAMMAR, parser="lalr", start="start")


class ParameterTransformer(Transformer):
    @staticmethod
    def start(pairs: list[tuple[str, str]]) -> dict[str, str]:
        """Combine (key, value) tuples into a dict"""
        return dict(pairs)

    @staticmethod
    def pair(items: list[Token, Token]) -> tuple[str, str]:
        """Normalise matched (key, value) tokens."""
        raw_key, raw_value = items
        key = maybe_strip(str(raw_key).lower())
        value = maybe_strip(str(raw_value))

        if key not in CASE_SENSITIVE_VALUES:
            value = value.lower()

        return key, value


# No token-specific (ALL_CAPS) methods, so visit_tokens=False.
_PARAMETER_TRANSFORMER = ParameterTransformer(visit_tokens=False)


def parse(
    raw_parameters: str,
    row_number: int,
) -> dict[str, str]:
    if not raw_parameters or not raw_parameters.strip():
        return {}

    try:
        return _PARAMETER_TRANSFORMER.transform(_PARAMETER_PARSER.parse(raw_parameters))
    except LarkError as e:
        raise PyXFormError(code=ErrorCode.SURVEY_004, context={"row": row_number}) from e
