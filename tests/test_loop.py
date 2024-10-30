"""
Test loop syntax.
"""

from unittest import TestCase

from pyxform.xls2xform import convert

from tests import utils


class TestLoop(TestCase):
    maxDiff = None

    def test_table(self):
        path = utils.path_to_text_fixture("simple_loop.xls")
        observed = convert(xlsform=path)._pyxform

        expected = {
            "name": "data",
            "title": "simple_loop",
            "sms_keyword": "simple_loop",
            "default_language": "default",
            "id_string": "simple_loop",
            "type": "survey",
            "children": [
                {
                    "children": [
                        {
                            "type": "integer",
                            "name": "count",
                            "label": {"English": "How many are there in this group?"},
                        }
                    ],
                    "type": "loop",
                    "name": "my_table",
                    "columns": [
                        {"name": "col1", "label": {"English": "Column 1"}},
                        {"name": "col2", "label": {"English": "Column 2"}},
                    ],
                    "label": {"English": "My Table"},
                },
                {
                    "control": {"bodyless": True},
                    "type": "group",
                    "name": "meta",
                    "children": [
                        {
                            "bind": {"readonly": "true()", "jr:preload": "uid"},
                            "type": "calculate",
                            "name": "instanceID",
                        }
                    ],
                },
            ],
            "choices": {
                "my_columns": [
                    {"label": {"English": "Column 1"}, "name": "col1"},
                    {"label": {"English": "Column 2"}, "name": "col2"},
                ]
            },
        }
        self.assertEqual(expected, observed)

    def test_loop(self):
        path = utils.path_to_text_fixture("another_loop.xls")
        observed = convert(xlsform=path)._survey.to_json_dict()
        observed.pop("_translations", None)
        observed.pop("_xpath", None)
        expected = {
            "name": "data",
            "id_string": "another_loop",
            "sms_keyword": "another_loop",
            "default_language": "default",
            "title": "another_loop",
            "type": "survey",
            "children": [
                {
                    "name": "loop_vehicle_types",
                    "type": "group",
                    "children": [
                        {
                            "label": {"English": "Car", "French": "Voiture"},
                            "name": "car",
                            "type": "group",
                            "children": [
                                {
                                    "label": {
                                        "English": "How many do you have?",
                                        "French": "Combien avoir?",
                                    },
                                    "name": "total",
                                    "type": "integer",
                                },
                                {
                                    "bind": {"constraint": ". <= ../total"},
                                    "label": {
                                        "English": "How many are working?",
                                        "French": "Combien marcher?",
                                    },
                                    "name": "working",
                                    "type": "integer",
                                },
                            ],
                        },
                        {
                            "label": {"English": "Motorcycle", "French": "Moto"},
                            "name": "motor_cycle",
                            "type": "group",
                            "children": [
                                {
                                    "label": {
                                        "English": "How many do you have?",
                                        "French": "Combien avoir?",
                                    },
                                    "name": "total",
                                    "type": "integer",
                                },
                                {
                                    "bind": {"constraint": ". <= ../total"},
                                    "label": {
                                        "English": "How many are working?",
                                        "French": "Combien marcher?",
                                    },
                                    "name": "working",
                                    "type": "integer",
                                },
                            ],
                        },
                    ],
                },
                {
                    "children": [
                        {
                            "bind": {"jr:preload": "uid", "readonly": "true()"},
                            "name": "instanceID",
                            "type": "calculate",
                        }
                    ],
                    "control": {"bodyless": True},
                    "name": "meta",
                    "type": "group",
                },
            ],
            "choices": {
                "types": [
                    {"label": {"English": "Car", "French": "Voiture"}, "name": "car"},
                    {
                        "label": {"English": "Motorcycle", "French": "Moto"},
                        "name": "motor_cycle",
                    },
                ]
            },
        }
        self.assertEqual(expected, observed)
