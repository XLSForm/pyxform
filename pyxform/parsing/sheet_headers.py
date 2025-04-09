from collections.abc import Container, Sequence
from itertools import chain, islice
from typing import Any

from pyxform import constants
from pyxform.errors import PyXFormError

INVALID_HEADER = (
    "Invalid headers provided for sheet: '{sheet_name}'. For XLSForms, this may be due "
    "a missing header row, in which case add a header row as per the reference template "
    "https://xlsform.org/en/ref-table/. For internal API usage, may be due to a missing "
    "mapping for '{header}', in which case ensure that the full set of headers appear "
    "within the first 100 rows, or specify the header row in '{sheet_name}_header'."
)
INVALID_DUPLICATE = (
    "Invalid headers provided for sheet: '{sheet_name}'. Headers that are different "
    "names for the same column were found: '{other}', '{header}'. Rename or remove one "
    "of these columns."
)
INVALID_MISSING_REQUIRED = (
    "Invalid headers provided for sheet: '{sheet_name}'. One or more required column "
    "headers were not found: {missing}. "
    "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
)


def merge_dicts(
    dict_a: dict, dict_b: dict, default_key: str = constants.DEFAULT_LANGUAGE_VALUE
) -> dict:
    """
    Recursively merge two nested dicts into a single dict.

    When keys match their values are merged using a recursive call to this function,
    otherwise they are just added to the output dict.
    """
    if not dict_a:
        return dict_b
    if not dict_b:
        return dict_a

    if not isinstance(dict_a, dict):
        if default_key in dict_b:
            return dict_b
        dict_a = {default_key: dict_a}
    if not isinstance(dict_b, dict):
        if default_key in dict_a:
            return dict_a
        dict_b = {default_key: dict_b}

    # Union keys but retain order (as opposed to set()), preferencing dict_a then dict_b.
    # E.g. {"a": 1, "b": 2} + {"c": 3, "a": 4} -> {"a": None, "b": None, "c": None}
    out_dict = dict_a
    for key in {k: None for k in (chain(dict_a, dict_b))}:
        out_dict[key] = merge_dicts(dict_a.get(key), dict_b.get(key), default_key)
    return out_dict


def list_to_nested_dict(lst: Sequence) -> dict:
    """
    [1,2,3,4] -> {1:{2:{3:4}}}
    """
    if len(lst) > 1:
        return {lst[0]: list_to_nested_dict(lst[1:])}
    else:
        return lst[0]


class DealiasAndGroupHeadersResult:
    __slots__ = ("headers", "data")

    def __init__(self, headers: tuple[tuple[str, ...], ...], data: Sequence[dict]):
        """
        :param headers: Distinct headers seen in the sheet, parsed / split if applicable.
        :param data: Sheet data rows, in grouped dict format.
        """
        self.headers: tuple[tuple[str, ...], ...] = headers
        self.data: Sequence[dict] = data


def to_snake_case(value: str) -> str:
    """
    Convert a name (e.g. column name or question type) to snake case.

    Removes duplicate, leading, trailing spaces.
    """
    return "_".join(value.split()).lower()


def process_header(
    header: str,
    use_double_colon: bool,
    header_aliases: dict[str, str | tuple[str, ...]],
    header_columns: Container[str],
) -> tuple[str, tuple[str, ...]]:
    """
    Lookup the header in the provided expected columns or aliases, or split the header.

    :param header: Original XLSForm data header.
    :param use_double_colon: If True, split the header on "::" rather than ":" (deprecated).
    :param header_aliases: Mapping of original headers to aliased (possibly split) headers.
    :param header_columns: The expected headers for the sheet.
    :return e.g. tuple[original, tuple[new,]] | tuple[original, tuple[new1, new2]]
    """
    # If the header is already recognised then nothing further needed.
    if header in header_columns and header not in header_aliases:
        return header, (header,)

    # Also try normalising to snake_case.
    header_normalised = to_snake_case(value=header)
    if header_normalised in header_columns and header_normalised not in header_aliases:
        return header_normalised, (header_normalised,)

    # Check for double columns to determine whether to use them or single colons to
    # delimit grouped headers. Single colons are bad because they conflict with with the
    # xform namespace syntax (i.e. jr:constraintMsg), so they are only used if necessary
    # for backwards compatibility.
    group_delimiter = "::"
    if use_double_colon or group_delimiter in header:
        tokens = tuple(t.strip() for t in header.split(group_delimiter))
    else:
        tokens = tuple(t.strip() for t in header.split(":"))
        # Handle "jr:count" or similar when used with single colon delimiters.
        if "jr" in tokens:
            jr_idx = tokens.index("jr")
            tokens = (
                *tokens[0:jr_idx],
                f"jr:{tokens[jr_idx + 1]}",
                *tokens[jr_idx + 2 :],
            )

    new_header = to_snake_case(tokens[0])
    dealiased_first_token = header_aliases.get(new_header)
    if dealiased_first_token:
        new_header = dealiased_first_token
        if isinstance(new_header, tuple):
            tokens = (*new_header, *tokens[1:])
        else:
            tokens = (new_header, *tokens[1:])
    elif new_header in header_columns:
        tokens = (new_header, *tokens[1:])
    # Avoid changing unknown columns, since it could break choice_filter expressions.
    else:
        new_header = header
        tokens = tuple(tokens)
    return new_header, tokens


