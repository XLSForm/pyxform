"""
Helpers for parsing and validating pyxform reference variables from strings.

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

from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import (
    RE_PYXFORM_REF_INNER,
    RE_PYXFORM_REF_OUTER,
)


def is_pyxform_reference_candidate(value: str) -> bool:
    """
    Does the string look like a pyxform reference?

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
) -> Generator[str, None, None]:
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
        if ref_candidate and RE_PYXFORM_REF_INNER.fullmatch(ref_candidate):
            if match_limit is not None and count >= match_limit:
                raise PyXFormError(code=ErrorCode.PYREF_002)

            yield ref_candidate
            count += 1
        else:
            raise PyXFormError(code=ErrorCode.PYREF_001)


@lru_cache(maxsize=128)
def is_pyxform_reference(value: str) -> bool:
    """
    Does the input string contain only a valid Pyxform reference? e.g. `${my_question}`

    :param value: The string to inspect.
    """
    try:
        return next(_parse(value=value, match_full=True), None) is not None
    except (StopIteration, PyXFormError):
        return False


@lru_cache(maxsize=128)
def has_pyxform_reference(value: str) -> bool:
    """
    Does the input string contain a valid Pyxform reference? e.g. `hi ${name}`

    :param value: The string to inspect.
    """
    try:
        return next(_parse(value=value), None) is not None
    except (StopIteration, PyXFormError):
        return False


@lru_cache(maxsize=128)
def has_pyxform_reference_with_last_saved(value: str) -> bool:
    """
    Does the input string contain a valid '#last-saved' reference? e.g. `${last-saved#my_question}`

    Needs 14 characters for "${last-saved#}", plus a name inside. This pre-check can help
    avoid more expensive full parsing.

    :param value: The string to inspect.
    """
    try:
        return len(value) > 14 and any(
            i.startswith("last-saved#") for i in _parse(value=value)
        )
    except (StopIteration, PyXFormError):
        return False


@lru_cache(maxsize=128)
def parse_pyxform_references(
    value: str,
    match_limit: int | None = None,
) -> tuple[str, ...]:
    """
    Parse all pyxform references in a string.

    :param value: The string to inspect.
    :param match_limit: If provided, parse only this many references in the string, and if
      more references than the limit are found, then raise an error.
    """
    return tuple(_parse(value=value, match_limit=match_limit))


def validate_pyxform_reference_syntax(
    value: str, sheet_name: str, row_number: int, column: str
) -> tuple[str, ...] | None:
    """
    Parse all pyxform references in a string, and raise an error if any are malformed.

    Generally the same as `parse_pyxform_references` but adds the XLSForm context to the
    error message, if any.

    :param value: The string to inspect.
    :param sheet_name: The XLSForm sheet the value is from.
    :param row_number: The XLSForm row the value is from.
    :param column: The XLSForm column the value is from.
    """
    # Skip columns in potentially large sheets where references are not allowed.
    if sheet_name == co.SURVEY:
        if column in {co.TYPE, co.NAME}:
            return None
    elif sheet_name == co.CHOICES:
        if column in {co.LIST_NAME_S, co.LIST_NAME_U, co.NAME}:
            return None
    elif sheet_name == co.ENTITIES:
        if column in {co.LIST_NAME_S, co.LIST_NAME_U}:
            return None

    try:
        return parse_pyxform_references(value=value)
    except PyXFormError as e:
        e.context.update(sheet=sheet_name, column=column, row=row_number)
        raise
