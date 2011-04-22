from subprocess import Popen, PIPE
import os, re

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ODK_VALIDATE_JAR = os.path.join(CURRENT_DIRECTORY, "java_lib", "ODK Validate.jar")

class ValidateException(Exception):
    def __init__(self, flag, message):
        self.flag = flag
        self.message = message
    
	def __str__(self):
	    return repr(self.message)

class ValidateError(ValidateException):
    pass

class ValidateWarning(ValidateException):
    pass

# Only the modded headless version of ODK Validate returns these codes.
#  see: lonely_java_src/FormValidator.java
HEADLESS_ODK_VALIDATE_REGEXS = {
    'result': r"\nResult: (.*)$",
    'error': r"\nError: (.*)$"
}

class XFormValidationStatus:
    def __init__(self):
        self.valid = False
    def set_flag(self, exc, e):
        self.exc = exc
        self.flag = e.flag
        self.message = e.message
    def __str__(self):
        return "%s: %s" % (self.flag, self.message)

def check_xform(filename):
    status = XFormValidationStatus()
    try:
        validate_xform(filename)
    except ValidateWarning, e:
        if re.match("valid", e.flag, re.I): status.valid = True
        status.set_flag("Warning", e)
    except ValidateError, e:
        status.set_flag("Error", e)
    return status

def validate_xform(p2x):
    jar_output = Popen(["java", "-jar", ODK_VALIDATE_JAR, p2x], stdout=PIPE, stderr=PIPE).communicate()
    
    # since i'm not sure whether errors get pumped to stderr/stdout, so I'll just
    # mush all the output together...
    result_str = "\n".join(jar_output)

    # Andrew added this print statement because check_xform wasn't
    # throwing the following error:
    # Parsing form...
    # Title: "Practice"
    # no <translation>s defined
    #     Problem found at nodeset: /html/head/model/itext
    #     With element <itext/>
    # Result: Invalid
    print result_str
    
    error_match = re.search(HEADLESS_ODK_VALIDATE_REGEXS['error'], result_str, flags=re.IGNORECASE)
    result_match = re.search(HEADLESS_ODK_VALIDATE_REGEXS['result'], result_str, flags=re.IGNORECASE)
    
    if error_match:
        error_flag = error_match.group(1)
        error_msg = re.sub(HEADLESS_ODK_VALIDATE_REGEXS['error'], "", result_str).strip()
        raise ValidateError(error_flag, error_msg)
    elif result_match:
        result_flag = result_match.group(1)
        warning = re.sub(HEADLESS_ODK_VALIDATE_REGEXS['result'], "", result_str).strip()
        raise ValidateWarning(result_flag, warning)