def process_row(
    sheet_name: str,
    row: dict[str, str],
    header_key: dict[str, tuple[str, ...]],
    default_language: str = constants.DEFAULT_LANGUAGE_VALUE,
) -> dict[str, str]:
    """
    Convert original headers and values to a possibly nested structure.

    :param sheet_name: Name of the sheet data being processed.
    :param row: Original XLSForm data row.
    :param header_key: Mapping from original headers to headers split on a delimiter.
    :param default_language: Default translation language for the form, used to group
      used to group labels/hints/etc without a language specified with localized versions.
    """
    out_row = {}
    for header, val in row.items():
        tokens = header_key.get(header, None)
        if header == "__row":
            out_row[header] = val
        elif not tokens:
            raise PyXFormError(
                INVALID_HEADER.format(sheet_name=sheet_name, header=header)
            )
        elif len(tokens) == 1:
            out_row[tokens[0]] = val
        else:
            new_value = list_to_nested_dict((*tokens[1:], val))
            out_row = merge_dicts(out_row, {tokens[0]: new_value}, default_language)

    return out_row


def dealias_and_group_headers(
    sheet_name: str,
    sheet_data: Sequence[dict[str, str]],
    sheet_header: Sequence[dict[str, Any]],
    header_aliases: dict[str, str],
    header_columns: set[str],
    headers_required: set[str] | None = None,
    default_language: str = constants.DEFAULT_LANGUAGE_VALUE,
) -> DealiasAndGroupHeadersResult:
    """
    Normalise headers and group keys that contain a delimiter.

    For example a row:
        {"text::english": "hello", "text::french" : "bonjour"}
    Becomes
        {"text": {"english": "hello", "french" : "bonjour"}.

    Dealiasing is done to the first token (the first term separated by the delimiter).

    :param sheet_name: Name of the sheet data being processed.
    :param sheet_data: The sheet data.
    :param sheet_header: The sheet column names (headers).
    :param header_aliases: Mapping of allowed column aliases (backwards compatibility).
    :param header_columns: Expected columns for the sheet.
    :param headers_required: Required columns for the sheet.
    :param default_language: Default translation language for the form, used to group
      used to group labels/hints/etc without a language specified with localized versions.
    """

    header_key: dict[str, tuple[str, ...]] = {}
    tokens_key: dict[tuple[str, ...], str] = {}

    # If not specified, try to guess the headers from the first 100 rows of data.
    # Should only happen if the XLSForm is provided as a dict with no "_headers" keys.
    if not sheet_header and sheet_data:
        sheet_header = {}
        for row in islice(sheet_data, 0, 100):
            for k in row:
                sheet_header[k] = None
        sheet_header = [sheet_header]

    if sheet_header:
        use_double_colon = any("::" in k for k in sheet_header[0])
        for header in sheet_header[0]:
            tokens = header_key.get(header, None)
            if tokens is None:
                new_header, tokens = process_header(
                    header=header,
                    use_double_colon=use_double_colon,
                    header_aliases=header_aliases,
                    header_columns=header_columns,
                )
                other_header = tokens_key.get(tokens)
                if other_header and new_header != header:
                    raise PyXFormError(
                        INVALID_DUPLICATE.format(
                            sheet_name=sheet_name,
                            other=other_header,
                            header=header,
                        )
                    )
                header_key[header] = tokens
                tokens_key[tokens] = header

    data = tuple(
        process_row(
            sheet_name=sheet_name,
            row=row,
            header_key=header_key,
            default_language=default_language,
        )
        for row in sheet_data
    )
    if headers_required and (data or sheet_name == constants.SURVEY):
        missing = {h for h in headers_required if h not in {h[0] for h in tokens_key}}
        if missing:
            raise PyXFormError(
                INVALID_MISSING_REQUIRED.format(
                    sheet_name=sheet_name, missing=", ".join(f"'{h}'" for h in missing)
                )
            )
    return DealiasAndGroupHeadersResult(headers=tuple(tokens_key), data=data)
