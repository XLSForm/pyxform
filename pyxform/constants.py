"""
This file contains constants that correspond with the property names in the json survey format. (@see json_form_schema.json)
These names are to be shared between X2json and json2Y programs.
By putting them in a shared file, the literal names can be easily changed, typos can be avoided, and references are easier to find.
"""
#TODO: Replace matching strings in the json2xforms code (builder.py, survey.py, survey_element.py, question.py) with these constants

TYPE = u"type"
TITLE = u"title"
NAME = u"name"
ID_STRING = u"id_string"
PUBLIC_KEY = u"public_key"
SUBMISSION_URL = u"submission_url"
DEFAULT_LANGUAGE = u"default_language"
LABEL = u"label"
HINT = u"hint"

BIND = u"bind"#TODO: What should I do with the nested types? (readonly and relevant)
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
CHOICES = u"choices"

# XLS Specific constants
LIST_NAME = u"list name"
CASCADING_SELECT = u"cascading_select"
TABLE_LIST = u"table-list" # hyphenated because it goes in appearance, and convention for appearance column is dashes

# The following are the possible sheet names:
SURVEY = u"survey"
SETTINGS = u"settings"
# These sheet names are for list sheets
CHOICES = u"choices"
COLUMNS = u"columns" #this is for loop statements
CHOICES_AND_COLUMNS = u"choices and columns"
CASCADING_CHOICES = u"cascades"
