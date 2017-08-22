import re
import xml.etree.ElementTree as ETree
from pyxform.builder import SurveyElementBuilder, create_survey_from_xls
from pyxform.xls2json import print_pyobj_to_json
from pyxform import Survey, InputQuestion
from pyxform.errors import PyXFormError
from pyxform.tests import utils
import os

FIXTURE_FILETYPE = "xls"


class BuilderTests(utils.XFormTestCase):
    maxDiff = None

#   Moving to spec tests
#    def test_new_widgets(self):
#        survey = utils.build_survey('widgets.xls')
#        path = utils.path_to_text_fixture('widgets.xml')
#        survey.to_xml
#        with open(path) as f:
#            expected = ETree.fromstring(survey.to_xml())
#            result = ETree.fromstring(f.read())
#            self.assertTrue(xml_compare(expected, result))

    def test_unknown_question_type(self):
        survey = utils.build_survey('unknown_question_type.xls',
                                    default_name='unknown_question_type')
        self.assertRaises(
            PyXFormError,
            survey.to_xml
        )

    def test_uniqueness_of_section_names(self):
        # Looking at the xls file, I think this test might be broken.
        survey = utils.build_survey(
            'group_names_must_be_unique.xls',
            default_name='group_names_must_be_unique')
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
        print_pyobj_to_json(self.survey_out_dict,
                            utils.path_to_text_fixture("how_old_are_you.json"))

    def test_create_from_file_object(self):
        path = utils.path_to_text_fixture('yes_or_no_question.xls')
        with open(path, 'rb') as f:
            create_survey_from_xls(f)

    def test_create_from_file_object_noname(self):
        xml_str = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms"
xmlns:ev="http://www.w3.org/2001/xml-events"
xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa"
xmlns:orx="http://openrosa.org/xforms"
xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>data</h:title>
    <model>
      <itext>
        <translation lang="english">
          <text id="/data/good_day:label">
            <value>have you had a good day today?</value>
          </text>
          <text id="/data/good_day/yes:label">
            <value>yes</value>
          </text>
          <text id="/data/good_day/no:label">
            <value>no</value>
          </text>
        </translation>
      </itext>
      <instance>
        <data id="data">
          <good_day/>
          <meta>
            <instanceID/>
          </meta>
        </data>
      </instance>
      <bind nodeset="/data/good_day" type="select1"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/data/meta/instanceID"
      readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <select1 ref="/data/good_day">
      <label ref="jr:itext('/data/good_day:label')"/>
      <item>
        <label ref="jr:itext('/data/good_day/yes:label')"/>
        <value>yes</value>
      </item>
      <item>
        <label ref="jr:itext('/data/good_day/no:label')"/>
        <value>no</value>
      </item>
    </select1>
  </h:body>
