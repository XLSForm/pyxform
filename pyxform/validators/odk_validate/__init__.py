from __future__ import print_function

"""
odk_validate.py
A python wrapper around ODK Validate
"""
import os
import re
import sys
from subprocess import Popen, PIPE
from pyxform.validators.util import run_popen_with_timeout, decode_stream


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "ODK_Validate.jar")


class ODKValidateError(Exception):
    pass


def _java_installed():
    # This alternative allows for java detection on Windows.
    try:
        p = Popen(["which", "java"], stdout=PIPE).stdout.readlines()
        found = len(p) != 0
    except WindowsError:
        p = Popen("java -version", stderr=PIPE, stdout=PIPE).stderr.read()
        found = p.startswith("java version".encode())
    return found


def _cleanup_errors(error_message):
    def get_last_item(xpath_str):
        l = xpath_str.split("/")
        return l[len(l) - 1]

    def replace_function(match):
        strmatch = match.group()
        # eliminate e.g /html/body/select1[@ref=/id_string/elId]/item/value
        # instance('q4')/root/item[...]
        if strmatch.startswith("/html/body") \
                or strmatch.startswith("/root/item") \
                or strmatch.startswith("/html/head/model/bind") \
                or strmatch.endswith("/item/value"):
            return strmatch
        return "${%s}" % get_last_item(match.group())

    pattern = "(/[a-z0-9\-_]+(?:/[a-z0-9\-_]+)+)"
    # moving flags into compile for python 2.6 compat
    error_message = re.compile(pattern, flags=re.I).sub(replace_function,
                                                        error_message)
    k = []
    lastline = ''
    for line in error_message.splitlines():
        # has a java filename (with line number)
        has_java_filename = line.find('.java:') is not -1
        # starts with '    at java class path or method path'
        is_a_java_method = line.find('\tat') is not -1
        # is the same as the last line
        is_duplicate = (line == lastline)
        lastline = line
        if not has_java_filename and not is_a_java_method and not is_duplicate:
            # remove java.lang.RuntimeException
            if line.startswith('java.lang.RuntimeException: '):
                line = line.replace('java.lang.RuntimeException: ', '')
            # remove org.javarosa.xpath.XPathUnhandledException
            if line.startswith('org.javarosa.xpath.XPathUnhandledException: '):
                line = line.replace(
                    'org.javarosa.xpath.XPathUnhandledException: ', '')
            # remove java.lang.NullPointerException
            if line.startswith('java.lang.NullPointerException'):
                continue
            k.append(line)
    return u'\n'.join(k)


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
                'ODK Validate Errors:\n' + _cleanup_errors(stderr))
        elif returncode == 0:
            if stderr:
                warnings.append('ODK Validate Warnings:\n' + stderr)
            return warnings
        elif returncode < 0:
            return ["Bad return code from ODK Validate."]


if __name__ == '__main__':
    print(__doc__)
    check_xform(sys.argv[1])
