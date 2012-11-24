"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect.
"""
import os, sys
import xls2json
import builder

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) < 3:
        print __doc__
        print 'Usage:'
        print argv[0] + ' path_to_XLSForm output_path'
    else:
        warnings = []
        json_survey = xls2json.parse_file_to_json(argv[1], warnings=warnings)
        survey = builder.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(argv[2])
        for w in warnings:
            print w
        print 'Conversion complete!'