"""
Testing creation of Surveys using verbose methods
"""
from unittest import TestCase

from pyxform import *
from pyxform.builder import create_survey_element_from_dict
from pyxform.tests.utils import prep_class_config

TESTING_BINDINGS = True


def ctw(control):
    """
    ctw stands for control_test_wrap, but ctw is shorter and easier. using
    begin_str and end_str to take out the wrap that xml gives us
    """
    return control.toxml()


class Json2XformQuestionValidationTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls)

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

        expected_string_control_xml = self.config.get(
            self.cls_name, "test_question_type_string_control")

        expected_string_binding_xml = self.config.get(
            self.cls_name, "test_question_type_string_binding")

        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_string_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_string_binding_xml)

    def test_select_one_question_multilingual(self):
        """
        Test the lowest common denominator of question types.
        """
        simple_select_one_json = {
            u"label": {u"f": u"ftext", u"e": u"etext"},
            u"type": u"select one",
            u"name": u"qname",
            u"choices": [
                {u"label": {u"f": u"fa", u"e": u"ea"}, u"name": u"a"},
                {u"label": {u"f": u"fb", u"e": u"eb"}, u"name": u"b"}
            ]
        }

        # I copied the response in, since this is not our method of testing
        # valid return values.
        expected_select_one_control_xml = self.config.get(
            self.cls_name, "test_select_one_question_multilingual_control")

        expected_select_one_binding_xml = self.config.get(
            self.cls_name, "test_select_one_question_multilingual_binding")

        q = create_survey_element_from_dict(simple_select_one_json)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_one_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()),
                             expected_select_one_binding_xml)

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

        expected_integer_control_xml = self.config.get(
            self.cls_name,
            "test_simple_integer_question_type_multilingual_control")

        expected_integer_binding_xml = self.config.get(
            self.cls_name,
            "test_simple_integer_question_type_multilingual_binding")

        q = create_survey_element_from_dict(simple_integer_question)

        self.s.add_child(q)

        self.assertEqual(ctw(q.xml_control()), expected_integer_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_integer_binding_xml)

    def test_simple_date_question_type_multilingual(self):
        """
        not sure how date questions should show up.
        """
        simple_date_question = {u"label": {u"f": u"fd", u"e": u"ed"},
                                u"type": u"date", u"name": u"date_q",
                                u"attributes": {}}

        expected_date_control_xml = self.config.get(
            self.cls_name,
            "test_simple_date_question_type_multilingual_control")

        expected_date_binding_xml = self.config.get(
            self.cls_name,
            "test_simple_date_question_type_multilingual_binding")

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

        expected_phone_number_control_xml = self.config.get(
            self.cls_name,
            "test_simple_phone_number_question_type_multilingual_control")

        expected_phone_number_binding_xml = self.config.get(
            self.cls_name,
            "test_simple_phone_number_question_type_multilingual_binding")

        q = create_survey_element_from_dict(simple_phone_number_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()),
                         expected_phone_number_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()),
                             expected_phone_number_binding_xml)

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

        expected_select_all_control_xml = self.config.get(
            self.cls_name,
            "test_simple_select_all_question_multilingual_control")

        expected_select_all_binding_xml = self.config.get(
            self.cls_name,
            "test_simple_select_all_question_multilingual_binding")

        q = create_survey_element_from_dict(simple_select_all_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_all_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()),
                             expected_select_all_binding_xml)

    def test_simple_decimal_question_multilingual(self):
        """
        not sure how decimal should show up.
        """
        simple_decimal_question = {u"label": {u"f": u"f text", u"e": u"e text"},
                                   u"type": u"decimal", u"name": u"decimal_q",
                                   u"attributes": {}}

        expected_decimal_control_xml = self.config.get(
            self.cls_name, "test_simple_decimal_question_multilingual_control")

        expected_decimal_binding_xml = self.config.get(
            self.cls_name, "test_simple_decimal_question_multilingual_binding")

        q = create_survey_element_from_dict(simple_decimal_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_decimal_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_binding()), expected_decimal_binding_xml)
