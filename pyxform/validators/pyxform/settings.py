from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import is_xml_tag


def validate_form_name(form_name: str | None):
    """
    The form_name must be a valid XML tag since it is used for the primary instance element.

    :param form_name: The value to check.
    """
    if form_name is not None and not is_xml_tag(value=form_name):
        raise PyXFormError(ErrorCode.NAMES_009.value.format(name="form_name"))
