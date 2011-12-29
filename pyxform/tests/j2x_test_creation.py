"""
Testing creation of Surveys using verbose methods
"""
from unittest import TestCase
from pyxform import *

import json


class Json2XformVerboseSurveyCreationTests(TestCase):

    def test_survey_can_be_created_in_a_verbose_manner(self):
        s = Survey()
        s.name = "simple_survey"

        q = MultipleChoiceQuestion()
        q.name = "cow_color"
        q.type = "select one"

        q.add_choice(label="Green", name="green")
        s.add_child(q)

        expected_dict = {
            u'name': 'simple_survey',
            u'children': [
                {
                    u'name': 'cow_color',
                    u'type' : 'select one',
                    u'children': [
                        {
                            u'label': 'Green',
                            u'name': 'green',
                            }
                        ],
                    }
                ],
            }
        self.maxDiff = None
        self.assertEqual(s.to_json_dict(), expected_dict)
    
    def test_survey_can_be_created_in_a_slightly_less_verbose_manner(self):
        option_dict_array = [
            {'name': 'red', 'label':'Red'},
            {'name': 'blue', 'label': 'Blue'}
            ]
        
        q = MultipleChoiceQuestion(name="Favorite_Color", choices=option_dict_array)
        q.type = u"select one"
        s = Survey(name="Roses_are_Red", children=[q])

        expected_dict = {
            u'name': 'Roses_are_Red',
            u'children': [
                {
                    u'name': 'Favorite_Color',
                    u'type' : u'select one',
                    u'children': [
                        {u'label': 'Red', u'name': 'red'},
                        {u'label': 'Blue', u'name': 'blue'}
                        ],
                    }
                ],
            }

        self.assertEqual(s.to_json_dict(), expected_dict)
    
    def test_two_options_cannot_have_the_same_value(self):
        q = MultipleChoiceQuestion(name="Favorite Color")
        q.add_choice(name="grey", label="Gray")
        q.add_choice(name="grey", label="Grey")
        self.assertRaises(Exception, q, 'validate')
    
    def test_one_section_cannot_have_two_conflicting_slugs(self):
        q1 = InputQuestion(name="YourName")
        q2 = InputQuestion(name="YourName")
        s = Survey(name="Roses are Red", children=[q1, q2])
        self.assertRaises(Exception, s, 'validate')
