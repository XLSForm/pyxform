from collections import defaultdict
from contextlib import nested
import os
import re
from tempfile import NamedTemporaryFile
import sys

from modilabs.utils.subprocess_timeout import Subprocess

# this is ugly, but allows running pyxform
# as a standalone xls validator from the cl
try:
    from pyxform.errors import ValidationError
except ImportError:
    from errors import ValidationError


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "java_lib",
        "ODK Validate.jar")

# Only the modded headless version of ODK Validate returns these codes.
# see: lonely_java_src/FormValidator.java
HEADLESS_ODK_VALIDATE_REGEXS = {
    'result': r"^Result: (.*)$",
    'error': r"^Error: (.*)$",
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
        return self._errors_and_result['result']==['Valid']

    def validate(self, path_to_xform, timeout=15):
        self._run_odk_validate(path_to_xform, timeout)
        self._parse_odk_validate_output()
        if not self.is_valid():
            raise ValidationError(self.get_odk_validate_output())


def check_xform(path):
    validator = XFormValidator()
    validator.validate(path)

if __name__ == '__main__':
    check_xform(sys.argv[1])
