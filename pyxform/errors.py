"""
Common base classes for pyxform exceptions.
"""

from string import Formatter


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


class PyXFormError(Exception):
    """Common base class for pyxform exceptions."""


class ValidationError(PyXFormError):
    """Common base class for pyxform validation exceptions."""


class PyXFormReadError(PyXFormError):
    """Common base class for pyxform exceptions occuring during reading XLSForm data."""
