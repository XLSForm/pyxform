"""
Test XLSForm sheet names.
"""

from collections.abc import Container
from dataclasses import dataclass
from unittest import skip

from pyxform import constants
from pyxform.errors import PyXFormError
from pyxform.parsing.sheet_headers import (
    INVALID_DUPLICATE,
    INVALID_HEADER,
    INVALID_MISSING_REQUIRED,
    dealias_and_group_headers,
    process_header,
    process_row,
    to_snake_case,
)
from pyxform.validators.pyxform import choices as vc
from pyxform.xls2xform import convert

from tests.pyxform_test_case import PyxformTestCase
from tests.utils import prep_for_xml_contains
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq
from tests.xpath_helpers.settings import xps


class TestSettingsColumns(PyxformTestCase):
    def test_case_insensitive_form_id_form_title(self):
        """Should find that settings column headers are case insensitive."""
        # Motivation for case insensitivity https://github.com/XLSForm/pyxform/issues/738
        # but also https://github.com/XLSForm/pyxform/issues/138
        md = """
        | settings |
        |          | Form_ID | Form_Title |
        |          | My Form | Welcome!   |
        | survey |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[xps.form_title("Welcome!"), xps.form_id("My Form")],
        )

    def test_form_id_variant(self):
        md = """
        | survey   |      |             |       |
        |          | type | name        | label |
        |          | text | member_name | name  |
        | settings |                                   |                        |             |
        |          | id_string                         | version                | form_id     |
        |          | get_option_from_two_repeat_answer | vWvvk3GYzjXcJQyvTWELej | AUTO-v2-jef |
        """
        self.assertPyxformXform(
            md=md,
            # setting 'id_string' is ignored.
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance/x:test_name[
                    @id='AUTO-v2-jef'
                    and @version='vWvvk3GYzjXcJQyvTWELej'
                  ]
                """
            ],
        )


class TestSurveyColumns(PyxformTestCase):
    """
    Invalid survey column tests
    """

    def test_missing_name(self):
        """
        every question needs a name (or alias of name)
        """
        self.assertPyxformXform(
            name="invalidcols",
            ss_structure={"survey": [{"type": "text", "label": "label"}]},
            errored=True,
            error__contains=["no name"],
        )

    def test_missing_name_but_has_alias_of_name(self):
        self.assertPyxformXform(
            name="invalidcols",
            ss_structure={"survey": [{"value": "q1", "type": "text", "label": "label"}]},
        )

    def test_label_or_hint__must_be_provided(self):
        self.assertPyxformXform(
            name="invalidcols",
            ss_structure={"survey": [{"type": "text", "name": "q1"}]},
            errored=True,
            error__contains=["no label or hint"],
        )

    def test_label_node_added_when_hint_given_but_no_label_value(self):
        """Should output a label node even if no label is specified."""
        expected = """
          <input ref="/data/a">
            <label/>
            <hint>h</hint>
          </input>
          <input ref="/data/b">
            <label>l</label>
          </input>
          <input ref="/data/c">
            <label ref="jr:itext('/data/c:label')"/>
          </input>
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |      |       |              |      |
            |        | type | name | label | media::image | hint |
            |        | text | a    |       |              | h    |
            |        | text | b    | l     |              |      |
            |        | text | c    |       | m.png        |      |
            """,
            xml__contains=prep_for_xml_contains(expected),
        )

    def test_big_image_invalid_if_no_image(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |      |                  |
            |        | type | name | media::big-image |
            |        | text | c    | m.png            |
            """,
            errored=True,
            error__contains=["must also specify an image"],
        )

    def test_media_column__is_ignored(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |      |       |
            |        | type | name | media |
            |        | text | c    | m.png |
            """,
            xml__excludes=["m.png"],
        )

    def test_column_case(self):
        """
        Ensure that column name is case insensitive
        """
        self.assertPyxformXform(
            md="""
            | Survey |         |         |               |
            |        | Type    | name    | Label         |
            |        | text    | Name    | the name      |
            |        | integer | age     | the age       |
            |        | text    | gender  | the gender    |
            """,
        )

    def test_label_caps_alternatives(self):
        """
        re: https://github.com/SEL-Columbia/pyxform/issues/76
        Capitalization of 'label' column can lead to confusing errors.
        """

        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | label |
            |        | note | q    | Q     |
            """,
            xml__xpath_match=["/h:html/h:body/x:input[./x:label='Q']"],
        )
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | Label |
            |        | note | q    | Q     |
            """,
            xml__xpath_match=["/h:html/h:body/x:input[./x:label='Q']"],
        )

    def test_calculate_alias(self):
        self.assertPyxformXform(
            name="calculatealias",
            md="""
            | survey |           |         |         |               |
            |        | type      | name    | label   | calculate     |
            |        | decimal   | amount  | Counter |               |
            |        | calculate | doubled | Doubled | ${amount} * 2 |
            """,
        )

    def test_missing_survey_headers(self):
        self.assertPyxformXform(
            md="""
            | survey |                 |    |
            |        | select_one list | S1 |
            """,
            errored=True,
            error__contains=[
                INVALID_MISSING_REQUIRED.format(sheet_name="survey", missing="'type'")
            ],
        )


