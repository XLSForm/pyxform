from pyxform.validators.pyxform import choices as vc

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


class ChoicesSheetTest(PyxformTestCase):
    def test_numeric_choice_names__for_static_selects__allowed(self):
        """
        Test numeric choice names for static selects.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |
            |          | type               | name | label |
            |          | select_one choices | a    | A     |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    | One   |
            |          | choices            | 2    | Two   |
            """,
            xml__xpath_match=[
                xpc.model_instance_choices_label("choices", (("1", "One"), ("2", "Two"))),
                xpq.body_select1_itemset("a"),
            ],
        )

    def test_numeric_choice_names__for_dynamic_selects__allowed(self):
        """
        Test numeric choice names for dynamic selects.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |               |
            |          | type               | name | label | choice_filter |
            |          | select_one choices | a    | A     | true()        |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    | One   |
            |          | choices            | 2    | Two   |
            """,
            xml__xpath_match=[
                xpc.model_instance_choices_label("choices", (("1", "One"), ("2", "Two"))),
                xpq.body_select1_itemset("a"),
            ],
        )

    def test_choices_without_labels__for_static_selects__allowed(self):
        """
        Test choices without labels for static selects. Validate will NOT fail.
        """
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |
            |          | type               | name | label |
            |          | select_one choices | a    | A     |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    |       |
            |          | choices            | 2    |       |
            """,
            xml__xpath_match=[
                xpq.body_select1_itemset("a"),
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root[
                  ./x:item/x:name/text() = '1'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                  and
                  ./x:item/x:name/text() = '2'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                ]
                """,
            ],
        )

    def test_choices_without_labels__for_dynamic_selects__allowed_by_pyxform(self):
        """
        Test choices without labels for dynamic selects. Validate will fail.
        """
        # TODO: validate doesn't fail
        self.assertPyxformXform(
            md="""
            | survey   |                    |      |       |               |
            |          | type               | name | label | choice_filter |
            |          | select_one choices | a    | A     | true()        |
            | choices  |                    |      |       |
            |          | list_name          | name | label |
            |          | choices            | 1    |       |
            |          | choices            | 2    |       |
            """,
            xml__xpath_match=[
                xpq.body_select1_itemset("a"),
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root[
                  ./x:item/x:name/text() = '1'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                  and
                  ./x:item/x:name/text() = '2'
                    and not(./x:item/x:label)
                    and not(./x:item/x:itextId)
                ]
                """,
            ],
        )

    def test_choices_extra_columns_output_order_matches_xlsform(self):
        """Should find that element order matches column order."""
        md = """
        | survey   |                    |      |       |
        |          | type               | name | label |
        |          | select_one choices | a    | A     |
        | choices  |                    |      |       |
        |          | list_name          | name | label | geometry                 |
        |          | choices            | 1    |       | 46.5841618 7.0801379 0 0 |
        |          | choices            | 2    |       | 35.8805082 76.515057 0 0 |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root/x:item[
                  ./x:name = ./x:*[text() = '1']
                  and ./x:geometry = ./x:*[text() = '46.5841618 7.0801379 0 0']
                ]
                """,
                """
                /h:html/h:head/x:model/x:instance[@id='choices']/x:root/x:item[
                  ./x:name = ./x:*[text() = '2']
                  and ./x:geometry = ./x:*[text() = '35.8805082 76.515057 0 0']
                ]
                """,
            ],
        )

    def test_unreferenced_lists_included_in_output(self):
        """Should find all specified choice lists in the output, even if unreferenced."""
        md = """
        | survey  |
        |         | type               | name | label |
        |         | select_one choices | a    | A     |
        | choices |
        |         | list_name | name | label |
        |         | choices   | 1    | Y     |
        |         | choices   | 2    | N     |
        |         | choices2  | 1    | Y     |
        |         | choices2  | 2    | N     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_instance_choices_label("choices", (("1", "Y"), ("2", "N"))),
                xpc.model_instance_choices_label("choices2", (("1", "Y"), ("2", "N"))),
            ],
        )

    def test_duplicate_choices_without_setting(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | b        | option b |
            |         | list            | b        | option c |
            """,
            errored=True,
            error__contains=[vc.INVALID_DUPLICATE.format(row=4)],
        )

    def test_multiple_duplicate_choices_without_setting(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | a        | option b |
            |         | list            | b        | option c |
            |         | list            | b        | option d |
            """,
            errored=True,
            error__contains=[
                vc.INVALID_DUPLICATE.format(row=3),
                vc.INVALID_DUPLICATE.format(row=5),
            ],
        )

    def test_duplicate_choices_with_setting_not_set_to_yes(self):
        self.assertPyxformXform(
            md="""
            | survey  |                 |          |          |
            |         | type            | name     | label    |
            |         | select_one list | S1       | s1       |
            | choices |                 |          |          |
            |         | list name       | name     | label    |
            |         | list            | a        | option a |
            |         | list            | b        | option b |
            |         | list            | b        | option c |
            | settings |                |          |          |
            |          | id_string    | allow_choice_duplicates   |
            |          | Duplicates   | Bob                       |
            """,
            errored=True,
            error__contains=[vc.INVALID_DUPLICATE.format(row=4)],
        )

    def test_duplicate_choices_with_allow_choice_duplicates_setting(self):
        md = """
            | survey  |                 |      |       |
            |         | type            | name | label |
            |         | select_one list | S1   | s1    |
            | choices |                 |      |       |
            |         | list name       | name | label |
            |         | list            | a    | A     |
            |         | list            | b    | B     |
            |         | list            | b    | C     |
            | settings |                |                         |
            |          | id_string      | allow_choice_duplicates |
            |          | Duplicates     | Yes                     |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_instance_choices_label(
                    "list", (("a", "A"), ("b", "B"), ("b", "C"))
                ),
                xpq.body_select1_itemset("S1"),
            ],
        )

    def test_duplicate_choices_with_allow_choice_duplicates_setting_and_translations(
        self,
    ):
        md = """
            | survey  |                 |      |       |
            |         | type            | name | label::en | label::ko |
            |         | select_one list | S1   | s1        | 질문 1     |
            | choices |                 |      |                |
            |         | list name       | name | label::en      | label::ko |
            |         | list            | a    | Pass           | 패스       |
            |         | list            | b    | Fail           | 실패       |
            |         | list            | c    | Skipped        | 건너뛴     |
            |         | list            | c    | Not Applicable | 해당 없음  |
            | settings |                |                         |
            |          | id_string      | allow_choice_duplicates |
            |          | Duplicates     | Yes                     |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "en",
                    "list",
                    ("Pass", "Fail", "Skipped", "Not Applicable"),
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "ko",
                    "list",
                    ("패스", "실패", "건너뛴", "해당 없음"),
                ),
            ],
        )

    def test_choice_list_without_duplicates_is_successful(self):
        md = """
            | survey  |                 |      |       |
            |         | type            | name | label |
            |         | select_one list | S1   | s1    |
            | choices |                 |      |       |
            |         | list name       | name | label |
            |         | list            | a    | A     |
            |         | list            | b    | B     |
            | settings |              |                         |
            |          | id_string    | allow_choice_duplicates |
            |          | Duplicates   | Yes                     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_instance_choices_label("list", (("a", "A"), ("b", "B"))),
                xpq.body_select1_itemset("S1"),
            ],
        )
