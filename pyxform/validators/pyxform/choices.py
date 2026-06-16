from typing import Any

from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.validators.pyxform.pyxform_reference import has_pyxform_reference


def validate_headers(
    headers: tuple[tuple[str, ...], ...], warnings: list[str]
) -> tuple[str, ...]:
    def check():
        for header in headers:
            header = header[0]
            if header != co.LIST_NAME_S and (" " in header or header == ""):
                warnings.append(ErrorCode.HEADER_004.value.format(column=header))
                yield header

    return tuple(check())


def validate_choice_list(
    options: list[dict], warnings: list[str], allow_duplicates: bool = False
) -> None:
    seen_options = set()
    duplicate_errors = []
    for option in options:
        if co.NAME not in option:
            raise PyXFormError(ErrorCode.NAMES_006.value.format(row=option["__row"]))
        elif co.LABEL not in option:
            warnings.append(ErrorCode.LABEL_001.value.format(row=option["__row"]))

        if not allow_duplicates:
            name = option[co.NAME]
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


def add_choices_info_to_question(
    question: dict[str, Any],
    list_name: str,
    choices: dict[str, list],
    choice_filter: str | None = None,
    file_extension: str | None = None,
):
    """
    Add choices-related info to the question dict, e.g. itemset, list_name, choices, etc.

    :param question: A dict with question details.
    :param list_name: The choice list name for the question.
    :param choices: The available choices in the survey.
    :param choice_filter: The question's choice_filter, if any.
    :param file_extension: The question's external select file_extension, if any.
    :return: The updated question dict.
    """
    if choice_filter is None:
        choice_filter = ""
    if file_extension is None:
        file_extension = ""

    question[co.ITEMSET] = list_name

    if choice_filter:
        # External selects e.g. type = "select_one_external city".
        if question[co.TYPE] == co.SELECT_ONE_EXTERNAL:
            question["query"] = list_name
        elif choices.get(list_name):
            # Reference to list name for data dictionary tools (ilri/odktools).
            question[co.LIST_NAME_U] = list_name
            # Copy choices for data export tools (onaio/onadata).
            # TODO: could onadata use the list_name to look up the list for
            #  export, instead of pyxform internally duplicating choices data?
            question[co.CHOICES] = choices[list_name]
    elif not (
        # Select with randomized choices.
        (
            co.ParametersSelect.RANDOMIZE in question[co.PARAMETERS]
            and question[co.PARAMETERS][co.ParametersSelect.RANDOMIZE] == "true"
        )
        # Select from file e.g. type = "select_one_from_file cities.xml".
        or file_extension in co.EXTERNAL_INSTANCE_EXTENSIONS
        # Select from previous answers e.g. type = "select_one ${q1}".
        or has_pyxform_reference(list_name)
    ):
        question[co.LIST_NAME_U] = list_name
        question[co.CHOICES] = choices[list_name]
