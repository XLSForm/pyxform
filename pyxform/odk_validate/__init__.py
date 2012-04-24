from subprocess import Popen, PIPE
import os, re, sys
from collections import defaultdict
# this is ugly, but allows running pyxform
# as a standalone xls validator from the cl
try:
    from pyxform.errors import ValidationError
except ImportError:
    from errors import ValidationError


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "java_lib", "ODK Validate.jar")

# Only the modded headless version of ODK Validate returns these codes.
# see: lonely_java_src/FormValidator.java
HEADLESS_ODK_VALIDATE_REGEXS = {
    'result': r"^Result: (.*)$",
    'error': r"^Error: (.*)$",
    }


class XFormValidator(object):

    def _run_odk_validate(self, path_to_xform):
        self._path_to_xform = path_to_xform
        stdout, stderr = Popen(["java", "-jar", ODK_VALIDATE_JAR, self._path_to_xform], stdout=PIPE, stderr=PIPE).communicate()
        self._odk_validate_output = (stdout + stderr).split('\n')

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

    def validate(self, path_to_xform):
        self._run_odk_validate(path_to_xform)
        self._parse_odk_validate_output()
        if not self.is_valid():
            raise ValidationError(self.get_odk_validate_output())


def check_xform(path):
    validator = XFormValidator()
    validator.validate(path)

if __name__ == '__main__':
    check_xform(sys.argv[1])
