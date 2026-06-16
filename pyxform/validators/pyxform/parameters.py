from typing import Any

from pyxform.errors import ErrorCode, PyXFormError
from pyxform.util.enum import StrEnum

PARAMETERS_TYPE = dict[str, Any]


def validate(
    parameters: PARAMETERS_TYPE,
    accepted: type[StrEnum],
    row_number: int,
) -> None:
    """
    Raise an error if 'parameters' includes any keys not named in 'accepted'.
    """
    extras = set(parameters) - accepted.value_set()
    if 0 < len(extras):
        raise PyXFormError(
            ErrorCode.SURVEY_005.value.format(
                row=row_number,
                accepted=accepted.value_str_sorted(),
                rejected=", ".join(sorted(extras)),
            )
        )
