"""
Test loop syntax.
"""

from unittest import TestCase

from pyxform.validators.pyxform import unique_names
from pyxform.xls2xform import convert

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.group import xpg
from tests.xpath_helpers.questions import xpq


class TestLoopOutput(PyxformTestCase):
    """
    A 'loop' is a type of group that, for each choice in the referenced choice list,
    generates grouped set of questions using the questions inside the loop definition.
    The pattern "%(name)s" or "%(label)s" can be used to insert the choice name or label
    into the question columns, e.g. to adjust the label to each choice.
    """

    def test_loop(self):
        """Should find that each item in the loop is repeated for each loop choice."""
        md = """
        | survey |
        |        | type               | name | label             |
        |        | begin_loop over c1 | l1   |                   |
        |        | integer            | q1   | Age               |
        |        | select_one c2      | q2   | Size of %(label)s |
        |        | end_loop           |      |                   |

        | choices |
        |         | list_name | name   | label   |
        |         | c1        | thing1 | Thing 1 |
        |         | c1        | thing2 | Thing 2 |
        |         | c2        | type1  | Big     |
        |         | c2        | type2  | Small   |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Instance
                xpq.model_instance_item("l1/x:thing1/x:q1"),
                xpq.model_instance_item("l1/x:thing1/x:q2"),
                xpq.model_instance_item("l1/x:thing2/x:q1"),
                xpq.model_instance_item("l1/x:thing2/x:q2"),
                # Bind
                xpq.model_instance_bind("l1/thing1/q1", "int"),
                xpq.model_instance_bind("l1/thing1/q2", "string"),
                xpq.model_instance_bind("l1/thing1/q1", "int"),
                xpq.model_instance_bind("l1/thing1/q1", "int"),
                # Control
                """
                /h:html/h:body/x:group[@ref = '/test_name/l1']/x:group[
                  @ref = '/test_name/l1/thing1'
                  and ./x:label = 'Thing 1'
                  and ./x:input[
                        @ref = '/test_name/l1/thing1/q1'
                        and ./x:label = 'Age'
                      ]
                  and ./x:select1[
                        @ref = '/test_name/l1/thing1/q2'
                        and ./x:label = 'Size of Thing 1'
                        and ./x:itemset[
                              @nodeset = "instance('c2')/root/item"
                              and ./x:value[@ref = 'name']
                              and ./x:label[@ref = 'label']
                            ]
                      ]
                ]
                """,
                """
                /h:html/h:body/x:group[@ref = '/test_name/l1']/x:group[
                  @ref = '/test_name/l1/thing2'
                  and ./x:label = 'Thing 2'
                  and ./x:input[
                        @ref = '/test_name/l1/thing2/q1'
                        and ./x:label = 'Age'
                      ]
                  and ./x:select1[
                        @ref = '/test_name/l1/thing2/q2'
                        and ./x:label = 'Size of Thing 2'
                        and ./x:itemset[
                              @nodeset = "instance('c2')/root/item"
                              and ./x:value[@ref = 'name']
                              and ./x:label[@ref = 'label']
                            ]
                      ]
                ]
                """,
            ],
        )

    def test_loop__groups_error(self):
        """Should find that using a group in a loop results in an error."""
        md = """
        | survey |
        |        | type               | name | label             |
        |        | begin_loop over c1 | l1   |                   |
        |        | begin_group        | g1   |                   |
        |        | integer            | q1   | Age               |
        |        | select_one c2      | q2   | Size of %(label)s |
        |        | end_group          |      |                   |
        |        | end_loop           |      |                   |

        | choices |
        |         | list_name | name   | label   |
        |         | c1        | thing1 | Thing 1 |
        |         | c1        | thing2 | Thing 2 |
        |         | c2        | type1  | Big     |
        |         | c2        | type2  | Small   |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Instance
                xpq.model_instance_item("l1/x:thing1/x:g1/x:q1"),
                xpq.model_instance_item("l1/x:thing1/x:g1/x:q2"),
                xpq.model_instance_item("l1/x:thing2/x:g1/x:q1"),
                xpq.model_instance_item("l1/x:thing2/x:g1/x:q2"),
                # Bind
                xpq.model_instance_bind("l1/thing1/g1/q1", "int"),
                xpq.model_instance_bind("l1/thing1/g1/q2", "string"),
                xpq.model_instance_bind("l1/thing1/g1/q1", "int"),
                xpq.model_instance_bind("l1/thing1/g1/q1", "int"),
                # Control
                # TODO: name/label substitution doesn't work with nested group
                """
                /h:html/h:body/x:group[@ref = '/test_name/l1']/x:group[
                  @ref = '/test_name/l1/thing1'
                  and ./x:label = 'Thing 1'
                ]/x:group[
                  @ref = '/test_name/l1/thing1/g1'
                  and ./x:input[
                        @ref = '/test_name/l1/thing1/g1/q1'
                        and ./x:label = 'Age'
                      ]
                  and ./x:select1[
                        @ref = '/test_name/l1/thing1/g1/q2'
                        and ./x:label = 'Size of %(label)s'
                        and ./x:itemset[
                              @nodeset = "instance('c2')/root/item"
                              and ./x:value[@ref = 'name']
                              and ./x:label[@ref = 'label']
                            ]
                      ]
                ]
                """,
                """
                /h:html/h:body/x:group[@ref = '/test_name/l1']/x:group[
                  @ref = '/test_name/l1/thing2'
                  and ./x:label = 'Thing 2'
                ]/x:group[
                  @ref = '/test_name/l1/thing2/g1'
                  and ./x:input[
                        @ref = '/test_name/l1/thing2/g1/q1'
                        and ./x:label = 'Age'
                      ]
                  and ./x:select1[
                        @ref = '/test_name/l1/thing2/g1/q2'
                        and ./x:label = 'Size of %(label)s'
                        and ./x:itemset[
                              @nodeset = "instance('c2')/root/item"
                              and ./x:value[@ref = 'name']
                              and ./x:label[@ref = 'label']
                            ]
                      ]
                ]
                """,
            ],
        )

    def test_loop__label__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label |
        | | begin_loop over c1 | g1   | G1    |
        | | text               | q1   | Q1    |
        | | end_loop           |      |       |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_label_no_translation("/test_name/g1", "G1"),
                # Choice loop group.
                xpg.group_label_no_translation(
                    "/test_name/g1/n1", "N1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__no_label__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label |
        | | begin_loop over c1 | g1   |       |
        | | text               | q1   | Q1    |
        | | end_loop           |      |       |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_no_label("/test_name/g1"),
                # Choice loop group.
                xpg.group_label_no_translation(
                    "/test_name/g1/n1", "N1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__label__translated__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label::English (en) |
        | | begin_loop over c1 | g1   | G1                  |
        | | text               | q1   | Q1                  |
        | | end_loop           |      |                     |

        | choices |
        | | list_name | name | label::English (en) |
        | | c1        | n1   | N1                  |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_label_translation("/test_name/g1"),
                # Choice loop group.
                xpg.group_label_translation(
                    "/test_name/g1/n1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__no_label__translated__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label::English (en) |
        | | begin_loop over c1 | g1   |                     |
        | | text               | q1   | Q1                  |
        | | end_loop           |      |                     |

        | choices |
        | | list_name | name | label::English (en) |
        | | c1        | n1   | N1                  |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_no_label("/test_name/g1"),
                # Choice loop group.
                xpg.group_label_translation(
                    "/test_name/g1/n1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__label__appearance__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label | appearance |
        | | begin_loop over c1 | g1   | G1    | field-list |
        | | text               | q1   | Q1    |            |
        | | end_loop           |      |       |            |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_label_no_translation_appearance(
                    "/test_name/g1", "G1", "field-list"
                ),
                # Choice loop group.
                xpg.group_label_no_translation(
                    "/test_name/g1/n1", "N1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__no_label__appearance__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label | appearance |
        | | begin_loop over c1 | g1   |       | field-list |
        | | text               | q1   | Q1    |            |
        | | end_loop           |      |       |            |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_no_label_appearance("/test_name/g1", "field-list"),
                # Choice loop group.
                xpg.group_label_no_translation(
                    "/test_name/g1/n1", "N1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__label__translated__appearance__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label::English (en) | appearance |
        | | begin_loop over c1 | g1   | G1                  | field-list |
        | | text               | q1   | Q1                  |            |
        | | end_loop           |      |                     |            |

        | choices |
        | | list_name | name | label::English (en) |
        | | c1        | n1   | N1                  |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_label_translation_appearance("/test_name/g1", "field-list"),
                # Choice loop group.
                xpg.group_label_translation(
                    "/test_name/g1/n1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )

    def test_loop__no_label__translated__appearance__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type               | name | label::English (en) | appearance |
        | | begin_loop over c1 | g1   |                     | field-list |
        | | text               | q1   | Q1                  |            |
        | | end_loop           |      |                     |            |

        | choices |
        | | list_name | name | label::English (en) |
        | | c1        | n1   | N1                  |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                # Primary loop group.
                xpg.group_no_label_appearance("/test_name/g1", "field-list"),
                # Choice loop group.
                xpg.group_label_translation(
                    "/test_name/g1/n1", "/x:group[@ref='/test_name/g1']"
                ),
            ],
        )


class TestLoopParsing(PyxformTestCase):
    def test_loop__repeats_error(self):
        """Should find that using a repeat in a loop results in an error."""
        md = """
        | survey |
        |        | type               | name | label             |
        |        | begin loop over c1 | l1   |                   |
        |        | begin repeat       | r1   |                   |
        |        | integer            | q1   | Count %(label)s   |
        |        | select_one c2      | q2   | Type of %(label)s |
        |        | end repeat         |      |                   |
        |        | end loop           |      |                   |

        | choices |
        |         | list_name | name   | label   |
        |         | c1        | thing1 | Thing 1 |
        |         | c1        | thing2 | Thing 2 |
        |         | c2        | type1  | Big     |
        |         | c2        | type2  | Small   |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            # Not caught by xls2json since loops are currently generated in builder.py
            error__contains=[unique_names.NAMES004.format(row=None, value="r1")],
        )

    def test_loop__references_error(self):
        """Should find that using a reference variable in a loop results in an error."""
        md = """
        | survey |
        |        | type               | name | label           |
        |        | begin loop over c1 | l1   |                 |
        |        | integer            | q1   | Count %(label)s |
        |        | note               | q2   | Counted ${q1}   |
        |        | end loop           |      |                 |

        | choices |
        |         | list_name | name   | label   |
        |         | c1        | thing1 | Thing 1 |
        |         | c1        | thing2 | Thing 2 |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                "There has been a problem trying to replace ${q1} with the XPath to the "
                "survey element named 'q1'. There are multiple survey elements named 'q1'."
            ],
        )


class TestLoopInternalRepresentation(TestCase):
    maxDiff = None

    def test_pyxform(self):
        """Should find that the internal pyxform data structure remains consistent."""
        md = """
        | survey |
        | | type                       | name     | label::English                    |
        | | begin loop over my_columns | my_table | My Table                          |
        | | integer                    | count    | How many are there in this group? |
        | | end loop                   |          |                                   |

        | choices |
        | | list name  | name | label:English |
        | | my_columns | col1 | Column 1      |
        | | my_columns | col2 | Column 2      |

        | settings |
        | | id_string   |
        | | simple_loop |
        """
        observed = convert(xlsform=md)._pyxform
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

    def test_survey_to_json_output(self):
        """Should find that the survey.to_json_dict output remains consistent."""
        md = """
        | survey |
        | | type                  | name               | label::English        | label::French    | constraint    |
        | | begin loop over types | loop_vehicle_types |                       |                  |               |
        | | integer               | total              | How many do you have? | Combien avoir?   |               |
        | | integer               | working            | How many are working? | Combien marcher? | . <= ../total |
        | | end loop              |                    |                       |                  |               |

        | choices |
        | | list_name | name        | label::English | label::French |
        | | types     | car         | Car            | Voiture       |
        | | types     | motor_cycle | Motorcycle     | Moto          |

        | settings |
        | | id_string    |
        | | another_loop |
        """
        observed = convert(xlsform=md)._survey.to_json_dict()
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
