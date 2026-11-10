from typing import Any


def maybe_strip(value: Any) -> Any:
    """
    If the value is a string and looks like it has whitespace at either end, strip it.

    If a string was "interned" (cached) by Python, string.strip() should generally return
    the existing string if no leading/trailing whitespace was found. But strings may or
    may not be interned by Python, and there may be a large cache for many unique values
    (which is likely for XLSForms), so this function tries to avoid calling strip().
    """
    if isinstance(value, str) and value and (value[0].isspace() or value[-1].isspace()):
        return value.strip()
    return value
