"""Validations for label/hint/media."""

from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError


def validate_big_image(row: dict, row_num: int, sheet_name: str) -> bool:
    """A 'big-image' value must be accompanied by an 'image' value."""
    if co.MEDIA in row and "big-image" in row[co.MEDIA] and "image" not in row[co.MEDIA]:
        raise PyXFormError(
            code=ErrorCode.LABEL_002, context={"row": row_num, "sheet": sheet_name}
        )
    else:
        return True
