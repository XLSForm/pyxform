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
            return kwargs.get(key, self.default_value)
        else:
            return super().get_value(key, args, kwargs)


_ERROR_FORMATTER = _ErrorFormatter()


class _Detail:
    """ErrorCode details."""

    __slots__ = ("msg", "name")

    def __init__(self, name: str, msg: str) -> None:
        self.name: str = name
        self.msg: str = msg

    def format(self, **kwargs):
        return _ERROR_FORMATTER.format(self.msg, **kwargs)


class ErrorCode(Enum):
    PYREF_001: _Detail = _Detail(
        name="PyXForm Reference Parsing Failed",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables must start with '${{', then a question name, and end with '}}'."
        ),
    )
    PYREF_002: _Detail = _Detail(
        name="PyXForm Reference Parsing Limit Reached",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variable lists must have a comma between each variable."
        ),
    )
    PYREF_003: _Detail = _Detail(
        name="PyXForm Reference Question Not Found",
        msg=(
            "[row : {row}] On the '{sheet}' sheet, the '{column}' value is invalid. "
            "Reference variables must refer to a question name. Could not find '{q}'."
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
                return self.code.value.name
        elif self.args[0]:
            return self.args[0]
        else:
            return super().__repr__()


class ValidationError(PyXFormError):
    """Common base class for pyxform validation exceptions."""


class PyXFormReadError(PyXFormError):
    """Common base class for pyxform exceptions occuring during reading XLSForm data."""
