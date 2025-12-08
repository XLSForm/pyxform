from collections import Counter
from itertools import chain, product

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.validators.pyxform import pyxform_reference as pr

from tests.pyxform_test_case import PyxformTestCase

ELEMENT_NAMES = Counter(("a", "b", "abc123"))
expression_contexts = [
    ("{}", "Single reference"),
    ("This: {}", "Single reference with prefix"),
    ("{} (that)", "Single reference with suffix"),
    ("This: {} (that)", "Single reference with prefix and suffix"),
    ("This:{}", "Single reference with prefix, no space"),
    ("{}(that)", "Single reference with suffix, no space"),
    ("This:{} (that)", "Single reference with prefix and suffix, no space"),
]
ok_tokens = [
    ("${a}", "OK"),
    ("${abc123}", "OK"),
    ("${last-saved#abc123}", "OK"),
]
error_tokens = [
    ("${a }", "Invalid question name"),
    ("${a\n}", "Invalid question name"),
    ("${a", "No end character"),
    ("${a${b}}", "Nested refererence"),
    ("${last-saved#a }", "Invalid question name"),
    ("${last-saved#a \n}", "Invalid question name"),
    ("${last-saved#a", "No end character"),
    ("${last-saved#a${b}}", "Nested refererence"),
]


class TestPyxformReference(PyxformTestCase):
    def test_single_reference__ok(self):
        """Should pass validation for all expected reference forms when used once."""
        for context, ctx_desc in expression_contexts:
            for token, tok_desc in ok_tokens:
                with self.subTest(c=context, ctx=ctx_desc, t=token, tok=tok_desc):
                    case = context.format(token)
                    pr.validate_pyxform_reference_syntax(
                        sheet_name="test",
                        sheet_data=({"label": case},),
                        element_names=ELEMENT_NAMES,
                        limit_to_columns={"label"},
                    )

    def test_single_reference__error(self):
        """Should fail validation when the reference is malformed and used once."""
        for context, ctx_desc in expression_contexts:
            for token, tok_desc in error_tokens:
                with (
                    self.subTest(c=context, ctx=ctx_desc, t=token, tok=tok_desc),
                    self.assertRaises(PyXFormError) as err,
                ):
                    case = context.format(token)
                    pr.validate_pyxform_reference_syntax(
                        sheet_name="test",
                        sheet_data=({"label": case},),
                        element_names=ELEMENT_NAMES,
                        limit_to_columns={"label"},
                    )
                self.assertEqual(
                    str(err.exception),
                    ErrorCode.PYREF_001.value.format(sheet="test", column="label", row=2),
                    msg=case,
                )

    def test_multiple_reference__ok(self):
        """Should pass validation for multiple (2x) expected reference form combinations."""
        # Pairs of all OK + OK, in all contexts, both in any order (many tests!).
        tokens = list(product(ok_tokens, repeat=2))
        contexts = list(product(expression_contexts, repeat=2))
        for (context1, ctx_desc1), (context2, ctx_desc2) in contexts:
            context = context1 + context2
            ctx_desc = (ctx_desc1, ctx_desc2)
            for (token1, tok_desc1), (token2, tok_desc2) in tokens:
                with self.subTest(
                    context=context,
                    contexts=ctx_desc,
                    tokens=(token1, token2),
                    tok_desc=(tok_desc1, tok_desc2),
                ):
                    case = context.format(token1, token2)
                    pr.validate_pyxform_reference_syntax(
                        sheet_name="test",
                        sheet_data=({"label": case},),
                        element_names=ELEMENT_NAMES,
                        limit_to_columns={"label"},
                    )

    def test_multiple_references__error(self):
        """Should fail validation when one of multiple (2x) references is malformed."""
        # Pairs of all OK + error, in all contexts, both in any order (tonnes of tests!).
        tokens = list(
            chain(product(ok_tokens, error_tokens), product(error_tokens, ok_tokens))
        )
        contexts = list(product(expression_contexts, repeat=2))
        for (context1, ctx_desc1), (context2, ctx_desc2) in contexts:
            context = context1 + context2
            ctx_desc = (ctx_desc1, ctx_desc2)
            for (token1, tok_desc1), (token2, tok_desc2) in tokens:
                with (
                    self.subTest(
                        context=context,
                        contexts=ctx_desc,
                        tokens=(token1, token2),
                        tok_desc=(tok_desc1, tok_desc2),
                    ),
                    self.assertRaises(PyXFormError) as err,
                ):
                    case = context.format(token1, token2)
                    pr.validate_pyxform_reference_syntax(
                        sheet_name="test",
                        sheet_data=({"label": case},),
                        element_names=ELEMENT_NAMES,
                        limit_to_columns={"label"},
                    )
                self.assertEqual(
                    str(err.exception),
                    ErrorCode.PYREF_001.value.format(sheet="test", column="label", row=2),
                    msg=case,
                )
