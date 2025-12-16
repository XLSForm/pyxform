from pyxform import constants
from pyxform.errors import ErrorCode, PyXFormError


def validate_headers(
    headers: tuple[tuple[str, ...], ...], warnings: list[str]
) -> tuple[str, ...]:
    def check():
        for header in headers:
            header = header[0]
            if header != constants.LIST_NAME_S and (" " in header or header == ""):
                warnings.append(ErrorCode.HEADER_004.value.format(column=header))
                yield header

    return tuple(check())


def validate_choice_list(
    options: list[dict], warnings: list[str], allow_duplicates: bool = False
) -> None:
    seen_options = set()
    duplicate_errors = []
    for option in options:
        if constants.NAME not in option:
            raise PyXFormError(ErrorCode.NAMES_006.value.format(row=option["__row"]))
        elif constants.LABEL not in option:
            warnings.append(ErrorCode.LABEL_001.value.format(row=option["__row"]))

        if not allow_duplicates:
            name = option[constants.NAME]
            if name in seen_options:
                duplicate_errors.append(
                    ErrorCode.NAMES_007.value.format(row=option["__row"])
                )
            else:
                seen_options.add(name)

    if duplicate_errors:
        raise PyXFormError("\n".join(duplicate_errors))


def validate_and_clean_choices(
    choices: dict[str, list[dict]],
    warnings: list[str],
    headers: tuple[tuple[str, ...], ...],
    allow_duplicates: bool = False,
) -> dict[str, list[dict]]:
    """
    Warn about invalid or duplicate choices, and remove choices with invalid headers.

    Choices columns are output as XML elements so they must be valid XML tags.

    :param choices: Choices data from the XLSForm.
    :param warnings: Warnings list.
    :param headers: choices data headers i.e. unique dict keys.
    :param allow_duplicates: If True, duplicate choice names are allowed in the XLSForm.
    """
    invalid_headers = validate_headers(headers, warnings)
    for options in choices.values():
        validate_choice_list(
            options=options,
            warnings=warnings,
            allow_duplicates=allow_duplicates,
        )
        for option in options:
            for invalid_header in invalid_headers:
                option.pop(invalid_header, None)
            option.pop("__row", None)
    return choices
