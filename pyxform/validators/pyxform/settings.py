from urllib.parse import urlsplit

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


def validate_submission_url(submission_url: str | None):
    """
    The submission_url must be a full HTTP(S) URL.

    :param submission_url: The value to check.
    """
    if submission_url in {None, ""}:
        return

    try:
        parsed = urlsplit(submission_url)
    except ValueError as err:
        raise PyXFormError(ErrorCode.SETTINGS_001.value.format()) from err

    if (
        any(c.isspace() for c in submission_url)
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.hostname is None
    ):
        raise PyXFormError(ErrorCode.SETTINGS_001.value.format())
