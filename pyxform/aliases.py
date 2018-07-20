from pyxform import constants

# Aliases:
# Ideally aliases should resolve to elements in the json form schema

# select, control and settings alias keys used for parsing,
# which is why self mapped keys are necessary.

control = {
    u"group": constants.GROUP,
    u"lgroup": constants.REPEAT,
    u"repeat": constants.REPEAT,
    u"loop": constants.LOOP,
    u"looped group": constants.REPEAT
}
select = {
    u"add select one prompt using": constants.SELECT_ONE,
    u"add select multiple prompt using": constants.SELECT_ALL_THAT_APPLY,
    u"select all that apply from": constants.SELECT_ALL_THAT_APPLY,
    u"select one from": constants.SELECT_ONE,
    u"select1": constants.SELECT_ONE,
    u"select_one": constants.SELECT_ONE,
    u"select one": constants.SELECT_ONE,
    u"select_multiple": constants.SELECT_ALL_THAT_APPLY,
    u"select all that apply": constants.SELECT_ALL_THAT_APPLY,
    u"select_one_external": u"select one external",
    u"select_one_from_file": constants.SELECT_ONE,
    u"select_multiple_from_file": constants.SELECT_ALL_THAT_APPLY,
    u"select one from file": constants.SELECT_ONE,
    u"select multiple from file": constants.SELECT_ALL_THAT_APPLY,
    u"rank": constants.RANK,
}
cascading = {
    u'cascading select': constants.CASCADING_SELECT,
    u'cascading_select': constants.CASCADING_SELECT,
}
settings_header = {
    u"form_title": constants.TITLE,
    u"set form title": constants.TITLE,
    u"form_id": constants.ID_STRING,
    u"sms_keyword": constants.SMS_KEYWORD,
    u"sms_separator": constants.SMS_SEPARATOR,
    u"sms_allow_media": constants.SMS_ALLOW_MEDIA,
    u"sms_date_format": constants.SMS_DATE_FORMAT,
    u"sms_datetime_format": constants.SMS_DATETIME_FORMAT,

    u"prefix": constants.COMPACT_PREFIX,
    u"delimiter": constants.COMPACT_DELIMITER,

    u"set form id": constants.ID_STRING,
    u"public_key": constants.PUBLIC_KEY,
    u"submission_url": constants.SUBMISSION_URL,
    u"auto_send": constants.AUTO_SEND,
    u"auto_delete": constants.AUTO_DELETE
}
# TODO: Check on bind prefix approach in json.
# Conversion dictionary from user friendly column names to meaningful values
survey_header = {
    u"Label": u"label",
    u"Name": u"name",
    u"SMS Field": constants.SMS_FIELD,
    u"SMS Option": constants.SMS_OPTION,
    u"SMS Sepatator": constants.SMS_SEPARATOR,
    u"SMS Allow Media": constants.SMS_ALLOW_MEDIA,
    u"SMS Date Format": constants.SMS_DATE_FORMAT,
    u"SMS DateTime Format": constants.SMS_DATETIME_FORMAT,
    u"SMS Response": constants.SMS_RESPONSE,
    u"compact_tag": u"instance::odk:tag", # used for compact representation
    u"Type": u"type",
    u"List_name": u"list_name",
    # u"repeat_count": u"jr:count",  duplicate key
    u"read_only": u"bind::readonly",
    u"readonly": u"bind::readonly",
    u"relevant": u"bind::relevant",
    u"caption": constants.LABEL,
    u"appearance": u"control::appearance",  # TODO: this is also an issue
    u"relevance": u"bind::relevant",
    u"required": u"bind::required",
    u"constraint": u"bind::constraint",
    u"constraining message": u"bind::jr:constraintMsg",
    u"constraint message": u"bind::jr:constraintMsg",
    u"constraint_message": u"bind::jr:constraintMsg",
    u"calculation": u"bind::calculate",
    u"calculate": u"bind::calculate",
    u"command": constants.TYPE,
    u"tag": constants.NAME,
    u"value": constants.NAME,
    u"image": u"media::image",
    u"audio": u"media::audio",
    u"video": u"media::video",
    u"count": u"control::jr:count",
    u"repeat_count": u"control::jr:count",
    u"jr:count": u"control::jr:count",
    u"autoplay": u"control::autoplay",
    u"rows": u"control::rows",
    # New elements that have to go into itext elements:
    u"noAppErrorString": u"bind::jr:noAppErrorString",
    u"no_app_error_string": u"bind::jr:noAppErrorString",
    u"requiredMsg": u"bind::jr:requiredMsg",
    u"required_message": u"bind::jr:requiredMsg",
    u"required message": u"bind::jr:requiredMsg",
    u"body": u"control",
    u"parameters": u"parameters",
}
list_header = {
    u"caption": constants.LABEL,
    u"list_name": constants.LIST_NAME,
    u"value": constants.NAME,
    u"image": u"media::image",
    u"audio": u"media::audio",
    u"video": u"media::video"
}
# Note that most of the type aliasing happens in all.xls
_type = {
    u"imei": u"deviceid",
    u"image": u"photo",
    u"add image prompt": u"photo",
    u"add photo prompt": u"photo",
    u"add audio prompt": u"audio",
    u"add video prompt": u"video",
    u"add file prompt": u"file"
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
    u"deviceid",
    u"phonenumber",
    u"simserial",
    u"calculate",
    u"start",
    u"end",
    u"today"
]
osm = {
    u"osm": constants.OSM_TYPE
}
