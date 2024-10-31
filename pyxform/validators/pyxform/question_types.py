"""
Validations for question types.
"""

from pyxform.errors import PyXFormError
from pyxform.parsing.expression import is_pyxform_reference
from pyxform.utils import PYXFORM_REFERENCE_REGEX

BACKGROUND_GEOPOINT_CALCULATION = "[row : {r}] For 'background-geopoint' questions, the 'calculation' column must be empty."
TRIGGER_INVALID = (
    "[row : {r}] For '{t}' questions, the 'trigger' column must be a reference to another "
    "question that exists, in the format ${{question_name_here}}."
)


def validate_background_geopoint_calculation(row: dict, row_num: int) -> bool:
    """A background-geopoint must not have a calculation."""
    try:
        row["bind"]["calculate"]
    except KeyError:
        return True
    else:
        raise PyXFormError(BACKGROUND_GEOPOINT_CALCULATION.format(r=row_num))


def validate_background_geopoint_trigger(row: dict, row_num: int) -> bool:
    """A background-geopoint must have a trigger."""
    if not row.get("trigger", False) or not is_pyxform_reference(value=row["trigger"]):
        raise PyXFormError(TRIGGER_INVALID.format(r=row_num, t=row["type"]))
    return True


def validate_references(referrers: list[tuple[dict, int]], questions: set[str]) -> bool:
    """Triggers must refer to a question that exists."""
    for row, row_num in referrers:
        matches = PYXFORM_REFERENCE_REGEX.match(row["trigger"])
        if matches is not None:
            trigger = matches.groups()[0]
            if trigger not in questions:
                raise PyXFormError(TRIGGER_INVALID.format(r=row_num, t=row["type"]))
    return True
