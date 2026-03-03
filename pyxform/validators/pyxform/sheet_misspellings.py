from collections.abc import Iterable

from pyxform import constants
from pyxform.errors import ErrorCode
from pyxform.utils import levenshtein_distance


def find_sheet_misspellings(key: str, keys: Iterable) -> "str | None":
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
        _k  # thanks to black
        for _k in keys
        if 2 >= levenshtein_distance(_k.lower(), key)
        and _k not in constants.SUPPORTED_SHEET_NAMES
        and not _k.startswith("_")
    )
    if 0 < len(candidates):
        return ErrorCode.NAMES_013.value.format(
            sheet=key, candidates=str(", ".join(f"'{c}'" for c in candidates))
        )
    else:
        return None
