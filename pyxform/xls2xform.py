"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect.
"""

import argparse
import json
import logging
import os
from os.path import splitext
from io import BytesIO
from pathlib import Path

from pyxform import builder, xls2json
from pyxform.utils import has_external_choices, sheet_to_csv
from pyxform.validators.odk_validate import ODKValidateError

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def get_xml_path(path):
    """
    Returns the xform file path

    Generates an output path for the xform file from the given
    xlsx input file path.
    """
    return splitext(path)[0] + ".xml"


def xls2xform_convert(
    xlsform_path,
    xform_path=None,
    validate=True,
    pretty_print=True,
    enketo=False,
    xlsform_object=None,
):
    """Convert an XLSForm input to XForm output.

    xlsform_path is mandatory and must contain the file exension.

    To use an in-memory XLSForm instead, set a dummy path for xlsform_path,
    such as '/tmp/form.xlsx' (the extension is important, however).

    If xform_path is provided the output will be written to a file.
    If xform_path is not provided, the output will be returned as a tuple:
        (xform_data, warnings, choices_data)
    However, in this scenario, validation of the output XForm will be disabled.

    Setting `validate` to false will cause the form not to be processed by ODK Validate.
    This may be desirable since ODK Validate requires launching a subprocess that runs
    some Java code.
    """
    if not xform_path and not xlsform_object:
        msg = "Either xform_path or xlsform_object params must be specified"
        logger.error(msg)
        raise ValueError(msg)

    warnings = []

    if xlsform_object:
        logger.debug("Input read from memory object.")

    json_survey = xls2json.parse_file_to_json(
        xlsform_path,
        warnings=warnings,
        file_object=BytesIO(xlsform_object.getvalue()) if xlsform_object else None,
    )

    survey = builder.create_survey_element_from_dict(json_survey)

    if not xform_path:
        logger.info("No xform_path specified. XForm validation will be skipped.")

    # Read input from memory & write output to memory object
    if xlsform_object:
        xform = survey.to_xml(
            validate=validate, pretty_print=pretty_print, warnings=warnings
        )
    # Read input from filesystem & write output to filesystem
    else:
        survey.print_xform_to_file(
            xform_path,
            validate=validate if xform_path else False,
            pretty_print=pretty_print,
            warnings=warnings,
            enketo=enketo if xform_path else False,
        )

    file_type = Path(xlsform_path).suffix.lower()
    choices_exported = None

    if file_type != ".csv" and has_external_choices(json_survey):
        itemsets_csv = None

        if xform_path:
            itemsets_csv = str(Path(xform_path).parent / "itemsets.csv")

        choices_exported = sheet_to_csv(
            BytesIO(xlsform_object.getvalue()) if xlsform_object else xlsform_path,
            "external_choices",
            csv_path=itemsets_csv if itemsets_csv else None,
            file_type=file_type,
        )

        if not choices_exported:
            warnings.append(
                "Could not export itemsets.csv, perhaps the "
                "external choices sheet is missing."
            )
        else:
            if itemsets_csv:
                logger.info("External choices csv is located at: %s", itemsets_csv)
            else:
                logger.info("External choices csv generated")

    if xlsform_object and not xform_path:
        # Return XForm data, else written to specified file
        if not choices_exported:
            return BytesIO(xform.encode("utf-8")), warnings
        return BytesIO(xform.encode("utf-8")), warnings, choices_exported

    return warnings


def _create_parser():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path_to_XLSForm",
        help="Path to the Excel XLSX file with the XLSForm definition.",
    )
    parser.add_argument("output_path", help="Path to save the output to.", nargs="?")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Capture everything and report in JSON format.",
    )
    parser.add_argument(
        "--skip_validate",
        action="store_false",
        default=True,
        help="Do not run any external validators on the output XForm XML. "
        "Without this flag, ODK Validate is run by default for backwards "
        "compatibility. Internal pyxform checks cannot be skipped.",
    )
    parser.add_argument(
        "--odk_validate",
        action="store_true",
        default=False,
        help="Run the ODK Validate XForm external validator.",
    )
    parser.add_argument(
        "--enketo_validate",
        action="store_true",
        default=False,
        help="Run the Enketo Validate XForm external validator.",
    )
    parser.add_argument(
        "--pretty_print",
        action="store_true",
        default=False,
        help="Print XML forms with collapsed whitespace instead of pretty-printed.",
    )
    return parser


def _validator_args_logic(args):
    """
    Implements logic for how validator arguments work in combination.

    As per: https://github.com/XLSForm/pyxform/pull/167#issuecomment-353382008

    **backwards-compatible**
    `xls2xform.py myform --skip_validate`: no validators
    `xls2xform.py myform`: ODK only

    **new**
    `xls2xform.py myform --enketo_validate`: Enketo only
    `xls2xform.py myform --odk_validate`: ODK only
    `xls2xform.py myform --enketo_validate --odk_validate`: both
    `xls2xform.py myform --enketo_validate --odk_validate --skip_validate`: no validators
    """
    if not args.skip_validate:
        args.odk_validate = False
        args.enketo_validate = False
    elif args.skip_validate and not (args.odk_validate or args.enketo_validate):
        args.odk_validate = True
        args.enketo_validate = False
    return args


def main_cli():
    parser = _create_parser()
    raw_args = parser.parse_args()
    args = _validator_args_logic(args=raw_args)

    # auto generate an output path if one was not given
    if args.output_path is None:
        args.output_path = get_xml_path(args.path_to_XLSForm)

    if args.json:
        # Store everything in a list just in case the user wants to output
        # as a JSON encoded string.
        response = {"code": None, "message": None, "warnings": []}

        try:
            response["warnings"] = xls2xform_convert(
                xlsform_path=args.path_to_XLSForm,
                xform_path=args.output_path,
                validate=args.odk_validate,
                pretty_print=args.pretty_print,
                enketo=args.enketo_validate,
            )

            response["code"] = 100
            response["message"] = "Ok!"

            if response["warnings"]:
                response["code"] = 101
                response["message"] = "Ok with warnings."

        except Exception as e:
            # Catch the exception by default.
            response["code"] = 999
            response["message"] = str(e)

        logger.info(json.dumps(response))
    else:
        try:
            warnings = xls2xform_convert(
                xlsform_path=args.path_to_XLSForm,
                xform_path=args.output_path,
                validate=args.odk_validate,
                pretty_print=args.pretty_print,
                enketo=args.enketo_validate,
            )
        except OSError:
            # Do not crash if 'java' not installed
            logger.exception("EnvironmentError during conversion")
        except ODKValidateError:
            # Remove output file if there is an error
            os.remove(args.output_path)
            logger.exception("ODKValidateError during conversion.")
        else:
            if len(warnings) > 0:
                logger.warning("Warnings:")
            for w in warnings:
                logger.warning(w)
            logger.info("Conversion complete!")


if __name__ == "__main__":
    main_cli()
