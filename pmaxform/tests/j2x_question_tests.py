"""
Testing creation of Surveys using verbose methods
"""
from unittest import TestCase
from pyxform import *
from pyxform.question import Question
from pyxform.builder import create_survey_element_from_dict

import json

from pyxform.utils import node

TESTING_BINDINGS = True

def ctw(control):
    """
    ctw stands for control_test_wrap, but ctw is shorter and easier. using begin_str and end_str to
    take out the wrap that lxml gives us
    """
    return control.toxml()

class Json2XformQuestionValidationTests(TestCase):
    maxDiff = None
    def setUp(self):
        self.s = Survey(name=u"test")
    
    def test_question_type_string(self):
        simple_string_json = {
            u"label": {
                u"French": u"Nom du travailleur agricole:",
                u"English": u"Name of Community Agricultural Worker"
                },
            u"type": u"text",
            u"name": u"enumerator_name"
        }

        q = create_survey_element_from_dict(simple_string_json)
        
        expected_string_control_xml = u"""<input ref="/test/enumerator_name"><label ref="jr:itext('/test/enumerator_name:label')"/></input>"""
        
        expected_string_binding_xml = u"""
        <bind nodeset="/test/enumerator_name" type="string"/>
        """.strip()
        
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_string_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_string_binding_xml)
    
    def test_select_one_question_multilingual(self):
        """
        Test the lowest common denominator of question types.
        """
        simple_select_one_json = {
            u"label" : {u"f": u"ftext",u"e": u"etext"},
            u"type" : u"select one",
            u"name" : u"qname",
            u"choices" : [
                {u"label": {u"f": u"fa",u"e": u"ea"},u"name": u"a"},
                {u"label": {u"f": u"fb",u"e": u"eb"},u"name": u"b"}
                ]
            }
        
        # I copied the response in, since this is not our method of testing
        # valid return values.
        expected_select_one_control_xml = u"""<select1 ref="/test/qname"><label ref="jr:itext('/test/qname:label')"/><item><label ref="jr:itext('/test/qname/a:label')"/><value>a</value></item><item><label ref="jr:itext('/test/qname/b:label')"/><value>b</value></item></select1>"""
        
        expected_select_one_binding_xml = u"""
        <bind nodeset="/test/qname" type="select1"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_select_one_json)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_one_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_select_one_binding_xml)

    def test_simple_integer_question_type_multilingual(self):
        """
        not sure how integer questions should show up.
        """
        simple_integer_question = {
            u"label": {u"f": u"fc", u"e": u"ec"},
            u"type": u"integer",
            u"name": u"integer_q",
            u"attributes": {}
            }

        expected_integer_control_xml = u"""
        <input ref="/test/integer_q"><label ref="jr:itext('/test/integer_q:label')"/></input>
        """.strip()
        
        expected_integer_binding_xml = u"""
        <bind nodeset="/test/integer_q" type="int"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_integer_question)
        
        self.s.add_child(q)
        
        self.assertEqual(ctw(q.xml_control()), expected_integer_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_integer_binding_xml)


    def test_simple_date_question_type_multilingual(self):
        """
        not sure how date questions should show up.
        """
        simple_date_question = {u"label": {u"f": u"fd", u"e": u"ed"}, u"type": u"date", u"name": u"date_q", u"attributes": {}}
        
        expected_date_control_xml = u"""
        <input ref="/test/date_q"><label ref="jr:itext('/test/date_q:label')"/></input>
        """.strip()
        
        expected_date_binding_xml = u"""
        <bind nodeset="/test/date_q" type="date"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_date_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_date_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_date_binding_xml)
    
    def test_simple_phone_number_question_type_multilingual(self):
        """
        not sure how phone number questions should show up.
        """
        simple_phone_number_question = {
            u"label": {u"f": u"fe", u"e": u"ee"},
            u"type": u"phone number",
            u"name": u"phone_number_q",
            }

        expected_phone_number_control_xml = u"""<input ref="/test/phone_number_q"><label ref="jr:itext('/test/phone_number_q:label')"/><hint>Enter numbers only.</hint></input>"""

        expected_phone_number_binding_xml = u"""
        <bind constraint="regex(., '^\d*$')" nodeset="/test/phone_number_q" type="string"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_phone_number_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_phone_number_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_phone_number_binding_xml)

    def test_simple_select_all_question_multilingual(self):
        """
        not sure how select all questions should show up...
        """
        simple_select_all_question = {
            u"label": {u"f": u"f choisit", u"e": u"e choose"},
            u"type": u"select all that apply",
            u"name": u"select_all_q",
            u"choices": [
                {u"label": {u"f": u"ff", u"e": u"ef"}, u"name": u"f"},
                {u"label": {u"f": u"fg", u"e": u"eg"}, u"name": u"g"},
                {u"label": {u"f": u"fh", u"e": u"eh"}, u"name": u"h"}
                ]
            }

        expected_select_all_control_xml = u"""<select ref="/test/select_all_q"><label ref="jr:itext('/test/select_all_q:label')"/><item><label ref="jr:itext('/test/select_all_q/f:label')"/><value>f</value></item><item><label ref="jr:itext('/test/select_all_q/g:label')"/><value>g</value></item><item><label ref="jr:itext('/test/select_all_q/h:label')"/><value>h</value></item></select>"""
        
        expected_select_all_binding_xml = u"""
<bind nodeset="/test/select_all_q" type="select"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_select_all_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_all_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_select_all_binding_xml)

    def test_simple_decimal_question_multilingual(self):
        """
        not sure how decimal should show up.
        """
        simple_decimal_question = {u"label": {u"f": u"f text", u"e": u"e text"}, u"type": u"decimal", u"name": u"decimal_q", u"attributes": {}}

        expected_decimal_control_xml = u"""
        <input ref="/test/decimal_q"><label ref="jr:itext('/test/decimal_q:label')"/></input>
        """.strip()
        
        expected_decimal_binding_xml = u"""
        <bind nodeset="/test/decimal_q" type="decimal"/>
        """.strip()
        
        q = create_survey_element_from_dict(simple_decimal_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_decimal_control_xml)
        
        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_decimal_binding_xml)
