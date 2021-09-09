from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TestWarnings(PyxformTestCase):
    def test_warnings__count(self):
        """Should raise an expected number of warnings for a diverse form."""
        # Converted from warnings.xls file for tests/xlsform_spec_test/WarningsTest
        md = """
        | survey   |                        |                         |                           |         |                    |              |       |       |
        |          | type                   | name                    | label                     | hint    | appearance         | image        | audio | video |
        |          | text                   | some_text               |                           | a hint  |                    |              |       |       |
        |          | note                   | number_label            |                           | a note  |                    |              |       |       |
        |          | note                   | display_image_test      |                           |         |                    | img_test.jpg |       |       |
        |          | select_one yes_no      | autocomplete_test       | autocomplete_test         |         | autocomplete       |              |       |       |
        |          | select_one yes_no      | autocomplete_chars_test | autocomplete_chars_test   |         | autocomplete_chars |              |       |       |
        |          | integer                | a_integer               |                           | integer |                    |              |       |       |
        |          | decimal                | a_decimal               |                           | decimal |                    |              |       |       |
        |          | begin repeat           | repeat_test             |                           |         |                    |              |       |       |
        |          | begin group            | group_test              |                           |         |                    |              |       |       |
        |          | text                   | required_text           | required_text             |         |                    |              |       |       |
        |          | select_multiple yes_no | select_multiple_test    | select multiple test      |         | minimal            |              |       |       |
        |          | end group              | adsaf                   |                           |         |                    |              |       |       |
        |          | begin group            | labeled_select_group    | labeled select group test |         | field-list         |              |       |       |
        |          | end group              |                         |                           |         |                    |              |       |       |
        |          | begin group            | name                    |                           |         | table-list         |              |       |       |
        |          | select_one yes_no      | table_list_question     | table list question       | hint    |                    |              |       |       |
        |          | end group              |                         |                           |         |                    |              |       |       |
        |          | select_one a_b         | compact-test            |                           | hint    | compact            |              |       |       |
        |          | end repeat             |                         |                           |         |                    |              |       |       |
        |          | acknowledge            | acknowledge_test        |                           | hint    |                    |              |       |       |
        |          | date                   | date_test               |                           | hint    |                    |              |       |       |
        |          | time                   | time_test               |                           | hint    |                    |              |       |       |
        |          | datetime               | datetime_test           |                           | hint    |                    |              |       |       |
        |          | geopoint               | geopoint_test           |                           | hint    |                    |              |       |       |
        |          | barcode                | barcode_test            |                           | hint    |                    |              |       |       |
        |          | image                  | image_test              |                           | hint    |                    |              |       |       |
        |          | audio                  | audio_test              |                           | hint    |                    |              |       |       |
        |          | video                  | video_test              |                           | hint    |                    |              |       |       |
        |          | start                  | start                   |                           |         |                    |              |       |       |
        |          | end                    | end                     |                           |         |                    |              |       |       |
        |          | today                  | today                   |                           |         |                    |              |       |       |
        |          | deviceid               | deviceid                |                           |         |                    |              |       |       |
        |          | phonenumber            | phonenumber             |                           |         |                    |              |       |       |
        | choices  |           |         |       |       |
        |          | list_name | name    | label | image |
        |          | yes_no    | yes     | yes   |       |
        |          | yes_no    | no      | no    |       |
        |          | a_b       | a       |       | a.jpg |
        |          | a_b       | b       |       | b.jpg |
        |          | animals   | zebra   |       |       |
        |          | animals   | buffalo |       |       |
        | settings |            |           |            |                |                  |
        |          | form_title | form_id   | public_key | submission_url | default_language |
        |          | spec_test  | spec_test |            |                |                  |
        """  # noqa
        warnings = []
        self.assertPyxformXform(
            name="spec_test", md=md, warnings=warnings,
        )
        self.maxDiff = 2000
        expected = [
            "On the choices sheet there is a option with no label. [list_name : a_b]",
            "On the choices sheet there is a option with no label. [list_name : a_b]",
            "On the choices sheet there is a option with no label. [list_name : animals]",
            "On the choices sheet there is a option with no label. [list_name : animals]",
            "[row : 9] Repeat has no label: {'name': 'repeat_test', 'type': 'begin repeat'}",
            "[row : 10] Group has no label: {'name': 'group_test', 'type': 'begin group'}",
            "[row : 16] Group has no label: {'name': 'name', 'type': 'begin group'}",
            "[row : 27] Use the max-pixels parameter to speed up submission "
            + "sending and save storage space. Learn more: https://xlsform.org/#image",
        ]
        self.assertListEqual(expected, warnings)

    def test_warnings__unknown_control_group__with_name(self):
        """Should raise an error when an unknown control group is found."""
        self.assertPyxformXform(
            name="spec_test",
            md="""
            | survey   |               |         |
            |          | type          | name    |
            |          | begin dancing | dancing |
            """,
            errored=True,
            error__contains=["Unknown question type 'begin dancing'."],
        )

    def test_warnings__unknown_control_group__no_name(self):
        """Should raise an error when an unknown control group is found."""
        self.assertPyxformXform(
            name="spec_test",
            md="""
            | survey   |               |         |
            |          | type          | name    |
            |          | begin         | empty   |
            """,
            errored=True,
            error__contains=["Unknown question type 'begin'."],
        )
