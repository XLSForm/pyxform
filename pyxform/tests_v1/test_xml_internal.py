# -*- coding: utf-8 -*-
"""
Test for the xml-internal question
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class XmlInternalTest(PyxformTestCase):
    def should_add_instances_for_xml_interna(self):
        md = """
            | survey  |                    |            |           |            |                   |
            |         | type               | name       | label     | hint       |appearance         |
            |         | xml-internal       | states     |           |            |                   |
            |         | xml-internal       | yes_no     |           |            |                   |
            | choices |                    |            |           |            |                   |
            |         | list_name          | name       | label     |            |                   |
            |         | yes_no             | yes        | Yes       |            |                   |
            |         | states             | VA         | Virginia  |            |                   |
            |         | states             | IN         | India     |            |                   |
            |         | fruits             | apple      | Apple     |            |                   |
            |         | fruits             | banana     | Banana    |            |                   |
            """
        survey = self.md_to_pyxform_survey(md_raw=md)
        survey_xml = survey._to_pretty_xml()

        self.assertContains(survey_xml, '<instance id="yes_no">', 1)
        self.assertContains(survey_xml, '<instance id="states">', 1)
        self.assertContains(survey_xml, '<instance id="fruits">', 1)

        self.assertPyxformXform(
            md=md,
            model__contains=[
                '<instance id="yes_no">',
                '<instance id="states">',
                '<instance id="fruits">',
            ],
        )

    def should_add_single_instance_with_choice_filter(self):
        md = """
            | survey  |                    |            |           |               |                   |
            |         | type               | name       | label     | choice_filter | appearance        |
            |         | xml-internal       | states     |           |               |                   |
            |         | xml-internal       | yes_no     |           |               |                   |
            |         | select_one states  | state      | The state | state!='VA'   |                   |
            | choices |                    |            |           |               |                   |
            |         | list_name          | name       | label     |               |                   |
            |         | yes_no             | yes        | Yes       |               |                   |
            |         | states             | VA         | Virginia  |               |                   |
            |         | states             | IN         | India     |               |                   |
            |         | fruits             | apple      | Apple     |               |                   |
            |         | fruits             | banana     | Banana    |               |                   |
            """
        survey = self.md_to_pyxform_survey(md_raw=md)
        survey_xml = survey._to_pretty_xml()

        self.assertContains(survey_xml, '<instance id="yes_no">', 1)
        self.assertContains(survey_xml, '<instance id="states">', 1)
        self.assertContains(survey_xml, '<instance id="fruits">', 1)

        self.assertPyxformXform(
            md=md,
            model__contains=[
                '<instance id="yes_no">',
                '<instance id="states">',
                '<instance id="fruits">',
            ],
        )

    def should_add_single_instance_with_select(self):
        md = """
            | survey  |                    |            |           |            |                   |
            |         | type               | name       | label     | hint       |appearance         |
            |         | begin_group        | tablelist1 | Table_Y_N |            |table-list minimal |
            |         | select_one yes_no  | options1a  | Q1        | first row! |                   |
            |         | select_one yes_no  | options1b  | Q2        |            |                   |
            |         | end_group          |            |           |            |                   |
            |         | xml-internal       | states     |           |            |                   |
            |         | select_one states  | state      | The state |            |                   |
            |         | xml-internal       | yes_no     |           |            |                   |
            | choices |                    |            |           |            |                   |
            |         | list_name          | name       | label     |            |                   |
            |         | yes_no             | yes        | Yes       |            |                   |
            |         | states             | VA         | Virginia  |            |                   |
            |         | states             | IN         | India     |            |                   |
            |         | fruits             | apple      | Apple     |            |                   |
            |         | fruits             | banana     | Banana    |            |                   |
            """
        survey = self.md_to_pyxform_survey(md_raw=md)
        survey_xml = survey._to_pretty_xml()

        self.assertContains(survey_xml, '<instance id="yes_no">', 1)
        self.assertContains(survey_xml, '<instance id="states">', 1)
        self.assertContains(survey_xml, '<instance id="fruits">', 1)

        self.assertPyxformXform(
            md=md,
            model__contains=[
                '<instance id="yes_no">',
                '<instance id="states">',
                '<instance id="fruits">',
            ],
        )
