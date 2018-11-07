"""
Testing simple cases for Xls2Json
"""
from unittest2 import TestCase
from pyxform.xls2json import SurveyReader
from pyxform.xls2json_backends import xls_to_dict, csv_to_dict
from pyxform.tests import utils
import os
import json
import codecs


# Nothing calls this AFAICT
def absolute_path(f, file_name):
    directory = os.path.dirname(f)
    return os.path.join(directory, file_name)


DIR = os.path.dirname(__file__)


class BasicXls2JsonApiTests(TestCase):
    maxDiff = None

    def test_simple_yes_or_no_question(self):
        filename = "yes_or_no_question.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".json")
        expected_output_path = os.path.join(DIR, "test_expected_output",
                                            root_filename + ".json")
        x = SurveyReader(path_to_excel_file)
        x_results = x.to_json_dict()
        with codecs.open(output_path, mode="w", encoding="utf-8") as fp:
            json.dump(x_results, fp=fp, ensure_ascii=False, indent=4)
        # Compare with the expected output:
        with codecs.open(expected_output_path, 'rb',
                         encoding="utf-8") as expected_file:
            with codecs.open(output_path, 'rb',
                             encoding="utf-8") as actual_file:
                expected_json = json.load(expected_file)
                actual_json = json.load(actual_file)
                self.assertEqual(expected_json, actual_json)

    def test_hidden(self):
        x = SurveyReader(utils.path_to_text_fixture("hidden.xls"))
        x_results = x.to_json_dict()

        expected_dict = [
            {
                u'type': u'hidden',
                u'name': u'hidden_test'
            },
            {
                'children': [
                    {
                        'bind': {
                            'calculate': "concat('uuid:', uuid())",
                            'readonly': 'true()'
                        },
                        'name': 'instanceID',
                        'type': 'calculate'
                    }
                ],
                'control': {
                    'bodyless': True
                },
                'name': 'meta',
                'type': 'group'
            }
        ]
        self.assertEqual(x_results[u"children"], expected_dict)

    def test_gps(self):
        x = SurveyReader(utils.path_to_text_fixture("gps.xls"))

        expected_dict = [
            {
                u'type': u'gps', u'name': u'location', u'label': u'GPS'},
            {
                'children': [
                    {
                        'bind': {
                            'calculate': "concat('uuid:', uuid())",
                            'readonly': 'true()'
                        },
                        'name': 'instanceID',
                        'type': 'calculate'
                    }
                ],
                'control': {
                    'bodyless': True
                },
                'name': 'meta',
                'type': 'group'
            }]

        self.assertEqual(x.to_json_dict()[u"children"], expected_dict)

    def test_text_and_integer(self):
        x = SurveyReader(utils.path_to_text_fixture("text_and_integer.xls"))

        expected_dict = [
            {
                u'label': {
                    u'english': u'What is your name?'
                },
                u'type': u'text',
                u'name': u'your_name'
            },
            {
                u'label': {
                    u'english': u'How many years old are you?'
                },
                u'type': u'integer',
                u'name': u'your_age'
            },
            {
                u'children': [
                    {
                        u'bind': {
                            'calculate': "concat('uuid:', uuid())",
                            'readonly': 'true()'
                        },
                        u'name': 'instanceID',
                        u'type': 'calculate'
                    }
                ],
                u'control': {
                    'bodyless': True
                },
                u'name': 'meta',
                u'type': u'group'
            }
        ]

        self.assertEqual(x.to_json_dict()[u"children"], expected_dict)

    def test_table(self):
        filename = "simple_loop.xls"
        path_to_excel_file = os.path.join(DIR, "example_xls", filename)
        # Get the xform output path:
        root_filename, ext = os.path.splitext(filename)
        output_path = os.path.join(DIR, "test_output", root_filename + ".json")
        expected_output_path = os.path.join(DIR, "test_expected_output",
                                            root_filename + ".json")
        x = SurveyReader(path_to_excel_file)
        x_results = x.to_json_dict()
        with codecs.open(output_path, mode="w", encoding="utf-8") as fp:
            json.dump(x_results, fp=fp, ensure_ascii=False, indent=4)
        # Compare with the expected output:
        with codecs.open(expected_output_path, 'rb',
                         encoding="utf-8") as expected_file:
            with codecs.open(output_path, 'rb',
                             encoding="utf-8") as actual_file:
                expected_json = json.load(expected_file)
                actual_json = json.load(actual_file)
                self.assertEqual(expected_json, actual_json)

    def test_choice_filter_choice_fields(self):
        """
        Test that the choice filter fields appear on children field of json
        """
        choice_filter_survey = SurveyReader(
            utils.path_to_text_fixture("choice_filter_test.xlsx"))

        expected_dict = [
            {
                u'choices': [
                    {
                        u'name': u'texas',
                        u'label': u'Texas'
                    },
                    {
                        u'name': u'washington',
                        u'label': u'Washington'
                    }
                ],
                u'type': u'select one',
                u'name': u'state',
                u'parameters': {},
                u'label': u'state'
            },
            {
                u'name': u'county',
                u'parameters': {},
                u'choice_filter': u'${state}=cf',
                u'label': u'county',
                u'itemset': u'counties',
                u'choices': [
                    {
                        u'label': u'King',
                        u'cf': u'washington',
                        u'name': u'king'
                    },
                    {
                        u'label': u'Pierce',
                        u'cf': u'washington',
                        u'name': u'pierce'
                    },
                    {
                        u'label': u'King',
                        u'cf': u'texas',
                        u'name': u'king'
                    },
                    {
                        u'label': u'Cameron',
                        u'cf': u'texas',
                        u'name': u'cameron'
                    }
                ],
                u'type': u'select one'
            },
            {
                u'name': u'city',
                u'parameters': {},
                u'choice_filter': u'${county}=cf',
                u'label': u'city',
                u'itemset': u'cities',
                u'choices': [
                    {
                        u'label': u'Dumont',
                        u'cf': u'king',
                        u'name': u'dumont'
                    },
                    {
                        u'label': u'Finney',
                        u'cf': u'king',
                        u'name': u'finney'
                    },
                    {
                        u'label': u'brownsville',
                        u'cf': u'cameron',
                        u'name': u'brownsville'
                    },
                    {
                        u'label': u'harlingen',
                        u'cf': u'cameron',
                        u'name': u'harlingen'
                    },
                    {
                        u'label': u'Seattle',
                        u'cf': u'king',
                        u'name': u'seattle'
                    },
                    {
                        u'label': u'Redmond',
                        u'cf': u'king',
                        u'name': u'redmond'
                    },
                    {
                        u'label': u'Tacoma',
                        u'cf': u'pierce',
                        u'name': u'tacoma'
                    },
                    {
                        u'label': u'Puyallup',
                        u'cf': u'pierce',
                        u'name': u'puyallup'
                    }
                ],
                u'type': u'select one'
            },
            {
                u'control': {
                    u'bodyless': True
                },
                u'type': u'group',
                u'name': u'meta',
                u'children': [
                    {
                        u'bind': {
                            u'readonly': u'true()',
                            u'calculate': u"concat('uuid:', uuid())"
                        },
                        u'type': u'calculate',
                        u'name': u'instanceID'
                    }
                ]
            }
        ]
        self.assertEqual(
            choice_filter_survey.to_json_dict()[u"children"], expected_dict)


class CsvReaderEquivalencyTest(TestCase):
    def test_equivalency(self):
        equivalent_fixtures = ['group', 'loop',  # 'gps',
                               'specify_other', 'include', 'text_and_integer',
                               'include_json', 'yes_or_no_question']
        for fixture in equivalent_fixtures:
            xls_path = utils.path_to_text_fixture("%s.xls" % fixture)
            csv_path = utils.path_to_text_fixture("%s.csv" % fixture)
            xls_inp = xls_to_dict(xls_path)
            csv_inp = csv_to_dict(csv_path)
            self.maxDiff = None
            self.assertEqual(csv_inp, xls_inp)


class UnicodeCsvTest(TestCase):
    def test_a_unicode_csv_works(self):
        """
        Simply tests that xls2json_backends.csv_to_dict does not have a problem
        with a csv with unicode characters
        """
        utf_csv_path = utils.path_to_text_fixture("utf_csv.csv")
        dict_value = csv_to_dict(utf_csv_path)
        self.assertTrue("\\ud83c" in json.dumps(dict_value))
