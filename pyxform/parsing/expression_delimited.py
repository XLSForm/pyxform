from collections.abc import Generator
from typing import TYPE_CHECKING

from lark import Lark, LarkError, Transformer

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.instance_expression import (
    replace_with_output as replace_with_output_old,
)
from pyxform.parsing.utils import maybe_strip
from pyxform.parsing.variable_reference import (
    is_pyxform_reference_candidate,
    resolve_variables,
    resolve_variables_as_nodes,
)
from pyxform.utils import Text, node

if TYPE_CHECKING:
    from lark import Token

    from pyxform.survey import Survey
    from pyxform.survey_element import SurveyElement
    from pyxform.utils import DetachableElement


expression_grammar = r"""
start: (expression | escaped | text)*

expression: _OPEN (invalid_nesting | ESCAPED_DELIMITER | TEXT_NON_DELIMITER | CHAR_NON_DELIMITER)* _CLOSE
invalid_nesting: expression
escaped: ESCAPED_DELIMITER
text: (TEXT_NON_DELIMITER | CHAR_NON_DELIMITER)+

_OPEN: "{{"
_CLOSE: /}\}(?!})/
ESCAPED_DELIMITER: "\\{{" | "\\}}"
TEXT_NON_DELIMITER: /[^{}\\]+/
CHAR_NON_DELIMITER: /[{}\\]/
"""


_EXPRESSION_PARSER = Lark(
    expression_grammar, parser="lalr", lexer="contextual", cache=True
)


class ExpressionTransformer(Transformer):
    def __init__(
        self, context: "SurveyElement", survey: "Survey", visit_tokens: bool = True
    ):
        super().__init__(visit_tokens=visit_tokens)
        self.context: SurveyElement = context
        self.survey: Survey = survey
        self.expression_modified: bool = False

    @staticmethod
    def _flatten(children: list["Token"]) -> str:
        """Combine leaf child strings into one string."""
        if len(children) == 0:
            return ""
        elif len(children) > 1:
            return "".join(children)
        else:
            return str(children[0])

    @staticmethod
    def start(
        children: list[Generator["Text | DetachableElement", None, None]],
    ) -> Generator["Text | DetachableElement", None, None]:
        """Return parsed elements as a flattened iterable."""
        for c in children:
            yield from c

    def text(
        self, children: list["Token"]
    ) -> Generator["Text | DetachableElement", None, None]:
        """Join all children strings, resolve variable references."""
        yield from resolve_variables_as_nodes(
            text=self._flatten(children=children),
            survey=self.survey,
            context=self.context,
            wrap=True,
        )

    def ESCAPED_DELIMITER(self, token: "Token") -> str:
        r"""Drop the leading backslash: `'\{{' -> '{{'`, `'\}}' -> '}}'`."""
        resolved = {r"\{{": "{{", r"\}}": "}}"}[token]
        self.expression_modified = True
        return resolved

    @staticmethod
    def escaped(children: list["Token"]) -> Generator[Text, None, None]:
        """Wrap an outer-level escaped delimiter in a Text object."""
        yield Text(data=children[0])

    def invalid_nesting(self, children: list["Token"]) -> None:
        """Raise an error if a nested expression is found."""
        raise PyXFormError(code=ErrorCode.INTERNAL_004)

    def expression(
        self, children: list["Token"]
    ) -> Generator["DetachableElement", None, None]:
        """Join/wrap children in XML: `<output value='children123'/>`, resolve variable references."""
        flat = self._flatten(children=children)
        if len(maybe_strip(flat)) == 0:
            raise PyXFormError(code=ErrorCode.INTERNAL_005)
        resolved = resolve_variables(text=flat, survey=self.survey, context=self.context)
        self.expression_modified = True
        yield node("output", value=resolved)


def replace_with_output(
    text: str, context: "SurveyElement", survey: "Survey"
) -> list["Text | DetachableElement"]:
    """
    Wrap expressions in output element: `{{contents}} -> <output value="contents"/>`.

    Resolves variable references inside and the expression.

    :param text: Text that may contain an expression.
    :param context: The element context that variable references should be resolved in,
      for example to determine relative references.
    :param survey: The parent Survey object.
    """
    # Minimum length token that could be changed.
    if len(text) < 3:
        return [Text(data=text)]

    try:
        if "{" in text or "}" in text:
            transformer = ExpressionTransformer(survey=survey, context=context)
            result = list(transformer.transform(_EXPRESSION_PARSER.parse(text)))
            if transformer.expression_modified:
                return result

        # Fallback for old func that only looks for non-delimited `instance()`.
        if len(text) > 9 and "instance(" in text:
            return list(
                replace_with_output_old(text=text, context=context, survey=survey)
            )
        elif is_pyxform_reference_candidate(value=text):
            return list(
                resolve_variables_as_nodes(
                    text=text, survey=survey, context=context, wrap=True
                )
            )
        else:
            return [Text(data=text)]
    except LarkError as e:
        if isinstance(e.__context__, PyXFormError):
            ctx = e.__context__
            if ctx.code:
                ctx.context["s"] = text
                raise PyXFormError(code=ctx.code, context=ctx.context) from e
            else:
                raise PyXFormError(ctx.args[0]) from e
        else:
            raise PyXFormError(code=ErrorCode.INTERNAL_003, context={"s": text}) from e
    except PyXFormError as e:
        if "s" not in e.context:
            e.context["s"] = text
        raise
