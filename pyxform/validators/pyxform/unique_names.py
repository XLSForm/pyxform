from pyxform import constants as const
from pyxform.errors import Detail, PyXFormError

NAMES001 = Detail(
    name="Invalid duplicate name in same context",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
        "Questions, groups, and repeats must be unique within their nearest parent group "
        "or repeat, or the survey if not inside a group or repeat."
    ),
)
NAMES002 = Detail(
    name="Invalid duplicate name in context (case-insensitive)",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is problematic. "
        "The name is a case-insensitive match to another name. Questions, groups, and "
        "repeats should be unique within the nearest parent group or repeat, or the survey "
        "if not inside a group or repeat. Some data processing tools are not "
        "case-sensitive, so the current names may make analysis difficult."
    ),
)
NAMES003 = Detail(
    name="Invalid repeat name same as survey",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
        "Repeat names must not be the same as the survey root (which defaults to 'data')."
    ),
)
NAMES004 = Detail(
    name="Invalid duplicate repeat name in the survey",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
        "Repeat names must unique anywhere in the survey, at all levels of group or "
        "repeat nesting."
    ),
)
NAMES005 = Detail(
    name="Invalid duplicate meta name in the survey",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'name' value 'meta' is invalid. "
        "The name 'meta' is reserved for form metadata."
    ),
)


def validate_question_group_repeat_name(
    name: str | None,
    seen_names: set[str],
    seen_names_lower: set[str],
    warnings: list[str],
    row_number: int | None = None,
    check_reserved: bool = True,
):
    """
    Warn about duplicate or problematic names on the survey sheet.

    May append the name to `seen_names` and `neen_names_lower`. May append to `warnings`.

    :param name: Question or group name.
    :param seen_names: Names already processed in the sheet.
    :param seen_names_lower: Same as seen_names but lower case.
    :param warnings: Warnings list.
    :param row_number: Current sheet row number.
    :param check_reserved: If True, check the name against any reserved names. When
      checking names in the context of SurveyElement processing, it's difficult to
      differentiate user-specified names from names added by pyxform.
    """
    if not name:
        return

    if check_reserved and not seen_names >= const.RESERVED_NAMES_SURVEY_SHEET:
        seen_names.update(const.RESERVED_NAMES_SURVEY_SHEET)

    if name in seen_names:
        if name == const.META:
            raise PyXFormError(NAMES005.format(row=row_number))
        else:
            raise PyXFormError(NAMES001.format(row=row_number, value=name))
    seen_names.add(name)

    question_name_lower = name.lower()
    if question_name_lower in seen_names_lower:
        # No case-insensitive warning for 'meta' since it's not an exported data table.
        warnings.append(NAMES002.format(row=row_number, value=name))
    seen_names_lower.add(question_name_lower)


def validate_repeat_name(
    name: str | None,
    control_type: str,
    instance_element_name: str,
    seen_names: set[str],
    row_number: int | None = None,
):
    """
    Warn about duplicate or problematic names.

    May appends the name to `seen_names` and `neen_names_lower`. May append to `warnings`.
    These checks are additional to the above in validate_survey_sheet_name so does not
    re-check reserved names etc.

    :param row_number: Current sheet row number.
    :param name: Question or group name.
    :param control_type: E.g. group, repeat, or loop.
    :param instance_element_name: Name of the main survey instance element.
    :param seen_names: Names already processed in the sheet.
    """
    if control_type == const.REPEAT:
        if name == instance_element_name:
            raise PyXFormError(NAMES003.format(row=row_number, value=name))
        elif name in seen_names:
            raise PyXFormError(NAMES004.format(row=row_number, value=name))
        seen_names.add(name)
