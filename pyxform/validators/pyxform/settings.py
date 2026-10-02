from pyxform import constants as co
from pyxform.aliases import yes_no
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import is_xml_tag

# setting name, default value.
BOOL_SETTINGS = {
    "add_none_option": "no",
    "clean_text_values": "yes",
    "omit_instanceID": "no",
    co.ALLOW_CHOICE_DUPLICATES: "no",
    co.AUTO_DELETE: "no",
    co.AUTO_SEND: "no",
    co.CLIENT_EDITABLE: "no",
}


def resolve_bool_settings(settings: dict, warnings: list[str]) -> None:
    """
    Update the settings data with resolved values for bool settings.

    :param settings: The settings data.
    :param warnings: If a value did not resolve, the default value is used with a warning.
    """
    for name, default in BOOL_SETTINGS.items():
        if name in settings:
            value = settings[name]
            resolved = yes_no.get(value, None)
            if resolved is None:
                warnings.append(
                    ErrorCode.SETTING_001.value.format(
                        name=name, value=value, default=default
                    ),
                )
                resolved = yes_no.get(default, False)
            settings[name] = resolved


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
