# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.

from unittest import TestCase
import pyxform
from pyxform.xls2xform import _create_parser, _validator_args_logic


class XLS2XFormTests(TestCase):
    survey_package = {
        'id_string': u'test_2011_08_29b',
        'name_of_main_section': u'gps',
        'sections': {
            u'gps': {
                u'children': [
                    {
                        u'name': u'location',
                        u'type': u'gps'
                        }
                    ],
                u'name': u'gps',
                u'type': u'survey'
                }
            },
        'title': u'test'
        }
    survey = pyxform.create_survey(**survey_package)

    def test_create_parser_without_args(self):
        """Should exit when no args provided."""
        with self.assertRaises(SystemExit):
            _create_parser().parse_args([])

    def test_create_parser_with_args(self):
        """Should parse the provided arguments."""
        arg_xlsform = 'xlsform.xlsx'
        arg_output = '.'
        arg_list = ['--json', '--skip_validate', '--no_pretty_print',
            arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(arg_xlsform, args.path_to_XLSForm)
        self.assertEqual(arg_output, args.output_path)
        self.assertEqual(True, args.json)
        self.assertEqual(False, args.skip_validate)
        self.assertEqual(False, args.no_pretty_print)

    def test_create_parser_file_name_with_space(self):
        """Should interpret the path correctly."""
        arg_xlsform = 'some/path/my xlsform.xlsx'
        arg_output = '.'
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(arg_xlsform, args.path_to_XLSForm)

    def test_create_parser_json_default_false(self):
        """Should have json=False if not specified."""
        arg_xlsform = 'xlsform.xlsx'
        arg_output = '.'
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(False, args.json)

    def test_create_parser_skip_validate_default_true(self):
        """Should have skip_validate=True if not specified."""
        arg_xlsform = 'xlsform.xlsx'
        arg_output = '.'
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(True, args.skip_validate)

    def test_create_parser_no_enketo_default_false(self):
        """Should have enketo_validate=False if not specified."""
        arg_xlsform = 'xlsform.xlsx'
        arg_output = '.'
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(False, args.enketo_validate)

    def test_create_parser_no_pretty_print_default_true(self):
        """Should have no_pretty_print=True if not specified."""
        args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
        ])
        self.assertEqual(True, args.no_pretty_print)

    def test_validator_args_logic_skip_validate_alone(self):
        """Should deactivate both validators."""
        raw_args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
            '--skip_validate'
        ])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(False, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    def test_validator_args_logic_odk_default(self):
        """Should activate ODK only."""
        raw_args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
        ])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(True, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    def test_validator_args_logic_enketo_only(self):
        """Should activate Enketo only."""
        raw_args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
            '--enketo_validate'
        ])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(False, args.odk_validate)
        self.assertEqual(True, args.enketo_validate)

    def test_validator_args_logic_odk_only(self):
        """Should activate ODK only."""
        raw_args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
            '--odk_validate'
        ])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(True, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)

    def test_validator_args_logic_odk_and_enketo(self):
        """Should activate ODK and Enketo."""
        raw_args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
            '--odk_validate',
            '--enketo_validate'
        ])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(True, args.odk_validate)
        self.assertEqual(True, args.enketo_validate)

    def test_validator_args_logic_skip_validate_override(self):
        """Should deactivate both validators"""
        raw_args = _create_parser().parse_args([
            'xlsform.xlsx',
            '.',
            '--skip_validate',
            '--odk_validate',
            '--enketo_validate',
        ])
        args = _validator_args_logic(args=raw_args)
        self.assertEqual(False, args.odk_validate)
        self.assertEqual(False, args.enketo_validate)
