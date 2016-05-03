# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.

from unittest import TestCase
import pyxform
from pyxform.xls2xform import _create_parser


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
        arg_json = '--json'
        arg_skip_validate = '--skip_validate'
        arg_list = [arg_json, arg_skip_validate, arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(arg_xlsform, args.path_to_XLSForm)
        self.assertEqual(arg_output, args.output_path)
        self.assertEqual(True, args.json)
        self.assertEqual(False, args.skip_validate)

    def test_create_parser_json_default_false(self):
        """Should have json=False if not specified."""
        arg_xlsform = 'xlsform.xlsx'
        arg_output = '.'
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(False, args.json)

    def test_create_parser_no_validate_default_true(self):
        """Should have no_validate=True if not specified."""
        arg_xlsform = 'xlsform.xlsx'
        arg_output = '.'
        arg_list = [arg_xlsform, arg_output]
        args = _create_parser().parse_args(arg_list)
        self.assertEqual(True, args.skip_validate)
