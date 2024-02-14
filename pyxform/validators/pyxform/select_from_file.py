import re
from pathlib import Path

from pyxform import aliases
from pyxform.constants import EXTERNAL_INSTANCE_EXTENSIONS, ROW_FORMAT_STRING
from pyxform.errors import PyXFormError

VALUE_OR_LABEL_TEST_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9\-_\.]*$")


def value_or_label_format_msg(name: str, row_number: int) -> str:
    return (
        ROW_FORMAT_STRING % str(row_number)
        + f" Parameter '{name}' has a value which is not valid."
        + " Values must begin with a letter or underscore. Subsequent "
        + "characters can include letters, numbers, dashes, underscores, and periods."
    )


def value_or_label_test(value: str) -> bool:
    query = VALUE_OR_LABEL_TEST_REGEX.search(value)
    if query is None:
        return False
    else:
        return query.group(0) == value


def value_or_label_check(name: str, value: str, row_number: int) -> None:
    """
    Check parameter values for invalid characters for use in a XPath expression.

    For example for a value of "val*", ODK Validate will throw an error like that shown
    below. This check looks for characters which seem to avoid the error.

      >> Something broke the parser. See above for a hint.
      org.javarosa.xpath.XPathException: XPath evaluation: Parse error in XPath path: [val*].
      Bad node: org.javarosa.xpath.parser.ast.ASTNodeAbstractExpr@63e2203c

    :param name: The name of the parameter value.
    :param value: The parameter value to validate.
    :param row_number: The survey sheet row number.
    """
    if not value_or_label_test(value=value):
        msg = value_or_label_format_msg(name=name, row_number=row_number)
        raise PyXFormError(msg)


def validate_list_name_extension(
    select_command: str, list_name: str, row_number: int
) -> None:
    """For select_from_file types, the list_name should end with a supported extension."""
    list_path = Path(list_name)
    if select_command in aliases.select_from_file and (
        1 != len(list_path.suffixes)
        or list_path.suffix not in EXTERNAL_INSTANCE_EXTENSIONS
    ):
        exts = ", ".join(f"'{e}'" for e in EXTERNAL_INSTANCE_EXTENSIONS)
        raise PyXFormError(
            ROW_FORMAT_STRING % row_number
            + f" File name for '{select_command} {list_name}' should end with one of "
            + f"the supported file extensions: {exts}"
        )
