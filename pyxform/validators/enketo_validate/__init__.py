import os
from subprocess import Popen, PIPE
from pyxform.validators.util import run_popen_with_timeout, decode_stream


CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
ENKETO_VALIDATE_JS = os.path.join(CURRENT_DIRECTORY, "enketo_validate.js")


class EnketoValidateError(Exception):
    pass


def _node_installed():
    try:
        p = Popen(["which", "node"], stdout=PIPE).stdout.readlines()
        found = len(p) != 0
    except WindowsError:
        p = Popen("node --version", stdout=PIPE)
        result = p.stdout.read()
        if not p.stdout.closed:
            p.stdout.close()
        found = result.startswith("v".encode())
    return found


def check_xform(path_to_xform):
    """
    Check the form with the Enketo validator.

    - return code 1: raise error with the stderr content.
    - return code 0: append warning with the stdout content (possibly none).

    :param path_to_xform: Path to the XForm to be validated.
    :return: warnings or List[str]
    """
    if not _node_installed():
        raise EnvironmentError(
            "pyxform enketo validate dependency: node not found")

    returncode, timeout, stdout, stderr = run_popen_with_timeout(
        ["node", ENKETO_VALIDATE_JS, path_to_xform], 100)
    warnings = []
    stderr = decode_stream(stderr)
    stdout = decode_stream(stdout)

    if timeout:
        return ["XForm took to long to completely validate."]
    else:
        if returncode > 0:  # Error invalid
            raise EnketoValidateError(
                'Enketo Validate Errors:\n' + stderr)
        elif returncode == 0:
            if stdout:
                warnings.append('Enketo Validate Warnings:\n' + stdout)
            return warnings
        elif returncode < 0:
            return ["Bad return code from Enketo Validate."]
