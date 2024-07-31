"""
xls2xform converts properly formatted Excel documents into XForms for
use with ODK Collect.
"""

import argparse
import json
import logging
from dataclasses import dataclass
from io import BytesIO
from os import PathLike
from os.path import splitext
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from pyxform import builder, xls2json
from pyxform.utils import coalesce, external_choices_to_csv, has_external_choices
from pyxform.validators.odk_validate import ODKValidateError
from pyxform.xls2json_backends import (
    definition_to_dict,
    get_definition_data,
)

if TYPE_CHECKING:
    from pyxform.survey import Survey

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


@dataclass
class ConvertResult:
    """
    Result data from the XLSForm to XForm conversion.

    :param xform: The result XForm
    :param warnings: Warnings raised during conversion.
    :param itemsets: If the XLSForm defined external itemsets, a CSV version of them.
    :param _pyxform: Internal representation of the XForm, may change without notice.
    :param _survey: Internal representation of the XForm, may change without notice.
    """

    xform: str
    warnings: list[str]
    itemsets: str | None
    _pyxform: dict
    _survey: "Survey"


def convert(
    xlsform: str | PathLike[str] | bytes | BytesIO | BinaryIO | dict,
    warnings: list[str] | None = None,
    validate: bool = False,
    pretty_print: bool = False,
    enketo: bool = False,
    form_name: str | None = None,
    default_language: str | None = None,
    file_type: str | None = None,
) -> ConvertResult:
    """
    Run the XLSForm to XForm conversion.

    This function avoids result file IO so it is more suited to library usage of pyxform.

    If validate=True or Enketo=True, then the XForm will be written to a temporary file
    to be checked by ODK Validate and/or Enketo Validate. These validators are run as
    external processes. A recent version of ODK Validate is distributed with pyxform,
    while Enketo Validate is not. A script to download or update these validators is
    provided in `validators/updater.py`.

    :param xlsform: The input XLSForm file path or content. If the content is bytes or
      supports read (a class that has read() -> bytes) it's assumed to relate to the file
      bytes content, not a path.
    :param warnings: The conversions warnings list.
    :param validate: If True, check the XForm with ODK Validate
    :param pretty_print: If True, format the XForm with spaces, line breaks, etc.
    :param enketo: If True, check the XForm with Enketo Validate.
    :param form_name: Used for the main instance root node name.
    :param default_language: The name of the default language for the form.
    :param file_type: If provided, attempt parsing the data only as this type. Otherwise,
      parsing of supported data types will be attempted until one of them succeeds. If the
      xlsform is provided as a dict, then it is used directly and this argument is ignored.
    """
    warnings = coalesce(warnings, [])
    if isinstance(xlsform, dict):
        workbook_dict = xlsform
        fallback_form_name = None
    else:
        definition = get_definition_data(definition=xlsform)
        if file_type is None:
            file_type = definition.file_type
        workbook_dict = definition_to_dict(definition=definition, file_type=file_type)
        fallback_form_name = definition.file_path_stem
    pyxform_data = xls2json.workbook_to_json(
        workbook_dict=workbook_dict,
        form_name=form_name,
        fallback_form_name=fallback_form_name,
        default_language=default_language,
        warnings=warnings,
    )
    survey = builder.create_survey_element_from_dict(pyxform_data)
    xform = survey.to_xml(
        validate=validate,
        pretty_print=pretty_print,
        warnings=warnings,
        enketo=enketo,
    )
    itemsets = None
    if has_external_choices(json_struct=pyxform_data):
        itemsets = external_choices_to_csv(workbook_dict=workbook_dict)
    return ConvertResult(
        xform=xform,
        warnings=warnings,
        itemsets=itemsets,
        _pyxform=pyxform_data,
        _survey=survey,
    )


def xls2xform_convert(
    xlsform_path: str | PathLike[str],
    xform_path: str | PathLike[str],
    validate: bool = True,
    pretty_print: bool = True,
    enketo: bool = False,
) -> list[str]:
    warnings = []
    result = convert(
        xlsform=xlsform_path,
        validate=validate,
        pretty_print=pretty_print,
        enketo=enketo,
        warnings=warnings,
    )
    with open(xform_path, mode="w", encoding="utf-8") as f:
        f.write(result.xform)
    if result.itemsets is not None:
        itemsets_path = Path(xform_path).parent / "itemsets.csv"
        with open(itemsets_path, mode="w", encoding="utf-8", newline="") as f:
            f.write(result.itemsets)
            logger.info("External choices csv is located at: %s", itemsets_path)
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
            Path(args.output_path).unlink(missing_ok=True)
            logger.exception("ODKValidateError during conversion.")
        else:
            if len(warnings) > 0:
                logger.warning("Warnings:")
            for w in warnings:
                logger.warning(w)
            logger.info("Conversion complete!")


if __name__ == "__main__":
    main_cli()
