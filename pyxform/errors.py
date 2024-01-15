"""
Common base classes for pyxform exceptions.
"""


class PyXFormError(Exception):
    """Common base class for pyxform exceptions."""


class ValidationError(PyXFormError):
    """Common base class for pyxform validation exceptions."""
