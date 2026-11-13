"""Validations for label/hint/media."""

from collections.abc import Mapping

from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_HAS_CONTROL
from pyxform.utils import coalesce


def validate_big_image(row: dict, row_num: int, sheet_name: str) -> bool:
    """A 'big-image' value must be accompanied by an 'image' value."""
    if co.MEDIA in row and "big-image" in row[co.MEDIA] and "image" not in row[co.MEDIA]:
        raise PyXFormError(
            code=ErrorCode.LABEL_002, context={"row": row_num, "sheet": sheet_name}
        )
    else:
        return True


def question_must_have_visible_control(row: Mapping) -> bool:
    """
    Determine whether the question definition must have a label/hint/media.

    Or in other words, would this question need to have a user-visible form control.
    """
    return (
        # Has a default control tag.
        row.get(co.TYPE) in QUESTION_TYPE_HAS_CONTROL
        # Has a calculation that sets the value.
        and not coalesce(row.get(co.BIND), {}).get(co.CALCULATE)
        # Has a trigger that clears (or sets) the value.
        and not row.get(co.TRIGGER)
        # Is a row header for a field-list group grid.
        and not coalesce(row.get(co.CONTROL), {}).get(co.APPEARANCE)
        == co.APPEARANCE_LABEL
    )


def question_has_control_content(row: Mapping) -> bool:
    return bool(row.get(co.LABEL) or row.get(co.HINT) or row.get(co.MEDIA))


def validate_control_content(row: dict, row_num: int) -> bool:
    """Check if a question has user-visible control content."""
    if question_must_have_visible_control(row=row) and not question_has_control_content(
        row=row
    ):
        raise PyXFormError(code=ErrorCode.LABEL_003, context={"row": row_num})
    else:
        return True