</h:html>
        """
        path = utils.path_to_text_fixture('yes_or_no_question.xls')
        with open(path, 'rb') as f:
            survey = create_survey_from_xls(f)
        self.assertXFormEqual(xml_str, survey.to_xml())

    def test_create_from_file_object_withname(self):
        xml_str = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms"
xmlns:ev="http://www.w3.org/2001/xml-events"
xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa"
xmlns:orx="http://openrosa.org/xforms"
xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>fancy-name</h:title>
    <model>
      <itext>
        <translation lang="english">
          <text id="/fancy-name/good_day:label">
            <value>have you had a good day today?</value>
          </text>
          <text id="/fancy-name/good_day/yes:label">
            <value>yes</value>
          </text>
          <text id="/fancy-name/good_day/no:label">
            <value>no</value>
          </text>
        </translation>
      </itext>
      <instance>
        <fancy-name id="fancy-name">
          <good_day/>
          <meta>
            <instanceID/>
          </meta>
        </fancy-name>
      </instance>
      <bind nodeset="/fancy-name/good_day" type="select1"/>
      <bind calculate="concat('uuid:', uuid())"
      nodeset="/fancy-name/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <select1 ref="/fancy-name/good_day">
      <label ref="jr:itext('/fancy-name/good_day:label')"/>
      <item>
        <label ref="jr:itext('/fancy-name/good_day/yes:label')"/>
        <value>yes</value>
      </item>
      <item>
        <label ref="jr:itext('/fancy-name/good_day/no:label')"/>
        <value>no</value>
      </item>
    </select1>
  </h:body>
</h:html>
        """
        path = utils.path_to_text_fixture('yes_or_no_question.xls')
        with open(path, 'rb') as f:
            survey = create_survey_from_xls(f, default_name="fancy-name")
        self.assertXFormEqual(xml_str, survey.to_xml())

    def tearDown(self):
        fixture_path = utils.path_to_text_fixture("how_old_are_you.json")
        if os.path.exists(fixture_path):
            os.remove(fixture_path)

    def test_create_table_from_dict(self):
        d = {
            u"type": u"loop",
            u"name": u"my_loop",
            u"label": {u"English": u"My Loop"},
            u"columns": [
                {
                    u"name": u"col1",
                    u"label": {u"English": u"column 1"},
                },
                {
                    u"name": u"col2",
                    u"label": {u"English": u"column 2"},
                },
            ],
            u"children": [
                {
                    u"type": u"integer",
                    u"name": u"count",
                    u"label": {
                        u"English": u"How many are there in this group?"
                    }
                },
            ]
        }
        builder = SurveyElementBuilder()
        g = builder.create_survey_element_from_dict(d)

        expected_dict = {
            u'name': u'my_loop',
            u'label': {u'English': u'My Loop'},
            u'type': u'group',
            u'children': [
                {
                    u'name': u'col1',
                    u'label': {u'English': u'column 1'},
                    u'type': u'group',
                    u'children': [
                        {
                            u'name': u'count',
                            u'label': {
                                u'English':
                                u'How many are there in this group?'
                            },
                            u'type': u'integer'
                        }
                    ]
                },
                {
                    u'name': u'col2',
                    u'label': {u'English': u'column 2'},
                    u'type': u'group',
                    u'children': [
                        {
                            u'name': u'count',
                            u'label': {
                                u'English':
                                u'How many are there in this group?'
                            },
                            u'type': u'integer'
                        }
                    ]
                }
            ]
        }

        self.assertEqual(g.to_json_dict(), expected_dict)

    def test_specify_other(self):
        survey = utils.create_survey_from_fixture("specify_other",
                                                  filetype=FIXTURE_FILETYPE,
                                                  default_name="specify_other")
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
                    u'children': [
                        # TODO Change to choices (there is stuff in the
                        # json2xform half that will need to change)
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
        testing to make sure that select ones whose choice names are the same
        as the name of the select one get compiled.
        """
        survey = utils.create_survey_from_fixture(
            "choice_name_same_as_select_name",
            filetype=FIXTURE_FILETYPE,
            default_name="choice_name_same_as_select_name")
        expected_dict = {
            u'name': u'choice_name_same_as_select_name',
            u'title': u'choice_name_same_as_select_name',
            u'sms_keyword': u'choice_name_same_as_select_name',
            u'default_language': u'default',
            u'id_string': u'choice_name_same_as_select_name',
            u'type': u'survey',
            u'children': [
                {
                    u'children': [
                        {
                            u'name': u'zone',
                            u'label': u'Zone'
                        }
                    ],
                    u'type': u'select one',
                    u'name': u'zone',
                    u'label': u'Zone',
                },
                {u'children': [
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

    def test_loop(self):
        survey = utils.create_survey_from_fixture(
            "loop",
            filetype=FIXTURE_FILETYPE,
            default_name="loop")
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
                    u'label': {
                        u'english':
                        u'What type of toilets are on the premises?'
                    },
                    u'type': u'select all that apply',
                    u'children': [
                        {
                            u'name': u'pit_latrine_with_slab',
                            u'label': {u'english': u'Pit latrine with slab'}
                        },
                        {
                            u'name': u'open_pit_latrine',
                            u'label': {
                                u'english':
                                u'Pit latrine without slab/open pit'
                            }
                        },
                        {
                            u'name': u'bucket_system',
                            u'label': {u'english': u'Bucket system'}
                        },
                        # Removing this because select alls shouldn't need
                        # an explicit none option
                        # {
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
                    u'bind': {
                        u'relevant':
                        u"selected(../available_toilet_types, 'other')"
                    },
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
                            u'type': u'group',
                            u'children': [
                                {
                                    u'name': u'number',
                                    u'label': {
                                        u'english':
                                        u'How many Pit latrine with slab are'
                                        u' on the premises?'
                                    },
                                    u'type': u'integer'
                                }]},
                        {
                            u'name': u'open_pit_latrine',
                            u'label': {
                                u'english':
                                u'Pit latrine without slab/open pit'
                            },
                            u'type': u'group',
                            u'children': [
                                {
                                    u'name': u'number',
                                    u'label': {
                                        u'english':
                                        u'How many Pit latrine without '
                                        u'slab/open pit are on the premises?'
                                    },
                                    u'type': u'integer'
                                }
                            ]
                        },
                        {
                            u'name': u'bucket_system',
                            u'label': {u'english': u'Bucket system'},
                            u'type': u'group',
                            u'children': [
                                {
                                    u'name': u'number',
                                    u'label': {
                                        u'english':
                                        u'How many Bucket system are on the'
                                        u' premises?'},
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

    def test_sms_columns(self):
        survey = utils.create_survey_from_fixture(
            "sms_info",
            filetype=FIXTURE_FILETYPE,
            default_name="sms_info")
        expected_dict = {
            u'children': [{
                u'children': [
                    {
                        u'label': u'How old are you?',
                        u'name': u'age',
                        u'sms_field': u'q1',
                        u'type': u'integer'
                    },
                    {
                        u'children': [
                            {
                                u'label': u'no',
                                u'name': u'0',
                                u'sms_option': u'n'
                            },
                            {
                                u'label': u'yes',
                                u'name': u'1',
                                u'sms_option': u'y'
                            }],
                        u'label': u'Do you have any children?',
                        u'name': u'has_children',
                        u'sms_field': u'q2',
                        u'type': u'select one'
                    },
                    {
                        u'label': u"What's your birth day?",
                        u'name': u'bday',
                        u'sms_field': u'q3',
                        u'type': u'date'
                    },
                    {
                        u'label': u'What is your name?',
                        u'name': u'name',
                        u'sms_field': u'q4',
                        u'type': u'text'
                    }
                ],
                u'name': u'section1',
                u'sms_field': u'a',
                u'type': u'group'
            },
                {
                    u'children': [
                        {
                            u'label': u'May I take your picture?',
                            u'name': u'picture',
                            u'type': u'photo'
                        },
                        {
                            u'label':
                            u'Record your GPS coordinates.',
                            u'name': u'gps',
                            u'type': u'geopoint'
                        }
                    ],
                    u'name': u'medias',
                    u'sms_field': u'c',
                    u'type': u'group'
            },
                {
                    u'children': [
                        {
                            u'children': [{
                                u'label': u'Mozilla Firefox',
                                u'name': u'firefox',
                                u'sms_option': u'ff'
                            },
                                {
                                    u'label': u'Google Chrome',
                                    u'name': u'chrome',
                                    u'sms_option': u'gc'
                            },
                                {
                                    u'label':
                                    u'Internet Explorer',
                                    u'name': u'ie',
                                    u'sms_option': u'ie'
                            },
                                {
                                    u'label': u'Safari',
                                    u'name': u'safari',
                                    u'sms_option': u'saf'
                            }
                            ],
                            u'label':
                            u'What web browsers do you use?',
                            u'name': u'web_browsers',
                            u'sms_field': u'q5',
                            u'type': u'select all that apply'
                        }
                    ],
                    u'name': u'browsers',
                    u'sms_field': u'b',
                    u'type': u'group'
            }, {
                    u'children': [{
                        u'label': u'Phone Number',
                        u'name': u'phone',
                        u'type': u'phonenumber'
                    }, {
                        u'label': u'Start DT',
                        u'name': u'start',
                        u'type': u'start'
                    }, {
                        u'label': u'End DT',
                        u'name': u'end',
                        u'type': u'end'
                    }, {
                        u'label': u'Send Day',
                        u'name': u'today',
                        u'type': u'today'
                    }, {
                        u'label': u'IMEI',
                        u'name': u'imei',
                        u'type': u'deviceid'
                    }, {
                        u'label': u'Hey!',
                        u'name': u'nope',
                        u'type': u'note'
                    }],
                    u'name': u'metadata',
                    u'sms_field': u'meta',
                    u'type': u'group'
            },
                {
                    u'children': [{
                        u'bind': {
                            'calculate': "concat('uuid:', uuid())",
                            'readonly': 'true()'
                        },
                        u'name': 'instanceID',
                        u'type': 'calculate'
                    }],
                    u'control': {'bodyless': True},
                    u'name': 'meta',
                    u'type': u'group'
            }],
            u'default_language': u'default',
            u'id_string': u'sms_info_form',
            u'name': u'sms_info',
            u'sms_allow_media': u'TRUE',
            u'sms_date_format': u'%Y-%m-%d',
            u'sms_datetime_format': u'%Y-%m-%d-%H:%M',
            u'sms_keyword': u'inf',
            u'sms_separator': u'+',
            u'title': u'SMS Example',
            u'type': u'survey'
        }
        self.assertEqual(survey.to_json_dict(), expected_dict)

    def test_style_column(self):
        survey = utils.create_survey_from_fixture(
            "style_settings",
            filetype=FIXTURE_FILETYPE,
            default_name="style_settings")
        expected_dict = {
            u'children': [
                {
                    u'label': {u'english': u'What is your name?'},
                    u'name': u'your_name',
                    u'type': u'text'
                },
                {
                    u'label': {u'english': u'How many years old are you?'},
                    u'name': u'your_age',
                    u'type': u'integer'
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
                    u'control': {'bodyless': True},
                    u'name': 'meta',
                    u'type': u'group'
                }
            ],
            u'default_language': u'default',
            u'id_string': u'new_id',
            u'name': u'style_settings',
            u'sms_keyword': u'new_id',
            u'style': u'ltr',
            u'title': u'My Survey',
            u'type': u'survey',
        }
        self.assertEqual(survey.to_json_dict(), expected_dict)

    STRIP_NS_FROM_TAG_RE = re.compile(r'\{.+\}')

    def test_style_not_added_to_body_if_not_present(self):
        survey = utils.create_survey_from_fixture(
            "settings",
            filetype=FIXTURE_FILETYPE,
            default_name="settings")
        xml = survey.to_xml()
        # find the body tag
        root_elm = ETree.fromstring(xml.encode('utf-8'))
        body_elms = list(filter(
            lambda e: self.STRIP_NS_FROM_TAG_RE.sub('', e.tag) == 'body',
            [c for c in root_elm.getchildren()]))
        self.assertEqual(len(body_elms), 1)
        self.assertIsNone(body_elms[0].get('class'))

    def test_style_added_to_body_if_present(self):
        survey = utils.create_survey_from_fixture(
            "style_settings",
            filetype=FIXTURE_FILETYPE,
            default_name="style_settings")
        xml = survey.to_xml()
        # find the body tag
        root_elm = ETree.fromstring(xml.encode('utf-8'))
        body_elms = list(filter(
            lambda e: self.STRIP_NS_FROM_TAG_RE.sub('', e.tag) == 'body',
            [c for c in root_elm.getchildren()]))
        self.assertEqual(len(body_elms), 1)
        self.assertEqual(body_elms[0].get('class'), 'ltr')
