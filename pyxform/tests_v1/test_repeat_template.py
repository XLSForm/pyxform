# -*- coding: utf-8 -*-
"""
Test repeat template and instance structure.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TestRepeatTemplate(PyxformTestCase):
    """
    Ensuring the template and instance structure are added correctly.
    """

    def test_repeat_adding_template_and_instance(self):
        """
        Repeat should add template and instances
        """
        md = """
            | survey |              |         |                      |
            |        | type         | name    | label                |
            |        | text         | aa      | Text AA              |
            |        | begin repeat | section | Section              |
            |        | text         | a       | Text A               |
            |        | text         | b       | Text B               |
            |        | text         | c       | Text C               |
            |        | note         | d       | Note D               |
            |        | end repeat   |         |                      |
            |        |              |         |                      |
            |        | begin repeat | repeat_a| Section A            |
            |        | begin repeat | repeat_b| Section B            |
            |        | text         | e       | Text E               |
            |        | begin repeat | repeat_c| Section C            |
            |        | text         | f       | Text F               |
            |        | end repeat   |         |                      |
            |        | end repeat   |         |                      |
            |        | text         | g       | Text G               |
            |        | begin repeat | repeat_d| Section D            |
            |        | note         | h       | Note H               |
            |        | end repeat   |         |                      |
            |        | note         | i       | Note I               |
            |        | end repeat   |         |                      |
            """

        survey = self.md_to_pyxform_survey(md_raw=md)
        survey_xml = survey._to_pretty_xml()

        section_template = '<section jr:template="">'
        self.assertEqual(1, survey_xml.count(section_template))
        repeat_a_template = '<repeat_a jr:template="">'
        self.assertEqual(1, survey_xml.count(repeat_a_template))
        repeat_b_template = '<repeat_b jr:template="">'
        self.assertEqual(1, survey_xml.count(repeat_b_template))
        repeat_c_template = '<repeat_c jr:template="">'
        self.assertEqual(1, survey_xml.count(repeat_c_template))
        repeat_d_template = '<repeat_d jr:template="">'
        self.assertEqual(1, survey_xml.count(repeat_d_template))

        section_instance = "<section>"
        self.assertEqual(1, survey_xml.count(section_instance))
        repeat_a_instance = "<repeat_a>"
        self.assertEqual(1, survey_xml.count(repeat_a_instance))
        repeat_b_instance = "<repeat_b>"
        self.assertEqual(1, survey_xml.count(repeat_b_instance))
        repeat_c_instance = "<repeat_c>"
        self.assertEqual(1, survey_xml.count(repeat_c_instance))
        repeat_d_instance = "<repeat_d>"
        self.assertEqual(1, survey_xml.count(repeat_d_instance))

        self.assertPyxformXform(
            md=md,
            instance__contains=[
                '<section jr:template="">',
                '<repeat_a jr:template="">',
                '<repeat_b jr:template="">',
                '<repeat_c jr:template="">',
                '<repeat_d jr:template="">',
                "<section>",
                "<repeat_a>",
                "<repeat_b>",
                "<repeat_c>",
                "<repeat_d>",
            ],
        )

    def test_repeat_adding_template_and_instance_with_group(self):
        """
        Repeat should add template and instance even when they are inside grouping
        """
        md = """
            | survey |              |         |                      |
            |        | type         | name    | label                |
            |        | text         | aa      | Text AA              |
            |        | begin repeat | section | Section              |
            |        | text         | a       | Text A               |
            |        | text         | b       | Text B               |
            |        | text         | c       | Text C               |
            |        | note         | d       | Note D               |
            |        | end repeat   |         |                      |
            |        |              |         |                      |
            |        | begin group  | group_a | Group A              |
            |        | begin repeat | repeat_a| Section A            |
            |        | begin repeat | repeat_b| Section B            |
            |        | text         | e       | Text E               |
            |        | begin group  | group_b | Group B              |
            |        | text         | f       | Text F               |
            |        | text         | g       | Text G               |
            |        | note         | h       | Note H               |
            |        | end group    |         |                      |
            |        | note         | i       | Note I               |
            |        | end repeat   |         |                      |
            |        | end repeat   |         |                      |
            |        | end group    |         |                      |
            """

        survey = self.md_to_pyxform_survey(md_raw=md)
        survey_xml = survey._to_pretty_xml()

        section_template = '<section jr:template="">'
        self.assertEqual(1, survey_xml.count(section_template))
        repeat_a_template = '<repeat_a jr:template="">'
        self.assertEqual(1, survey_xml.count(repeat_a_template))
        repeat_b_template = '<repeat_b jr:template="">'
        self.assertEqual(1, survey_xml.count(repeat_b_template))

        section_instance = "<section>"
        self.assertEqual(1, survey_xml.count(section_instance))
        repeat_a_instance = "<repeat_a>"
        self.assertEqual(1, survey_xml.count(repeat_a_instance))
        repeat_b_instance = "<repeat_b>"
        self.assertEqual(1, survey_xml.count(repeat_b_instance))

        self.assertPyxformXform(
            md=md,
            instance__contains=[
                '<section jr:template="">',
                '<repeat_a jr:template="">',
                '<repeat_b jr:template="">',
                "<section>",
                "<repeat_a>",
                "<repeat_b>",
            ],
        )