class TestChoicesColumns(PyxformTestCase):
    """
    Invalid choice sheet column tests
    """

    @staticmethod
    def _simple_choice_ss(choice_sheet=None):
        """
        Return simple choices sheet
        """

        if choice_sheet is None:
            choice_sheet = []
        return {
            "survey": [
                {
                    "type": "select_one l1",
                    "name": "l1choice",
                    "label": "select one from list l1",
                }
            ],
            "choices": choice_sheet,
        }

    def test_valid_choices_sheet_passes(self):
        """
        Test invalid choices sheet passes
        """

        self.assertPyxformXform(
            name="valid_choices",
            ss_structure=self._simple_choice_ss(
                [
                    {"list_name": "l1", "name": "c1", "label": "choice 1"},
                    {"list_name": "l1", "name": "c2", "label": "choice 2"},
                ]
            ),
        )

    def test_invalid_choices_sheet_fails(self):
        """
        Test invalid choices sheet fails
        """

        self.assertPyxformXform(
            name="missing_name",
            ss_structure=self._simple_choice_ss(
                [
                    {"list_name": "l1", "label": "choice 1"},
                    {"list_name": "l1", "label": "choice 2"},
                ]
            ),
            errored=True,
            error__contains=[
                INVALID_MISSING_REQUIRED.format(sheet_name="choices", missing="'name'")
            ],
        )

    def test_missing_list_name(self):
        """
        Test missing sheet name
        """

        self.assertPyxformXform(
            name="missing_list_name",
            ss_structure=self._simple_choice_ss(
                [
                    {"bad_column": "l1", "name": "l1c1", "label": "choice 1"},
                    {"bad_column": "l1", "name": "l1c1", "label": "choice 2"},
                ]
            ),
            errored=True,
            # some basic keywords that should be in the error:
            error__contains=["choices", "name", "list_name"],
        )

    def test_clear_filename_error_message(self):
        """Test clear filename error message"""
        error_message = "The name 'bad@filename' contains an invalid character '@'. Names must begin with a letter, colon, or underscore. Other characters can include numbers, dashes, and periods."
        self.assertPyxformXform(
            name="bad@filename",
            ss_structure=self._simple_choice_ss(
                [
                    {"list_name": "l1", "name": "c1", "label": "choice 1"},
                    {"list_name": "l1", "name": "c2", "label": "choice 2"},
                ]
            ),
            errored=True,
            error__contains=[error_message],
        )

    def test_missing_choice_headers(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |      |
            |         | type            | label    | name |
            |         | select_one list | S1       | s1   |
            | choices |                 |          |      |
            |         | list            | option a | a    |
            |         | list            | option b | b    |
            """,
            errored=True,
            error__contains=[
                INVALID_MISSING_REQUIRED.format(sheet_name="choices", missing="'name'")
            ],
        )


class TestColumnAliases(PyxformTestCase):
    """
    Aliases Tests
    """

    def test_value_and_name(self):
        """
        confirm that both 'name' and 'value' columns of choice list work
        """
        md = """
        | survey  |               |                |            |
        |         | type          | name           | label      |
        |         | select_one yn | q1             | Question 1 |
        | choices |               |                |            |
        |         | list name     | {name_alias}   | label      |
        |         | yn            | yes            | Yes        |
        |         | yn            | no             | No         |
        """
        for name_alias in ("name", "value"):
            self.assertPyxformXform(
                md=md.format(name_alias=name_alias),
                xml__xpath_match=[
                    xpq.model_instance_item("q1"),
                    xpq.model_instance_bind("q1", "string"),
                    xpq.body_select1_itemset("q1"),
                    xpc.model_instance_choices_label(
                        "yn", (("yes", "Yes"), ("no", "No"))
                    ),
                ],
            )

    def test_conflicting_aliased_values_raises_error(self):
        """Should find that specifying a column and its alias raises an error."""
        self.assertPyxformXform(
            md="""
            | survey |      |        |         |            |
            |        | type | name   | value   | label      |
            |        | text | q_name | q_value | Question 1 |
            """,
            errored=True,
            error__contains=[
                INVALID_DUPLICATE.format(
                    sheet_name="survey", other="name", header="value"
                )
            ],
        )

    # TODO: should warn about duplicate headers but requires xls2json_backends refactoring.
    @skip
    def test_duplicate_header_raises_error(self):
        """Should find that specifying a column more than once raises an error."""
        self.assertPyxformXform(
            md="""
            | survey |      |        |         |            |
            |        | type | name   | name    | label      |
            |        | text | q_name | q_value | Question 1 |
            """,
            errored=True,
            error__contains=[
                INVALID_DUPLICATE.format(sheet_name="survey", other="name", header="name")
            ],
        )

    def test_repeat_count__jr_alias(self):
        """Should find that the old "jr:" alias for repeat_count is recognised."""
        md = """
        | survey |
        |        | type         | name    | label | jr:count |
        |        | begin repeat | a       | 1     | 3        |
        |        | text         | b       | 2     |          |
        |        | end repeat   | a       |       |          |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model/x:bind[
                     @nodeset='/test_name/a_count' and @calculate='3'
                   ]
                """
            ],
        )


class TestHeaderProcessing(PyxformTestCase):
    def test_to_snake_case(self):
        """Should find input strings are snake_cased."""
        cases = (
            # Lowercased
            ("name", "name"),
            ("NAME", "name"),
            ("Name", "name"),
            # Snaked
            ("constraint_message", "constraint_message"),
            ("constraint message", "constraint_message"),
            # Collapse/strip spaces
            ("constraint  message", "constraint_message"),
            (" constraint message ", "constraint_message"),
            # Edge cases
            ("", ""),
            (" ", ""),
            ("@", "@"),
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(case[1], to_snake_case(case[0]))

    def test_process_header(self):
        """Should find the header input is processed per each case expectation."""

        @dataclass(slots=True)
        class Case:
            header: str
            use_double_colon: bool
            header_aliases: dict[str, str | tuple[str, ...]]
            header_columns: Container[str]

        # key is expected value, values are inputs that result in that value.
        case_groups = {
            # # # # # # # # # #
            # No delimiter.
            # # # # # # # # # #
            ("my_col", ("my_col",)): (
                Case("my_col", False, {}, {"my_col"}),
                Case("my col", False, {}, {"my_col"}),
                Case("my_Col", False, {}, {"my_col"}),
                Case("MY Col", False, {}, {"my_col"}),
                Case("my_col", False, {"my_col": "my_col"}, {}),
                Case("my col", False, {"my_col": "my_col"}, {}),
                Case("my_Col", False, {"my_col": "my_col"}, {}),
                Case("MY Col", False, {"my_col": "my_col"}, {}),
                # has jr: prefix is an alias.
                Case("jr:my_col", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:my_Col", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:my col", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:MY Col", False, {"jr:my_col": "my_col"}, {}),
            ),
            # header_aliases is a tuple.
            (("bind", "my_col"), ("bind", "my_col")): (
                Case("my_col", False, {"my_col": ("bind", "my_col")}, {}),
                Case("my_Col", False, {"my_col": ("bind", "my_col")}, {}),
                Case("my col", False, {"my_col": ("bind", "my_col")}, {}),
                Case("MY Col", False, {"my_col": ("bind", "my_col")}, {}),
            ),
            # jr: prefix is an expected column.
            ("jr:my_col", ("jr:my_col",)): (
                Case("jr:my_col", False, {}, {"jr:my_col"}),
                Case("jr:my_Col", False, {}, {"jr:my_col"}),
                Case("jr:my col", False, {}, {"jr:my_col"}),
                Case("jr:MY Col", False, {}, {"jr:my_col"}),
            ),
            # # # # # # # # # #
            # Has delimiter.
            # # # # # # # # # #
            ("my_col", ("my_col", "English (en)")): (
                # Has :: delimiter
                Case("my_col::English (en)", False, {}, {"my_col"}),
                Case("my col::English (en)", False, {}, {"my_col"}),
                Case("my_Col::English (en)", False, {}, {"my_col"}),
                Case("MY Col::English (en)", False, {}, {"my_col"}),
                Case("my_col::English (en)", False, {"my_col": "my_col"}, {}),
                Case("my col::English (en)", False, {"my_col": "my_col"}, {}),
                Case("my_Col::English (en)", False, {"my_col": "my_col"}, {}),
                Case("MY Col::English (en)", False, {"my_col": "my_col"}, {}),
                # + has jr: prefix is an alias.
                Case("jr:my_col::English (en)", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:my_Col::English (en)", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:my col::English (en)", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:MY Col::English (en)", False, {"jr:my_col": "my_col"}, {}),
                # Has : delimiter
                Case("my_col:English (en)", False, {}, {"my_col"}),
                Case("my col:English (en)", False, {}, {"my_col"}),
                Case("my_Col:English (en)", False, {}, {"my_col"}),
                Case("MY Col:English (en)", False, {}, {"my_col"}),
                Case("my_col:English (en)", False, {"my_col": "my_col"}, {}),
                Case("my col:English (en)", False, {"my_col": "my_col"}, {}),
                Case("my_Col:English (en)", False, {"my_col": "my_col"}, {}),
                Case("MY Col:English (en)", False, {"my_col": "my_col"}, {}),
                # + has jr: prefix is an alias.
                Case("jr:my_col:English (en)", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:my_Col:English (en)", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:my col:English (en)", False, {"jr:my_col": "my_col"}, {}),
                Case("jr:MY Col:English (en)", False, {"jr:my_col": "my_col"}, {}),
            ),
            # header_aliases is a tuple.
            (("bind", "my_col"), ("bind", "my_col", "English (en)")): (
                # Has :: delimiter
                Case("my_col::English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                Case("my_Col::English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                Case("my col::English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                Case("MY Col::English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                # Has : delimiter
                Case("my_col:English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                Case("my_Col:English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                Case("my col:English (en)", False, {"my_col": ("bind", "my_col")}, {}),
                Case("MY Col:English (en)", False, {"my_col": ("bind", "my_col")}, {}),
            ),
            # jr: prefix is an expected column.
            ("jr:my_col", ("jr:my_col", "English (en)")): (
                # Has :: delimiter
                Case("jr:my_col::English (en)", False, {}, {"jr:my_col"}),
                Case("jr:my_Col::English (en)", False, {}, {"jr:my_col"}),
                Case("jr:my col::English (en)", False, {}, {"jr:my_col"}),
                Case("jr:MY Col::English (en)", False, {}, {"jr:my_col"}),
                # Has : delimiter
                Case("jr:my_col:English (en)", False, {}, {"jr:my_col"}),
                Case("jr:my_Col:English (en)", False, {}, {"jr:my_col"}),
                Case("jr:my col:English (en)", False, {}, {"jr:my_col"}),
                Case("jr:MY Col:English (en)", False, {}, {"jr:my_col"}),
            ),
            # # # # # # # # # #
            # Unknown columns.
            # # # # # # # # # #
            # No delimiter.
            ("NAME", ("NAME",)): (Case("NAME", False, {}, {}),),
            ("NA_ME", ("NA_ME",)): (Case("NA_ME", False, {}, {}),),
            ("NA Me", ("NA Me",)): (Case("NA Me", False, {}, {}),),
            # Has :: delimiter.
            ("name::English (en)", ("name", "English (en)")): (
                Case("name::English (en)", False, {}, {}),
            ),
            ("NA_ME::English (en)", ("NA_ME", "English (en)")): (
                Case("NA_ME::English (en)", False, {}, {}),
            ),
            ("NA Me::English (en)", ("NA Me", "English (en)")): (
                Case("NA Me::English (en)", False, {}, {}),
            ),
            # Has : delimiter.
            ("name:English (en)", ("name", "English (en)")): (
                Case("name:English (en)", False, {}, {}),
            ),
            ("NA_ME:English (en)", ("NA_ME", "English (en)")): (
                Case("NA_ME:English (en)", False, {}, {}),
            ),
            ("NA Me:English (en)", ("NA Me", "English (en)")): (
                Case("NA Me:English (en)", False, {}, {}),
            ),
            # Has jr: prefix.
            ("jr:NAME", ("jr:NAME",)): (Case("jr:NAME", False, {}, {}),),
            ("jr:NA_ME", ("jr:NA_ME",)): (Case("jr:NA_ME", False, {}, {}),),
            ("jr:NA Me", ("jr:NA Me",)): (Case("jr:NA Me", False, {}, {}),),
        }
        for expected, cases in case_groups.items():
            for case in cases:
                with self.subTest(case=(expected, case)):
                    self.assertEqual(
                        expected,
                        process_header(
                            header=case.header,
                            use_double_colon=case.use_double_colon,
                            header_aliases=case.header_aliases,
                            header_columns=case.header_columns,
                        ),
                    )

    def test_choice_filter_columns_not_normalised(self):
        """Should find that non-XLSForm choices columns are not changed."""
        # choice_filter expressions would break if the extra choices column headers changed.
        md = """
        | survey  |
        |         | type          | name | label | choice_filter |
        |         | text          | q0   | Q0    |               |
        |         | select_one c1 | q1   | Q1    | ${q0} = CF or ${q0} = A_B or ${q0} = Cd or ${q0} = h-I or ${q0} = J.k |
        | choices |
        |         | list name | name | label | CF | A_B | Cd | e f | h-I | J.k |
        |         | c1        | na   | la    | a1 | a2  | a3 | a4  | a5  | a6  |
        |         | c1        | nb   | lb    | b1 | b2  | b3 | b4  | b5  | b6  |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=(
                # Choices instance has valid header keys, but not the invalid one ("e f").
                # The not(*[not(...)]) is to check there are no elements other than those
                # listed, rather than selecting unwanted cases like 'e f', 'e', 'f', etc.
                """
                /h:html/h:head/x:model/x:instance[@id = 'c1']/x:root/x:item[
                  ./x:name = 'na'
                  and not(*[not(
                    local-name()='name'
                    or local-name()='label'
                    or local-name()='CF'
                    or local-name()='A_B'
                    or local-name()='Cd'
                    or local-name()='h-I'
                    or local-name()='J.k'
                  )])
                ]
                """,
            ),
            warnings__contains=(vc.INVALID_HEADER.format(column="e f"),),
        )

    def test_dealias_and_group_headers__use_double_colon_modes(self):
        """Should find headers are split based on whether a double colon is found."""
        cases = (
            # No delimiter
            (
                [{"col1": "val1", "col2": "val2"}],
                (("col1",), ("col2",)),
                ({"col1": "val1", "col2": "val2"},),
            ),
            # Double colon before/after no delimiter
            (
                [{"col1::sep1": "val1", "col2": "val2"}],
                (("col1", "sep1"), ("col2",)),
                ({"col1": {"sep1": "val1"}, "col2": "val2"},),
            ),
            (
                [{"col1": "val1", "col2::sep2": "val2"}],
                (("col1",), ("col2", "sep2")),
                ({"col1": "val1", "col2": {"sep2": "val2"}},),
            ),
            # Single colon before/after no delimiter
            (
                [{"col1:sep1": "val1", "col2": "val2"}],
                (("col1", "sep1"), ("col2",)),
                ({"col1": {"sep1": "val1"}, "col2": "val2"},),
            ),
            (
                [{"col1": "val1", "col2:sep2": "val2"}],
                (("col1",), ("col2", "sep2")),
                ({"col1": "val1", "col2": {"sep2": "val2"}},),
            ),
            # Single colon before/after double
            (
                [{"col1:sep1": "val1", "col2::sep2": "val2"}],
                (("col1:sep1",), ("col2", "sep2")),
                ({"col1:sep1": "val1", "col2": {"sep2": "val2"}},),
            ),
            (
                [{"col1::sep1": "val1", "col2:sep2": "val2"}],
                (("col1", "sep1"), ("col2:sep2",)),
                ({"col1": {"sep1": "val1"}, "col2:sep2": "val2"},),
            ),
            # No delimiter, jr: prefix with single/double colon
            (
                [{"col1": "val1", "jr:col2:sep2": "val2"}],
                (("col1",), ("jr:col2", "sep2")),
                ({"col1": "val1", "jr:col2": {"sep2": "val2"}},),
            ),
            (
                [{"jr:col2:sep2": "val2", "col1": "val1"}],
                (("jr:col2", "sep2"), ("col1",)),
                ({"jr:col2": {"sep2": "val2"}, "col1": "val1"},),
            ),
            (
                [{"col1": "val1", "jr:col2::sep2": "val2"}],
                (("col1",), ("jr:col2", "sep2")),
                ({"col1": "val1", "jr:col2": {"sep2": "val2"}},),
            ),
            (
                [{"jr:col2::sep2": "val2", "col1": "val1"}],
                (("jr:col2", "sep2"), ("col1",)),
                ({"jr:col2": {"sep2": "val2"}, "col1": "val1"},),
            ),
            # Single colon, jr: prefix with single/double colon
            (
                [{"col1:sep1": "val1", "jr:col2:sep2": "val2"}],
                (("col1", "sep1"), ("jr:col2", "sep2")),
                ({"col1": {"sep1": "val1"}, "jr:col2": {"sep2": "val2"}},),
            ),
            (
                [{"jr:col2:sep2": "val2", "col1:sep1": "val1"}],
                (("jr:col2", "sep2"), ("col1", "sep1")),
                ({"jr:col2": {"sep2": "val2"}, "col1": {"sep1": "val1"}},),
            ),
            (
                [{"col1:sep1": "val1", "jr:col2::sep2": "val2"}],
                (("col1:sep1",), ("jr:col2", "sep2")),
                ({"col1:sep1": "val1", "jr:col2": {"sep2": "val2"}},),
            ),
            (
                [{"jr:col2::sep2": "val2", "col1:sep1": "val1"}],
                (("jr:col2", "sep2"), ("col1:sep1",)),
                ({"jr:col2": {"sep2": "val2"}, "col1:sep1": "val1"},),
            ),
            ## Double colon, jr: prefix with single/double colon
            (
                [{"col1::sep1": "val1", "jr:col2:sep2": "val2"}],
                (("col1", "sep1"), ("jr:col2:sep2",)),
                ({"col1": {"sep1": "val1"}, "jr:col2:sep2": "val2"},),
            ),
            (
                [{"jr:col2:sep2": "val2", "col1::sep1": "val1"}],
                (("jr:col2:sep2",), ("col1", "sep1")),
                ({"jr:col2:sep2": "val2", "col1": {"sep1": "val1"}},),
            ),
            (
                [{"col1::sep1": "val1", "jr:col2::sep2": "val2"}],
                (("col1", "sep1"), ("jr:col2", "sep2")),
                ({"col1": {"sep1": "val1"}, "jr:col2": {"sep2": "val2"}},),
            ),
            (
                [{"jr:col2::sep2": "val2", "col1::sep1": "val1"}],
                (("jr:col2", "sep2"), ("col1", "sep1")),
                ({"jr:col2": {"sep2": "val2"}, "col1": {"sep1": "val1"}},),
            ),
        )
        for i, case in enumerate(cases):
            with self.subTest((i, case[0])):
                observed = dealias_and_group_headers(
                    sheet_name="test",
                    sheet_data=case[0],
                    sheet_header=[{k: None for k in case[0][0]}],
                    header_aliases={},
                    header_columns=set(),
                )
                self.assertEqual(case[1], observed.headers)
                self.assertEqual(case[2], observed.data)

    def test_process_row__bad_header_info__unit(self):
        """Should raise an error if incomplete header info is provided."""
        # Unit test for bad sheet_header info received.
        with self.assertRaises(PyXFormError) as err:
            process_row(
                sheet_name="survey",
                row={"a": "b", "c": "d", "e": "f"},
                header_key={"a": ("a",), "c": ("b", "z")},
                default_language=constants.DEFAULT_LANGUAGE_VALUE,
            )
        self.assertEqual(
            INVALID_HEADER.format(sheet_name="survey", header="e"),
            err.exception.args[0],
        )

    def test_process_row__bad_header_info__dict(self):
        """Should raise an error if incomplete header info is provided."""
        # For dict input, sheet_header guess takes first 100 rows, so additional keys in
        # rows beyond that would trigger the error.
        survey_data = [
            {"type": "text", "name": f"q{i}", "label": f"Q{i}"} for i in range(100)
        ]
        survey_data.append({"type": "text", "name": "q101", "label": "Q101", "e": "?"})
        with self.assertRaises(PyXFormError) as err:
            convert(xlsform={"survey": survey_data})
        self.assertEqual(
            INVALID_HEADER.format(sheet_name="survey", header="e"),
            err.exception.args[0],
        )

    def test_process_row__bad_header_info__markdown(self):
        """Should raise an error if incomplete header info is provided."""
        # For markdown (or other) input, could get an error if no header is provided. The
        # expected error "None" is due to the first empty cell: "|        |".
        header = """
        | survey |
        """
        question = """
        |        | text | q{i} | Q{i}  | {e} |
        """
        questions = "\n".join(question.format(i=i, e="") for i in range(100))
        md = "".join((header, questions, question.format(i=101, e="?")))
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=INVALID_HEADER.format(sheet_name="survey", header="None"),
        )

    def test_process_row__bad_header_info__happy_path(self):
        """Should not raise an error if complete header info is provided."""
        # For markdown (or other) input, normally no error due to header gathered during
        # backend processing of properly formatted XLSForms.
        header = """
        | survey |
        |        | type | name | label | e   |
        """
        question = """
        |        | text | q{i} | Q{i}  | {e} |
        """
        questions = "\n".join(question.format(i=i, e="") for i in range(100))
        md = "".join((header, questions, question.format(i=101, e="?")))
        self.assertPyxformXform(md=md)
