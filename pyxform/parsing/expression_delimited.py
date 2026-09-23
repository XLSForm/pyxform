from typing import TYPE_CHECKING

from lark import Lark, LarkError, Transformer, Tree

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import RE_PYXFORM_REF
from pyxform.parsing.instance_expression import (
    replace_with_output as replace_with_output_old,
)
from pyxform.utils import node
from pyxform.validators.pyxform.pyxform_reference import is_pyxform_reference_candidate

if TYPE_CHECKING:
    from lark import Token

    from pyxform.survey import Survey
    from pyxform.survey_element import SurveyElement


expression_grammar = r"""
start: (expression | escaped | text)*

expression: _OPEN (invalid_nesting | escaped | TEXT_NON_DELIMITER | CHAR_NON_DELIMITER)* _CLOSE
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


def resolve_variables(
    xml_text: str,
    survey: "Survey",
    context: "SurveyElement | None" = None,
    wrap: bool = False,
):
    """
    Replace ${} variables with XPath references, optionally wrapped in <output/>.

    :param xml_text: Input string to process.
    :param survey: Survey object for reference lookup.
    :param context: The document node that the text belongs to.
    :param wrap: If True, enclose resolved references in <output/> tags.
    """

    def resolver(match):
        replaced = survey._var_repl_function(match, context)
        if wrap:
            return node("output", value=replaced).toxml()
        else:
            return replaced

    if is_pyxform_reference_candidate(value=xml_text):
        return RE_PYXFORM_REF.sub(resolver, xml_text)
    return xml_text


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

    def start(self, children: list["Token"]) -> str:
        """Join all children strings."""
        return self._flatten(children=children)

    def text(self, children: list["Token"]) -> str:
        """Join all children strings."""
        original = self._flatten(children=children)
        resolved = resolve_variables(
            xml_text=original, survey=self.survey, context=self.context, wrap=True
        )
        if original != resolved:
            return resolved
        else:
            return original

    def escaped(self, children: list["Token"]) -> str:
        r"""Drop the leading backslash: `'\{{' -> '{{'`, `'\}}' -> '}}'`."""
        original = children[0]
        resolved = {r"\{{": "{{", r"\}}": "}}"}[original]
        if original != resolved:
            self.expression_modified = True
            return resolved
        else:
            return original

    def invalid_nesting(self, children: list["Token"]) -> str:
        """Raise an error if a nested expression is found."""
        raise PyXFormError(code=ErrorCode.INTERNAL_004)

    def expression(self, children: list["Token"]) -> str:
        """Join/wrap children in XML: `<output value='children123'/>`."""
        resolved = resolve_variables(
            xml_text=self._flatten(children=children),
            survey=self.survey,
            context=self.context,
        )
        self.expression_modified = True
        return node("output", value=resolved).toxml()


def replace_with_output(xml_text: str, context: "SurveyElement", survey: "Survey") -> str:
    """
    Wrap expressions in output element: `{{contents}} -> <output value="contents"/>`.

    Resolves variable references inside the expression, but not outside, so an extra pass
    over the string is required.

    :param xml_text: Text that may contain an expression.
    :param context: The element context that variable references should be resolved in,
      for example to determine relative references.
    :param survey: The parent Survey object.
    """
    # Minimum length token that could be changed.
    if len(xml_text) < 3:
        return xml_text

    try:
        if "{" in xml_text or "}" in xml_text:
            transformer = ExpressionTransformer(survey=survey, context=context)
            out_str = transformer.transform(_EXPRESSION_PARSER.parse(xml_text))
            if transformer.expression_modified:
                return out_str

        # Fallback for old func that only looks for non-delimited `instance()`.
        fallback = replace_with_output_old(xml_text, context, survey)
        if is_pyxform_reference_candidate(fallback):
            fallback = resolve_variables(
                xml_text=fallback, survey=survey, context=context, wrap=True
            )
        if fallback != xml_text:
            return fallback
        else:
            return xml_text
    except LarkError as e:
        if isinstance(e.__context__, PyXFormError):
            ctx = e.__context__
            if ctx.code:
                ctx.context["s"] = xml_text
                raise PyXFormError(code=ctx.code, context=ctx.context) from e
            else:
                raise PyXFormError(ctx.args[0]) from e
        else:
            raise PyXFormError(
                code=ErrorCode.INTERNAL_003, context={"s": xml_text}
            ) from e
