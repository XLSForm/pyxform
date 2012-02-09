"""
Testing simple cases for Xls2Json
"""
from unittest import TestCase
from pyxform.xls2json import SurveyReader
import utils
import os

#Nothing calls this AFAICT
def absolute_path(f, file_name):
    directory = os.path.dirname(f)
    return os.path.join(directory, file_name)


class BasicXls2JsonApiTests(TestCase):

    def test_simple_yes_or_no_question(self):
        x = SurveyReader(utils.path_to_text_fixture("yes_or_no_question.xls"))
        x_results = x.to_json_dict()

        expected_dict = [
            {
                u'label': {u'english': u'have you had a good day today?'},
                u'type': u'select one',
                u'name': u'good_day',
                u'choices': [
                    {
                        u'label': {u'english': u'yes'},
                        u'name': u'yes'
                        },
                    {
                        u'label': {u'english': u'no'},
                        u'name': u'no'
                        }
                    ]
                }
            ]
        self.assertEqual(x_results[u"children"], expected_dict)

    def test_gps(self):
        x = SurveyReader(utils.path_to_text_fixture("gps.xls"))

        expected_dict = [{u'type': u'gps', u'name': u'location', u'label': u'GPS'}]

        self.assertEqual(x.to_json_dict()[u"children"], expected_dict)

    def test_text_and_integer(self):
        x = SurveyReader(utils.path_to_text_fixture("text_and_integer.xls"))

        expected_dict = [{u'text': {u'english': u'What is your name?'}, u'type': u'text', u'name': u'your_name'}, {u'text': {u'english': u'How many years old are you?'}, u'type': u'integer', u'name': u'your_age'}]

        self.assertEqual(x.to_json_dict()[u"children"], expected_dict)

    def test_table(self):
        x = SurveyReader(utils.path_to_text_fixture("simple_loop.xls"))

        expected_dict = {
            u'type': u'survey',
            u'name': u'simple_loop',
            u'id_string': u'simple_loop',
            u'default_language': u'default',
            u'title': u'simple_loop',
            u'children': [
                {
                    u'children': [
                        {
                            u'type': u'integer',
                            u'name': u'count',
                            u'label': {u'English': u'How many are there in this group?'}
                            }
                        ],
                    u'type': u'loop',
                    u'name': u'my_table',
                    u'columns': [
                        {
                            u'name': u'col1',
                            u'label': {u'English': u'Column 1'}
                            },
                        {
                            u'name': u'col2',
                            u'label': {u'English': u'Column 2'}
                            }
                        ],
                    u'label': {u'English': u'My Table'}
                    }]}
        self.maxDiff = None
        self.assertEqual(x.to_json_dict(), expected_dict)

    def test_xlsx_fails(self):
        def load_xlsx_file():
            x = SurveyReader(utils.path_to_text_fixture("text_and_integer_xlsx.xlsx"))
        self.assertRaises(Exception, load_xlsx_file)

from pyxform.xls2json_backends import xls_to_dict, csv_to_dict

class CsvReaderEquivalencyTest(TestCase):
    def test_equivalency(self):
        equivalent_fixtures = ['group', 'loop',  #'gps',
                'specify_other', 'include', 'text_and_integer', \
                'include_json', 'yes_or_no_question']
        for fixture in equivalent_fixtures:
            xls_path = utils.path_to_text_fixture("%s.xls" % fixture)
            csv_path = utils.path_to_text_fixture("%s.csv" % fixture)
            xls_inp = xls_to_dict(xls_path)
            csv_inp = csv_to_dict(csv_path)
            self.maxDiff = None
            self.assertEqual(csv_inp, xls_inp)
