import re
from typing import KeysView, Optional

from pyxform import constants
from pyxform.utils import levenshtein_distance

# http://www.w3.org/TR/REC-xml/
TAG_START_CHAR = r"[a-zA-Z:_]"
TAG_CHAR = r"[a-zA-Z:_0-9\-.]"
XFORM_TAG_REGEXP = "%(start)s%(char)s*" % {"start": TAG_START_CHAR, "char": TAG_CHAR}


def find_sheet_misspellings(key: str, keys: "KeysView") -> "Optional[str]":
    """
    Find possible sheet name misspellings to warn the user about.

    It's possible that this will warn about sheet names for sheets that have
    auxilliary metadata that is not meant for processing by pyxform. For
    example the "osm" sheet name may be similar to many other initialisms.

    :param key: The sheet name to look for.
    :param keys: The workbook sheet names.
    """
    candidates = tuple(
        _k  # thanks to black
        for _k in keys
        if 2 >= levenshtein_distance(_k.lower(), key)
        and _k not in constants.SUPPORTED_SHEET_NAMES
        and not _k.startswith("_")
    )
    if 0 < len(candidates):
        msg = (
            "When looking for a sheet named '{k}', the following sheets with "
            "similar names were found: {c}."
        ).format(k=key, c=str(", ".join(("'{}'".format(c) for c in candidates))))
        return msg
    else:
        return None


def is_valid_xml_tag(tag):
    """
    Use a regex to see if there are any invalid characters (i.e. spaces).
    """
    return re.search(r"^" + XFORM_TAG_REGEXP + r"$", tag)
