from django.test import TestCase, Client
from pyxform.builder import create_survey_element_from_dict
from pyxform.xls2json import ExcelReader

class BuilderTests(TestCase):
    
    def test_create_table_from_dict(self):
        d = {
            u"type" : u"table",
            u"name" : u"my_table",
            u"label" : {u"English" : u"My Table"},
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
        g = create_survey_element_from_dict(d)

        expected_dict = {
            u'name': u'my_table',
            u'label': {u'English': u'My Table'},
            u'children': [
                {
                    u'name': u'col1',
                    u'label': {u'English': u'column 1'},
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

        self.assertEqual(g.to_dict(), expected_dict)

    def test_specify_other(self):
        excel_reader = ExcelReader("pyxform/tests/specify_other.xls")
        d = excel_reader.to_dict()
        survey = create_survey_element_from_dict(d)
        expected_dict = {
            u'name': 'specify_other',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'sex',
                    u'label': {u'English': u'What sex are you?'},
                    u'type': u'select one',
                    u'children': [
                        {
                            u'name': u'male',
                            u'value': u'male',
                            u'label': {u'English': u'Male'}
                            },
                        {
                            u'name': u'female',
                            u'value': u'female',
                            u'label': {u'English': u'Female'}
                            },
                        {
                            u'name': u'other',
                            u'value': u'other',
                            u'label': {u'English': u'Other'}
                            }
                        ]
                    },
                {
                    u'name': u'sex_other',
                    u'bind': {u'relevant': u"selected(../sex, 'other')"},
                    u'label': {u'English': u'What sex are you?'},
                    u'type': u'text'}
                ]
            }
        self.assertEqual(survey.to_dict(), expected_dict)

    def test_include(self):
        excel_reader = ExcelReader("pyxform/tests/include.xls")
        d = excel_reader.to_dict()
        survey = create_survey_element_from_dict(d)
        expected_dict = {
            u'name': 'include',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'name',
                    u'label': {u'English': u"What's your name?"},
                    u'type': u'text'
                    },
                    {
                        u'name': u'good_day',
                        u'label': {u'english': u'have you had a good day today?'},
                        u'type': u'select one',
                        u'children': [
                            {
                                u'name': u'yes',
                                u'value': u'yes',
                                u'label': {u'english': u'yes'}
                                },
                            {
                                u'name': u'no',
                                u'value': u'no',
                                u'label': {u'english': u'no'}
                                }
                            ]}]}

        self.assertEqual(survey.to_dict(), expected_dict)

    def test_loop(self):
        excel_reader = ExcelReader("pyxform/tests/loop.xls")
        d = excel_reader.to_dict()
        survey = create_survey_element_from_dict(d)

        expected_dict = {
            u'name': 'loop',
            u'type': u'survey',
            u'children': [
                {
                    u'name': u'available_toilet_types',
                    u'label': {u'english': u'What type of toilets are on the premises?'},
                    u'type': u'select all that apply',
                    u'children': [
                        {u'name': u'pit_latrine_with_slab', u'value': u'pit_latrine_with_slab', u'label': {u'english': u'Pit latrine with slab'}},
                        {u'name': u'open_pit_latrine', u'value': u'open_pit_latrine', u'label': {u'english': u'Pit latrine without slab/open pit'}},
                        {u'name': u'bucket_system', u'value': u'bucket_system', u'label': {u'english': u'Bucket system'}},
                        {u'name': u'other', u'value': u'other', u'label': {u'english': u'Other'}}
                        ]
                    },
                {
                    u'name': u'available_toilet_types_other',
                    u'bind': {u'relevant': u"selected(../available_toilet_types, 'other')"},
                    u'label': {u'english': u'What type of toilets are on the premises?'},
                    u'type': u'text'
                    },
                {
                    u'name': u'number_of_pit_latrine_with_slab',
                    u'label': {u'english': u'How many Pit latrine with slab are on the premises?'},
                    u'type': u'integer'
                    },
                {
                    u'name': u'number_of_open_pit_latrine',
                    u'label': {u'english': u'How many Pit latrine without slab/open pit are on the premises?'},
                    u'type': u'integer'
                    },
                {
                    u'name': u'number_of_bucket_system',
                    u'label': {u'english': u'How many Bucket system are on the premises?'},
                    u'type': u'integer'
                    },
                {
                    u'name': u'number_of_other',
                    u'label': {u'english': u'How many Other are on the premises?'},
                    u'type': u'integer'
                    }]}

        self.assertEqual(survey.to_dict(), expected_dict)
