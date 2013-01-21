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
        #Setting validate to false will cause the form not to be processed by ODK Validate.
        #This may be desirable since ODK Validate requires launching a subprocess that runs some java code.
        survey.print_xform_to_file(argv[2], validate=True, warnings=warnings)
        for w in warnings:
            print w
        print 'Conversion complete!'