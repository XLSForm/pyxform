# -*- coding: utf-8 -*-
"""
test_repeat.py
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TestRepeat(PyxformTestCase):
    """
    TestRepeat class.
    """
    def test_repeat_relative_reference(self):
        """
        Test relative reference in repeats.
        """
        self.assertPyxformXform(
            name="test_repeat",
            title="Relative Paths in repeats",
            md="""
                | survey |              |          |            |                      |
                |        | type         | name     | relevant   | label                |
                |        | text         | Z        |            | Fruit                |
                |        | begin repeat | section  |            | Section              |
                |        | text         | AA       |            | Anything really      |
                |        | text         | A        |            | A oat                |
                |        | text         | B        | ${A}='oat' | B w ${A}             |
                |        | note         | note1    |            | Noted ${AA} w ${A}   |
                |        | end repeat   |          |            |                      |
                |        |              |          |            |                      |
                |        | begin repeat | section2 |            | Section 2            |
                |        | text         | C        |            | C                    |
                |        | begin group  | sectiona |            | Section A            |
                |        | text         | D        |            | D oat                |
                |        | text         | E        | ${D}='oat' | E w ${Z}             |
                |        | note         | note2    |            | Noted ${C} w ${E}    |
                |        | end group    |          |            |                      |
                |        | note         | note3    |            | Noted ${C} w ${E}    |
                |        | end repeat   |          |            |                      |
                |        |              |          |            |                      |
                |        | begin repeat | section3 |            | Section 3            |
                |        | text         | FF       |            | F any text           |
                |        | text         | F        |            | F oat                |
                |        | begin group  | sectionb |            | Section B            |
                |        | text         | G        |            | G oat                |
                |        | text         | H        | ${G}='oat' | H w ${Z}             |
                |        | note         | note4    |            | Noted ${H} w ${Z}    |
                |        | end group    |          |            |                      |
                |        | begin repeat | sectionc |            | Section B            |
                |        | text         | I        |            | I                    |
                |        | text         | J        | ${I}='oat' | J w ${Z}             |
                |        | text         | K        | ${F}='oat' | K w ${Z}             |
                |        | text         | L        | ${G}='oat' | K w ${Z}             |
                |        | note         | note5    |            | Noted ${FF} w ${H}   |
                |        | note         | note6    |            | JKL #${J}#${K}#${L}  |
                |        | end repeat   |          |            |                      |
                |        | note         | note7    |            | Noted ${FF} w ${H}   |
                |        | begin group  | sectiond |            | Section D            |
                |        | text         | M        |            | M oat                |
                |        | text         | N        | ${G}='oat' | N w ${Z}             |
                |        | text         | O        | ${M}='oat' | O w ${Z}             |
                |        | note         | note8    |            | NO #${N} #${O}       |
                |        | end group    |          |            |                      |
                |        | note         | note9    |            | ${FF} ${H} ${N} ${N} |
                |        | end repeat   |          |            |                      |
                |        |              |          |            |                      |
                """,  # noqa pylint: disable=line-too-long
            instance__contains=[
                '<section jr:template="">',
                '<A/>',
                '<B/>',
                '</section>',
                ],
            model__contains=[
                """<bind nodeset="/test_repeat/section/A" """
                """type="string"/>""",
                """<bind nodeset="/test_repeat/section/B" """
                """relevant=" ../A ='oat'" """
                """type="string"/>""",
                """<bind nodeset="/test_repeat/section2/sectiona/E" """
                """relevant=" ../D ='oat'" type="string"/>""",
                """<bind nodeset="/test_repeat/section3/sectionc/K" """
                """relevant=" ../../F ='oat'" type="string"/>""",
                """<bind nodeset="/test_repeat/section3/sectionc/L" """
                """relevant=" ../../sectionb/G ='oat'" """
                """type="string"/>""",
                """<bind nodeset="/test_repeat/section3/sectiond/N" """
                """relevant=" ../../sectionb/G ='oat'" """
                """type="string"/>"""
                ],
            xml__contains=[
                '<group ref="/test_repeat/section">',
                '<label>Section</label>',
                '</group>',
                """<label> B w <output value=" ../A "/> </label>""",
                """<label> E w <output value=" /test_repeat/Z "/> </label>""",
                """<label> Noted <output value=" ../FF "/> w """
                """<output value=" ../sectionb/H "/> </label></input>"""
            ],
        )

    def test_calculate_relative_path(self):
        """Test relative paths in calculate column."""
        self.assertPyxformXform(
            name="data",
            title="Paths in a calculate within a repeat are relative.",
            md="""
                | survey  |                      |       |        |                |
                |         | type                 | name  | label  | calculation    |
                |         | begin repeat         | rep   |        |                |
                |         | select_one crop_list | crop  | Select |                |
                |         | text                 | a     | Verify | name = ${crop} |
                |         | begin group          | group |        |                |
                |         | text                 | b     | Verify | name = ${crop} |
                |         | end group            |       |        |                |
                |         | end repeat           |       |        |                |
                |         |                      |       |        |                |
                | choices |                      |       |        |                |
                |         | list name            | name  | label  |                |
                |         | crop_list            | maize | Maize  |                |
                |         | crop_list            | beans | Beans  |                |
                |         | crop_list            | kale  | Kale   |                |
            """,  # noqa pylint: disable=line-too-long
            model__contains=[
                """<bind calculate="name =  ../crop " """
                """nodeset="/data/rep/a" type="string"/>""",
                """<bind calculate="name =  ../../crop " """
                """nodeset="/data/rep/group/b" type="string"/>""",
            ],
        )

    def test_choice_filter_relative_path(self):  # pylint: disable=invalid-name
        """Test relative paths in choice_filter column."""
        self.assertPyxformXform(
            name="data",
            title="Choice filter uses relative path",
            md="""
                | survey  |                      |       |        |                |
                |         | type                 | name  | label  | choice_filter  |
                |         | begin repeat         | rep   |        |                |
                |         | select_one crop_list | crop  | Select |                |
                |         | select_one crop_list | a     | Verify | name = ${crop} |
                |         | begin group          | group |        |                |
                |         | select_one crop_list | b     | Verify | name = ${crop} |
                |         | end group            |       |        |                |
                |         | end repeat           |       |        |                |
                |         |                      |       |        |                |
                | choices |                      |       |        |                |
                |         | list name            | name  | label  |                |
                |         | crop_list            | maize | Maize  |                |
                |         | crop_list            | beans | Beans  |                |
                |         | crop_list            | kale  | Kale   |                |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<itemset nodeset="instance('crop_list')/root/item[name =  current()/../crop ]">""",  # noqa pylint: disable=line-too-long
                """<itemset nodeset="instance('crop_list')/root/item[name =  current()/../../crop ]">""",  # noqa pylint: disable=line-too-long
            ],
        )

    def test_indexed_repeat_relative_path(self):
        """Test relative path not used with indexed-repeat()."""
        self.assertPyxformXform(
            name="data",
            title="Paths in a calculate within a repeat are relative.",
            md="""
                | survey  |                      |       |        |                                  |
                |         | type                 | name  | label  | calculation                      |
                |         | begin repeat         | rep   |        |                                  |
                |         | begin repeat         | rep2  |        |                                  |
                |         | select_one crop_list | crop  | Select |                                  |
                |         | text                 | a     | Verify |                                  |
                |         | begin group          | group |        |                                  |
                |         | text                 | b     | Verify |                                  |
                |         | end group            |       |        |                                  |
                |         | end repeat           |       |        |                                  |
                |         | calculate            | c1    |        | indexed-repeat(${a}, ${rep2}, 1) |
                |         | end repeat           |       |        |                                  |
                |         |                      |       |        |                                  |
                |         |                      |       |        |                                  |
                | choices |                      |       |        |                                  |
                |         | list name            | name  | label  |                                  |
                |         | crop_list            | maize | Maize  |                                  |
                |         | crop_list            | beans | Beans  |                                  |
                |         | crop_list            | kale  | Kale   |                                  |
            """,  # noqa pylint: disable=line-too-long
            model__contains=[
                """<bind calculate="indexed-repeat( /data/rep/rep2/a ,  /data/rep/rep2 , 1)" nodeset="/data/rep/c1" type="string"/>""",  # noqa pylint: disable=line-too-long
            ],
        )
