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
        self.name: str = name
        self.msg: str = msg

    def format(self, **kwargs):
        return _ERROR_FORMATTER.format(self.msg, **kwargs)


class ErrorCode(Enum):
    HEADER_001: Detail = Detail(
        name="Invalid missing header row.",
        msg=(
            "Invalid headers provided for sheet: '{sheet_name}'. For XLSForms, this may be due "
            "a missing header row, in which case add a header row as per the reference template "
            "https://xlsform.org/en/ref-table/. For internal API usage, may be due to a missing "
            "mapping for '{header}', in which case ensure that the full set of headers appear "
            "within the first 100 rows, or specify the header row in '{sheet_name}_header'."
        ),
    )
    HEADER_002: Detail = Detail(
        name="Invalid duplicate header.",
        msg=(
            "Invalid headers provided for sheet: '{sheet_name}'. Headers that are different "
            "names for the same column were found: '{other}', '{header}'. Rename or remove one "
            "of these columns."
        ),
    )
    HEADER_003: Detail = Detail(
        name="Invalid missing required header.",
        msg=(
            "Invalid headers provided for sheet: '{sheet_name}'. One or more required column "
            "headers were not found: {missing}. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    HEADER_004: Detail = Detail(
        name="Invalid choices header.",
        msg=(
            "[row : 1] On the 'choices' sheet, the '{column}' value is invalid. "
            "Column headers must not be empty and must not contain spaces. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    NAMES_001: Detail = Detail(
        name="Invalid duplicate name in same context",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
            "Questions, groups, and repeats must be unique within their nearest parent group "
            "or repeat, or the survey if not inside a group or repeat."
        ),
    )
    NAMES_002: Detail = Detail(
        name="Invalid duplicate name in context (case-insensitive)",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is problematic. "
            "The name is a case-insensitive match to another name. Questions, groups, and "
            "repeats should be unique within the nearest parent group or repeat, or the survey "
            "if not inside a group or repeat. Some data processing tools are not "
            "case-sensitive, so the current names may make analysis difficult."
        ),
    )
    NAMES_003: Detail = Detail(
        name="Invalid repeat name same as survey",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
            "Repeat names must not be the same as the survey root (which defaults to 'data')."
        ),
    )
    NAMES_004: Detail = Detail(
        name="Invalid duplicate repeat name in the survey",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value '{value}' is invalid. "
            "Repeat names must unique anywhere in the survey, at all levels of group or "
            "repeat nesting."
        ),
    )
    NAMES_005: Detail = Detail(
        name="Invalid duplicate meta name in the survey",
        msg=(
            "[row : {row}] On the 'survey' sheet, the 'name' value 'meta' is invalid. "
            "The name 'meta' is reserved for form metadata."
        ),
    )
    NAMES_006: Detail = Detail(
        name="Invalid missing name in the choices sheet",
        msg=(
            "[row : {row}] On the 'choices' sheet, the 'name' value is invalid. "
            "Choices must have a name. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    NAMES_007: Detail = Detail(
        name="Invalid duplicate name in the choices sheet",
        msg=(
            "[row : {row}] On the 'choices' sheet, the 'name' value is invalid. "
            "Choice names must be unique for each choice list. "
            "If this is intentional, use the setting 'allow_choice_duplicates'. "
            "Learn more: https://xlsform.org/#choice-names."
        ),
    )
    LABEL_001: Detail = Detail(
        name="Invalid missing label in the choices sheet",
        msg=(
            "[row : {row}] On the 'choices' sheet, the 'label' value is invalid. "
            "Choices should have a label. "
            "Learn more: https://xlsform.org/en/#setting-up-your-worksheets"
        ),
    )
    PYREF_001: Detail = Detail(
        name="PyXForm Reference Parsing Failed",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables must start with '${{', then a question name, and end with '}}'."
        ),
    )
    PYREF_002: Detail = Detail(
        name="PyXForm Reference Parsing Limit Reached",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variable lists must have a comma between each variable."
        ),
    )
    PYREF_003: Detail = Detail(
        name="PyXForm Reference Name Not Found",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables must contain a name from the 'survey' sheet. Could not "
            "find the name '{q}'."
        ),
    )
    PYREF_004: Detail = Detail(
        name="PyXForm Reference Duplicate Name",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables names must be unique anywhere in the 'survey'. The name "
            "'{q}' appears more than once."
        ),
    )
    INTERNAL_001: Detail = Detail(
        name="Internal error: Incorrectly Processed Question Trigger Data",
        msg=(
            "Internal error: "
            "PyXForm expected processed trigger data as a tuple, but received a "
            "type '{type}' with value '{value}'."
        ),
    )
    SURVEY_003: Detail = Detail(
        name="Survey Sheet - invalid geoshape/geotrace parameter 'incremental'",
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
