"""
Test xls2xform module.
"""
# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.

import os
import argparse
import logging
from io import BytesIO
from unittest import TestCase, mock

from pyxform.xls2xform import (
    _create_parser,
    _validator_args_logic,
    get_xml_path,
    main_cli,
    xls2xform_convert,
)

from tests.utils import path_to_text_fixture


class XLS2XFormTests(TestCase):
    def test_create_parser_without_args(self):
        """Should exit when no args provided."""
        with self.assertRaises(SystemExit):
            _create_parser().parse_args([])

    def test_create_parser_optional_output_path(self):
        """
        Should run fine for a single argument i.e. that is the
        path to the xlsx file path, while the output path is left out
        """
        try:
            _create_parser().parse_args(["/some/path/tofile.xlsx"])
        except SystemExit:
            self.fail()

    def test_create_parser_with_args(self):
        """Should parse the provided arguments."""
        arg_xlsform = "xlsform.xlsx"
        arg_output = "."
        arg_list = [
            "--json",
            "--skip_validate",
            "--pretty_print",
            arg_xlsform,
            arg_output,
        ]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(arg_xlsform, args.path_to_XLSForm)
        self.assertEqual(arg_output, args.output_path)
        self.assertEqual(True, args.json)
        self.assertEqual(False, args.skip_validate)
        self.assertEqual(True, args.pretty_print)

    def test_create_parser_file_name_with_space(self):
        """Should interpret the path correctly."""
        arg_xlsform = "some/path/my xlsform.xlsx"
        arg_output = "."
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(arg_xlsform, args.path_to_XLSForm)

    def test_create_parser_json_default_false(self):
        """Should have json=False if not specified."""
        arg_xlsform = "xlsform.xlsx"
        arg_output = "."
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(False, args.json)

    def test_create_parser_skip_validate_default_true(self):
        """Should have skip_validate=True if not specified."""
        arg_xlsform = "xlsform.xlsx"
        arg_output = "."
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(True, args.skip_validate)

    def test_create_parser_no_enketo_default_false(self):
        """Should have enketo_validate=False if not specified."""
        arg_xlsform = "xlsform.xlsx"
        arg_output = "."
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(False, args.enketo_validate)

    def test_create_parser_pretty_print_default_False(self):
        """Should have pretty_print=False if not specified."""
        args = _create_parser().parse_args(["xlsform.xlsx", "."])
        self.assertFalse(args.pretty_print)

    def test_validator_args_logic_skip_validate_alone(self):
        """Should deactivate both validators."""
        raw_args = _create_parser().parse_args(["xlsform.xlsx", ".", "--skip_validate"])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(False, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    def test_validator_args_logic_odk_default(self):
        """Should activate ODK only."""
        raw_args = _create_parser().parse_args(["xlsform.xlsx", "."])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(True, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    def test_validator_args_logic_enketo_only(self):
        """Should activate Enketo only."""
        raw_args = _create_parser().parse_args(["xlsform.xlsx", ".", "--enketo_validate"])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(False, args.odk_validate)
        self.assertEqual(True, args.enketo_validate)

    def test_validator_args_logic_odk_only(self):
        """Should activate ODK only."""
        raw_args = _create_parser().parse_args(["xlsform.xlsx", ".", "--odk_validate"])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(True, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    def test_validator_args_logic_odk_and_enketo(self):
        """Should activate ODK and Enketo."""
        raw_args = _create_parser().parse_args(
            ["xlsform.xlsx", ".", "--odk_validate", "--enketo_validate"]
        )
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(True, args.odk_validate)
        self.assertEqual(True, args.enketo_validate)

    def test_validator_args_logic_skip_validate_override(self):
        """Should deactivate both validators"""
        raw_args = _create_parser().parse_args(
            [
                "xlsform.xlsx",
                ".",
                "--skip_validate",
                "--odk_validate",
                "--enketo_validate",
            ]
        )
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(False, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            path_to_XLSForm="xlsform.xlsx",
            output_path=None,
            json=False,
            skip_validate=False,
            odk_validate=False,
            enketo_validate=False,
            pretty_print=False,
        ),
    )
    @mock.patch("pyxform.xls2xform.xls2xform_convert")
    def test_xls2form_convert_parameters(self, converter_mock, parser_mock_args):
        """
        Checks that xls2xform_convert is given the right arguments, when the
        output-path is not given
        """
        converter_mock.return_value = "{}"
        main_cli()
        converter_mock.assert_called_once_with(
            xlsform_path="xlsform.xlsx",
            xform_path="xlsform.xml",
            validate=False,
            pretty_print=False,
            enketo=False,
        )

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            path_to_XLSForm="xlsform.xlsx",
            output_path=None,
            json=True,
            skip_validate=False,
            odk_validate=False,
            enketo_validate=False,
            pretty_print=False,
        ),
    )
    @mock.patch("pyxform.xls2xform.xls2xform_convert")
    def test_xls2xform_convert_params_with_flags(self, converter_mock, parser_mock_args):
        """
        Should call xlsform_convert with the correct input for output
        path where only the xlsform input path and json flag were provided, since
        the xlsform-convert can be called if json flag was set or when not
        """
        converter_mock.return_value = "{}"
        main_cli()
        converter_mock.assert_called_once_with(
            xlsform_path="xlsform.xlsx",
            xform_path="xlsform.xml",
            validate=False,
            pretty_print=False,
            enketo=False,
        )

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            path_to_XLSForm=path_to_text_fixture("bad_calc.xlsx"),
            output_path=None,
            json=False,
            skip_validate=True,
            odk_validate=True,
            enketo_validate=True,
            pretty_print=True,
        ),
    )
    def test_xls2xform_convert_throwing_odk_error(self, parser_mock_args):
        """
        Parse and validate bad_calc.xlsx
        """
        logger = logging.getLogger("pyxform.xls2xform")
        with mock.patch.object(logger, "error") as mock_debug:
            main_cli()
            self.assertEqual(mock_debug.call_count, 1)

    def test_xls2form_convert_via_api(self):
        """
        Tests xls2form_convert directly from API.
        """
        # Call the conversion function
        warnings = xls2xform_convert(
            xlsform_path="./tests/example_xls/tutorial.xls",
            xform_path="/tmp/xform.xml",
            validate=False,
            pretty_print=False,
            enketo=False
        )
        # Check if conversion was successful
        self.assertEqual(
            warnings,
            [
                'On the choices sheet there is a column ("tutorial notes") with an '
                'illegal header. Headers cannot include spaces.'
            ]
        )

    def test_xls2form_convert_invalid_input(self):
        """
        Tests xls2form_convert cannot be called without xform_path or xlsform_object set.
        """
        with self.assertRaises(ValueError):
            xls2xform_convert(
                xlsform_path="/tmp/form.xlsx",
                validate=False,
                pretty_print=False,
                enketo=False,
            )

    def test_xls2form_convert_xlsx_bytesio(self):
        """
        Tests xls2form_convert with XLSX BytesIO object instead of file path.
        """
        # Read in XLSX
        with open("./tests/example_xls/yes_or_no_question.xlsx", "rb") as xlsform:
            xlsxdata = BytesIO(xlsform.read())

        # Call the conversion function
        xform, warnings = xls2xform_convert(
            xlsform_path="/tmp/form.xlsx",
            validate=False,
            pretty_print=False,
            enketo=False,
            xlsform_object=xlsxdata,
        )
        # Check if conversion was successful
        self.assertEqual(
            warnings,
            [
                'The following language declarations do not contain valid machine-readable '
                'codes: english. Learn more: http://xlsform.org#multiple-language-support'
            ]
        )
        self.assertEqual(type(xform), BytesIO)
        self.assertEqual(len(xform.getvalue()), 1245)

    def test_xls2form_convert_xls_bytesio(self):
        """
        Tests xls2form_convert with XLS BytesIO object instead of file path.
        """
        # Read in XLS
        with open("./tests/example_xls/choice_name_same_as_select_name.xls", "rb") as xlsform:
            xlsdata = BytesIO(xlsform.read())

        # Call the conversion function
        xform, warnings = xls2xform_convert(
            xlsform_path="/tmp/form.xls",
            validate=False,
            pretty_print=False,
            enketo=False,
            xlsform_object=xlsdata,
        )
        # Check if conversion was successful
        self.assertEqual(
            warnings,
            []
        )
        self.assertEqual(type(xform), BytesIO)
        self.assertEqual(len(xform.getvalue()), 879)

    def test_xls2form_convert_csv_bytesio(self):
        """
        Tests xls2form_convert with CSV BytesIO object instead of file path.
        """
        # Read in CSV
        with open("./tests/example_xls/yes_or_no_question.csv", "rb") as xlsform:
            csvdata = BytesIO(xlsform.read())

        # Call the conversion function
        xform, warnings = xls2xform_convert(
            xlsform_path="/tmp/form.csv",
            validate=False,
            pretty_print=False,
            enketo=False,
            xlsform_object=csvdata,
        )
        # Check if conversion was successful
        self.assertEqual(
            warnings,
            [
                'The following language declarations do not contain valid machine-readable '
                'codes: english. Learn more: http://xlsform.org#multiple-language-support'
            ]
        )
        self.assertEqual(type(xform), BytesIO)
        self.assertEqual(len(xform.getvalue()), 1245)

    def test_xls2form_convert_xls_select_one_external(self):
        """
        Tests xls2form_convert with XLS select one external option.
        """
        # Call the conversion function with file input
        warnings = xls2xform_convert(
            xlsform_path="./tests/example_xls/select_one_external.xls",
            xform_path="/tmp/form.xml",
            validate=False,
            pretty_print=False,
            enketo=False,
        )

        assert os.path.exists("/tmp/itemsets.csv"), "itemsets.csv not found in /tmp directory"

        self.assertEqual(
            warnings,
            [
                'The following language declarations do not contain valid machine-readable '
                'codes: English, French. Learn more: '
                'http://xlsform.org#multiple-language-support'
            ]
        )

        # Check content of written choices file
        with open("/tmp/itemsets.csv", "r") as choices_csv:
            data = choices_csv.read()
        assert len(data) == 759
        # Check random char
        assert data[3] == "s"
        assert data[-3] == "p"

    def test_xls2form_convert_xlsx_select_one_external(self):
        """
        Tests xls2form_convert with XLSX select one external option.
        """
        # Call the conversion function with file input
        warnings = xls2xform_convert(
            xlsform_path="./tests/example_xls/select_one_external.xlsx",
            xform_path="/tmp/form.xml",
            validate=False,
            pretty_print=False,
            enketo=False,
        )

        assert os.path.exists("/tmp/itemsets.csv"), "itemsets.csv not found in /tmp directory"

        self.assertEqual(
            warnings,
            [
                'The following language declarations do not contain valid machine-readable '
                'codes: English, French. Learn more: '
                'http://xlsform.org#multiple-language-support'
            ]
        )

        # Check content of written choices file
        with open("/tmp/itemsets.csv", "r") as choices_csv:
            data = choices_csv.read()
        assert len(data) == 791
        # Check random char
        assert data[3] == "s"
        assert data[-3] == "p"

        # Read in XLSX
        with open("./tests/example_xls/select_one_external.xlsx", "rb") as xlsform:
            xlsxdata = BytesIO(xlsform.read())

        # Call the conversion function with BytesIO input
        xform, warnings, choices = xls2xform_convert(
            xlsform_path="/tmp/form.xlsx",
            validate=False,
            pretty_print=False,
            enketo=False,
            xlsform_object=xlsxdata,
        )
        # Check if conversion was successful
        self.assertEqual(
            warnings,
            [
                'The following language declarations do not contain valid machine-readable '
                'codes: English, French. Learn more: '
                'http://xlsform.org#multiple-language-support'
            ]
        )
        data = choices.getvalue()
        assert len(data) == 806
        # Check random char
        decoded = data.decode("utf-8").strip()
        assert decoded[3] == "s"
        assert decoded[-3] == "u"

    def test_get_xml_path_function(self):
        """Should return an xml path in the same directory as the xlsx file"""
        xlsx_path = "/home/user/Desktop/xlsform.xlsx"
        expected = "/home/user/Desktop/xlsform.xml"
        self.assertEqual(expected, get_xml_path(xlsx_path))
        # check that it also handles spaced routes
        xlsx_path = "/home/user/Desktop/my xlsform.xlsx"
        expected = "/home/user/Desktop/my xlsform.xml"
        self.assertEqual(expected, get_xml_path(xlsx_path))
