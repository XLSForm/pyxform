"""
Testing simple cases for Xls2Json
"""
from unittest import TestCase
from pyxform.xls2json import SurveyReader
from pyxform.builder import create_survey_element_from_dict
from pyxform.tests import utils


class GroupTests(TestCase):

    def test_json(self):
        x = SurveyReader(utils.path_to_text_fixture("group.xls"))
        x_results = x.to_json_dict()
        expected_dict = {
            u'name': u'group',
            u'title': u'group',
            u'id_string': u'group',
            u'sms_keyword': u'group',
            u'default_language': u'default',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'family_name',
                    u'type': u'text',
                    u'label': {u'English': u"What's your family name?"}
                    },
                {
                    u'name': u'father',
                    u'type': u'group',
                    u'label': {u'English': u'Father'},
                    u'children': [
                        {
                            u'name': u'phone_number',
                            u'type': u'phone number',
                            u'label': {
                                u'English':
                                    u"What's your father's phone number?"}
                            },
                        {
                            u'name': u'age',
                            u'type': u'integer',
                            u'label': {u'English': u'How old is your father?'}
                            }
                        ],
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
                ],
            }
        self.maxDiff = None
        self.assertEqual(x_results, expected_dict)

    def test_equality_of_to_dict(self):
        x = SurveyReader(utils.path_to_text_fixture("group.xls"))
        x_results = x.to_json_dict()

        survey = create_survey_element_from_dict(x_results)
        survey_dict = survey.to_json_dict()
        # using the builder sets the title attribute to equal name
        # this won't happen through reading the excel file as done by
        # SurveyReader.
        # Now it happens.
        # del survey_dict[u'title']
        self.maxDiff = None
        self.assertEqual(x_results, survey_dict)
