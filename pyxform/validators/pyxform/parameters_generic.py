from typing import Any, Dict, Sequence

from pyxform.errors import PyXFormError

PARAMETERS_TYPE = Dict[str, Any]


def parse(raw_parameters: str) -> PARAMETERS_TYPE:
    parts = raw_parameters.split(";")
    if len(parts) == 1:
        parts = raw_parameters.split(",")
    if len(parts) == 1:
        parts = raw_parameters.split()

    params = {}
    for param in parts:
        if "=" not in param:
            raise PyXFormError(
                "Expecting parameters to be in the form of "
                "'parameter1=value parameter2=value'."
            )
        k, v = param.split("=")[:2]
        key = k.lower().strip()
        params[key] = v.lower().strip()

    return params


def validate(
    parameters: PARAMETERS_TYPE,
    allowed: Sequence[str],
) -> Dict[str, str]:
    """
    Raise an error if 'parameters' includes any keys not named in 'allowed'.
    """
    extras = set(parameters.keys()) - (set(allowed))
    if 0 < len(extras):
        msg = (
            "Accepted parameters are '{a}'. "
            "The following are invalid parameter(s): '{e}'."
        ).format(a=", ".join(sorted(allowed)), e=", ".join(sorted(extras)))
        raise PyXFormError(msg)
    return parameters
