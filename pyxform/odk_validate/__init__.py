"""
odk_validate.py
A python wrapper around ODK Validate
"""
from subprocess import Popen, PIPE
import os, re, sys

import time
import threading
import signal

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "ODK_Validate.jar")

#Adapted from:
#http://betabug.ch/blogs/ch-athens/1093
def run_popen_with_timeout(command, timeout):
    """
    Run a sub-program in subprocess.Popen, pass it the input_data,
    kill it if the specified timeout has passed.
    returns a tuple of success, stdout, stderr
    """
    print 'a'
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
    print ODK_VALIDATE_JAR
    returncode, timeout, stdout, stderr = run_popen_with_timeout(["java", "-jar", ODK_VALIDATE_JAR, path_to_xform], 60)
    #I could possibly do more to parse the output from validate.
    #warnings = (stdout + stderr).split('\n\n')
    #Consider leaving out stdout because it has a bunch of errors about unrecognized attributes that will always appear.
    warnings = ['stderr:\n' + stderr] #['stdout:\n' + stdout] + 
    if timeout:
        warnings.append("XForm took to long to completely validate.")
    if returncode > 0: #Error invalid
        raise Exception('\n\n'.join(warnings))
    if returncode == 0:
        return warnings
    if returncode < 0:
        return ["Validate process incomplete. This error shouldn't happen."] + warnings

if __name__ == '__main__':
    print __doc__
    check_xform(sys.argv[1])
