# -*- coding: utf-8 -*-
"""
Test reapeat structure.
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
                "<A/>",
                "<B/>",
                "</section>",
            ],
            model__contains=[
                """<bind nodeset="/test_repeat/section/A" """ """type="string"/>""",
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
                """type="string"/>""",
            ],
            xml__contains=[
                '<group ref="/test_repeat/section">',
                "<label>Section</label>",
                "</group>",
                """<label> B w <output value=" ../A "/> </label>""",
                """<label> E w <output value=" /test_repeat/Z "/> </label>""",
                """<label> Noted <output value=" ../FF "/> w """
                """<output value=" ../sectionb/H "/> </label></input>""",
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
                """<bind calculate="indexed-repeat( /data/rep/rep2/a ,  /data/rep/rep2 , 1)" nodeset="/data/rep/c1" type="string"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_output_with_translation_relative_path(self):
        md = """
        | survey |              |             |                |              |               |                             |                           |                           |
        |        | type         | name        | label::English | calculation  | hint::English | constraint_message::English | required_message::English | noAppErrorString::English |
        |        | begin repeat | member      |                |              |               |                             |                           |                           |
        |        | calculate    | pos         |                | position(..) |               |                             |                           |                           |
        |        | text         | member_name | Name of ${pos} |              |               |                             |                           |                           |
        |        | text         | a           | A              |              | hint ${pos}   | constraint ${pos}           | required ${pos}           | app error ${pos}          |
        |        | end repeat   |             |                |              |               |                             |                           |                           |
        """

        self.assertPyxformXform(
            md=md,
            name="inside-repeat-relative-path",
            xml__contains=[
                '<translation lang="English">',
                '<value> Name of <output value=" ../pos "/> </value>',
                '<value> hint <output value=" ../pos "/> </value>',
                '<value> constraint <output value=" ../pos "/> </value>',
                '<value> required <output value=" ../pos "/> </value>',
                '<value> app error <output value=" ../pos "/>',
            ],
        )

    def test_output_with_guidance_hint_translation_relative_path(self):
        md = """
        | survey |              |             |                |                        |              |
        |        | type         | name        | label::English | guidance_hint::English | calculation  |
        |        | begin repeat | member      |                |                        |              |
        |        | calculate    | pos         |                |                        | position(..) |
        |        | text         | member_name | Name of ${pos} | More ${pos}            |              |
        |        | end repeat   |             |                |                        |              |
        """

        self.assertPyxformXform(
            md=md,
            name="inside-repeat-relative-path",
            xml__contains=[
                '<translation lang="English">',
                '<value> Name of <output value=" ../pos "/> </value>',
                '<value form="guidance"> More <output value=" ../pos "/> </value>',
            ],
        )

    def test_output_with_multiple_translations_relative_path(self):
        md = """
        | survey |              |                |                |                  |              |
        |        | type         | name           | label::English | label::Indonesia | calculation  |
        |        | begin repeat | member         |                |                  |              |
        |        | calculate    | pos            |                |                  | position(..) |
        |        | text         | member_name    | Name of ${pos} | Nama ${pos}      |              |
        |        | text         | member_address |                | Alamat           |              |
        |        | end repeat   |                |                |                  |              |
        """

        self.assertPyxformXform(
            md=md,
            name="inside-repeat-relative-path",
            xml__contains=[
                '<translation lang="English">',
                '<value> Name of <output value=" ../pos "/> </value>',
            ],
        )

    def test_hints_are_not_present_within_repeats(self):
        """Hints are not present within repeats"""
        md = """
            | survey |                   |                |                   |                      |
            |        | type              | name           | label             | hint                 |
            |        | begin repeat      | pets           | Pets              | Pet details          |
            |        | text              | pets_name      | Pet's name        | Pet's name hint      |
            |        | select_one pet    | pet_type       | Type of pet       | Type of pet hint     |
            |        | image             | pet_picture    | Picture of pet    | Take a nice photo    |
            |        | end repeat        |                |                   |                      |
            | choices|                   |                |                   |                      |
            |        | list name         | name           | label             |                      |
            |        | pet               | dog            | Dog               |                      |
            |        | pet               | cat            | Cat               |                      |
            |        | pet               | bird           | Bird              |                      |
            |        | pet               | fish           | Fish              |                      |
            """  # noqa

        expected = """
    <group ref="/pyxform_autotestname/pets">
      <label>Pets</label>
      <repeat nodeset="/pyxform_autotestname/pets">
        <input ref="/pyxform_autotestname/pets/pets_name">
          <label>Pet's name</label>
          <hint>Pet's name hint</hint>
        </input>
        <select1 ref="/pyxform_autotestname/pets/pet_type">
          <label>Type of pet</label>
          <hint>Type of pet hint</hint>
          <item>
            <label>Dog</label>
            <value>dog</value>
          </item>
          <item>
            <label>Cat</label>
            <value>cat</value>
          </item>
          <item>
            <label>Bird</label>
            <value>bird</value>
          </item>
          <item>
            <label>Fish</label>
            <value>fish</value>
          </item>
        </select1>
        <upload mediatype="image/*" ref="/pyxform_autotestname/pets/pet_picture">
          <label>Picture of pet</label>
          <hint>Take a nice photo</hint>
        </upload>
      </repeat>
    </group>
"""

        self.assertPyxformXform(md=md, xml__contains=[expected], run_odk_validate=True)

    def test_hints_are_present_within_groups(self):
        """Tests that hints are present within groups."""
        md = """
            | survey |                   |                        |                                                         |                              |
            |        | type              | name                   | label                                                   | hint                         |
            |        | begin group       | child_group            | Please enter birth information for each child born.     | Pet details                  |
            |        | text              | child_name             | Name of child?                                          | Should be a text             |
            |        | decimal           | birthweight            | Child birthweight (in kgs)?                             | Should be a decimal          |
            |        | end group         |                        |                                                         |                              |
            """  # noqa
        expected = """<group ref="/pyxform_autotestname/child_group">
      <label>Please enter birth information for each child born.</label>
      <input ref="/pyxform_autotestname/child_group/child_name">
        <label>Name of child?</label>
        <hint>Should be a text</hint>
      </input>
      <input ref="/pyxform_autotestname/child_group/birthweight">
        <label>Child birthweight (in kgs)?</label>
        <hint>Should be a decimal</hint>
      </input>
    </group>"""  # noqa

        self.assertPyxformXform(md=md, xml__contains=[expected], run_odk_validate=True)

    def test_choice_from_previous_repeat_answers(self):
        """Select one choices from previous repeat answers."""
        xlsform_md = """
        | survey  |                    |            |                |
        |         | type               | name       | label          |
        |         | begin repeat       | rep        | Repeat         |
        |         | text               | name       | Enter name     |
        |         | end repeat         |            |                |
        |         | select one ${name} | choice     | Choose name    |
        """
        self.assertPyxformXform(
            name="data",
            md=xlsform_md,
            xml__contains=[
                "<itemset nodeset=\"/data/rep[./name != '']\">",
                '<value ref="name"/>',
                '<label ref="name"/>',
            ],
        )

    def test_choice_from_previous_repeat_answers_not_name(self):
        """Select one choices from previous repeat answers."""
        xlsform_md = """
        | survey  |                      |            |                |
        |         | type                 | name       | label          |
        |         | begin repeat         | rep        | Repeat         |
        |         | text                 | answer     | Enter name     |
        |         | end repeat           |            |                |
        |         | select one ${answer} | choice     | Choose name    |
        """
        self.assertPyxformXform(
            name="data",
            md=xlsform_md,
            xml__contains=[
                "<itemset nodeset=\"/data/rep[./answer != '']\">",
                '<value ref="answer"/>',
                '<label ref="answer"/>',
            ],
        )

    def test_choice_from_previous_repeat_answers_with_choice_filter(self):
        """Select one choices from previous repeat answers with choice filter"""
        xlsform_md = """
        | survey  |                    |                |                |                           |
        |         | type               | name           | label          | choice_filter             |
        |         | begin repeat       | rep            | Repeat         |                           |
        |         | text               | name           | Enter name     |                           |
        |         | begin group        | demographics   | Demographics   |                           |
        |         | integer            | age            | Enter age      |                           |
        |         | end group          | demographics   |                |                           |
        |         | end repeat         |                |                |                           |
        |         | select one fruits  | fruit          | Choose a fruit |                           |
        |         | select one ${name} | choice         | Choose name    | starts-with(${name}, "b")  |
        |         | select one ${name} | choice_18_over | Choose name    | ${age} > 18               |
        | choices |                    |                |                |                           |
        |         | list name          | name           | label          |                           |
        |         | fruits             | banana         | Banana         |                           |
        |         | fruits             | mango          | Mango          |                           |
        """
        self.assertPyxformXform(
            name="data",
            id_string="some-id",
            md=xlsform_md,
            xml__contains=[
                '<itemset nodeset="/data/rep[starts-with( ./name , &quot;b&quot;)]">',
                '<itemset nodeset="/data/rep[ ./demographics/age  &gt; 18]">',
            ],
            run_odk_validate=False,
        )

    def test_choice_from_previous_repeat_answers_in_child_repeat(self):
        """
        Select one choice from previous repeat answers when within a child of a repeat
        """
        xlsform_md = """
        | survey  |                    |                           |                                                |                             |
        |         | type               | name                      | label                                          | choice_filter               |
        |         | begin repeat       | household                 | Household Repeat                               |                             |
        |         | begin repeat       | member                    | Household member repeat                        |                             |
        |         | text               | name                      | Enter name of a household member               |                             |
        |         | integer            | age                       | Enter age of the household member              |                             |
        |         | begin repeat       | adult                     | Select a representative                        |                             |
        |         | select one ${name} | adult_name                | Choose a name                                  | ${age} > 18                 |
        |         | end repeat         | adult                     |                                                |                             |
        |         | end repeat         | member                    |                                                |                             |
        |         | end repeat         | household                 |                                                |                             |
        """
        self.assertPyxformXform(
            name="data",
            id_string="some-id",
            md=xlsform_md,
            xml__contains=['<itemset nodeset="../../../member[ ./age  &gt; 18]">'],
        )

    def test_choice_from_previous_repeat_answers_in_nested_repeat(self):
        """Select one choices from previous repeat answers within a nested repeat"""
        xlsform_md = """
        | survey  |                    |                           |                                                |                             |
        |         | type               | name                      | label                                          | choice_filter               |
        |         | begin repeat       | household                 | Household Repeat                               |                             |
        |         | begin repeat       | person                    | Household member repeat                        |                             |
        |         | text               | name                      | Enter name of a household member               |                             |
        |         | integer            | age                       | Enter age of the household member              |                             |
        |         | end repeat         | person                    |                                                |                             |
        |         | begin repeat       | adult                     | Select a representative                        |                             |
        |         | select one ${name} | adult_name                | Choose a name                                  | ${age} > 18                 |
        |         | end repeat         | adult                     |                                                |                             |
        |         | end repeat         | household                 |                                                |                             |
        """
        self.assertPyxformXform(
            name="data",
            id_string="some-id",
            md=xlsform_md,
            xml__contains=['<itemset nodeset="../../person[ ./age  &gt; 18]">'],
        )

    def test_choice_from_previous_repeat_answers_in_nested_repeat_uses_current(self):
        """
        Select one choices from previous repeat answers within a nested repeat should use current if a sibling node of a select is used
        """
        xlsform_md = """
        | survey  |                    |                           |                                                |                             |
        |         | type               | name                      | label                                          | choice_filter               |
        |         | text               | enumerators_name          | Enter enumerators name                         |                             |
        |         | begin repeat       | household_rep             | Household Repeat                               |                             |
        |         | integer            | household_id              | Enter household ID                             |                             |
        |         | begin repeat       | household_mem_rep         | Household member repeat                        |                             |
        |         | text               | name                      | Enter name of a household member               |                             |
        |         | integer            | age                       | Enter age of the household member              |                             |
        |         | end repeat         | household_mem_rep         |                                                |                             |
        |         | begin repeat       | selected                  | Select a representative                        |                             |
        |         | integer            | target_min_age            | Minimum age requirement                        |                             |
        |         | select one ${name} | selected_name             | Choose a name                                  | ${age} > ${target_min_age}  |
        |         | end repeat         | selected                  |                                                |                             |
        |         | end repeat         | household_rep             |                                                |                             |
        """
        self.assertPyxformXform(
            name="data",
            id_string="some-id",
            md=xlsform_md,
            xml__contains=[
                '<itemset nodeset="../../household_mem_rep[ ./age  &gt;  current()/../target_min_age ]">',
            ],
        )

    def test_indexed_repeat_regular_calculation_relative_path_exception(self):
        """Test relative path exception (absolute path) in indexed-repeat() using regular calculation."""
        self.assertPyxformXform(
            name="data",
            title="regular calculation indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |           |                                  |                                              |
                |         | type           | name      | label                            | calculation                                  |
                |         | begin_repeat   | person    | Person                           |                                              |
                |         | integer        | pos       |                                  | position(..)                                 |
                |         | text           | name      | Enter name                       |                                              |
                |         | text           | prev_name | Name in previous repeat instance | indexed-repeat(${name}, ${person}, ${pos}-1) |
                |         | end repeat     |           |                                  |                                              |
            """,  # noqa pylint: disable=line-too-long
            model__contains=[
                """<bind calculate="indexed-repeat( /data/person/name ,  /data/person ,  ../pos -1)" nodeset="/data/person/prev_name" type="string"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_indexed_repeat_dynamic_default_relative_path_exception(self):
        """Test relative path exception (absolute path) in indexed-repeat() using dynamic default."""
        self.assertPyxformXform(
            name="data",
            title="dynamic default indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |           |                                  |                                                    |
                |         | type           | name      | label                            | default                                            |
                |         | begin_repeat   | person    | Person                           |                                                    |
                |         | text           | name      | Enter name                       |                                                    |
                |         | text           | prev_name | Name in previous repeat instance | indexed-repeat(${name}, ${person}, position(..)-1) |
                |         | end repeat     |           |                                  |                                                    |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<setvalue event="odk-instance-first-load odk-new-repeat" ref="/data/person/prev_name" value="indexed-repeat( /data/person/name ,  /data/person , position(..)-1)"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_indexed_repeat_nested_repeat_relative_path_exception(self):
        """Test relative path exception (absolute path) in indexed-repeat() using nested repeat."""
        self.assertPyxformXform(
            name="data",
            title="In nested repeat, indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |                |                                                        |                                                     |
                |         | type           | name           | label                                                  | default                                             |
                |         | begin_repeat   | family         | Family                                                 |                                                     |
                |         | integer        | members_number | How many members in this family?                       |                                                     |
                |         | begin_repeat   | person         | Person                                                 |                                                     |
                |         | text           | name           | Enter name                                             |                                                     |
                |         | text           | prev_name      | Non-sensible previous name in first family, 2nd person | indexed-repeat(${name}, ${family}, 1, ${person}, 2) |
                |         | end repeat     |                |                                                        |                                                     |
                |         | end repeat     |                |                                                        |                                                     |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<setvalue event="odk-instance-first-load odk-new-repeat" ref="/data/family/person/prev_name" value="indexed-repeat( /data/family/person/name ,  /data/family , 1,  /data/family/person , 2)"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_indexed_repeat_math_expression_nested_repeat_relative_path_exception(
        self,
    ):
        """Test relative path exception (absolute path) in indexed-repeat() with math expression using nested repeat."""
        self.assertPyxformXform(
            name="data",
            title="In nested repeat, indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |                |                                  |                                                        |
                |         | type           | name           | label                            | calculation                                            |
                |         | begin_repeat   | family         | Family                           |                                                        |
                |         | integer        | members_number | How many members in this family? |                                                        |
                |         | begin_repeat   | person         | Person                           |                                                        |
                |         | text           | name           | Enter name                       |                                                        |
                |         | integer        | age            | Enter age                        |                                                        |
                |         | text           | prev_name      | Expression label                 | 7 * indexed-repeat(${age}, ${family}, 1, ${person}, 2) |
                |         | end repeat     |                |                                  |                                                        |
                |         | end repeat     |                |                                  |                                                        |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<bind calculate="7 * indexed-repeat( /data/family/person/age ,  /data/family , 1,  /data/family/person , 2)" nodeset="/data/family/person/prev_name" type="string"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_multiple_indexed_repeat_in_expression_nested_repeat_relative_path_exception(
        self,
    ):
        """Test relative path exception (absolute path) in multiple indexed-repeat() inside an expression using nested repeat."""
        self.assertPyxformXform(
            name="data",
            title="In nested repeat, indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |                |                                  |                                                                                                                 |
                |         | type           | name           | label                            | required                                                                                                        |
                |         | begin_repeat   | family         | Family                           |                                                                                                                 |
                |         | integer        | members_number | How many members in this family? |                                                                                                                 |
                |         | begin_repeat   | person         | Person                           |                                                                                                                 |
                |         | text           | name           | Enter name                       |                                                                                                                 |
                |         | integer        | age            | Enter age                        |                                                                                                                 |
                |         | text           | prev_name      | Expression label                 | concat(indexed-repeat(${name}, ${family}, 1, ${person}, 2), indexed-repeat(${age}, ${family}, 1, ${person}, 2)) |
                |         | end repeat     |                |                                  |                                                                                                                 |
                |         | end repeat     |                |                                  |                                                                                                                 |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<bind nodeset="/data/family/person/prev_name" required="concat(indexed-repeat( /data/family/person/name ,  /data/family , 1,  /data/family/person , 2), indexed-repeat( /data/family/person/age ,  /data/family , 1,  /data/family/person , 2))" type="string"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_mixed_variables_and_indexed_repeat_in_expression_text_type_nested_repeat_relative_path_exception(
        self,
    ):
        """Test relative path exception (absolute path) in an expression contains variables and indexed-repeat() in a text type using nested repeat."""
        self.assertPyxformXform(
            name="data",
            title="In nested repeat, indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |                |                                  |                                                                                                                 |
                |         | type           | name           | label                            | calculation                                                                                                        |
                |         | begin_repeat   | family         | Family                           |                                                                                                                 |
                |         | integer        | members_number | How many members in this family? |                                                                                                                 |
                |         | begin_repeat   | person         | Person                           |                                                                                                                 |
                |         | text           | name           | Enter name                       |                                                                                                                 |
                |         | integer        | age            | Enter age                        |                                                                                                                 |
                |         | text           | prev_name      | Expression label                 | concat(${name}, indexed-repeat(${age}, ${family}, 1, ${person}, 2), ${age})                                     |
                |         | end repeat     |                |                                  |                                                                                                                 |
                |         | end repeat     |                |                                  |                                                                                                                 |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<bind calculate="concat( ../name , indexed-repeat( /data/family/person/age ,  /data/family , 1,  /data/family/person , 2),  ../age )" nodeset="/data/family/person/prev_name" type="string"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_mixed_variables_and_indexed_repeat_in_expression_integer_type_nested_repeat_relative_path_exception(
        self,
    ):
        """Test relative path exception (absolute path) in an expression contains variables and indexed-repeat() in an integer type using nested repeat."""
        self.assertPyxformXform(
            name="data",
            title="In nested repeat, indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |          |                        |                                                                             |
                |         | type           | name     | label                  | default                                                                     |
                |         | begin_group    | page     |                        |                                                                             |
                |         | begin_repeat   | bp_rg    |                        |                                                                             |
                |         | integer        | bp_row   | Repeating group entry  |                                                                             |
                |         | text           | bp_pos   | Position               |                                                                             |
                |         | integer        | bp_sys   | Systolic pressure      |                                                                             |
                |         | integer        | bp_dia   | Diastolic pressure     | if(${bp_row} = 1, '',  indexed-repeat(${bp_dia}, ${bp_rg}, ${bp_row} - 1))  |
                |         | end repeat     |          |                        |                                                                             |
                |         | end group      |          |                        |                                                                             |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<setvalue event="odk-instance-first-load odk-new-repeat" ref="/data/page/bp_rg/bp_dia" value="if( ../bp_row  = 1, '', indexed-repeat( /data/page/bp_rg/bp_dia ,  /data/page/bp_rg ,  ../bp_row  - 1))"/>"""  # noqa pylint: disable=line-too-long
            ],
        )

    def test_indexed_repeat_math_expression_with_double_variable_in_nested_repeat_relative_path_exception(
        self,
    ):
        """Test relative path exception (absolute path) in indexed-repeat() with math expression and double variable using nested repeat."""
        self.assertPyxformXform(
            name="data",
            title="In nested repeat, indexed-repeat 1st, 2nd, 4th, and 6th argument is using absolute path",
            md="""
                | survey  |                |                |                                  |                                                             |
                |         | type           | name           | label                            | relevant                                                    |
                |         | begin_repeat   | family         | Family                           |                                                             |
                |         | integer        | members_number | How many members in this family? |                                                             |
                |         | begin_repeat   | person         | Person                           |                                                             |
                |         | text           | name           | Enter name                       |                                                             |
                |         | integer        | age            | Enter age                        |                                                             |
                |         | text           | prev_name      | Expression label                 | ${age} > indexed-repeat(${age}, ${family}, 1, ${person}, 2) |
                |         | end repeat     |                |                                  |                                                             |
                |         | end repeat     |                |                                  |                                                             |
            """,  # noqa pylint: disable=line-too-long
            xml__contains=[
                """<bind nodeset="/data/family/person/prev_name" relevant=" ../age  &gt; indexed-repeat( /data/family/person/age ,  /data/family , 1,  /data/family/person , 2)" type="string"/>"""  # noqa pylint: disable=line-too-long
            ],
        )
