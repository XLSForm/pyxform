from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import is_xml_tag


def validate_name(name: str | None, from_sheet: bool = True):
    """
    The name must be a valid XML Name since it is used for the primary instance element.

    :param name: The value to check.
    :param from_sheet: If True, the value is from the settings sheet (rather than the
      file name or form_name API usage), so the sheet name should be included in the
      error (if any).
    """
    if name is not None and not is_xml_tag(value=name):
        if from_sheet:
            raise PyXFormError(
                ErrorCode.NAMES_008.value.format(sheet=co.SETTINGS, row=1, column=co.NAME)
            )
        else:
            raise PyXFormError(ErrorCode.NAMES_009.value.format(name="form_name"))
