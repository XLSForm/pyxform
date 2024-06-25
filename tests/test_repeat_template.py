"""
Test repeat template and instance structure.
"""

from tests.pyxform_test_case import PyxformTestCase


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
            | survey |              |          |           |
            |        | type         | name     | label     |
            |        | text         | aa       | Text AA   |
            |        | begin repeat | section  | Section   |
            |        | text         | a        | Text A    |
            |        | text         | b        | Text B    |
            |        | text         | c        | Text C    |
            |        | note         | d        | Note D    |
            |        | end repeat   |          |           |
            |        |              |          |           |
            |        | begin repeat | repeat_a | Section A |
            |        | begin repeat | repeat_b | Section B |
            |        | text         | e        | Text E    |
            |        | begin repeat | repeat_c | Section C |
            |        | text         | f        | Text F    |
            |        | end repeat   |          |           |
            |        | end repeat   |          |           |
            |        | text         | g        | Text G    |
            |        | begin repeat | repeat_d | Section D |
            |        | note         | h        | Note H    |
            |        | end repeat   |          |           |
            |        | note         | i        | Note I    |
            |        | end repeat   |          |           |
            """,
            xml__xpath_match=[
                "/h:html/h:head/x:model/x:instance/x:test_name/x:section[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:section[not(@jr:template)]",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a[not(@jr:template)]",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a/x:repeat_b[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a/x:repeat_b[not(@jr:template)]",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a/x:repeat_b/x:repeat_c[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a/x:repeat_b/x:repeat_c[not(@jr:template)]",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a/x:repeat_d[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:repeat_a/x:repeat_d[not(@jr:template)]",
            ],
        )

    def test_repeat_adding_template_and_instance_with_group(self):
        """
        Repeat should add template and instance even when they are inside grouping
        """
        self.assertPyxformXform(
            md="""
            | survey |              |          |           |
            |        | type         | name     | label     |
            |        | text         | aa       | Text AA   |
            |        | begin repeat | section  | Section   |
            |        | text         | a        | Text A    |
            |        | text         | b        | Text B    |
            |        | text         | c        | Text C    |
            |        | note         | d        | Note D    |
            |        | end repeat   |          |           |
            |        |              |          |           |
            |        | begin group  | group_a  | Group A   |
            |        | begin repeat | repeat_a | Section A |
            |        | begin repeat | repeat_b | Section B |
            |        | text         | e        | Text E    |
            |        | begin group  | group_b  | Group B   |
            |        | text         | f        | Text F    |
            |        | text         | g        | Text G    |
            |        | note         | h        | Note H    |
            |        | end group    |          |           |
            |        | note         | i        | Note I    |
            |        | end repeat   |          |           |
            |        | end repeat   |          |           |
            |        | end group    |          |           |
            """,
            xml__xpath_match=[
                "/h:html/h:head/x:model/x:instance/x:test_name/x:section[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:section[not(@jr:template)]",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:group_a/x:repeat_a[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:group_a/x:repeat_a[not(@jr:template)]",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:group_a/x:repeat_a/x:repeat_b[@jr:template='']",
                "/h:html/h:head/x:model/x:instance/x:test_name/x:group_a/x:repeat_a/x:repeat_b[not(@jr:template)]",
            ],
        )
