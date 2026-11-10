"""
Helpers for parsing variable references from strings.

The relatively small LRU cache sizes used here attempt to balance:
a) how expensive is the function? Regex and/or Scanner is worse than len and membership,
   and there is also a cost to hash/lookup from the cache.
b) how much memory is it reasonable to spend on getting a high cache hit ratio vs.
   lower ratio with extra time re-parsing; and the memory for the key and return value?
c) how likely is it that a large variety of unique strings are present in a XLSForm, and
   how likely is it that similar strings are close to each other vs. randomly dispersed?
"""

from collections.abc import Generator
from functools import lru_cache
from typing import TYPE_CHECKING

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import (
    RE_PYXFORM_REF,
    RE_PYXFORM_REF_INNER,
    RE_PYXFORM_REF_OUTER,
)
from pyxform.utils import node

if TYPE_CHECKING:
    from pyxform.survey import Survey
    from pyxform.survey_element import SurveyElement


class ParsedReference:
    __slots__ = ("last_saved", "name")

    def __init__(self, name: str, last_saved: bool = False):
        self.name: str = name
        self.last_saved: bool = last_saved


@lru_cache(maxsize=128)
def is_pyxform_reference_candidate(value: str) -> bool:
    """
    Check if the string looks like a pyxform reference.

    Needs 2 characters for "${", plus at least 1 more for a name inside. Does not look
    for closing brace because full parsing will try to detect malformed references. This
    pre-check can help avoid more expensive full parsing.

    :param value: The string to inspect.
    """
    return len(value) > 2 and "${" in value


def _parse(
    value: str,
    match_limit: int | None = None,
    match_full: bool = False,
) -> Generator[ParsedReference, None, None]:
    """
    Parse the string and return reference target(s) e.g. `name` from `${name}`.

    It is an error if the reference token contains anything other than a valid ncname
    (a question name), optionally with the `last-saved#` prefix.

    Does not otherwise treat `last-saved#` differently since https://docs.getodk.org/form-logic/
    says: "References to the last saved record could be used as part of any expression
    wherever expressions are allowed".

    :param value: The string to inspect.
    :param match_limit: If provided, parse only this many references in the string, and if
      more references than the limit are found, then raise an error.
    :param match_full: If True, require that the string contains a reference and nothing
      else (no other characters or references).
    """
    if not is_pyxform_reference_candidate(value):
        return None

    if match_full:
        outer_matches = RE_PYXFORM_REF_OUTER.fullmatch(value)
        if not outer_matches:
            # Expression may contain a reference but has other characters e.g. func call.
            return None
        outer_matches = (outer_matches,)
    else:
        outer_matches = RE_PYXFORM_REF_OUTER.finditer(value)

    count = 0
    # Look for any possible matches, then check each one for valid reference syntax.
    for match in outer_matches:
        ref_candidate = match.group("pyxform_ref")
        # Although it's an "any" match pattern, fullmatch is used to require "only".
        # Return the ref_candidate since it has original string start/end positions.
        if ref_candidate:
            ref_inner = RE_PYXFORM_REF_INNER.fullmatch(ref_candidate)
            if ref_inner:
                if match_limit is not None and count >= match_limit:
                    raise PyXFormError(code=ErrorCode.PYREF_002)

                yield ParsedReference(
                    name=ref_inner.group("ncname"),
                    last_saved=ref_inner.group("last_saved") is not None,
                )
                count += 1
            else:
                raise PyXFormError(code=ErrorCode.PYREF_001)
        else:
            raise PyXFormError(code=ErrorCode.PYREF_001)


@lru_cache(maxsize=128)
def is_pyxform_reference(value: str) -> bool:
    """
    Does the input string contain only a valid Pyxform reference? e.g. `${my_question}`.

    :param value: The string to inspect.
    """
    try:
        return next(_parse(value=value, match_full=True), None) is not None
    except (StopIteration, PyXFormError):
        return False


@lru_cache(maxsize=128)
def has_pyxform_reference(value: str) -> bool:
    """
    Does the input string contain a valid Pyxform reference? e.g. `hi ${name}`.

    :param value: The string to inspect.
    """
    try:
        return next(_parse(value=value), None) is not None
    except (StopIteration, PyXFormError):
        return False


@lru_cache(maxsize=128)
def has_pyxform_reference_with_last_saved(value: str) -> bool:
    """
    Does the input string contain a valid '#last-saved'? e.g. `${last-saved#my_question}`.

    Needs 14 characters for "${last-saved#}", plus a name inside. This pre-check can help
    avoid more expensive full parsing.

    :param value: The string to inspect.
    """
    try:
        return len(value) > 14 and any(i.last_saved for i in _parse(value=value))
    except (StopIteration, PyXFormError):
        return False


@lru_cache(maxsize=128)
def parse_pyxform_references(
    value: str,
    match_limit: int | None = None,
    match_full: bool = False,
) -> tuple[ParsedReference, ...]:
    """
    Parse all pyxform references in a string.

    :param value: The string to inspect.
    :param match_limit: If provided, parse only this many references in the string, and if
      more references than the limit are found, then raise an error.
    :param match_full: If True, require that the string contains a reference and nothing
      else (no other characters or references).
    """
    return tuple(_parse(value=value, match_limit=match_limit, match_full=match_full))


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
