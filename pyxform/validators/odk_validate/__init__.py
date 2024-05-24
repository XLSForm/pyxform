"""
odk_validate.py
A python wrapper around ODK Validate
"""

import logging
import os
import shutil
import sys
from typing import TYPE_CHECKING

from pyxform.validators.error_cleaner import ErrorCleaner
from pyxform.validators.util import (
    XFORM_SPEC_PATH,
    check_readable,
    run_popen_with_timeout,
)

if TYPE_CHECKING:
    from pyxform.validators.util import PopenResult


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_PATH = os.path.join(CURRENT_DIRECTORY, "bin", "ODK_Validate.jar")


class ODKValidateError(Exception):
    """ODK Validation exception error."""


def install_exists():
    """Returns True if ODK_VALIDATE_PATH exists."""
    return os.path.exists(ODK_VALIDATE_PATH)


def _call_validator(path_to_xform, bin_file_path=ODK_VALIDATE_PATH) -> "PopenResult":
    return run_popen_with_timeout(
        ["java", "-Djava.awt.headless=true", "-jar", bin_file_path, path_to_xform], 100
    )


def install_ok(bin_file_path=ODK_VALIDATE_PATH):
    """
    Check if ODK Validate functions as expected.
    """
    check_readable(file_path=XFORM_SPEC_PATH)
    result = _call_validator(
        path_to_xform=XFORM_SPEC_PATH,
        bin_file_path=bin_file_path,
    )
    if result.return_code == 1:
        return False

    return True


def check_java_available():
    """
    Check if 'which java' returncode is 0. If not, raise an error since java is required.
    """
    java_path = shutil.which(cmd="java")
    if java_path is not None:
        return
    msg = (
        "Form validation failed because Java (8+ required) could not be found. "
        "To fix this, please either: 1) install Java, or 2) run pyxform with the "
        "--skip_validate flag, or 3) add the installed Java to the environment path."
    )
    raise OSError(msg)


def check_xform(path_to_xform):
    """Run ODK Validate against the XForm in `path_to_xform`.

    Returns an array of warnings if the form is valid.
    Throws an exception if it is not
    Does not do a LBYL check for compatible java version as per pyxform/#481
    """
    # check for available java version
    check_java_available()

    # resultcode indicates validity of the form
    # timeout indicates whether validation ran out of time to complete
    # stdout is not used because it has some warnings that always
    # appear and can be ignored.
    # stderr is treated as a warning if the form is valid or an error
    # if it is invalid.
    result = _call_validator(path_to_xform=path_to_xform)
    warnings = []

    if result.timeout:
        return ["XForm took to long to completely validate."]
    elif result.return_code > 0:  # Error invalid
        raise ODKValidateError(
            "ODK Validate Errors:\n" + ErrorCleaner.odk_validate(result.stderr)
        )
    elif result.return_code == 0:
        if result.stderr:
            warnings.append("ODK Validate Warnings:\n" + result.stderr)
    elif result.return_code < 0:
        return ["Bad return code from ODK Validate."]

    return warnings


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.info(__doc__)

    check_xform(sys.argv[1])
