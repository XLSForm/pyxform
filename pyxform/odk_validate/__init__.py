from collections import defaultdict
from contextlib import nested
import os
import re
from tempfile import NamedTemporaryFile
import sys

#Inlining code from:
#https://github.com/modilabs/python-utils/blob/master/modilabs/utils/subprocess_timeout.py
#to avoid the added dependency.
import subprocess
import threading

class ProcessTimedOut(Exception):
    pass

class Subprocess(object):
    """
    Enables to run subprocess commands in a different thread
    with TIMEOUT option!

    Based on http://github.com/dimagi/dimagi-utils/blob/master/dimagi/utils/\
    subprocess_timeout.py
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.process = None

    def run(self, timeout=None):
        def target(*args, **kwargs):
            self.process = subprocess.Popen(*args, **kwargs)
            self.process.communicate()

        thread = threading.Thread(target=target, args=self.args,
                kwargs=self.kwargs)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
            raise ProcessTimedOut("Process `%s` timed out after %s seconds" % (
                ' '.join(self.args[0] if self.args else self.kwargs.get('args')),
                timeout
            ))
        else:
            return self.process.returncode

# this is ugly, but allows running pyxform
# as a standalone xls validator from the cl
try:
    from pyxform.errors import ValidationError
except ImportError:
    from errors import ValidationError


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(
        CURRENT_DIRECTORY, "ODK_Validate.jar")

# Only the modded headless version of ODK Validate returns these codes.
# see: lonely_java_src/FormValidator.java
HEADLESS_ODK_VALIDATE_REGEXS = {
    'result': r"^>> (Xform is valid!) (.*)$",
    'error': r"^>> XML is invalid.: (.*)$",
    }


class XFormValidator(object):

    # helpers
    def open_w(self):
        return NamedTemporaryFile("w", suffix=".txt", delete=False)

    def open_r(self, _file):
        return open(_file.name, 'r')

    def delete(self, _file):
        try:
            os.unlink(_file.name)
        except Exception:
            pass

    def _run_odk_validate(self, path_to_xform, timeout):
        stdout_w = stderr_w = None
        self._path_to_xform = path_to_xform

        try:
            with nested(self.open_w(), self.open_w()) as (
                    stdout_w, stderr_w):
                Subprocess(
                    ["java", "-jar", ODK_VALIDATE_JAR, path_to_xform],
                    shell=False,
                    stdout=stdout_w,
                    stderr=stderr_w,
                ).run(timeout=timeout)

            with self.open_r(stdout_w) as stdout_r:
                output = stdout_r.read()

            with self.open_r(stderr_w) as stderr_r:
                error = stderr_r.read()
        finally:
            for _file in (stdout_w, stderr_w):
                self.delete(_file)

        self._odk_validate_output = (output + error).split('\n')

    def get_odk_validate_output(self):
        return "\n".join(self._odk_validate_output)

    def _parse_odk_validate_output(self):
        self._errors_and_result = defaultdict(list)
        for line in self._odk_validate_output:
            for key, regexp in HEADLESS_ODK_VALIDATE_REGEXS.items():
                m = re.search(regexp, line)
                if m:
                    self._errors_and_result[key].append(m.group(1))

    def is_valid(self):
        return self._errors_and_result['result']==['Xform is valid!']

    def validate(self, path_to_xform, timeout=15):
        self._run_odk_validate(path_to_xform, timeout)
        self._parse_odk_validate_output()
        if not self.is_valid():
            raise ValidationError(self.get_odk_validate_output())


def check_xform(path):
    validator = XFormValidator()
    validator.validate(path)
    return validator.get_odk_validate_output()

if __name__ == '__main__':
    print __doc__
    check_xform(sys.argv[1])
