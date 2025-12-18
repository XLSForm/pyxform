from typing import TYPE_CHECKING

from pyxform.parsing.expression import RE_PYXFORM_REF, parse_expression
from pyxform.utils import node

if TYPE_CHECKING:
    from pyxform.survey import Survey
    from pyxform.survey_element import SurveyElement


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
    tokens = parse_expression(xml_text)
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


def replace_with_output(xml_text: str, context: "SurveyElement", survey: "Survey") -> str:
    """
    Find occurrences of instance expressions and replace them with <output/> elements.

    :param xml_text: The text string to search/replace.
    :param context: The SurveyElement that this string belongs to.
    :param survey: The Survey that the context is in.
    :return: The possibly modified string.
    """
    # 9 = len("instance(")
    if len(xml_text) <= 9 or "instance(" not in xml_text:
        return xml_text
    boundaries = find_boundaries(xml_text=xml_text)
    if boundaries:
        new_strings = []
        for start, end in boundaries:
            old_str = xml_text[start:end]
            # Pass the new string through the pyxform reference replacer.
            # noinspection PyProtectedMember
            new_str = RE_PYXFORM_REF.sub(
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
            xml_text = f"{xml_text[: s + offset]}{n}{xml_text[e + offset :]}"
            offset += len(n) - len(o)
    return xml_text
