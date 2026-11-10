from collections.abc import Iterable

from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.utils import levenshtein_distance


def find_sheet_misspellings(key: str, keys: Iterable[str]) -> str | None:
    """
    Find possible sheet name misspellings to warn the user about.

    It's possible that this will warn about sheet names for sheets that have
    auxilliary metadata that is not meant for processing by pyxform. For
    example the "osm" sheet name may be similar to many other initialisms.

    :param key: The sheet name to look for.
    :param keys: The workbook sheet names.
    """
    if not keys:
        return None
    candidates = tuple(
        _k
        for _k in keys
        if 2 >= levenshtein_distance(_k.lower(), key)
        and _k not in co.SUPPORTED_SHEET_NAMES
        and not _k.startswith("_")
    )
    if 0 < len(candidates):
        return ", ".join(f"'{c}'" for c in candidates)
    else:
        return None


def validate_survey(sheet_names: Iterable[str]) -> None:
    """
    Check for misspellings of the 'survey' sheet.

    :param sheet_names: The XLSForm sheet names.
    """
    similar = find_sheet_misspellings(key=co.SURVEY, keys=sheet_names)
    if similar is None:
        raise PyXFormError(code=ErrorCode.SURVEY_011)
    else:
        raise PyXFormError(code=ErrorCode.SURVEY_012, context={"candidates": similar})


def validate_optional(
    sheet_name: str, sheet_names: Iterable[str], warnings: list[str]
) -> list[str]:
    """
    Check for misspellings of optional sheets (settings, entities), add a warning if relevant.

    :param sheet_name: The sheet name to check.
    :param sheet_names: The XLSForm sheet names.
    :param warnings: Warnings list.
    """
    similar = find_sheet_misspellings(key=sheet_name, keys=sheet_names)
    if similar is not None:
        warnings.append(
            ErrorCode.NAMES_013.value.format(sheet=sheet_name, candidates=similar)
        )
    return warnings


def validate_choices(
    row_number: int, sheet_name: str, sheet_names: Iterable[str]
) -> None:
    """
    Check for misspellings of the (external) choices sheets.

    :param row_number: The row number of a select control that would require choices.
    :param sheet_name: The sheet name to check.
    :param sheet_names: The XLSForm sheet names.
    """
    similar = find_sheet_misspellings(key=sheet_name, keys=sheet_names)
    if similar is None:
        raise PyXFormError(
            code=ErrorCode.SURVEY_013,
            context={"row": row_number, "missing": sheet_name},
        )
    else:
        raise PyXFormError(
            code=ErrorCode.SURVEY_014,
            context={"row": row_number, "missing": sheet_name, "candidates": similar},
        )
