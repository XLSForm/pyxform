"""
Testing creation of Surveys using verbose methods
"""

from unittest import TestCase

from pyxform import Survey
from pyxform.builder import create_survey_element_from_dict

from tests.utils import prep_class_config

TESTING_BINDINGS = True


def ctw(control):
    """
    ctw stands for control_test_wrap, but ctw is shorter and easier. using
    begin_str and end_str to take out the wrap that xml gives us
    """
    if isinstance(control, list) and len(control) == 1:
        control = control[0]
    return control.toxml()


class Json2XformQuestionValidationTests(TestCase):
    maxDiff = None
    config = None
    cls_name = None

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls)

    def setUp(self):
        self.s = Survey(name="test")

    def test_question_type_string(self):
        simple_string_json = {
            "label": {
                "French": "Nom du travailleur agricole:",
                "English": "Name of Community Agricultural Worker",
            },
            "type": "text",
            "name": "enumerator_name",
        }

        q = create_survey_element_from_dict(simple_string_json)

        expected_string_control_xml = self.config.get(
            self.cls_name, "test_question_type_string_control"
        )

        expected_string_binding_xml = self.config.get(
            self.cls_name, "test_question_type_string_binding"
        )

        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_string_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_bindings()), expected_string_binding_xml)

    def test_select_one_question_multilingual(self):
        """
        Test the lowest common denominator of question types.
        """
        simple_select_one_json = {
            "label": {"f": "ftext", "e": "etext"},
            "type": "select one",
            "name": "qname",
            "choices": [
                {"label": {"f": "fa", "e": "ea"}, "name": "a"},
                {"label": {"f": "fb", "e": "eb"}, "name": "b"},
            ],
        }

        # I copied the response in, since this is not our method of testing
        # valid return values.
        expected_select_one_control_xml = self.config.get(
            self.cls_name, "test_select_one_question_multilingual_control"
        )

        expected_select_one_binding_xml = self.config.get(
            self.cls_name, "test_select_one_question_multilingual_binding"
        )

        q = create_survey_element_from_dict(simple_select_one_json)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_one_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_bindings()), expected_select_one_binding_xml)

    def test_simple_integer_question_type_multilingual(self):
        """
        not sure how integer questions should show up.
        """
        simple_integer_question = {
            "label": {"f": "fc", "e": "ec"},
            "type": "integer",
            "name": "integer_q",
            "attributes": {},
        }

        expected_integer_control_xml = self.config.get(
            self.cls_name, "test_simple_integer_question_type_multilingual_control"
        )

        expected_integer_binding_xml = self.config.get(
            self.cls_name, "test_simple_integer_question_type_multilingual_binding"
        )

        q = create_survey_element_from_dict(simple_integer_question)

        self.s.add_child(q)

        self.assertEqual(ctw(q.xml_control()), expected_integer_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_bindings()), expected_integer_binding_xml)

    def test_simple_date_question_type_multilingual(self):
        """
        not sure how date questions should show up.
        """
        simple_date_question = {
            "label": {"f": "fd", "e": "ed"},
            "type": "date",
            "name": "date_q",
            "attributes": {},
        }

        expected_date_control_xml = self.config.get(
            self.cls_name, "test_simple_date_question_type_multilingual_control"
        )

        expected_date_binding_xml = self.config.get(
            self.cls_name, "test_simple_date_question_type_multilingual_binding"
        )

        q = create_survey_element_from_dict(simple_date_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_date_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_bindings()), expected_date_binding_xml)

    def test_simple_phone_number_question_type_multilingual(self):
        """
        not sure how phone number questions should show up.
        """
        simple_phone_number_question = {
            "label": {"f": "fe", "e": "ee"},
            "type": "phone number",
            "name": "phone_number_q",
        }

        q = create_survey_element_from_dict(simple_phone_number_question)
        self.s.add_child(q)

        # Inspect XML Control
        observed = q.xml_control()
        self.assertEqual("input", observed.nodeName)
        self.assertEqual("/test/phone_number_q", observed.attributes["ref"].nodeValue)
        observed_label = observed.childNodes[0]
        self.assertEqual("label", observed_label.nodeName)
        self.assertEqual(
            "jr:itext('/test/phone_number_q:label')",
            observed_label.attributes["ref"].nodeValue,
        )
        observed_hint = observed.childNodes[1]
        self.assertEqual("hint", observed_hint.nodeName)
        self.assertEqual("Enter numbers only.", observed_hint.childNodes[0].nodeValue)

        # Inspect XML Binding
        expected = {
            "nodeset": "/test/phone_number_q",
            "type": "string",
            "constraint": r"regex(., '^\d*$')",
        }
        observed = {k: v for k, v in q.xml_bindings()[0].attributes.items()}  # noqa: C416
        self.assertDictEqual(expected, observed)

    def test_simple_select_all_question_multilingual(self):
        """
        not sure how select all questions should show up...
        """
        simple_select_all_question = {
            "label": {"f": "f choisit", "e": "e choose"},
            "type": "select all that apply",
            "name": "select_all_q",
            "choices": [
                {"label": {"f": "ff", "e": "ef"}, "name": "f"},
                {"label": {"f": "fg", "e": "eg"}, "name": "g"},
                {"label": {"f": "fh", "e": "eh"}, "name": "h"},
            ],
        }

        expected_select_all_control_xml = self.config.get(
            self.cls_name, "test_simple_select_all_question_multilingual_control"
        )

        expected_select_all_binding_xml = self.config.get(
            self.cls_name, "test_simple_select_all_question_multilingual_binding"
        )

        q = create_survey_element_from_dict(simple_select_all_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_select_all_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_bindings()), expected_select_all_binding_xml)

    def test_simple_decimal_question_multilingual(self):
        """
        not sure how decimal should show up.
        """
        simple_decimal_question = {
            "label": {"f": "f text", "e": "e text"},
            "type": "decimal",
            "name": "decimal_q",
            "attributes": {},
        }

        expected_decimal_control_xml = self.config.get(
            self.cls_name, "test_simple_decimal_question_multilingual_control"
        )

        expected_decimal_binding_xml = self.config.get(
            self.cls_name, "test_simple_decimal_question_multilingual_binding"
        )

        q = create_survey_element_from_dict(simple_decimal_question)
        self.s.add_child(q)
        self.assertEqual(ctw(q.xml_control()), expected_decimal_control_xml)

        if TESTING_BINDINGS:
            self.assertEqual(ctw(q.xml_bindings()), expected_decimal_binding_xml)
