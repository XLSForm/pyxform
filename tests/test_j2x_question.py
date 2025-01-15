"""
Testing creation of Surveys using verbose methods
"""

from collections.abc import Generator

from pyxform import Survey
from pyxform.builder import create_survey_element_from_dict

from tests.pyxform_test_case import PyxformTestCase
from tests.utils import prep_class_config
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


def ctw(control):
    """
    ctw stands for control_test_wrap, but ctw is shorter and easier. using
    begin_str and end_str to take out the wrap that xml gives us
    """
    if isinstance(control, list) and len(control) == 1:
        control = control[0]
    elif isinstance(control, Generator):
        control = next(control)
    return control.toxml()


class Json2XformQuestionValidationTests(PyxformTestCase):
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
        self.assertEqual(ctw(q.xml_control(survey=self.s)), expected_string_control_xml)
        self.assertEqual(ctw(q.xml_bindings(survey=self.s)), expected_string_binding_xml)

    def test_select_one_question_multilingual(self):
        """Should be able to build a valid XForm from a dict with a multi-language select."""
        survey = {
            "type": "survey",
            "name": "test_name",
            "id_string": "data",
            "children": [
                {
                    "label": {"f": "ftext", "e": "etext"},
                    "type": "select one",
                    "name": "q1",
                    "itemset": "c1",
                }
            ],
            "choices": {
                "c1": [
                    {"label": {"f": "fa", "e": "ea"}, "name": "a"},
                    {"label": {"f": "fb", "e": "eb"}, "name": "b"},
                ]
            },
        }
        self.assertPyxformXform(
            survey=create_survey_element_from_dict(survey),
            xml__xpath_match=[
                # question has data binding, control, and itemset reference.
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.body_label_itext("select1", "q1"),
                # itext has secondary choices instance, and labels for each language.
                xpq.model_instance_exists("c1"),
                xpq.model_itext_label("q1", "f", "ftext"),
                xpq.model_itext_label("q1", "e", "etext"),
                xpc.model_instance_choices_itext("c1", ("a", "b")),
                xpc.model_itext_choice_text_label_by_pos("f", "c1", ("fa", "fb")),
                xpc.model_itext_choice_text_label_by_pos("e", "c1", ("ea", "eb")),
            ],
        )

    def test_select_one_question_multilingual__common_choices(self):
        """Should be able to build a valid XForm from a dict where 2 questions use 1 choice list."""
        survey = {
            "type": "survey",
            "name": "test_name",
            "id_string": "data",
            "children": [
                {
                    "label": "Q1",
                    "type": "select one",
                    "name": "q1",
                    "itemset": "c1",
                },
                {
                    "label": "Q2",
                    "type": "select one",
                    "name": "q2",
                    "itemset": "c1",
                },
            ],
            "choices": {
                "c1": [
                    {"label": {"f": "fa", "e": "ea"}, "name": "a"},
                    {"label": {"f": "fb", "e": "eb"}, "name": "b"},
                ]
            },
        }
        self.assertPyxformXform(
            survey=create_survey_element_from_dict(survey),
            xml__xpath_match=[
                # question has data binding, control, and itemset reference.
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.body_label_inline("select1", "q1", "Q1"),
                xpq.model_instance_item("q2"),
                xpq.model_instance_bind("q2", "string"),
                xpq.body_label_inline("select1", "q2", "Q2"),
                # itext has secondary choices instance, and labels for each language.
                xpq.model_instance_exists("c1"),
                xpc.model_instance_choices_itext("c1", ("a", "b")),
                xpc.model_itext_choice_text_label_by_pos("f", "c1", ("fa", "fb")),
                xpc.model_itext_choice_text_label_by_pos("e", "c1", ("ea", "eb")),
            ],
        )

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

        self.assertEqual(ctw(q.xml_control(survey=self.s)), expected_integer_control_xml)
        self.assertEqual(ctw(q.xml_bindings(survey=self.s)), expected_integer_binding_xml)

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
        self.assertEqual(ctw(q.xml_control(survey=self.s)), expected_date_control_xml)
        self.assertEqual(ctw(q.xml_bindings(survey=self.s)), expected_date_binding_xml)

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
        observed = q.xml_control(survey=self.s)
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
        binding = next(q.xml_bindings(survey=self.s))
        observed = {k: v for k, v in binding.attributes.items()}  # noqa: C416
        self.assertDictEqual(expected, observed)

    def test_simple_select_all_question_multilingual(self):
        """
        not sure how select all questions should show up...
        """
        survey = {
            "type": "survey",
            "name": "test_name",
            "id_string": "data",
            "children": [
                {
                    "label": {"f": "ftext", "e": "etext"},
                    "type": "select all that apply",
                    "name": "q1",
                    "itemset": "c1",
                }
            ],
            "choices": {
                "c1": [
                    {"label": {"f": "fa", "e": "ea"}, "name": "a"},
                    {"label": {"f": "fb", "e": "eb"}, "name": "b"},
                ]
            },
        }
        self.assertPyxformXform(
            survey=create_survey_element_from_dict(survey),
            xml__xpath_match=[
                # question has data binding, control, and itemset reference.
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.body_label_itext("select", "q1"),
                # itext has secondary choices instance, and labels for each language.
                xpq.model_instance_exists("c1"),
                xpq.model_itext_label("q1", "f", "ftext"),
                xpq.model_itext_label("q1", "e", "etext"),
                xpc.model_instance_choices_itext("c1", ("a", "b")),
                xpc.model_itext_choice_text_label_by_pos("f", "c1", ("fa", "fb")),
                xpc.model_itext_choice_text_label_by_pos("e", "c1", ("ea", "eb")),
            ],
        )

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
        self.assertEqual(ctw(q.xml_control(survey=self.s)), expected_decimal_control_xml)
        self.assertEqual(ctw(q.xml_bindings(survey=self.s)), expected_decimal_binding_xml)
