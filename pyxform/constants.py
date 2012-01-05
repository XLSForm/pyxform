"""
This file constains constants that correspond to the json survey format property names. (@see json_form_schema.json)
These names need to be shared between X2json and json2Y programs.
By putting them in a shared file, the literal names can be easily changed, typos can be avoided, and dev tools can be used to find all references to the names.
"""

TYPE = u"type"
TITLE = u"title"
NAME = u"name"
ID_STRING = u"id_string"
LABEL = u"label"
HINT = u"hint"
READONLY = u"readonly"
BIND = u"bind"#TODO: What should I do with the nested types? (readonly and relevant)
MEDIA = u"media"
APPEARANCE = u"appearance"
LOOP = u"loop"
REPEAT = u"repeat"
COLUMNS = u"columns"
GROUP = u"group"
CHILDREN = u"children"
CHOICES = u"choices"