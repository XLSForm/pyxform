from pyxform import constants as co
from pyxform.errors import PyXFormError
from pyxform.parsing.expression import parse_expression

PYXFORM_REFERENCE_INVALID = (
    "[row : {row_number}] On the '{sheet}' sheet, the '{column}' value is invalid. "
    "Reference expressions must only include question names, and end with '}}'."
)


def validate_pyxform_reference_syntax(
    value: str, sheet_name: str, row_number: int, key: str
) -> None:
    # Needs 3 characters for "${}" plus a name inside, but need to catch ${ for warning.
    if not value or len(value) <= 2 or "${" not in value:
        return
    # Skip columns in potentially large sheets where references are not allowed.
    elif sheet_name == co.SURVEY:
        if key in {co.TYPE, co.NAME}:
            return
    elif sheet_name == co.CHOICES:
        if key in {co.LIST_NAME_S, co.LIST_NAME_U, co.NAME}:
            return
    elif sheet_name == co.ENTITIES:
        if key in {co.LIST_NAME_S, co.LIST_NAME_U}:
            return

    tokens, _ = parse_expression(value)
    start_token = None

    for t in tokens:
        # The start of an expression.
        if t is not None and t.name == "PYXFORM_REF_START" and start_token is None:
            start_token = t
        # Tokens that are part of an expression.
        elif start_token is not None:
            if t.name == "NAME":
                continue
            elif t.name == "PYXFORM_REF_END":
                start_token = None
            elif t.name in ("PYXFORM_REF_START", "PYXFORM_REF"):
                msg = PYXFORM_REFERENCE_INVALID.format(
                    sheet=sheet_name, row_number=row_number, column=key
                )
                raise PyXFormError(msg)
            else:
                msg = PYXFORM_REFERENCE_INVALID.format(
                    sheet=sheet_name, row_number=row_number, column=key
                )
                raise PyXFormError(msg)

    if start_token is not None:
        msg = PYXFORM_REFERENCE_INVALID.format(
            sheet=sheet_name, row_number=row_number, column=key
        )
        raise PyXFormError(msg)
