from __future__ import print_function

"""
odk_validate.py
A python wrapper around ODK Validate
"""
import os
import sys
from pyxform.validators.util import run_popen_with_timeout, decode_stream, \
    XFORM_SPEC_PATH, check_readable
from pyxform.validators.error_cleaner import ErrorCleaner


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_PATH = os.path.join(CURRENT_DIRECTORY, "bin", "ODK_Validate.jar")


class ODKValidateError(Exception):
    pass


def install_exists():
    return os.path.exists(ODK_VALIDATE_PATH)


def _call_validator(path_to_xform, bin_file_path=ODK_VALIDATE_PATH):
    return run_popen_with_timeout(
        ["java", "-jar", bin_file_path, path_to_xform], 100)


def install_ok(bin_file_path=ODK_VALIDATE_PATH):
    """
    Check if ODK Validate functions as expected.
    """
    check_readable(file_path=XFORM_SPEC_PATH)
    return_code, _, _, _ = _call_validator(
        path_to_xform=XFORM_SPEC_PATH, bin_file_path=bin_file_path)
    if return_code == 1:
        return False
    else:
        return True


def _check_java_version():
    stderr = run_popen_with_timeout(["java", "-version"], 100)[3]
    stderr = stderr.strip().decode('utf-8')
    if not "java version" in stderr and not "openjdk version" in stderr:
        raise EnvironmentError(
            "pyxform odk validate dependency: java not found")
    # extract version number from version string
    # last string from first line of the output
    java_version = stderr.split('\n')[0].split(' ')[-1][1:-1]
    java_version_numbers = java_version.split('.')
    if not int(java_version_numbers[0]) > 0 or not int(java_version_numbers[1]) > 7:
        raise EnvironmentError(
            'pyxform odk validate dependency: java 8 or newer version not found')


def check_xform(path_to_xform):
    """
    Returns an array of warnings if the form is valid.
    Throws an exception if it is not
    """
    # check for available java version
    _check_java_version()

    # resultcode indicates validity of the form
    # timeout indicates whether validation ran out of time to complete
    # stdout is not used because it has some warnings that always
    # appear and can be ignored.
    # stderr is treated as a warning if the form is valid or an error
    # if it is invalid.
    returncode, timeout, stdout, stderr = _call_validator(
        path_to_xform=path_to_xform)
    warnings = []
    stderr = decode_stream(stderr)

    if timeout:
        return ["XForm took to long to completely validate."]
    else:
        if returncode > 0:  # Error invalid
            raise ODKValidateError(
                b'ODK Validate Errors:\n' + ErrorCleaner.odk_validate(stderr).encode('utf-8'))
        elif returncode == 0:
            if stderr:
                warnings.append('ODK Validate Warnings:\n' + stderr)
            return warnings
        elif returncode < 0:
            return ["Bad return code from ODK Validate."]


if __name__ == '__main__':
    print(__doc__)
    check_xform(sys.argv[1])
