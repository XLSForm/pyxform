"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect.
"""
import sys
import xls2json
import builder
import json


# Converter.
def xls2xform_convert():
    # Warnings.
    warnings = []

    json_survey = xls2json.parse_file_to_json(argv[1], warnings=warnings)
    survey = builder.create_survey_element_from_dict(json_survey)
    # Setting validate to false will cause the form not to be processed by
    # ODK Validate.
    # This may be desirable since ODK Validate requires launching a subprocess
    # that runs some java code.
    survey.print_xform_to_file(argv[2], validate=True, warnings=warnings)

    return warnings


if __name__ == '__main__':
    argv = sys.argv
    if len(argv) < 3:
        print __doc__
        print 'Usage:'
        print argv[0] + ' path_to_XLSForm output_path'
        print '--json    Output results in json format.'
    else:

        # --json flag present. Capture everything and report in JSON format.
        if '--json' in argv:
            # Store everything in a list just in case the user wants to output
            # as a JSON encoded string.
            response = {'code': None, 'message': None, 'warnings': []}

            try:
                response['warnings'] = xls2xform_convert()

                response['code'] = 100
                response['message'] = "Ok!"

                if response['warnings']:
                    response['code'] = 101
                    response['message'] = 'Ok with warnings.'

            except Exception as e:
                # Catch the exception by default.
                response['code'] = 999
                response['message'] = str(e)

            print json.dumps(response)

        # --json not present. Do not capture anything.
        else:
            warnings = xls2xform_convert()

            # Regular output. Just print.
            for w in warnings:
                print w
            print 'Conversion complete!'
