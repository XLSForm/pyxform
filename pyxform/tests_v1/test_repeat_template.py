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
        self.assertPyxformXform(
            md="""
                | survey |              |          |                      |
                |        | type         | name     | label                |
                |        | text         | aa       | Text AA              |
                |        | begin repeat | section  | Section              |
                |        | text         | a        | Text A               |
                |        | text         | b        | Text B               |
                |        | text         | c        | Text C               |
                |        | note         | d        | Note D               |
                |        | end repeat   |          |                      |
                |        |              |          |                      |
                |        | begin repeat | section_a| Section A            |
                |        | begin repeat | section_b| Section B            |
                |        | text         | e        | Text E               |
                |        | begin repeat | section_c| Section C            |
                |        | text         | f        | Text F               |
                |        | end repeat   |          |                      |
                |        | end repeat   |          |                      |
                |        | text         | g        | Text G               |
                |        | begin repeat | section_d| Section D            |
                |        | note         | h        | Note H               |
                |        | end repeat   |          |                      |
                |        | note         | i        | Note I               |
                |        | end repeat   |          |                      |
                """,
            debug=True,
            instance__contains=[],
            model__contains=[],
            xml__contains=[],
        )

    def test_repeat_adding_template_and_instance_with_group(self):
        """
        Repeat should add template and instance even when they are inside grouping
        """
        self.assertPyxformXform(
            md="""
                | survey |              |          |                      |
                |        | type         | name     | label                |
                |        | text         | aa       | Text AA              |
                |        | begin repeat | section  | Section              |
                |        | text         | a        | Text A               |
                |        | text         | b        | Text B               |
                |        | text         | c        | Text C               |
                |        | note         | d        | Note D               |
                |        | end repeat   |          |                      |
                |        |              |          |                      |
                |        | begin group  | group_a  | Group A              |
                |        | begin repeat | section_a| Section A            |
                |        | begin repeat | section_b| Section B            |
                |        | text         | e        | Text E               |
                |        | begin group  | group_b  | Group B              |
                |        | text         | f        | Text F               |
                |        | text         | g        | Text G               |
                |        | note         | h        | Note H               |
                |        | end group    |          |                      |
                |        | note         | i        | Note I               |
                |        | end repeat   |          |                      |
                |        | end repeat   |          |                      |
                |        | end group    |          |                      |
                """,
            debug=True,
            instance__contains=[],
            model__contains=[],
            xml__contains=[],
        )
