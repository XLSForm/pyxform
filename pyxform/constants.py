"""
This file contains constants that correspond with the property names in the
json survey format. (@see json_form_schema.json) These names are to be shared
between X2json and json2Y programs. By putting them in a shared file,
the literal names can be easily changed, typos can be avoided, and references
are easier to find.
"""
# TODO: Replace matching strings in the json2xforms code (builder.py,
# survey.py, survey_element.py, question.py) with these constants

TYPE = u"type"
TITLE = u"title"
NAME = u"name"
ID_STRING = u"id_string"
SMS_KEYWORD = u"sms_keyword"
SMS_FIELD = u"sms_field"
SMS_OPTION = u"sms_option"
SMS_SEPARATOR = u"sms_separator"
SMS_ALLOW_MEDIA = u"sms_allow_media"
SMS_DATE_FORMAT = u"sms_date_format"
SMS_DATETIME_FORMAT = u"sms_datetime_format"
SMS_RESPONSE = u"sms_response"

# compact representation (https://opendatakit.github.io/xforms-spec/#compact-record-representation-(for-sms))
COMPACT_PREFIX = u"prefix"
COMPACT_DELIMITER = u"delimiter"
COMPACT_TAG = u"compact_tag"

VERSION = u"version"
PUBLIC_KEY = u"public_key"
SUBMISSION_URL = u"submission_url"
AUTO_SEND = u"auto_send"
AUTO_DELETE = u"auto_delete"
DEFAULT_LANGUAGE = u"default_language"
LABEL = u"label"
HINT = u"hint"
STYLE = u"style"
ATTRIBUTE = u"attribute"

BIND = u"bind"  # TODO: What should I do with the nested types? (readonly and relevant) # noqa
MEDIA = u"media"
CONTROL = u"control"
APPEARANCE = u"appearance"

LOOP = u"loop"
COLUMNS = u"columns"

REPEAT = u"repeat"
GROUP = u"group"
CHILDREN = u"children"

SELECT_ONE = u"select one"
SELECT_ALL_THAT_APPLY = u"select all that apply"
RANK = u"rank"
CHOICES = u"choices"

# XLS Specific constants
LIST_NAME = u"list name"
CASCADING_SELECT = u"cascading_select"
TABLE_LIST = u"table-list"  # hyphenated because it goes in appearance, and convention for appearance column is dashes # noqa

# The following are the possible sheet names:
SURVEY = u"survey"
SETTINGS = u"settings"
# These sheet names are for list sheets
CHOICES_AND_COLUMNS = u"choices and columns"
CASCADING_CHOICES = u"cascades"

OSM = u"osm"
OSM_TYPE = u"binary"

NAMESPACES = u"namespaces"

SUPPORTED_SHEET_NAMES = [
    SURVEY,
    CASCADING_CHOICES,
    CHOICES,
    COLUMNS,
    CHOICES_AND_COLUMNS,
    SETTINGS,
    OSM,
]
SUPPORTED_FILE_EXTENSIONS = ['.xls', '.xlsx', '.xlsm']

LOCATION_PRIORITY = u"location-priority"
LOCATION_MIN_INTERVAL = u"location-min-interval"
LOCATION_MAX_AGE = u"location-max-age"
