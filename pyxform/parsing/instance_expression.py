from collections.abc import Generator
from typing import TYPE_CHECKING

from pyxform.parsing.expression import lex_expression
from pyxform.parsing.variable_reference import (
    resolve_variables,
    resolve_variables_as_nodes,
)
from pyxform.utils import Text, node

if TYPE_CHECKING:
    from pyxform.survey import Survey
    from pyxform.survey_element import SurveyElement
    from pyxform.utils import DetachableElement


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
    tokens = lex_expression(xml_text)
    if not tokens:
        return []
    instance_enter = False
    path_enter = False
    pred_enter = False
    last_token = None
    boundaries = []

    for t in tokens:
        emit = False
        # If an instance expression had started, note the string position boundary.
        if not instance_enter and t.type == "FUNC_CALL" and t.value == "instance(":
            instance_enter = True
            emit = True
            boundaries.append(t.start_pos)
        # Tokens that are part of an instance expression.
        elif instance_enter:
            # Tokens that are part of the instance call.
            if (
                t.type == "SYSTEM_LITERAL"
                and last_token.type == "FUNC_CALL"
                and last_token.value == "instance("
            ):
                emit = True
            elif last_token.type == "SYSTEM_LITERAL" and t.type == "CLOSE_PAREN":
                emit = True
            elif t.type == "PATH_SEP" and last_token.type == "CLOSE_PAREN":
                emit = True
                path_enter = True
            # A XPath path may continue after a predicate.
            elif t.type == "PATH_SEP" and last_token.type == "XPATH_PRED_END":
                emit = True
                path_enter = True
            # Tokens that are part of a XPath path.
            elif path_enter:
                if t.type == "WHITESPACE":
                    path_enter = False
                elif t.type != "XPATH_PRED_START":
                    emit = True
                elif t.type == "XPATH_PRED_START":
                    emit = True
                    path_enter = False
                    pred_enter = True
            # Tokens that are part of a XPath predicate.
            elif pred_enter:
                if t.type != "XPATH_PRED_END":
                    emit = True
                elif t.type == "XPATH_PRED_END":
                    emit = True
                    pred_enter = False
        # Track instance expression tokens, ignore others.
        if emit:
            last_token = t
        # If an instance expression had ended, note the string position boundary.
        elif instance_enter:
            instance_enter = False
            boundaries.append(last_token.end_pos)

    if last_token is not None:
        boundaries.append(last_token.end_pos)

    # Pair up the boundaries [1, 2, 3, 4] -> [(1, 2), (3, 4)].
    bounds = iter(boundaries)
    pos_bounds = list(zip(bounds, bounds, strict=False))
    return pos_bounds


def replace_with_output(
    text: str, context: "SurveyElement", survey: "Survey"
) -> Generator["DetachableElement | Text", None, None]:
    """
    Find occurrences of instance expressions and replace them with <output/> elements.

    :param text: The text string to search/replace.
    :param context: The SurveyElement that this string belongs to.
    :param survey: The Survey that the context is in.
    """
    # 9 = len("instance(")
    if len(text) <= 9 or "instance(" not in text:
        yield Text(data=text)
        return

    boundaries = find_boundaries(xml_text=text)
    if not boundaries:
        yield Text(data=text)
        return

    cursor = 0
    for start, end in boundaries:
        # Text before this match.
        if start > cursor:
            yield from resolve_variables_as_nodes(
                text=text[cursor:start], survey=survey, context=context, wrap=True
            )

        # Pass the instance string through the variable reference resolver.
        yield node(
            "output",
            value=resolve_variables(text=text[start:end], survey=survey, context=context),
        )
        cursor = end

    # Text after all match(es).
    if cursor < len(text):
        yield from resolve_variables_as_nodes(
            text=text[cursor:], survey=survey, context=context, wrap=True
        )
