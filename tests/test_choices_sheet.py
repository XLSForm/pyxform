# -*- coding: utf-8 -*-
from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


class ChoicesSheetTest(PyxformTestCase):
    def test_numeric_choice_names__for_static_selects__allowed(self):
        """
        Test numeric choice names for static selects.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |
            |          | type               | name | label |
            |          | select_one choices | a    | A     |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    | One   |
            |          | choices            | 2    | Two   |
            """,
            xml__xpath_match=[
                xpc.model_instance_choices_label("choices", (("1", "One"), ("2", "Two"))),
                xpq.body_select1_itemset("a"),
            ],
        )

    def test_numeric_choice_names__for_dynamic_selects__allowed(self):
        """
        Test numeric choice names for dynamic selects.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |               |
            |          | type               | name | label | choice_filter |
            |          | select_one choices | a    | A     | true()        |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    | One   |
            |          | choices            | 2    | Two   |
            """,
            xml__xpath_match=[
                xpc.model_instance_choices_label("choices", (("1", "One"), ("2", "Two"))),
                xpq.body_select1_itemset("a"),
            ],
        )

    def test_choices_without_labels__for_static_selects__allowed(self):
        """
        Test choices without labels for static selects. Validate will NOT fail.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |
            |          | type               | name | label |
            |          | select_one choices | a    | A     |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    |       |
            |          | choices            | 2    |       |
            """,
            xml__xpath_match=[
                xpq.body_select1_itemset("a"),
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root[
                  ./x:item/x:name/text() = '1'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                  and
                  ./x:item/x:name/text() = '2'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                ]
                """,
            ],
        )

    def test_choices_without_labels__for_dynamic_selects__allowed_by_pyxform(self):
        """
        Test choices without labels for dynamic selects. Validate will fail.
        """
        # TODO: validate doesn't fail
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |               |
            |          | type               | name | label | choice_filter |
            |          | select_one choices | a    | A     | true()        |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    |       |
            |          | choices            | 2    |       |
            """,
            run_odk_validate=False,
            xml__xpath_match=[
                xpq.body_select1_itemset("a"),
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root[
                  ./x:item/x:name/text() = '1'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                  and
                  ./x:item/x:name/text() = '2'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                ]
                """,
            ],
        )

    def test_choices_extra_columns_output_order_matches_xlsform(self):
        """Should find that element order matches column order."""
        md = """
        | survey   |                    |      |       |
        |          | type               | name | label |
        |          | select_one choices | a    | A     |
        | choices  |                    |      |       |
        |          | list_name          | name | label | geometry                 |
        |          | choices            | 1    |       | 46.5841618 7.0801379 0 0 |
        |          | choices            | 2    |       | 35.8805082 76.515057 0 0 |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_contains=[
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root/x:item[
                  ./x:name[position() = 1 and text() = '1']
                  and ./x:geometry[position() = 2]
                ]
                """
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root/x:item[
                  ./x:name[position() = 1 and text() = '2']
                  and ./x:geometry[position() = 2]
                ]
                """
            ],
        )
