from collections.abc import Iterable

from pyxform.utils import parse_expression


def is_single_token_expression(expression: str, token_types: Iterable[str]) -> bool:
    """
    Does the expression contain single token of one of the provided token types?
    """
    tokens, _ = parse_expression(text=expression.strip())
    if 1 == len(tokens) and tokens[0].name in token_types:
        return True
    else:
        return False
