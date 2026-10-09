"""Test groups."""

from unittest import TestCase

from pyxform.builder import create_survey_element_from_dict
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.xls2xform import convert

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.group import xpg
from tests.xpath_helpers.questions import xpq


class TestGroupOutput(PyxformTestCase):
    """Test output for groups."""

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
        """Should find that the table-list shortcut applies field-list and list-nolabel."""
        md = """
        | survey  |
        | | type          | name | label | hint       | appearance |
        | | begin_group   | g1   | G1    |            | table-list |
        | | select_one c1 | q1   | Q1    | first row! |            |
        | | select_one c1 | q2   | Q2    |            |            |
        | | end_group     |      |       |            |            |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # Model instance for specified + generated items.
                xpq.model_instance_item("g1"),
                xpq.model_instance_item("g1/x:generated_table_list_label_2"),
                xpq.model_instance_item("g1/x:reserved_name_for_field_list_labels_3"),
                xpq.model_instance_item("g1/x:q1"),
                xpq.model_instance_item("g1/x:q2"),
                # Model bind for specified + generated items.
                xpq.model_instance_bind("g1/generated_table_list_label_2", "string"),
                xpq.model_instance_bind(
                    "g1/reserved_name_for_field_list_labels_3", "string"
                ),
                xpq.model_instance_bind("g1/q1", "string"),
                xpq.model_instance_bind("g1/q2", "string"),
                # Body control group and selects are assigned appearances.
                xpg.group_no_label_appearance("/test_name/g1", "field-list"),
                xpq.body_label_inline(
                    "group/x:input", "g1/generated_table_list_label_2", "G1"
                ),
                xpq.body_group_select1_itemset(
                    "g1", "reserved_name_for_field_list_labels_3", "label"
                ),
                xpq.body_label_inline(
                    "group/x:select1", "g1/reserved_name_for_field_list_labels_3", " "
                ),
                xpq.body_group_select1_itemset("g1", "q1", "list-nolabel"),
                xpq.body_label_inline("group/x:select1", "g1/q1", "Q1"),
                """
                /h:html/h:body/x:group/x:select1[@ref='/test_name/g1/q1']
                  /x:hint[text()='first row!']
                """,
                xpq.body_group_select1_itemset("g1", "q2", "list-nolabel"),
                xpq.body_label_inline("group/x:select1", "g1/q2", "Q2"),
            ],
        )

    def test_table_list_appearance__preserve_additional_appearances(self):
        """Should find that the table-list shortcut keeps any extra appearances."""
        # Currently the documented / supported appearances for groups are 'table-list' and
        # 'field-list', so an extra 'fake' appearance is added to check that anything else
        # will be preserved (without adding confusion as to what is supported).
        md = """
        | survey  |
        | | type          | name | label | hint       | appearance      |
        | | begin_group   | g1   | G1    |            | table-list fake |
        | | select_one c1 | q1   | Q1    | first row! |                 |
        | | select_one c1 | q2   | Q2    |            |                 |
        | | end_group     |      |       |            |                 |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpg.group_no_label_appearance("/test_name/g1", "field-list fake"),
            ],
        )

    def test_group__label__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin_group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end_group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_label_no_translation("/test_name/g1", "G1"),
            ],
        )

    def test_group__no_label__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin_group | g1   |       |
        | | text        | q1   | Q1    |
        | | end_group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_no_label("/test_name/g1"),
            ],
        )

    def test_group__label__translated__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label::English (en) |
        | | begin_group | g1   | G1                  |
        | | text        | q1   | Q1                  |
        | | end_group   |      |                     |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_label_translation("/test_name/g1"),
            ],
        )

    def test_group__no_label__translated__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label::English (en) |
        | | begin_group | g1   |                     |
        | | text        | q1   | Q1                  |
        | | end_group   |      |                     |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_no_label("/test_name/g1"),
            ],
        )

    def test_group__label__appearance__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label | appearance |
        | | begin_group | g1   | G1    | field-list |
        | | text        | q1   | Q1    |            |
        | | end_group   |      |       |            |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_label_no_translation_appearance(
                    "/test_name/g1", "G1", "field-list"
                ),
            ],
        )

    def test_group__no_label__appearance__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label | appearance |
        | | begin_group | g1   |       | field-list |
        | | text        | q1   | Q1    |            |
        | | end_group   |      |       |            |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_no_label_appearance("/test_name/g1", "field-list"),
            ],
        )

    def test_group__label__translated__appearance__ok(self):
        """Should find a group control with a child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label::English (en) | appearance |
        | | begin_group | g1   | G1                  | field-list |
        | | text        | q1   | Q1                  |            |
        | | end_group   |      |                     |            |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_label_translation_appearance("/test_name/g1", "field-list"),
            ],
        )

    def test_group__no_label__translated__appearance__ok(self):
        """Should find a group control with no child `label` element and no warnings."""
        md = """
        | survey |
        | | type        | name | label::English (en) | appearance |
        | | begin_group | g1   |                     | field-list |
        | | text        | q1   | Q1                  |            |
        | | end_group   |      |                     |            |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpg.group_no_label_appearance("/test_name/g1", "field-list"),
            ],
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
            error__contains=[ErrorCode.NAMES_001.value.format(row=5, value="g1")],
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
            error__contains=[ErrorCode.NAMES_001.value.format(row=5, value="g1")],
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
            error__contains=[ErrorCode.NAMES_001.value.format(row=6, value="g2")],
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
            error__contains=[ErrorCode.NAMES_001.value.format(row=6, value="g2")],
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
            error__contains=[ErrorCode.NAMES_001.value.format(row=6, value="g2")],
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
            error__contains=[ErrorCode.NAMES_001.value.format(row=6, value="g2")],
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
            md=md,
            warnings__contains=[ErrorCode.NAMES_002.value.format(row=5, value="G1")],
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
            md=md,
            warnings__contains=[ErrorCode.NAMES_002.value.format(row=5, value="G1")],
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
            md=md,
            warnings__contains=[ErrorCode.NAMES_002.value.format(row=6, value="G2")],
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
            md=md,
            warnings__contains=[ErrorCode.NAMES_002.value.format(row=6, value="G2")],
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
            md=md,
            warnings__contains=[ErrorCode.NAMES_002.value.format(row=6, value="G2")],
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
            md=md,
            warnings__contains=[ErrorCode.NAMES_002.value.format(row=6, value="G2")],
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
            error__contains=[
                ErrorCode.SURVEY_002.value.format(row=2, type="group", name="g1")
            ],
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
            error__contains=[ErrorCode.SURVEY_001.value.format(row=4, type="repeat")],
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
            error__contains=[
                ErrorCode.SURVEY_002.value.format(row=2, type="group", name="g1")
            ],
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
            error__contains=[ErrorCode.SURVEY_001.value.format(row=3, type="group")],
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
            error__contains=[
                ErrorCode.SURVEY_001.value.format(row=3, type="group", name="g1")
            ],
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
                ErrorCode.SURVEY_001.value.format(
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
            error__contains=[ErrorCode.SURVEY_001.value.format(row=4, type="group")],
        )

    def test_group__required__error(self):
        """Should raise an error if 'required' is used on a group."""
        md = """
        | survey |
        |        | type        | name | label | required |
        |        | begin group | g1   | G1    | yes      |
        |        | text        | q1   | Q1    |          |
        |        | end group   |      |       |          |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.SURVEY_011.value.format(row=2)],
        )

    def test_repeat__required__error(self):
        """Should raise an error if 'required' is used on a repeat."""
        md = """
        | survey |
        |        | type         | name | label | required |
        |        | begin repeat | r1   | R1    | yes      |
        |        | text         | q1   | Q1    |          |
        |        | end repeat   |      |       |          |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.SURVEY_011.value.format(row=2)],
        )

    def test_group__required_no__ok(self):
        """Should not raise an error if 'required' is explicitly 'no' on a group."""
        md = """
        | survey |
        |        | type        | name | label | required |
        |        | begin group | g1   | G1    | no       |
        |        | text        | q1   | Q1    |          |
        |        | end group   |      |       |          |
        """
        self.assertPyxformXform(md=md)

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

    def test_group_required_bind__error(self):
        """Should raise an error if a group is built with a required bind."""
        d = {
            "name": "data",
            "title": "data",
            "type": "survey",
            "id_string": "data",
            "children": [
                {
                    "type": "group",
                    "name": "g1",
                    "label": "G1",
                    "bind": {"required": "true()"},
                    "children": [
                        {"type": "text", "name": "q1", "label": "Q1"},
                    ],
                }
            ],
        }
        survey = create_survey_element_from_dict(d)
        with self.assertRaises(PyXFormError):
            survey.xml()
