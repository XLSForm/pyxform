"""
Validations for question types.
"""

from collections.abc import Collection, Iterable

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


def parse_trigger(trigger: str | None) -> tuple[str, ...] | None:
    """A trigger may contain one pyxform reference, or multiple comma-separated references."""
    if not trigger:
        return None

    if is_pyxform_reference_candidate(trigger):
        trigger_values = trigger.split(",")
        trigger_refs = tuple(
            r
            for t in trigger_values
            for r in parse_pyxform_references(value=t, match_limit=1)
        )
        if trigger_refs:
            return trigger_refs
    else:
        raise PyXFormError(code=ErrorCode.PYREF_001, context={"q": trigger})
