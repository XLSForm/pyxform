"""
Aliases for elements which could mean the same element in XForm but is represented
differently on the XLSForm.
"""

from pyxform import constants

# Aliases:
# Ideally aliases should resolve to elements in the json form schema

# select, control and settings alias keys used for parsing,
# which is why self mapped keys are necessary.

control = {
    "group": constants.GROUP,
    "lgroup": constants.REPEAT,
    "repeat": constants.REPEAT,
    "loop": constants.LOOP,
    "looped group": constants.REPEAT,
}
select_from_file = {
    "select_one_from_file": constants.SELECT_ONE,
    "select_multiple_from_file": constants.SELECT_ALL_THAT_APPLY,
    "select one from file": constants.SELECT_ONE,
    "select multiple from file": constants.SELECT_ALL_THAT_APPLY,
}
select = {
    "add select one prompt using": constants.SELECT_ONE,
    "add select multiple prompt using": constants.SELECT_ALL_THAT_APPLY,
    "select all that apply from": constants.SELECT_ALL_THAT_APPLY,
    "select one from": constants.SELECT_ONE,
    "select1": constants.SELECT_ONE,
    "select_one": constants.SELECT_ONE,
    "select one": constants.SELECT_ONE,
    "select_multiple": constants.SELECT_ALL_THAT_APPLY,
    "select all that apply": constants.SELECT_ALL_THAT_APPLY,
    "select_one_external": constants.SELECT_ONE_EXTERNAL,
    **select_from_file,
    "rank": constants.RANK,
}
cascading = {
    "cascading select": constants.CASCADING_SELECT,
    "cascading_select": constants.CASCADING_SELECT,
}
settings_header = {
    "form_title": constants.TITLE,
    "set_form_title": constants.TITLE,
    "form_id": constants.ID_STRING,
    "set_form_id": constants.ID_STRING,
    "prefix": constants.COMPACT_PREFIX,
}
# TODO: Check on bind prefix approach in json.
# Conversion dictionary from user friendly column names to meaningful values
survey_header = {
    "sms_field": constants.SMS_FIELD,
    "sms_option": constants.SMS_OPTION,
    "sms_separator": constants.SMS_SEPARATOR,
    "sms_allow_media": constants.SMS_ALLOW_MEDIA,
    "sms_date_format": constants.SMS_DATE_FORMAT,
    "sms_datetime_format": constants.SMS_DATETIME_FORMAT,
    "sms_response": constants.SMS_RESPONSE,
    "compact_tag": ("instance", "odk:tag"),  # used for compact representation
    "read_only": ("bind", "readonly"),
    "readonly": ("bind", "readonly"),
    "relevant": ("bind", "relevant"),
    "caption": constants.LABEL,
    "appearance": ("control", "appearance"),
    "relevance": ("bind", "relevant"),
    "required": ("bind", "required"),
    "constraint": ("bind", "constraint"),
    "constraining_message": ("bind", "jr:constraintMsg"),
    "constraint_message": ("bind", "jr:constraintMsg"),
    "calculation": ("bind", "calculate"),
    "calculate": ("bind", "calculate"),
    "command": constants.TYPE,
    "tag": constants.NAME,
    "value": constants.NAME,
    "image": ("media", "image"),
    "big-image": ("media", "big-image"),
    "audio": ("media", "audio"),
    "video": ("media", "video"),
    "count": ("control", "jr:count"),
    "repeat_count": ("control", "jr:count"),
    "jr:count": ("control", "jr:count"),
    "autoplay": ("control", "autoplay"),
    "rows": ("control", "rows"),
    # New elements that have to go into itext elements:
    "noapperrorstring": ("bind", "jr:noAppErrorString"),
    "no_app_error_string": ("bind", "jr:noAppErrorString"),
    "requiredmsg": ("bind", "jr:requiredMsg"),
    "required_message": ("bind", "jr:requiredMsg"),
    "body": "control",
    constants.ENTITIES_SAVETO: ("bind", "entities:saveto"),
}

entities_header = {constants.LIST_NAME_U: "dataset"}

TRANSLATABLE_SURVEY_COLUMNS = {
    constants.LABEL: constants.LABEL,
    # Per ODK Spec, could include "short" once pyxform supports it.
    constants.HINT: constants.HINT,
    "guidance_hint": "guidance_hint",
    "image": survey_header["image"],
    "big-image": survey_header["big-image"],
    "audio": survey_header["audio"],
    "video": survey_header["video"],
    "jr:constraintMsg": "constraint_message",
    "jr:requiredMsg": "required_message",
}
TRANSLATABLE_CHOICES_COLUMNS = {
    "label": constants.LABEL,
    "image": survey_header["image"],
    "big-image": survey_header["big-image"],
    "audio": survey_header["audio"],
    "video": survey_header["video"],
}
list_header = {
    "caption": constants.LABEL,
    constants.LIST_NAME_U: constants.LIST_NAME_S,
    "value": constants.NAME,
    "image": survey_header["image"],
    "big-image": survey_header["big-image"],
    "audio": survey_header["audio"],
    "video": survey_header["video"],
}
# Note that most of the type aliasing happens in all.xls
_type_alias_map = {
    "imei": "deviceid",
    "image": "photo",
    "add image prompt": "photo",
    "add photo prompt": "photo",
    "add audio prompt": "audio",
    "add video prompt": "video",
    "add file prompt": "file",
}
yes_no = {
    "yes": True,
    "Yes": True,
    "YES": True,
    "true": True,
    "True": True,
    "TRUE": True,
    "true()": True,
    "no": False,
    "No": False,
    "NO": False,
    "false": False,
    "False": False,
    "FALSE": False,
    "false()": False,
}
label_optional_types = [
    "calculate",
    "deviceid",
    "end",
    "phonenumber",
    "simserial",
    "start",
    "start-geopoint",
    "today",
    "username",
]
osm = {"osm": constants.OSM_TYPE}
BINDING_CONVERSIONS = {
    "yes": "true()",
    "Yes": "true()",
    "YES": "true()",
    "true": "true()",
    "True": "true()",
    "TRUE": "true()",
    "no": "false()",
    "No": "false()",
    "NO": "false()",
    "false": "false()",
    "False": "false()",
    "FALSE": "false()",
}
