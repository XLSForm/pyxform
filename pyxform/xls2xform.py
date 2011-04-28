"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect. xl2xform is called at the command line using::

    python xls2xform.py path-to-excel-file

To learn what sort of features are supported by xls2xform please refer
to xls/tutorial-v0.1.xls. This example survey is the most straight
forward introduction to the xls2xform syntax.
"""
import sys
from builder import create_survey_from_path

if __name__ == '__main__':
    survey = create_survey_from_path(sys.argv[1])
    path = "%s.xml" % survey.id_string()
    survey.print_xform_to_file(path=path)
