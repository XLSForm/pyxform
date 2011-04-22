"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect. xl2xform is called at the command line using::

    python xls2xform.py path-to-excel-file

To learn what sort of features are supported by xls2xform please refer
to xls/tutorial-v0.1.xls. This example survey is the most straight
forward introduction to the xls2xform syntax.
"""

import sys
from xls2json import SurveyReader
from builder import create_survey_element_from_json

def xls2json(name):
    converter = SurveyReader("%s.xls" % name)
    converter.print_json_to_file()

def json2xform(name):
    s = create_survey_element_from_json("%s.json" % name)
    path = "%(name)s_%(date)s.xml" % {
        "name" : name,
        "date" : s.date_stamp()
        }
    s.print_xform_to_file(path=path)

def xls2xform(path):
    assert path.endswith(".xls")
    name = path[:-4]
    xls2json(name)
    json2xform(name)

if __name__=="__main__":
    name = sys.argv[1]
    xls2xform(name)
