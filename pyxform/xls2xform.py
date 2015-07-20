"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect.
"""
import sys
import xls2json
import builder
import json
import argparse
from utils import sheet_to_csv, has_external_choices
import os
import odk_validate

def xls2xform_convert(xlsform_path, xform_path, validate=True):
    warnings = []

    json_survey = xls2json.parse_file_to_json(xlsform_path, warnings=warnings)
    survey = builder.create_survey_element_from_dict(json_survey)
    # Setting validate to false will cause the form not to be processed by
    # ODK Validate.
    # This may be desirable since ODK Validate requires launching a subprocess
    # that runs some java code.
    survey.print_xform_to_file(xform_path, validate=validate, warnings=warnings)
    output_dir = os.path.split(xform_path)[0]
    if has_external_choices(json_survey):
        itemsets_csv = os.path.join(output_dir, "itemsets.csv")
        choices_exported = sheet_to_csv(xlsform_path, itemsets_csv, "external_choices")
        if not choices_exported:
            warnings.append("Could not export itemsets.csv, perhaps the external choices sheet is missing.")
        else:
            print 'External choices csv is located at:', itemsets_csv
    return warnings


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path_to_XLSForm')
    parser.add_argument('output_path')
    parser.add_argument('--json',
                        action='store_true',
                        help="Capture everything and report in JSON format.")
    parser.add_argument('--novalidate',
                        action='store_false',
                        help=("Do not validate XForm with ODK Validate. "
                              "Default is to validate."))
    args = parser.parse_args()
    
    if args.json:
        # Store everything in a list just in case the user wants to output
        # as a JSON encoded string.
        response = {'code': None, 'message': None, 'warnings': []}

        try:
            response['warnings'] = xls2xform_convert(args.path_to_XLSForm,
                                                     args.output_path,
                                                     validate=args.novalidate)

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
    else:
        try:
            warnings = xls2xform_convert(args.path_to_XLSForm, args.output_path,
                                         validate=args.novalidate)
            if len(warnings) > 0:
                print "Warnings:"
            for w in warnings:
                print w
            print 'Conversion complete!'
        except EnvironmentError as e:
            # Do not crash if 'java' not installed
            print e.message
        except odk_validate.ODKValidateError as e:
            # Remove output file if there is an error
            os.remove(args.output_path)
            print e.message