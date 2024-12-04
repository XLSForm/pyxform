"""
Test XForm groups.
"""

from tests.pyxform_test_case import PyxformTestCase


class GroupsTests(PyxformTestCase):
    """
    Test XForm groups.
    """

    def test_group_type(self):
        self.assertPyxformXform(
            md="""
            | survey |             |         |                  |
            |        | type        | name    | label            |
            |        | text        | pregrp  | Pregroup text    |
            |        | begin group | xgrp    | XGroup questions |
            |        | text        | xgrp_q1 | XGroup Q1        |
            |        | integer     | xgrp_q2 | XGroup Q2        |
            |        | end group   |         |                  |
            |        | note        | postgrp | Post group note  |
            """,
            model__contains=[
                "<pregrp/>",
                "<xgrp>",
                "<xgrp_q1/>",  # nopep8
                "<xgrp_q1/>",  # nopep8
                "<xgrp_q2/>",  # nopep8
                "</xgrp>",
                "<postgrp/>",
            ],
        )

    def test_group_intent(self):
        self.assertPyxformXform(
            name="intent_test",
            md="""
            | survey |             |         |                  |                                                             |
            |        | type        | name    | label            | intent                                                      |
            |        | text        | pregrp  | Pregroup text    |                                                             |
            |        | begin group | xgrp    | XGroup questions | ex:org.redcross.openmapkit.action.QUERY(osm_file=${pregrp}) |
            |        | text        | xgrp_q1 | XGroup Q1        |                                                             |
            |        | integer     | xgrp_q2 | XGroup Q2        |                                                             |
            |        | end group   |         |                  |                                                             |
            |        | note        | postgrp | Post group note  |                                                             |
            """,  # nopep8
            xml__contains=[
                '<group intent="ex:org.redcross.openmapkit.action.QUERY(osm_file= /intent_test/pregrp )" ref="/intent_test/xgrp">'  # nopep8
            ],
        )

    def test_group_relevant_included_in_bind(self):
        """Should find the group relevance expression in the group binding."""
        md = """
        | survey |
        |        | type        | name | label | relevant  |
        |        | integer     | q1   | Q1    |           |
        |        | begin group | g1   | G1    | ${q1} = 1 |
        |        | text        | q2   | Q2    |           |
        |        | end group   |      |       |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:bind[
                  @nodeset = '/test_name/g1' and @relevant=' /test_name/q1  = 1'
                ]
                """
            ],
        )
