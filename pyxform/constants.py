# -*- coding: utf-8 -*-
"""
This file contains constants that correspond with the property names in the
json survey format. (@see json_form_schema.json) These names are to be shared
between X2json and json2Y programs. By putting them in a shared file,
the literal names can be easily changed, typos can be avoided, and references
are easier to find.
"""
# TODO: Replace matching strings in the json2xforms code (builder.py,
# survey.py, survey_element.py, question.py) with these constants

TYPE = "type"
TITLE = "title"
NAME = "name"
ENTITIES_SAVETO = "save_to"
ID_STRING = "id_string"
SMS_KEYWORD = "sms_keyword"
SMS_FIELD = "sms_field"
SMS_OPTION = "sms_option"
SMS_SEPARATOR = "sms_separator"
SMS_ALLOW_MEDIA = "sms_allow_media"
SMS_DATE_FORMAT = "sms_date_format"
SMS_DATETIME_FORMAT = "sms_datetime_format"
SMS_RESPONSE = "sms_response"

# compact representation (https://opendatakit.github.io/xforms-spec/#compact-record-representation-(for-sms))
COMPACT_PREFIX = "prefix"
COMPACT_DELIMITER = "delimiter"
COMPACT_TAG = "compact_tag"

VERSION = "version"
PUBLIC_KEY = "public_key"
SUBMISSION_URL = "submission_url"
AUTO_SEND = "auto_send"
AUTO_DELETE = "auto_delete"
DEFAULT_LANGUAGE_KEY = "default_language"
DEFAULT_LANGUAGE_VALUE = "default"
LABEL = "label"
HINT = "hint"
STYLE = "style"
ATTRIBUTE = "attribute"
ALLOW_CHOICE_DUPLICATES = "allow_choice_duplicates"

BIND = (
    "bind"  # TODO: What should I do with the nested types? (readonly and relevant) # noqa
)
MEDIA = "media"
CONTROL = "control"
APPEARANCE = "appearance"

LOOP = "loop"
COLUMNS = "columns"

REPEAT = "repeat"
GROUP = "group"
CHILDREN = "children"

SELECT_ONE = "select one"
SELECT_ALL_THAT_APPLY = "select all that apply"
RANK = "rank"
CHOICES = "choices"

# XLS Specific constants
LIST_NAME = "list name"
CASCADING_SELECT = "cascading_select"
TABLE_LIST = "table-list"  # hyphenated because it goes in appearance, and convention for appearance column is dashes # noqa
FIELD_LIST = "field-list"

SURVEY = "survey"
SETTINGS = "settings"
EXTERNAL_CHOICES = "external_choices"
ENTITIES = "entities"

OSM = "osm"
OSM_TYPE = "binary"

NAMESPACES = "namespaces"

# The following are the possible sheet names:
SUPPORTED_SHEET_NAMES = [
    SURVEY,
    CHOICES,
    SETTINGS,
    EXTERNAL_CHOICES,
    OSM,
    ENTITIES,
]
XLS_EXTENSIONS = [".xls"]
XLSX_EXTENSIONS = [".xlsx", ".xlsm"]
SUPPORTED_FILE_EXTENSIONS = XLS_EXTENSIONS + XLSX_EXTENSIONS

LOCATION_PRIORITY = "location-priority"
LOCATION_MIN_INTERVAL = "location-min-interval"
LOCATION_MAX_AGE = "location-max-age"
TRACK_CHANGES = "track-changes"
IDENTIFY_USER = "identify-user"
TRACK_CHANGES_REASONS = "track-changes-reasons"

# supported bind keywords for which external instances will be created for pulldata function
EXTERNAL_INSTANCES = ["calculate", "constraint", "readonly", "required", "relevant"]

# The ODK XForms version that generated forms comply to
CURRENT_XFORMS_VERSION = "1.0.0"

# The ODK entities spec version that generated forms comply to
CURRENT_ENTITIES_VERSION = "2022.1.0"
ENTITY_RELATED = "entity_related"
ENTITIES_RESERVED_PREFIX = "__"

DEPRECATED_DEVICE_ID_METADATA_FIELDS = ["subscriberid", "simserial"]

AUDIO_QUALITY_VOICE_ONLY = "voice-only"
AUDIO_QUALITY_LOW = "low"
AUDIO_QUALITY_NORMAL = "normal"
AUDIO_QUALITY_EXTERNAL = "external"

EXTERNAL_INSTANCE_EXTENSIONS = [".xml", ".csv", ".geojson"]

EXTERNAL_CHOICES_ITEMSET_REF_LABEL = "label"
EXTERNAL_CHOICES_ITEMSET_REF_VALUE = "name"

EXTERNAL_CHOICES_ITEMSET_REF_LABEL_GEOJSON = "title"
EXTERNAL_CHOICES_ITEMSET_REF_VALUE_GEOJSON = "id"

ROW_FORMAT_STRING: str = "[row : %s]"
XML_IDENTIFIER_ERROR_MESSAGE = "must begin with a letter, colon, or underscore. Other characters can include numbers, dashes, and periods."
_MSG_SUPPRESS_SPELLING = (
    " If you do not mean to include a sheet, to suppress this message, "
    "prefix the sheet name with an underscore. For example 'setting' "
    "becomes '_setting'."
)
