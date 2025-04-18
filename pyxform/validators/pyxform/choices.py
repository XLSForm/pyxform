from pyxform import constants
from pyxform.errors import PyXFormError

INVALID_NAME = (
    "[row : {row}] On the 'choices' sheet, the 'name' value is invalid. "
    "Choices must have a name. "
    "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
)
INVALID_LABEL = (
    "[row : {row}] On the 'choices' sheet, the 'label' value is invalid. "
    "Choices should have a label. "
    "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
)
INVALID_HEADER = (
    "[row : 1] On the 'choices' sheet, the '{column}' value is invalid. "
    "Column headers must not be empty and must not contain spaces. "
    "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
)
INVALID_DUPLICATE = (
    "[row : {row}] On the 'choices' sheet, the 'name' value is invalid. "
    "Choice names must be unique for each choice list. "
    "If this is intentional, use the setting 'allow_choice_duplicates'. "
    "Learn more: https://xlsform.org/#choice-names."
)


def validate_headers(
    headers: tuple[tuple[str, ...], ...], warnings: list[str]
) -> tuple[str, ...]:
    def check():
        for header in headers:
            header = header[0]
            if header != constants.LIST_NAME_S and (" " in header or header == ""):
                warnings.append(INVALID_HEADER.format(column=header))
                yield header

    return tuple(check())


def validate_choice_list(
    options: list[dict], warnings: list[str], allow_duplicates: bool = False
) -> None:
    seen_options = set()
    duplicate_errors = []
    for option in options:
        if constants.NAME not in option:
            raise PyXFormError(INVALID_NAME.format(row=option["__row"]))
        elif constants.LABEL not in option:
            warnings.append(INVALID_LABEL.format(row=option["__row"]))

        if not allow_duplicates:
            name = option[constants.NAME]
            if name in seen_options:
                duplicate_errors.append(INVALID_DUPLICATE.format(row=option["__row"]))
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
