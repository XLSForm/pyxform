from lxml import etree
from formencode.doctest_xml_compare import xml_compare
from unittest import TestCase
from pyxform.builder import SurveyElementBuilder, create_survey_from_xls
from pyxform.xls2json import print_pyobj_to_json
from pyxform import Survey, InputQuestion
from pyxform.errors import PyXFormError
import utils
import os

FIXTURE_FILETYPE = "xls"

class BuilderTests(TestCase):
    maxDiff = None

#   Moving to spec tests
#    def test_new_widgets(self):
#        survey = utils.build_survey('widgets.xls')
#        path = utils.path_to_text_fixture('widgets.xml')
#        survey.to_xml
#        with open(path) as f:
#            expected = etree.fromstring(survey.to_xml())
#            result = etree.fromstring(f.read())
#            self.assertTrue(xml_compare(expected, result))

    def test_unknown_question_type(self):
        survey = utils.build_survey('unknown_question_type.xls')
        self.assertRaises(
            PyXFormError,
            survey.to_xml
            )

    def test_uniqueness_of_section_names(self):
        #Looking at the xls file, I think this test might be broken.
        survey = utils.build_survey('group_names_must_be_unique.xls')
        self.assertRaises(
            Exception,
            survey.to_xml
            )

    def setUp(self):
        self.this_directory = os.path.dirname(__file__)
        survey_out = Survey(
            name=u"age",
            sms_keyword=u"age",
            type=u"survey"
            )
        question = InputQuestion(name=u"age")
        question.type = u"integer"
        question.label = u"How old are you?"
        survey_out.add_child(question)
        self.survey_out_dict = survey_out.to_json_dict()
        print_pyobj_to_json(self.survey_out_dict, utils.path_to_text_fixture("how_old_are_you.json"))

    def test_create_from_file_object(self):
        path = utils.path_to_text_fixture('yes_or_no_question.xls')
        with open(path) as f:
            s = create_survey_from_xls(f)

    def tearDown(self):
        import os
        os.remove(utils.path_to_text_fixture("how_old_are_you.json"))

    def test_create_table_from_dict(self):
        d = {
            u"type" : u"loop",
            u"name" : u"my_loop",
            u"label" : {u"English" : u"My Loop"},
            u"columns" : [
                {
                    u"name" : u"col1",
                    u"label" : {u"English" : u"column 1"},
                    },
                {
                    u"name" : u"col2",
                    u"label" : {u"English" : u"column 2"},
                    },
                ],
            u"children" : [
                {
                    u"type": u"integer",
                    u"name": u"count",
                    u"label": {u"English": u"How many are there in this group?"}
                    },
                ]
            }
        builder = SurveyElementBuilder()
        g = builder.create_survey_element_from_dict(d)

        expected_dict = {
            u'name': u'my_loop',
            u'label': {u'English': u'My Loop'},
            u'type' : u'group',
            u'children': [
                {
                    u'name': u'col1',
                    u'label': {u'English': u'column 1'},
                    u'type' : u'group',
                    u'children': [
                        {
                            u'name': u'count',
                            u'label': {u'English': u'How many are there in this group?'},
                            u'type': u'integer'
                            }
                        ]
                    },
                {
                    u'name': u'col2',
                    u'label': {u'English': u'column 2'},
                    u'type' : u'group',
                    u'children': [
                        {
                            u'name': u'count',
                            u'label': {u'English': u'How many are there in this group?'},
                            u'type': u'integer'
                            }
                        ]
                    }
                ]
            }

        self.assertEqual(g.to_json_dict(), expected_dict)

    def test_specify_other(self):
        survey = utils.create_survey_from_fixture("specify_other", filetype=FIXTURE_FILETYPE)
        expected_dict = {
            u'name': u'specify_other',
            u'type': u'survey',
            u'title': u'specify_other',
            u'default_language': u'default',
            u'id_string': u'specify_other',
            u'sms_keyword': u'specify_other',
            u'children': [
                {
                    u'name': u'sex',
                    u'label': {u'English': u'What sex are you?'},
                    u'type': u'select one',
                    u'children': [ #TODO Change to choices (there is stuff in the json2xform half that will need to change)
                        {
                            u'name': u'male',
                            u'label': {u'English': u'Male'}
                            },
                        {
                            u'name': u'female',
                            u'label': {u'English': u'Female'}
                            },
                        {
                            u'name': u'other',
                            u'label': u'Other'
                            }
                        ]
                    },
                {
                    u'name': u'sex_other',
                    u'bind': {u'relevant': u"selected(../sex, 'other')"},
                    u'label': u'Specify other.',
                    u'type': u'text'},
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
            }
        self.maxDiff = None
        self.assertEqual(survey.to_json_dict(), expected_dict)

    def test_select_one_question_with_identical_choice_name(self):
        """
        testing to make sure that select ones whose choice names are the same as
        the name of the select one get compiled.
        """
        survey = utils.create_survey_from_fixture("choice_name_same_as_select_name", filetype=FIXTURE_FILETYPE)
        expected_dict = {
                u'name': u'choice_name_same_as_select_name',
                u'title': u'choice_name_same_as_select_name',
                u'sms_keyword': u'choice_name_same_as_select_name',
                u'default_language': u'default',
                u'id_string': u'choice_name_same_as_select_name',
                u'type': u'survey',
                u'children':  [
                {
                       u'children':  [
                        {
                               u'name': u'zone',
                               u'label': u'Zone'
                        }
                        ],
                               u'type': u'select one',
                               u'name': u'zone',
                               u'label': u'Zone',
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
        }
        self.maxDiff = None
        self.assertEqual(survey.to_json_dict(), expected_dict)

#    def test_include(self):
#        survey = utils.create_survey_from_fixture(u"include", filetype=FIXTURE_FILETYPE,
#                                                  include_directory=True)
#        expected_dict = {
#            u'name': u'include',
#            u'title': u'include',
#            u'id_string': u'include',
#            u'default_language': u'default',
#            u'type': u'survey',
#            u'children': [
#                {
#                    u'name': u'name',
#                    u'label': {u'English': u"What's your name?"},
#                    u'type': u'text'
#                    },
#                    {
#                        u'name': u'good_day',
#                        u'label': {u'English': u'have you had a good day today?'},
#                        u'type': u'select one',
#                        u'children': [
#                            {
#                                u'name': u'yes',
#                                u'label': {u'English': u'yes'}
#                                },
#                            {
#                                u'name': u'no',
#                                u'label': {u'English': u'no'}
#                                }
#                            ]}]}
#
#        self.assertEqual(survey.to_json_dict(), expected_dict)
#
#    def test_include_json(self):
#        survey_in = utils.create_survey_from_fixture(
#            u"include_json",
#            filetype=FIXTURE_FILETYPE,
#            include_directory=True
#            )
#        expected_dict = {
#            u'name': u'include_json',
#            u'title': u'include_json',
#            u'default_language': u'default',
#            u'id_string': u'include_json',
#            u'type': u'survey',
#            u'children': [
#                {
#                    u'label': u'How old are you?',
#                    u'name': u'age',
#                    u'type': u'integer'
#                },
#                {
#                    u'children': [
#                        {
#                            u'bind': {
#                                'calculate': "concat('uuid:', uuid())",
#                                'readonly': 'true()'
#                            },
#                            u'name': 'instanceID',
#                            u'type': 'calculate'
#                        }
#                    ],
#                    u'control': {
#                        'bodyless': True
#                    },
#                    u'name': 'meta',
#                    u'type': u'group'
#                }
#            ],
#            }
#        self.assertEquals(survey_in.to_json_dict(), expected_dict)

    def test_loop(self):
        survey = utils.create_survey_from_fixture("loop", filetype=FIXTURE_FILETYPE)
        expected_dict = {
            u'name': u'loop',
            u'id_string': u'loop',
            u'sms_keyword': u'loop',
            u'title': u'loop',
            u'type': u'survey',
            u'default_language': u'default',
            u'children': [
                {
                    u'name': u'available_toilet_types',
                    u'label': {u'english': u'What type of toilets are on the premises?'},
                    u'type': u'select all that apply',
                    #u'bind': {u'constraint': u"(.='none' or not(selected(., 'none')))"},
                    u'children': [
                        {
                            u'name': u'pit_latrine_with_slab',
                            u'label': {u'english': u'Pit latrine with slab'}
                            },
                        {
                            u'name': u'open_pit_latrine',
                            u'label': {u'english': u'Pit latrine without slab/open pit'}
                            },
                        {
                            u'name': u'bucket_system',
                            u'label': {u'english': u'Bucket system'}
                            },
                        #Removing this because select alls shouldn't need an explicit none option
                        #{
                        #    u'name': u'none',
                        #    u'label': u'None',
                        #    },
                        {
                            u'name': u'other',
                            u'label': u'Other'
                            },
                        ]
                    },

                {
                    u'name': u'available_toilet_types_other',
                    u'bind': {u'relevant': u"selected(../available_toilet_types, 'other')"},
                    u'label': u'Specify other.',
                    u'type': u'text'
                    },
                {
                    u'name': u'loop_toilet_types',
                    u'type': u'group',
                    u'children': [
                        {
                            u'name': u'pit_latrine_with_slab',
                            u'label': {u'english': u'Pit latrine with slab'},
                            u'type' : u'group',
                            u'children': [
                                {
                                    u'name': u'number',
                                    u'label': {u'english': u'How many Pit latrine with slab are on the premises?'},
                                    u'type': u'integer'
                                }]},
                        {
                            u'name': u'open_pit_latrine',
                            u'label': {u'english': u'Pit latrine without slab/open pit'},
                            u'type' : u'group',
                            u'children': [
                                {
                                    u'name': u'number',
                                    u'label': {u'english': u'How many Pit latrine without slab/open pit are on the premises?'},
                                    u'type': u'integer'
                                    }
                                ]
                        },
                        {
                            u'name': u'bucket_system',
                            u'label': {u'english': u'Bucket system'},
                            u'type' : u'group',
                            u'children': [
                                {
                                    u'name': u'number',
                                    u'label': {u'english': u'How many Bucket system are on the premises?'},
                                    u'type': u'integer'
                                    }
                                ]
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
                }]}
        self.maxDiff = None
        self.assertEqual(survey.to_json_dict(), expected_dict)

    def test_cascading_selects(self):
        # TODO: remove this test, it is no longer equivalent structure wise
        '''
        survey_cs = utils.create_survey_from_fixture("cascading_select_test", filetype=FIXTURE_FILETYPE)
        survey_eq = utils.create_survey_from_fixture("cascading_select_test_equivalent", filetype=FIXTURE_FILETYPE)
        self.assertEqual(survey_cs.to_json_dict(), survey_eq.to_json_dict())'''
        pass

    def test_sms_columns(self):
        survey = utils.create_survey_from_fixture("sms_info", filetype=FIXTURE_FILETYPE)
        expected_dict = {u'children': [{u'children': [{u'label': u'How old are you?',
                                       u'name': u'age',
                                       u'sms_id': u'q1',
                                       u'type': u'integer'},
                                      {u'children': [{u'label': u'no',
                                                      u'name': u'0',
                                                      u'sms_id': u'n'},
                                                     {u'label': u'yes',
                                                      u'name': u'1',
                                                      u'sms_id': u'y'}],
                                       u'label': u'Do you have any children?',
                                       u'name': u'has_children',
                                       u'sms_id': u'q2',
                                       u'type': u'select one'},
                                      {u'label': u"What's your birth day?",
                                       u'name': u'bday',
                                       u'sms_id': u'q3',
                                       u'type': u'date'},
                                      {u'label': u'What is your name?',
                                       u'name': u'name',
                                       u'sms_id': u'q4',
                                       u'type': u'text'}],
                        u'name': u'section1',
                        u'sms_id': u'a',
                        u'type': u'group'},
                       {u'children': [{u'label': u'May I take your picture?',
                                       u'name': u'picture',
                                       u'type': u'photo'},
                                      {u'label': u'Record your GPS coordinates.',
                                       u'name': u'gps',
                                       u'type': u'geopoint'}],
                        u'name': u'medias',
                        u'sms_id': u'c',
                        u'type': u'group'},
                       {u'children': [{u'children': [{u'label': u'Mozilla Firefox',
                                                      u'name': u'firefox',
                                                      u'sms_id': u'ff'},
                                                     {u'label': u'Google Chrome',
                                                      u'name': u'chrome',
                                                      u'sms_id': u'gc'},
                                                     {u'label': u'Internet Explorer',
                                                      u'name': u'ie',
                                                      u'sms_id': u'ie'},
                                                     {u'label': u'Safari',
                                                      u'name': u'safari',
                                                      u'sms_id': u'saf'}],
                                       u'label': u'What web browsers do you use?',
                                       u'name': u'web_browsers',
                                       u'sms_id': u'q5',
                                       u'type': u'select all that apply'}],
                        u'name': u'browsers',
                        u'sms_id': u'b',
                        u'type': u'group'},
                       {u'children': [{u'label': u'Phone Number',
                                       u'name': u'phone',
                                       u'type': u'phonenumber'},
                                      {u'label': u'Start DT',
                                       u'name': u'start',
                                       u'type': u'start'},
                                      {u'label': u'End DT',
                                       u'name': u'end',
                                       u'type': u'end'},
                                      {u'label': u'Send Day',
                                       u'name': u'today',
                                       u'type': u'today'},
                                      {u'label': u'IMEI',
                                       u'name': u'imei',
                                       u'type': u'deviceid'},
                                      {u'label': u'Hey!',
                                       u'name': u'nope',
                                       u'type': u'note'}],
                        u'name': u'metadata',
                        u'sms_id': u'meta',
                        u'type': u'group'},
                       {u'children': [{u'bind': {'calculate': "concat('uuid:', uuid())",
                                                 'readonly': 'true()'},
                                       u'name': 'instanceID',
                                       u'type': 'calculate'}],
                        u'control': {'bodyless': True},
                        u'name': 'meta',
                        u'type': u'group'}],
         u'default_language': u'default',
         u'id_string': u'sms_info_form',
         u'name': u'sms_info',
         u'sms_allow_medias': u'TRUE',
         u'sms_date_format': u'%Y-%m-%d',
         u'sms_datetime_format': u'%Y-%m-%d-%H:%M',
         u'sms_keyword': u'inf',
         u'sms_separator': u'+',
         u'title': u'SMS Example',
         u'type': u'survey'}
        self.assertEqual(survey.to_json_dict(), expected_dict)
