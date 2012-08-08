"""
odk_validate.py
A python wrapper around ODK Validate
"""
import os, re, sys
from subprocess import Popen, PIPE
import time, threading, signal

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "ODK_Validate.jar")

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
        kill_check.set() # tell the main routine that we had to kill
        # use SIGKILL if hard to kill...
        return
    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    pid = p.pid
    watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
    watchdog.start()
    (stdout, stderr) = p.communicate()
    watchdog.cancel() # if it's still waiting to run
    timeout = kill_check.isSet()
    kill_check.clear()
    return (p.returncode, timeout, stdout, stderr)

def check_xform(path_to_xform):
    """
    Returns an array of warnings if the form is valid.
    Throws an exception if it is not
    """
    #resultcode indicates validity of the form
    #timeout indicates whether validation ran out of time to complete
    #stdout is not used because it has some warnings that always appear and can be ignored.
    #stderr is treated as a warning if the form is valid or an error if it is invalid.
    returncode, timeout, stdout, stderr = run_popen_with_timeout(["java", "-jar", ODK_VALIDATE_JAR, path_to_xform], 60)
    warnings = ['ODK Validate Warnings:\n' + stderr]
    if timeout:
        warnings.append("XForm took to long to completely validate.")
    if returncode > 0: #Error invalid
        raise Exception('ODK Validate Errors:\n' + stderr)
    elif returncode == 0:
        return warnings
    elif returncode < 0:
        return ["Validate process incomplete."] + warnings

if __name__ == '__main__':
    print __doc__
    check_xform(sys.argv[1])
