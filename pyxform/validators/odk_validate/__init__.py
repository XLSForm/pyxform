from __future__ import print_function

"""
odk_validate.py
A python wrapper around ODK Validate
"""
import os
import sys
from pyxform.validators.util import run_popen_with_timeout, decode_stream
from pyxform.validators.error_cleaner import ErrorCleaner


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "ODK_Validate.jar")


class ODKValidateError(Exception):
    pass


def _java_installed():
    stderr = run_popen_with_timeout(["java", "-version"], 100)[3]
    stderr = stderr.strip().decode('utf-8')
    return "java version" in stderr or "openjdk version" in stderr


def check_xform(path_to_xform):
    """
    Returns an array of warnings if the form is valid.
    Throws an exception if it is not
    """
    # provide useful error message if java is not installed
    if not _java_installed():
        raise EnvironmentError(
            "pyxform odk validate dependency: java not found")

    # resultcode indicates validity of the form
    # timeout indicates whether validation ran out of time to complete
    # stdout is not used because it has some warnings that always
    # appear and can be ignored.
    # stderr is treated as a warning if the form is valid or an error
    # if it is invalid.
    returncode, timeout, stdout, stderr = run_popen_with_timeout(
        ["java", "-jar", ODK_VALIDATE_JAR, path_to_xform], 100)
    warnings = []
    stderr = decode_stream(stderr)

    if timeout:
        return ["XForm took to long to completely validate."]
    else:
        if returncode > 0:  # Error invalid
            raise ODKValidateError(
                'ODK Validate Errors:\n' + ErrorCleaner.odk_validate(stderr))
        elif returncode == 0:
            if stderr:
                warnings.append('ODK Validate Warnings:\n' + stderr)
            return warnings
        elif returncode < 0:
            return ["Bad return code from ODK Validate."]


if __name__ == '__main__':
    print(__doc__)
    check_xform(sys.argv[1])
