"""
odk_validate.py
A python wrapper around ODK Validate
"""
import os
import re
import sys
from subprocess import Popen, PIPE
import threading
import signal

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "ODK_Validate.jar")

class ODKValidateError(Exception):
    pass

#Adapted from:
#http://betabug.ch/blogs/ch-athens/1093
def run_popen_with_timeout(command, timeout):
    """
    Run a sub-program in subprocess.Popen, pass it the input_data,
    kill it if the specified timeout has passed.
    returns a tuple of resultcode, timeout, stdout, stderr
    """
    kill_check = threading.Event()

    def _kill_process_after_a_timeout(pid):
        os.kill(pid, signal.SIGTERM)
        kill_check.set()  # tell the main routine that we had to kill
        # use SIGKILL if hard to kill...
        return
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    pid = p.pid
    watchdog = threading.Timer(
        timeout, _kill_process_after_a_timeout, args=(pid, ))
    watchdog.start()
    (stdout, stderr) = p.communicate()
    watchdog.cancel()  # if it's still waiting to run
    timeout = kill_check.isSet()
    kill_check.clear()
    return (p.returncode, timeout, stdout, stderr)

def _java_installed():
    # This alternative allows for java detection on Windows.
    try:
        p = Popen(["which", "java"], stdout=PIPE).stdout.readlines()
        found = len(p) != 0
    except WindowsError:
        p = Popen('java -version', stderr=PIPE, stdout=PIPE).stderr.read()
        found = p.startswith('java version')
    return found

def _cleanup_errors(error_message):
    def get_last_item(xpathStr):
        l = xpathStr.split("/")
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
    #moving flags into compile for python 2.6 compat
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
                line = line.replace('org.javarosa.xpath.XPathUnhandledException: ', '')
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
        raise EnvironmentError("pyxform odk validate dependency: java not found")

    #resultcode indicates validity of the form
    #timeout indicates whether validation ran out of time to complete
    #stdout is not used because it has some warnings that always
    #appear and can be ignored.
    #stderr is treated as a warning if the form is valid or an error
    #if it is invalid.
    returncode, timeout, stdout, stderr = run_popen_with_timeout(
        ["java", "-jar", ODK_VALIDATE_JAR, path_to_xform], 100)
    warnings = []
    # On Windows, stderr may be latin-1; in which case utf-8 decode will fail.
    # If both utf-8 and latin-1 decoding fail then raise all as IOError.
    # If the above validate jar call fails, add make sure that the java path
    #  is set, e.g. PATH=C:\Program Files (x86)\Java\jre1.8.0_71\bin
    try:
        stderr = stderr.decode('utf-8')
    except UnicodeDecodeError as ude:
        try:
            stderr = stderr.decode('latin-1')
        except BaseException as be:
            msg = "Failed to decode validate stderr as utf-8 or latin-1."
            raise IOError(msg, ude, be)

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
    print __doc__
    check_xform(sys.argv[1])
