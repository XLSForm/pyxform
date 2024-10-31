"""
Test XLSForm sheet names.
"""

from pyxform.validators.pyxform import choices as vc

from tests.pyxform_test_case import PyxformTestCase
from tests.utils import prep_for_xml_contains
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


class InvalidSurveyColumnsTests(PyxformTestCase):
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
            name="mixedcasecolumns",
            md="""
            | Survey |         |         |               |
            |        | Type    | name    | Label         |
            |        | text    | Name    | the name      |
            |        | integer | age     | the age       |
            |        | text    | gender  | the gender    |
            """,
        )


class InvalidChoiceSheetColumnsTests(PyxformTestCase):
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
            error__contains=[vc.INVALID_NAME.format(row=2)],
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


class AliasesTests(PyxformTestCase):
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


''' # uncomment when re-implemented
    # TODO: test that this fails for the correct reason
    def test_conflicting_aliased_values_raises_error(self):
        # example:
        # an xlsform has {"name": "q_name", "value": "q_value"}
        # should not compile because "name" and "value" columns are aliases

        self.assertPyxformXform(
            # debug=True,
            name="aliases",
            md="""
            | survey |      |        |         |            |
            |        | type | name   | value   | label      |
            |        | text | q_name | q_value | Question 1 |
            """,
            errored=True,
        )
'''
