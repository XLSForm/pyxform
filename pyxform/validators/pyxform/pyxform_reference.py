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

from collections import Counter
from collections.abc import Generator, Sequence
from functools import lru_cache
from typing import TYPE_CHECKING

from pyxform import aliases
from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import (
    RE_PYXFORM_REF_INNER,
    RE_PYXFORM_REF_OUTER,
)

if TYPE_CHECKING:
    from pyxform.xls2json_backends import DefinitionData


class ParsedReference:
    __slots__ = ("last_saved", "name")

    def __init__(self, name: str, last_saved: bool = False):
        self.name: str = name
        self.last_saved: bool = last_saved


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


def validate_pyxform_reference_syntax(
    sheet_name: str,
    sheet_data: Sequence[dict[str, str]],
    element_names: Counter,
    limit_to_columns: set[str] | None = None,
    ignore_columns: set[str] | None = None,
) -> None:
    """
    Parse all pyxform references, and raise an error if any are malformed or invalid.

    :param sheet_name: The XLSForm sheet the value is from.
    :param limit_to_columns: Only parse values in these columns.
    :param ignore_columns: Do not parse values in these columns.
    :param sheet_data: The XLSForm sheet data.
    :param element_names: The names in the 'survey' sheet 'name' column.
    """
    if not sheet_data:
        return

    for row_number, row in enumerate(sheet_data, start=2):
        for column, value in row.items():
            if limit_to_columns and column not in limit_to_columns:
                continue
            if ignore_columns and column in ignore_columns:
                continue
            try:
                refs = parse_pyxform_references(value=value)
            except PyXFormError as e:
                e.context.update(sheet=sheet_name, column=column, row=row_number)
                raise
            if refs:
                for ref in refs:
                    element_count = element_names.get(ref.name, None)
                    if element_count is None:
                        raise PyXFormError(
                            code=ErrorCode.PYREF_003,
                            context={
                                "row": row_number,
                                "sheet": sheet_name,
                                "column": column,
                                "q": ref.name,
                            },
                        )
                    elif 1 != element_count:
                        raise PyXFormError(
                            code=ErrorCode.PYREF_004,
                            context={
                                "row": row_number,
                                "sheet": sheet_name,
                                "column": column,
                                "q": ref.name,
                            },
                        )


def validate_pyxform_references_in_workbook(
    workbook_dict: "DefinitionData",
    survey_headers: tuple[tuple[str, ...], ...],
    choices_headers: tuple[tuple[str, ...], ...],
    element_names: Counter,
) -> None:
    """
    Parse pyxform references, and raise an error if any are malformed or invalid.

    The original workbook_dict data is used to a) allow row/column references in error
    message and b) avoid needing to iterate into sheet-specific nested data structures.

    The external_choices sheet isn't checked at all since this data is written to CSV for
    verbatim lookups and so cannot contain dynamic references.

    In the survey sheet, references aren't allowed for the  'type' and 'name' columns and
    this is validated separately, but since these columns have aliases, the parsed
    survey_headers is required to get the relevant actual column names to ignore.

    In the choices sheet, references are only inserted for translatable columns, and the
    choices sheet can contain a lot of extra data (e.g. for choice filters). So the
    parsed/validated choices_header is used to ignore extra data, using a positional
    lookup e.g. if 'label' is column 3 -> get 3rd column 'label::en'.

    :param workbook_dict: The XLSForm data.
    :param survey_headers: The parsed column headers for the survey sheet.
    :param choices_headers: The parsed column headers for the choices sheet.
    :param element_names: The names in the 'survey' sheet 'name' column.
    """
    # In order of likely smallest to largest.
    validate_pyxform_reference_syntax(
        sheet_name=co.SETTINGS,
        sheet_data=workbook_dict.settings,
        element_names=element_names,
    )
    # Avoids circular import.
    from pyxform.entities.entities_parsing import EC

    validate_pyxform_reference_syntax(
        sheet_name=co.ENTITIES,
        sheet_data=workbook_dict.entities,
        element_names=element_names,
        ignore_columns={co.LIST_NAME_S, co.LIST_NAME_U, EC.REPEAT},
    )

    # type is validated against the question_type_dict.
    # name is validated against XML tag name rules.
    # trigger is validated against question names only (not groups or repeats).
    survey_ignore_columns = {co.TYPE, co.NAME, "trigger"}
    if workbook_dict.survey_header:
        survey_ignore_columns = {
            tuple(workbook_dict.survey_header[0])[i]
            for i, c in enumerate(survey_headers, start=0)
            if c[0] in survey_ignore_columns
        }
    else:
        # The 'survey_header' may not be populated if pyxform is used as a library and
        # the caller passes in incomplete dict data (e.g. not using a pyxform parser).
        survey_ignore_columns = {
            tuple(workbook_dict.survey[0])[i]
            for i, c in enumerate(survey_headers, start=0)
            if c[0] in survey_ignore_columns
        }
    validate_pyxform_reference_syntax(
        sheet_name=co.SURVEY,
        sheet_data=workbook_dict.survey,
        element_names=element_names,
        ignore_columns=survey_ignore_columns,
    )

    if workbook_dict.choices_header:
        choices_limit_to_columns = {
            tuple(workbook_dict.choices_header[0])[i]
            for i, c in enumerate(choices_headers, start=0)
            if c[0] in aliases.TRANSLATABLE_CHOICES_COLUMNS
        }
    else:
        # The 'choices_header' may not be populated if pyxform is used as a library and
        # the caller passes in incomplete dict data (e.g. not using a pyxform parser).
        choices_limit_to_columns = {
            tuple(workbook_dict.choices[0])[i]
            for i, c in enumerate(choices_headers, start=0)
            if c[0] in aliases.TRANSLATABLE_CHOICES_COLUMNS
        }
    validate_pyxform_reference_syntax(
        sheet_name=co.CHOICES,
        sheet_data=workbook_dict.choices,
        element_names=element_names,
        limit_to_columns=choices_limit_to_columns,
    )
