from pyxform_test_case import PyxformTestCase


class GroupsTests(PyxformTestCase):

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
                '<pregrp/>',
                '<xgrp>',
                    '<xgrp_q1/>',  # nopep8
                    '<xgrp_q1/>',  # nopep8
                    '<xgrp_q2/>',  # nopep8
                '</xgrp>',
                '<postgrp/>',
                ])
