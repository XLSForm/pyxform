from enum import Enum


class StrEnum(str, Enum):
    """Base Enum class with common helper function."""

    # Copied from Python 3.11 enum.py. In many cases can use members as strings, but
    # sometimes need to deref with ".value" property e.g. `EnumClass.MEMBERNAME.value`.
    def __new__(cls, *values):
        "values must already be of type `str`"
        if len(values) > 3:
            raise TypeError(f"too many arguments for str(): {values!r}")
        if len(values) == 1:
            # it must be a string
            if not isinstance(values[0], str):
                raise TypeError(f"{values[0]!r} is not a string")
        if len(values) >= 2:
            # check that encoding argument is a string
            if not isinstance(values[1], str):
                raise TypeError(f"encoding must be a string, not {values[1]!r}")
        if len(values) == 3:
            # check that errors argument is a string
            if not isinstance(values[2], str):
                raise TypeError(f"errors must be a string, not {values[2]!r}")
        value = str(*values)
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    @classmethod
    def value_list(cls):
        return list(cls.__members__.values())
