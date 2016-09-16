from unittest import TestCase
from pyxform.builder import create_survey_from_xls
from pyxform.tests import utils


class LoopTests(TestCase):
    def test_loop(self):
        path = utils.path_to_text_fixture('another_loop.xls')
        survey = create_survey_from_xls(path)
        self.maxDiff = None
        expected_dict = {
            u'name': u'another_loop',
            u'id_string': u'another_loop',
            u'sms_keyword': u'another_loop',
            u'default_language': u'default',
            u'title': u'another_loop',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'loop_vehicle_types',
                    u'type': u'group',
                    u'children': [
                        {
                            u'label': {u'English': u'Car',
                                       u'French': u'Voiture'},
                            u'name': u'car',
                            u'type': u'group',
                            u'children': [
                                {
                                    u'label': {
                                        u'English': u'How many do you have?',
                                        u'French': u'Combien avoir?'
                                    },
                                    u'name': u'total',
                                    u'type': u'integer'
                                },
                                {
                                    u'bind': {u'constraint': u'. <= ../total'},
                                    u'label': {
                                        u'English': u'How many are working?',
                                        u'French': u'Combien marcher?'
                                    },
                                    u'name': u'working',
                                    u'type': u'integer'
                                }
                            ],
                        },
                        {
                            u'label': {u'English': u'Motorcycle',
                                       u'French': u'Moto'},
                            u'name': u'motor_cycle',
                            u'type': u'group',
                            u'children': [
                                {
                                    u'label': {
                                        u'English': u'How many do you have?',
                                        u'French': u'Combien avoir?'
                                    },
                                    u'name': u'total',
                                    u'type': u'integer'
                                },
                                {
                                    u'bind': {u'constraint': u'. <= ../total'},
                                    u'label': {
                                        u'English': u'How many are working?',
                                        u'French': u'Combien marcher?'
                                    },
                                    u'name': u'working',
                                    u'type': u'integer'
                                }
                            ],
                        }]},
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
        self.assertEquals(survey.to_json_dict(), expected_dict)
