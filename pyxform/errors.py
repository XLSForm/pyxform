"""
Common base classes for pyxform exceptions.
"""

from enum import Enum
from string import Formatter
from typing import Any


class _ErrorFormatter(Formatter):
    """Allows specifying a default for missing format keys."""

    def __init__(self, default_value: str = "unknown"):
        self.default_value: str = default_value

    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            value = kwargs.get(key, None)
            if value is None:
                return self.default_value
            else:
                return value
        else:
            return super().get_value(key, args, kwargs)


_ERROR_FORMATTER = _ErrorFormatter()


class Detail:
    """ErrorCode details."""

    __slots__ = ("msg", "name")

    def __init__(self, name: str, msg: str) -> None:
        """
        :param name: A brief description of the error, used for organising messages and/or
          technical words that are not suitable for the user-visible message.
        :param msg: The message shown to the user. May include string formatting {tokens}
          which are resolved from context data made available to the PyXFormError.
        """
        self.name: str = name
        self.msg: str = msg

    def format(self, **kwargs):
        return _ERROR_FORMATTER.format(self.msg, **kwargs)


class ErrorCode(Enum):
    """
    A collection of error messages used in pyxform.

    The enum names only have to be unique, but for organisation purposes, try to use a
    prefix word that aligns to the topic of the message. The number suffix is not
    significant and does not have to be sequential. With reference to the SQLSTATE standard
    as an example, the enum name would be the sqlstate code, and the Detail.name would be
    the "class text" and the Detail.msg would be the "subclass text" (with app context).
    """

    ENTITY_001 = Detail(
        name="Entities - save_to but no entities",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'save_to' value is invalid. "
            "To save entity properties using the save_to column, add an entities sheet and "
            "declare an entity."
        ),
    )
    ENTITY_002 = Detail(
        name="Entities - duplicate save_to property",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'save_to' value is invalid. "
            "The save_to property '{saveto}' is already assigned by row '{other_row}'. "
            "Either remove or change one of these duplicate save_to property names."
        ),
    )
    ENTITY_003 = Detail(
        name="Entities - save_to in group or repeat row",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'save_to' value is invalid. "
            "Groups and repeats can't be saved as entity properties. "
            "Either remove or move the save_to value in this row."
        ),
    )
    ENTITY_004 = Detail(
        name="Entities - list_name not found",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'save_to' value is invalid. "
            "The entity list name '{dataset}' was not found on the entities sheet. "
            "Please either: check the spelling of the list name in the save_to value, or "
            "on the entities sheet add a row for this entity list, or check the spelling "
            "of existing entity list names."
        ),
    )
    ENTITY_005 = Detail(
        name="Entities - missing entity create label",
        msg=(
            "[row : {row}] On the 'entities' sheet, the entity declaration is invalid. "
            "The entity list name '{dataset}' does not have a label, but a 'label' is "
            "required when creating entities. Creating entities is indicated by using "
            "a 'create_if' expression, or by not using 'entity_id' expression. "
            "Please either: add a 'label' for this entity declaration, or to update "
            "entities instead provide an 'entity_id' (and optionally 'update_if') expression."
        ),
    )
    ENTITY_006 = Detail(
        name="Entities - missing entity upsert update_if",
        msg=(
            "[row : {row}] On the 'entities' sheet, the entity declaration is invalid. "
            "The entity list name '{dataset}' does not have an 'update_if' expression, "
            "but an 'update_if' is required when upserting entities. Upserting entities "
            "is indicated by using 'create_if' and 'entity_id' expressions. "
            "Please either: add an 'update_if' for this entity declaration, or to only "
            "create entities instead remove the 'entity_id' expression."
        ),
    )
    ENTITY_007 = Detail(
        name="Entities - missing entity update/upsert entity_id",
        msg=(
            "[row : {row}] On the 'entities' sheet, the entity declaration is invalid. "
            "The entity list name '{dataset}' does not have an 'entity_id' expression, "
            "but an 'entity_id' is required when updating entities. Updating entities "
            "is indicated by using 'entity_id' and/or 'update_if' expressions. "
            "Please either: add an 'entity_id' for this entity declaration, or to only "
            "create entities instead move the 'update_if' to 'create_if'."
        ),
    )
    ENTITY_008 = Detail(
        name="Entities - missing save_to prefix with multiple entities",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'save_to' value is invalid. "
            "When there is more than one entity declaration, 'save_to' names must be "
            "prefixed with the entity 'list_name' that the property belongs to. "
            "Please either: add the entity 'list_name' prefix separated with a '#' "
            "e.g. my_list#my_save_to (where 'my_list' is the entity 'list_name', and "
            "'my_save_to' is the 'save_to' property name), or remove all but one entity "
            "declarations."
        ),
    )
    ENTITY_009 = Detail(
        name="Entities - unsolvable meta/entity topology",
        msg=(
            "[row : {row}] On the 'entities' sheet, the entity declaration is invalid. "
            "Each container (survey, group, repeat) may have only one entity declaration, "
            "but there are no valid containers available in the scope: '{scope}'. "
            "Please either: check which entities are referred to from the 'survey' sheet"
            "in the 'save_to' column, or check which questions are being referred to "
            "from the 'entities' sheet with variable references (such as in the 'label')."
        ),
    )
    ENTITY_010 = Detail(
        name="Entities - save_to scope breach",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'save_to' value is invalid. "
            "The entity list name '{dataset}' is also referenced by a 'save_to' in "
            "the 'survey' sheet row {other_row}, which is in a different container scope. "
            "Please either: check the spelling of the list name in the 'save_to', or "
            "copy either value into the desired container scope with a 'calculate' "
            "question then use that 'calculate' for the 'save_to'."
        ),
    )
    HEADER_001: Detail = Detail(
        name="Headers - invalid missing header row",
        msg=(
            "Invalid headers provided for sheet: '{sheet_name}'. For XLSForms, this may be due "
            "a missing header row, in which case add a header row as per the reference template "
            "https://xlsform.org/en/ref-table/. For internal API usage, may be due to a missing "
            "mapping for '{header}', in which case ensure that the full set of headers appear "
            "within the first 100 rows, or specify the header row in '{sheet_name}_header'."
        ),
    )
    HEADER_002: Detail = Detail(
        name="Headers - invalid duplicate",
        msg=(
            "Invalid headers provided for sheet: '{sheet_name}'. Headers that are different "
            "names for the same column were found: '{other}', '{header}'. Rename or remove one "
            "of these columns."
        ),
    )
    HEADER_003: Detail = Detail(
        name="Headers - invalid missing required header",
        msg=(
            "Invalid headers provided for sheet: '{sheet_name}'. One or more required column "
            "headers were not found: {missing}. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    HEADER_004: Detail = Detail(
        name="Headers - invalid choices header",
        msg=(
            "[row : 1] On the 'choices' sheet, the '{column}' value is invalid. "
            "Column headers must not be empty and must not contain spaces. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    HEADER_005: Detail = Detail(
        name="Headers - invalid entities header",
        msg=(
            "[row : 1] On the 'entities' sheet, one or more column names are invalid. "
            "The following column(s) are not supported by this version of pyxform: {columns}. "
            "Please either: check the spelling of the column names, remove the columns, "
            "or update pyxform."
        ),
    )
    INTERNAL_001: Detail = Detail(
        name="Internal error - incorrectly processed question trigger data",
        msg=(
            "Internal error: "
            "PyXForm expected processed trigger data as a tuple, but received a "
            "type '{type}' with value '{value}'."
        ),
    )
    LABEL_001: Detail = Detail(
        name="Labels - invalid missing label in the choices sheet",
        msg=(
            "[row : {row}] On the 'choices' sheet, the 'label' value is invalid. "
            "Choices should have a label. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    NAMES_001: Detail = Detail(
        name="Names - invalid duplicate name in same context",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
            "Questions, groups, and repeats must be unique within their nearest parent group "
            "or repeat, or the survey if not inside a group or repeat."
        ),
    )
    NAMES_002: Detail = Detail(
        name="Names - invalid duplicate name in context (case-insensitive)",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is problematic. "
            "The name is a case-insensitive match to another name. Questions, groups, and "
            "repeats should be unique within the nearest parent group or repeat, or the survey "
            "if not inside a group or repeat. Some data processing tools are not "
            "case-sensitive, so the current names may make analysis difficult."
        ),
    )
    NAMES_003: Detail = Detail(
        name="Names - invalid repeat name same as survey",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
            "Repeat names must not be the same as the survey root (which defaults to 'data')."
        ),
    )
    NAMES_004: Detail = Detail(
        name="Names - invalid duplicate repeat name in the survey",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
            "Repeat names must unique anywhere in the survey, at all levels of group or "
            "repeat nesting."
        ),
    )
    NAMES_005: Detail = Detail(
        name="Names - invalid duplicate meta name in the survey",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value 'meta' is invalid. "
            "The name 'meta' is reserved for form metadata."
        ),
    )
    NAMES_006: Detail = Detail(
        name="Names - invalid missing name in the choices sheet",
        msg=(
            "[row : {row}] On the 'choices' sheet, the 'name' value is invalid. "
            "Choices must have a name. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    NAMES_007: Detail = Detail(
        name="Names - invalid duplicate name in the choices sheet",
        msg=(
            "[row : {row}] On the 'choices' sheet, the 'name' value is invalid. "
            "Choice names must be unique for each choice list. "
            "If this is intentional, use the setting 'allow_choice_duplicates'. "
            "Learn more: https://xlsform.org/#choice-names."
        ),
    )
    NAMES_008: Detail = Detail(
        name="Names - invalid character(s) in name (XML identifier)",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Names must begin with a letter or underscore. After the first character, "
            "names may contain letters, digits, underscores, hyphens, or periods."
        ),
    )
    NAMES_009: Detail = Detail(
        name="Names - invalid character(s) in name (XML identifier)(no sheet context)",
        msg=(
            "The '{name}' value is invalid. "
            "Names must begin with a letter or underscore. After the first character, "
            "names may contain letters, digits, underscores, hyphens, or periods."
        ),
    )
    NAMES_010: Detail = Detail(
        name="Names - invalid character(s) in entity-related name (XML identifier)(underscores)",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Names used here must not begin with two underscores."
        ),
    )
    NAMES_011: Detail = Detail(
        name="Names - invalid character(s) in entity-related name (XML identifier)(period)",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Names used here must not contain a period."
        ),
    )
    NAMES_012: Detail = Detail(
        name="Names - invalid character(s) in entity-related name (XML identifier)(reserved words)",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Names used here must not be 'name' or 'label' (case-insensitive)."
        ),
    )
    NAMES_013: Detail = Detail(
        name="Names - possible sheet name misspelling",
        msg=(
            "When looking for a sheet named '{sheet}', the following sheets with "
            "similar names were found: {candidates}."
        ),
    )
    NAMES_014: Detail = Detail(
        name="Names - invalid duplicate name in the entities sheet",
        msg=(
            "[row : {row}] On the 'entities' sheet, the 'list_name' value is invalid. "
            "The 'list_name' column must not have any duplicate names. "
        ),
    )
    PYREF_001: Detail = Detail(
        name="PyXForm reference - parsing failed",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables must start with '${{', then a question name, and end with '}}'."
        ),
    )
    PYREF_002: Detail = Detail(
        name="PyXForm reference - parsing limit reached",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variable lists must have a comma between each variable."
        ),
    )
    PYREF_003: Detail = Detail(
        name="PyXForm reference - name not found",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables must contain a name from the 'survey' sheet. Could not "
            "find the name '{q}'."
        ),
    )
    PYREF_004: Detail = Detail(
        name="PyXForm reference - duplicate name",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables names must be unique anywhere in the 'survey'. The name "
            "'{q}' appears more than once."
        ),
    )
    SURVEY_001 = Detail(
        name="Survey sheet - unmatched group/repeat/loop end",
        msg=(
            "[row : {row}] Unmatched 'end_{type}'. "
            "No matching 'begin_{type}' was found for the name '{name}'."
        ),
    )
    SURVEY_002 = Detail(
        name="Survey sheet - unmatched group/repeat/loop begin",
        msg=(
            "[row : {row}] Unmatched 'begin_{type}'. "
            "No matching 'end_{type}' was found for the name '{name}'."
        ),
    )
    SURVEY_003: Detail = Detail(
        name="Survey sheet - invalid geoshape/geotrace parameter 'incremental'",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "For geoshape and geotrace questions, the 'incremental' parameter may either "
            "be 'true' or not included."
        ),
    )


class PyXFormError(Exception):
    """Common base class for pyxform exceptions."""

    def __init__(
        self, *args, code: ErrorCode | None = None, context: dict[str, Any] | None = None
    ) -> None:
        """
        :param args: Args for the base exception, such as a pre-formatted error message.
        :param code: If provided, used for an error message template.
        :param context: If provided, used to format the error message template.
        """
        super().__init__(*args)
        self.code: ErrorCode | None = code
        self.context: dict = context if context else {}

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.code:
            if self.context:
                return self.code.value.format(**self.context)
            else:
                # If there's somehow no context for creating a helpful message, at least
                # try to give some kind of normal-looking indication of the type of issue.
                return self.code.value.name
        elif self.args[0]:
            return self.args[0]
        else:
            return super().__repr__()


class ValidationError(PyXFormError):
    """Common base class for pyxform validation exceptions."""


class PyXFormReadError(PyXFormError):
    """Common base class for pyxform exceptions occuring during reading XLSForm data."""
