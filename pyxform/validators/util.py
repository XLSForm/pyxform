import os
from subprocess import Popen, PIPE
import threading
import signal


# Adapted from:
# http://betabug.ch/blogs/ch-athens/1093
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
        timeout, _kill_process_after_a_timeout, args=(pid,))
    watchdog.start()
    (stdout, stderr) = p.communicate()
    watchdog.cancel()  # if it's still waiting to run
    timeout = kill_check.isSet()
    kill_check.clear()
    return p.returncode, timeout, stdout, stderr


def decode_stream(stream):
    """
    Decode a stream, e.g. stdout or stderr.

    On Windows, stderr may be latin-1; in which case utf-8 decode will fail.
    If both utf-8 and latin-1 decoding fail then raise all as IOError.
    If the above validate jar call fails, add make sure that the java path
    is set, e.g. PATH=C:\Program Files (x86)\Java\jre1.8.0_71\bin
    """
    try:
        return stream.decode('utf-8')
    except UnicodeDecodeError as ude:
        try:
            return stream.decode('latin-1')
        except BaseException as be:
            msg = "Failed to decode validate stderr as utf-8 or latin-1."
            raise IOError(msg, ude, be)
