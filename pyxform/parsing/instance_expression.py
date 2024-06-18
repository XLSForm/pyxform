import re
from typing import TYPE_CHECKING

from pyxform.utils import BRACKETED_TAG_REGEX, EXPRESSION_LEXER, ExpLexerToken, node

if TYPE_CHECKING:
    from pyxform.survey import Survey
    from pyxform.survey_element import SurveyElement


def instance_func_start(token: ExpLexerToken) -> bool:
    """
    Determine if the token is the start of an instance expression.

    :param token: The token to examine.
    :return: If True, the token is the start of an instance expression.
    """
    if token is None:
        return False
    return token.name == "FUNC_CALL" and token.value == "instance("


def find_boundaries(xml_text: str) -> list[tuple[int, int]]:
    """
    Find token boundaries of any instance() expression.

    Presumed:
    - An instance expression is followed by an XML path expression.
    - Any token is allowed inside a predicate (e.g. nested paths/preds/funcs).
    - When not inside a predicate, whitespace terminates a XML path expression.
    - instance expressions are valid inside predicates of other instance expressions.

    :param xml_text: XML text that may contain an instance expression.
    :return: Tokens in instance expression, and the string position boundaries.
    """
    instance_enter = False
    path_enter = False
    pred_enter = False
    last_token = None
    tokens, _ = EXPRESSION_LEXER.scan(xml_text)
    boundaries = []

    for t in tokens:
        emit = False
        # If an instance expression had started, note the string position boundary.
        if instance_func_start(token=t) and not instance_enter:
            instance_enter = True
            emit = True
            boundaries.append(t.start)
        # Tokens that are part of an instance expression.
        elif instance_enter:
            # Tokens that are part of the instance call.
            if instance_func_start(token=last_token) and t.name == "SYSTEM_LITERAL":
                emit = True
            elif last_token.name == "SYSTEM_LITERAL" and t.name == "CLOSE_PAREN":
                emit = True
            elif t.name == "PATH_SEP" and last_token.name == "CLOSE_PAREN":
                emit = True
                path_enter = True
            # A XPath path may continue after a predicate.
            elif t.name == "PATH_SEP" and last_token.name == "XPATH_PRED_END":
                emit = True
                path_enter = True
            # Tokens that are part of a XPath path.
            elif path_enter:
                if t.name == "WHITESPACE":
                    path_enter = False
                elif t.name != "XPATH_PRED_START":
                    emit = True
                elif t.name == "XPATH_PRED_START":
                    emit = True
                    path_enter = False
                    pred_enter = True
            # Tokens that are part of a XPath predicate.
            elif pred_enter:
                if t.name != "XPATH_PRED_END":
                    emit = True
                elif t.name == "XPATH_PRED_END":
                    emit = True
                    pred_enter = False
        # Track instance expression tokens, ignore others.
        if emit:
            last_token = t
        # If an instance expression had ended, note the string position boundary.
        elif instance_enter:
            instance_enter = False
            boundaries.append(last_token.end)

    if last_token is not None:
        boundaries.append(last_token.end)

    # Pair up the boundaries [1, 2, 3, 4] -> [(1, 2), (3, 4)].
    bounds = iter(boundaries)
    pos_bounds = list(zip(bounds, bounds, strict=False))
    return pos_bounds


def replace_with_output(xml_text: str, context: "SurveyElement", survey: "Survey") -> str:
    """
    Find occurrences of instance expressions and replace them with <output/> elements.

    :param xml_text: The text string to search/replace.
    :param context: The SurveyElement that this string belongs to.
    :param survey: The Survey that the context is in.
    :return: The possibly modified string.
    """
    boundaries = find_boundaries(xml_text=xml_text)
    if 0 < len(boundaries):
        new_strings = []
        for start, end in boundaries:
            old_str = xml_text[start:end]
            # Pass the new string through the pyxform reference replacer.
            # noinspection PyProtectedMember
            new_str = re.sub(
                BRACKETED_TAG_REGEX,
                lambda m: survey._var_repl_function(m, context),
                old_str,
            )
            # Generate a node so that character escapes are applied.
            new_strings.append(
                (start, end, old_str, node("output", value=new_str).toxml())
            )
        # Position-based replacement avoids strings which are substrings of other
        # replacements being inserted incorrectly. Offset tracking deals with changing
        # expression positions due to incremental replacement.
        offset = 0
        for s, e, o, n in new_strings:
            xml_text = xml_text[: s + offset] + n + xml_text[e + offset :]
            offset += len(n) - len(o)
    return xml_text
