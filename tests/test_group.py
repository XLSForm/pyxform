"""
Test groups.
"""

from unittest import TestCase

from pyxform.builder import create_survey_element_from_dict
from pyxform.validators.pyxform import unique_names
from pyxform.xls2json import SURVEY_001, SURVEY_002
from pyxform.xls2xform import convert

from tests.pyxform_test_case import PyxformTestCase


class TestGroupOutput(PyxformTestCase):
    """
    Test output for groups.
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

    def test_table_list_appearance(self):
        md = """
        | survey  |
        | | type              | name       | label     | hint       | appearance         |
        | | begin_group       | tablelist1 | Table_Y_N |            | table-list minimal |
        | | select_one yes_no | options1a  | Q1        | first row! |                    |
        | | select_one yes_no | options1b  | Q2        |            |                    |
        | | end_group         |            |           |            |                    |
        | choices |
        | | list_name | name | label |
        | | yes_no    | yes  | Yes   |
        """
        xml_contains = """
    <group appearance="field-list minimal" ref="/table-list-appearance-mod/tablelist1">
      <input ref="/table-list-appearance-mod/tablelist1/generated_table_list_label_2">
        <label>Table_Y_N</label>
      </input>
      <select1 appearance="label" ref="/table-list-appearance-mod/tablelist1/reserved_name_for_field_list_labels_3">
        <label> </label>
        <itemset nodeset="instance('yes_no')/root/item">
          <value ref="name"/>
          <label ref="label"/>
        </itemset>
      </select1>
      <select1 appearance="list-nolabel" ref="/table-list-appearance-mod/tablelist1/options1a">
        <label>Q1</label>
        <hint>first row!</hint>
