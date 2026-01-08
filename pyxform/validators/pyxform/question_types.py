"""
Validations for question types.
"""

from collections.abc import Collection, Iterable

from pyxform import aliases
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.validators.pyxform.pyxform_reference import (
    is_pyxform_reference_candidate,
    parse_pyxform_references,
)

BACKGROUND_GEOPOINT_CALCULATION = (
    "[row : {r}] For 'background-geopoint' questions, "
    "the 'calculation' column must be empty."
)
BACKGROUND_GEOPOINT_TRIGGER = (
    "[row : {r}] For 'background-geopoint' questions, "
    "the 'trigger' column must not be empty."
)


def validate_background_geopoint_calculation(row: dict, row_num: int) -> bool:
    """A background-geopoint must not have a calculation."""
    try:
        row["bind"]["calculate"]
    except KeyError:
        return True
    else:
        raise PyXFormError(BACKGROUND_GEOPOINT_CALCULATION.format(r=row_num))


def validate_background_geopoint_trigger(trigger: str | None, row_num: int) -> bool:
    """A background-geopoint must have a trigger."""
    if not trigger:
        raise PyXFormError(BACKGROUND_GEOPOINT_TRIGGER.format(r=row_num))
    return True


def validate_references(
    referrers: Iterable[Iterable[str | None, int]], questions: Collection[str]
) -> bool:
    """Pyxform references must refer to a question that exists."""
    for target, row_num in referrers:
        if target not in questions:
            raise PyXFormError(
                code=ErrorCode.PYREF_003, context={"q": target, "row": row_num}
            )
    return True


def process_trigger(
    trigger: str | None, row_num: int, trigger_references: list[tuple[str, int]]
) -> tuple[str, ...] | None:
    """
    Try to parse the content of the "trigger" column into a list of question names.

    A trigger may contain one pyxform reference, or multiple comma-separated references.
    If a trigger is found, it will be added to trigger_references.

    :param trigger: The trigger data.
    :param row_num: The current row number.
    :param trigger_references: Which questions are being referred to by which row.
    """
    if not trigger:
        return None
    elif not is_pyxform_reference_candidate(trigger):
        raise PyXFormError(
            code=ErrorCode.PYREF_001,
            context={
                "sheet": "survey",
                "column": "trigger",
                "row": row_num,
                "q": trigger,
            },
        )

    try:
        trigger = tuple(
            r.name
            for t in trigger.split(",")
            for r in parse_pyxform_references(value=t, match_limit=1)
        )
    except PyXFormError as e:
        e.context.update(sheet="survey", column="trigger", row=row_num)
        raise

    if trigger:
        trigger_references.extend((t, row_num) for t in trigger)
        return trigger
    else:
        return None


def validate_geo_parameter_incremental(value: str) -> None:
    """For geoshape and geotrace, the 'incremental' parameter can only resolve to 'true'."""
    incremental = aliases.yes_no.get(value, None)
    if incremental is None or not incremental:
        raise PyXFormError(
            code=ErrorCode.SURVEY_003,
        )
