from collections.abc import Container, Sequence
from itertools import chain

from pyxform import constants
from pyxform.errors import PyXFormError


def merge_dicts(dict_a: dict, dict_b: dict, default_key: str = "default") -> dict:
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
    all_keys = {k: None for k in (chain(dict_a, dict_b))}

    out_dict = dict_a
    for key in all_keys:
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
) -> tuple[str, tuple[str, ...], bool]:
    # If the header is already recognised then nothing further needed.
    if header in header_columns and header not in header_aliases:
        return header, (header,), use_double_colon

    # Also try normalising to snake_case.
    header_normalised = to_snake_case(value=header)
    if header_normalised in header_columns and header_normalised not in header_aliases:
        return header_normalised, (header_normalised,), use_double_colon

    # Check for double columns to determine whether to use them or single colons to
    # delimit grouped headers. Single colons are bad because they conflict with with the
    # xform namespace syntax (i.e. jr:constraintMsg), so they are only used if necessary
    # for backwards compatibility.
    group_delimiter = "::"
    if use_double_colon or group_delimiter in header:
        use_double_colon = True
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
    return new_header, tokens, use_double_colon


def dealias_and_group_headers(
    sheet_name: str,
    dict_array: list[dict],
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
    :param dict_array: The sheet data.
    :param header_aliases: Mapping of allowed column aliases (backwards compatibility).
    :param header_columns: Expected columns for the sheet.
    :param headers_required: Required columns for the sheet.
    :param default_language: Default translation language for the form, used to group
      used to group labels/hints/etc without a language specified with localized versions.
    """

    header_key: dict[str, tuple[str, ...]] = {}
    tokens_key: dict[tuple[str, ...], str] = {}

    def process_row(row):
        use_double_colon = False
        out_row = {}
        for header, val in row.items():
            tokens = header_key.get(header, None)
            if tokens is None:
                new_header, tokens, use_double_colon = process_header(
                    header=header,
                    use_double_colon=use_double_colon,
                    header_aliases=header_aliases,
                    header_columns=header_columns,
                )
                other_header = tokens_key.get(tokens)
                if other_header and new_header != header:
                    raise PyXFormError(
                        f"While processing the '{sheet_name}' sheet, columns which are "
                        f"different names for the same column were found: '{other_header}'"
                        f", '{header}'. Please remove or rename one of these columns."
                    )
                header_key[header] = tokens
                tokens_key[tokens] = header

            if len(tokens) == 1:
                out_row[tokens[0]] = val
            else:
                new_value = list_to_nested_dict((*tokens[1:], val))
                out_row = merge_dicts(out_row, {tokens[0]: new_value}, default_language)

        return out_row

    data = tuple(process_row(row) for row in dict_array)
    if headers_required and (data or sheet_name == constants.SURVEY):
        missing = {h for h in headers_required if h not in {h[0] for h in tokens_key}}
        if missing:
            raise PyXFormError(
                f"The '{sheet_name}' sheet is missing one or more required column "
                f"""headers: {', '.join(f"'{h}'" for h in missing)}."""
            )
    return DealiasAndGroupHeadersResult(headers=tuple(tokens_key), data=data)