""".strip()
        self.assertPyxformXform(
            name="table-list-appearance-mod",
            md=md,
            xml__contains=[xml_contains],
        )


class TestGroupParsing(PyxformTestCase):
    def test_names__group_basic_case__ok(self):
        """Should find that a single unique group name is ok."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__group_different_names_same_context__ok(self):
        """Should find that groups with unique names in the same context is ok."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | g2   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__group_same_as_group_in_different_group_context__ok(self):
        """Should find that a group name can be the same as another group in a different context."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | g2   | G2    |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__group_same_as_group_in_different_repeat_context__ok(self):
        """Should find that a group name can be the same as another group in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | text         | q1   | Q1    |
        | | end group    |      |       |
        | | begin repeat | r1   | R1    |
        | | begin group  | g1   | G1    |
        | | text         | q1   | Q1    |
        | | end group    |      |       |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__group_same_as_repeat_in_different_group_context__ok(self):
        """Should find that a repeat name can be the same as a group in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | begin repeat | g2   | G2    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | end group    |      |       |
        | | begin group  | g2   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__group_same_as_repeat_in_different_repeat_context__ok(self):
        """Should find that a repeat name can be the same as a group in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | begin repeat | g2   | G2    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | end repeat   |      |       |
        | | begin group  | g2   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__group_same_as_survey_root__ok(self):
        """Should find that a group name can be the same as the survey root."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | data | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            name="data",
            warnings_count=0,
        )

    def test_names__group_same_as_survey_root_case_insensitive__ok(self):
        """Should find that a group name can be the same (CI) as the survey root."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | DATA | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            name="data",
            warnings_count=0,
        )

    def test_names__group_same_as_group_in_same_context_in_survey__error(self):
        """Should find that a duplicate group name raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | g1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=5, value="g1")],
        )

    def test_names__group_same_as_repeat_in_same_context_in_survey__error(self):
        """Should find that a duplicate group name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | g1   | G1    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | begin group  | g1   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=5, value="g1")],
        )

    def test_names__group_same_as_group_in_same_context_in_group__error(self):
        """Should find that a duplicate group name raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | begin group | g2   | G2    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | g2   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=6, value="g2")],
        )

    def test_names__group_same_as_repeat_in_same_context_in_group__error(self):
        """Should find that a duplicate group name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | begin repeat | g2   | G2    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | begin group  | g2   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=6, value="g2")],
        )

    def test_names__group_same_as_group_in_same_context_in_repeat__error(self):
        """Should find that a duplicate group name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | begin group  | g2   | G2    |
        | | text         | q1   | Q1    |
        | | end group    |      |       |
        | | begin group  | g2   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=6, value="g2")],
        )

    def test_names__group_same_as_repeat_in_same_context_in_repeat__error(self):
        """Should find that a duplicate group name raises an error."""
        md = """
        | survey |
        | | type          | name | label |
        | | begin repeat  | r1   | R1    |
        | | begin repeat  | g2   | G2    |
        | | text          | q1   | Q1    |
        | | end repeat    |      |       |
        | | begin group   | g2   | G2    |
        | | text          | q2   | Q2    |
        | | end group     |      |       |
        | | end repeat    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=6, value="g2")],
        )

    def test_names__group_same_as_group_in_same_context_in_survey__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate group name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | G1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=5, value="G1")]
        )

    def test_names__group_same_as_repeat_in_same_context_in_survey__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate group name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | G1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=5, value="G1")]
        )

    def test_names__group_same_as_group_in_same_context_in_group__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate group name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | begin group | g2   | G2    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | begin group | G2   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=6, value="G2")]
        )

    def test_names__group_same_as_repeat_in_same_context_in_group__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate group name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | begin repeat | g2   | G2    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | begin group  | G2   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=6, value="G2")]
        )

    def test_names__group_same_as_group_in_same_context_in_repeat__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate group name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | begin group  | g2   | G2    |
        | | text         | q1   | Q1    |
        | | end group    |      |       |
        | | begin group  | G2   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=6, value="G2")]
        )

    def test_names__group_same_as_repeat_in_same_context_in_repeat__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate group name (CI) raises a warning."""
        md = """
        | survey |
        | | type          | name | label |
        | | begin repeat  | r1   | R1    |
        | | begin repeat  | g2   | G2    |
        | | text          | q1   | Q1    |
        | | end repeat    |      |       |
        | | begin group   | G2   | G2    |
        | | text          | q2   | Q2    |
        | | end group     |      |       |
        | | end repeat    |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=6, value="G2")]
        )

    def test_group__no_end_error__no_name(self):
        """Should raise an error if there is a "begin group" with no "end group" and no name."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | begin group |      | G1    |
        |        | text        | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=["[row : 2] Question or group with no name."],
        )

    def test_group__no_end_error(self):
        """Should raise an error if there is a "begin group" with no "end group"."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | begin group | g1   | G1    |
        |        | text        | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[SURVEY_002.format(row=2, type="group", name="g1")],
        )

    def test_group__no_end_error__different_end_type(self):
        """Should raise an error if there is a "begin group" with no "end group"."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | begin group | g1   | G1    |
        |        | text        | q1   | Q1    |
        |        | end repeat  |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[SURVEY_001.format(row=4, type="repeat")],
        )

    def test_group__no_end_error__with_another_closed_group(self):
        """Should raise an error if there is a "begin group" with no "end group"."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | begin group | g1   | G1    |
        |        | begin group | g2   | G2    |
        |        | text        | q1   | Q1    |
        |        | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[SURVEY_002.format(row=2, type="group", name="g1")],
        )

    def test_group__no_begin_error(self):
        """Should raise an error if there is a "end group" with no "begin group"."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | text        | q1   | Q1    |
        |        | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[SURVEY_001.format(row=3, type="group")],
        )

    def test_group__no_begin_error__with_name(self):
        """Should raise an error if there is a "end group" with no "begin group"."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | text        | q1   | Q1    |
        |        | end group   | g1   |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[SURVEY_001.format(row=3, type="group", name="g1")],
        )

    def test_group__no_begin_error__with_another_closed_group(self):
        """Should raise an error if there is a "end group" with no "begin group"."""
        md = """
        | survey |
        |        | type        | name | label |
        |        | begin group | g1   | G1    |
        |        | text        | q1   | Q1    |
        |        | end group   |      |       |
        |        | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                SURVEY_001.format(
                    row=5,
                    type="group",
                )
            ],
        )

    def test_group__no_begin_error__with_another_closed_repeat(self):
        """Should raise an error if there is a "end group" with no "begin group"."""
        md = """
        | survey |
        |        | type         | name | label |
        |        | begin repeat | g1   | G1    |
        |        | text         | q1   | Q1    |
        |        | end group    |      |       |
        |        | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[SURVEY_001.format(row=4, type="group")],
        )

    def test_empty_group__no_question__error(self):
        """Should raise an error for an empty group with no questions."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=True,  # Error about empty groups is from Validate only.
            odk_validate_error__contains=[
                "Group has no children! Group: ${g1}. The XML is invalid."
            ],
        )

    def test_empty_group__no_question_control__error(self):
        """Should raise an error for an empty group with no question controls."""
        md = """
        | survey |
        | | type        | name | label | calculation |
        | | begin group | g1   | G1    |             |
        | | text        | q1   |       | 0 + 0       |
        | | end group   |      |       |             |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=True,  # Error about empty groups is from Validate only.
            odk_validate_error__contains=[
                "Group has no children! Group: ${g1}. The XML is invalid."
            ],
        )

    def test_unlabeled_group(self):
        self.assertPyxformXform(
            md="""
            | survey |
            | | type        | name     | label   |
            | | begin_group | my-group |         |
            | | text        | my-text  | my-text |
            | | end_group   |          |         |
            """,
            warnings_count=0,
            xml__xpath_match=[
                """
                /h:html/h:body/x:group[
                  @ref = '/test_name/my-group'
                ]
                """
            ],
        )

    def test_unlabeled_group_alternate_syntax(self):
        self.assertPyxformXform(
            md="""
            | survey |
            | | type        | name     | label::English (en) |
            | | begin group | my-group |                     |
            | | text        | my-text  | my-text             |
            | | end group   |          |                     |
            """,
            warnings_count=0,
            xml__xpath_match=[
                """
                /h:html/h:body/x:group[
                  @ref = '/test_name/my-group'
                ]
                """
            ],
        )

class TestGroupInternalRepresentations(TestCase):
    maxDiff = None

    def test_survey_to_json_output(self):
        """Should find that the survey.to_json_dict output remains consistent."""
        md = """
        | survey |
        | | type         | name         | label::English (en)                |
        | | text         | family_name  | What's your family name?           |
        | | begin group  | father       | Father                             |
        | | phone number | phone_number | What's your father's phone number? |
        | | integer      | age          | How old is your father?            |
        | | end group    |              |                                    |

        | settings |
        | | id_string |
        | | group     |
        """
        observed = convert(xlsform=md, form_name="group")._survey.to_json_dict()
        expected = {
            "name": "group",
            "title": "group",
            "id_string": "group",
            "sms_keyword": "group",
            "default_language": "default",
            "type": "survey",
            "children": [
                {
                    "name": "family_name",
                    "type": "text",
                    "label": {"English (en)": "What's your family name?"},
                },
                {
                    "name": "father",
                    "type": "group",
                    "label": {"English (en)": "Father"},
                    "children": [
                        {
                            "name": "phone_number",
                            "type": "phone number",
                            "label": {
                                "English (en)": "What's your father's phone number?"
                            },
                        },
                        {
                            "name": "age",
                            "type": "integer",
                            "label": {"English (en)": "How old is your father?"},
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
        }
        self.assertEqual(expected, observed)

    def test_to_json_round_trip(self):
        """Should find that survey.to_json_dict output can be re-used to build the survey."""
        md = """
        | survey |
        | | type         | name         | label::English (en)                |
        | | text         | family_name  | What's your family name?           |
        | | begin group  | father       | Father                             |
        | | phone number | phone_number | What's your father's phone number? |
        | | integer      | age          | How old is your father?            |
        | | end group    |              |                                    |

        | settings |
        | | id_string |
        | | group     |
        """
        expected = convert(xlsform=md, form_name="group")._survey.to_json_dict()
        observed = create_survey_element_from_dict(expected).to_json_dict()
        self.assertEqual(expected, observed)
