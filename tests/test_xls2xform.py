"""
Test xls2xform module.
"""

# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.
import argparse
import logging
from io import BytesIO
from itertools import product
from pathlib import Path
from unittest import TestCase, mock

from pyxform.errors import PyXFormError
from pyxform.xls2xform import (
    ConvertResult,
    _create_parser,
    _validator_args_logic,
    convert,
    get_xml_path,
    main_cli,
    xls2xform_convert,
)

from tests import example_xls
from tests.utils import get_temp_dir, get_temp_file, path_to_text_fixture


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

    def test_get_xml_path_function(self):
        """Should return an xml path in the same directory as the xlsx file"""
        xlsx_path = "/home/user/Desktop/xlsform.xlsx"
        expected = "/home/user/Desktop/xlsform.xml"
        self.assertEqual(expected, get_xml_path(xlsx_path))
        # check that it also handles spaced routes
        xlsx_path = "/home/user/Desktop/my xlsform.xlsx"
        expected = "/home/user/Desktop/my xlsform.xml"
        self.assertEqual(expected, get_xml_path(xlsx_path))


class TestXLS2XFormConvert(TestCase):
    """
    Tests for `xls2xform_convert`.
    """

    def test_xls2xform_convert__ok(self):
        """Should find the expected output files for the conversion."""
        xlsforms = (
            Path(example_xls.PATH) / "group.xlsx",
            Path(example_xls.PATH) / "group.xls",
            Path(example_xls.PATH) / "group.csv",
            Path(example_xls.PATH) / "group.md",
            Path(example_xls.PATH) / "choice_name_as_type.xls",  # has external choices
        )
        kwargs = (
            ("validate", (True, False)),
            ("pretty_print", (True, False)),
        )
        names, values = zip(*kwargs, strict=False)
        combos = [dict(zip(names, c, strict=False)) for c in product(*values)]
        with get_temp_file() as xform:
            for x in xlsforms:
                for k in combos:
                    with self.subTest(msg=f"{x.name}, {k}"):
                        observed = xls2xform_convert(
                            xlsform_path=x, xform_path=xform, **k
                        )
                        self.assertIsInstance(observed, list)
                        self.assertEqual(len(observed), 0)
                        self.assertGreater(len(Path(xform).read_text()), 0)
                        if x.name == "choice_name_as_type.xls":
                            self.assertTrue(
                                (Path(xform).parent / "itemsets.csv").is_file()
                            )


class TestXLS2XFormConvertAPI(TestCase):
    """
    Tests for the `convert` library API entrypoint (not xls2xform_convert).
    """

    @staticmethod
    def with_xlsform_path_str(**kwargs):
        return convert(xlsform=kwargs.pop("xlsform").as_posix(), **kwargs)

    @staticmethod
    def with_xlsform_path_pathlike(**kwargs):
        return convert(**kwargs)

    @staticmethod
    def with_xlsform_data_str(**kwargs):
        return convert(xlsform=kwargs.pop("xlsform").read_text(), **kwargs)

    @staticmethod
    def with_xlsform_data_bytes(**kwargs):
        return convert(xlsform=kwargs.pop("xlsform").read_bytes(), **kwargs)

    @staticmethod
    def with_xlsform_data_bytesio(**kwargs):
        with open(kwargs.pop("xlsform"), mode="rb") as f:
            return convert(xlsform=BytesIO(f.read()), **kwargs)

    @staticmethod
    def with_xlsform_data_binaryio(**kwargs):
        with open(kwargs.pop("xlsform"), mode="rb") as f:
            return convert(xlsform=f, **kwargs)

    def test_args_combinations__ok(self):
        """Should find that generic call patterns return a ConvertResult without error."""
        funcs = [
            ("str (path)", self.with_xlsform_path_str),
            ("PathLike[str]", self.with_xlsform_path_pathlike),
            ("bytes", self.with_xlsform_data_bytes),
            ("BytesIO", self.with_xlsform_data_bytesio),
            ("BinaryIO", self.with_xlsform_data_binaryio),
            ("str (data)", self.with_xlsform_data_str),  # Only for .csv, .md.
        ]
        xlsforms = (
            (Path(example_xls.PATH) / "group.xlsx", funcs[:4]),
            (Path(example_xls.PATH) / "group.xls", funcs[:4]),
            (Path(example_xls.PATH) / "group.csv", funcs),
            (Path(example_xls.PATH) / "group.md", funcs),
            (
                Path(example_xls.PATH) / "choice_name_as_type.xls",
                funcs[:4],
            ),  # has external choices
        )
        # Not including validate here because it's slow, the test is more about input,
        # and these same forms are checked with validate=True above via xls2xform_convert.
        kwargs = (
            ("warnings", (None, [])),
            ("pretty_print", (True, False)),
        )
        names, values = zip(*kwargs, strict=False)
        combos = [dict(zip(names, c, strict=False)) for c in product(*values)]
        for x, fn in xlsforms:
            for n, f in fn:
                for k in combos:
                    with self.subTest(msg=f"{x.name}, {n}, {k}"):
                        if k["warnings"] is not None:  # Want a new list per iteration.
                            k["warnings"] = []
                        observed = f(xlsform=x, **k)
                        self.assertIsInstance(observed, ConvertResult)
                        self.assertGreater(len(observed.xform), 0)

    def test_invalid_input_raises(self):
        """Should raise an error for invalid input or file types."""
        msg = "Argument 'definition' was not recognized as a supported type"

        with get_temp_file() as empty, get_temp_dir() as td:
            bad_xls = Path(td) / "bad.xls"
            bad_xls.write_text("bad")
            bad_xlsx = Path(td) / "bad.xlsx"
            bad_xlsx.write_text("bad")
            bad_type = Path(td) / "bad.txt"
            bad_type.write_text("bad")
            cases = (
                None,
                "",
                b"",
                "ok",
                b"ok",
                empty,
                bad_xls,
                bad_xlsx,
                bad_type,
            )
            for case in cases:
                with self.subTest(msg=f"{case}"):
                    with self.assertRaises(PyXFormError) as err:
                        convert(xlsform=case)
                    self.assertTrue(
                        err.exception.args[0].startswith(msg), msg=str(err.exception)
                    )

    def test_call_with_dict__ok(self):
        """Should find that passing in a dict returns a ConvertResult without error."""
        ss_structure = {
            "survey": [
                {
                    "type": "text",
                    "name": "family_name",
                    "label:English (en)": "What's your family name?",
                },
                {
                    "type": "begin group",
                    "name": "father",
                    "label:English (en)": "Father",
                },
                {
                    "type": "phone number",
                    "name": "phone_number",
                    "label:English (en)": "What's your father's phone number?",
                },
                {
                    "type": "integer",
                    "name": "age",
                    "label:English (en)": "How old is your father?",
                },
                {
                    "type": "end group",
                },
            ]
        }
        observed = convert(xlsform=ss_structure)
        self.assertIsInstance(observed, ConvertResult)
        self.assertGreater(len(observed.xform), 0)
