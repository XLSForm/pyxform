import os

import psutil
from pyxform.xls2json_backends import get_xlsform, md_table_to_workbook
from pyxform.xls2xform import get_xml_path, xls2xform_convert

from tests import example_xls, test_output
from tests.pyxform_test_case import PyxformTestCase
from tests.utils import get_temp_dir

# Common XLSForms used in below TestCases
CHOICES = """
| survey   |               |           |       |
|          | type          | name      | label |
|          | select_one l1 | q1        | Q1    |
| {name}   |               |           |       |
|          | list_name     | name      | label |
|          | l1            | 1         | C1    |
"""
# Doubled braces ${{}} here because it's used as a format string.
EXTERNAL_CHOICES = """
| survey |                        |           |       |               |
|        | type                   | name      | label | choice_filter |
|        | text                   | q1        | Q1    |               |
|        | select_one_external l1 | q2        | Q2    | q1=${{q1}}    |
| {name} |                        |           |       |               |
|        | list_name              | name      | q1    |               |
|        | l1                     | 1         | 1     |               |
|        | l1                     | 2         | 2     |               |
"""
SETTINGS = """
| survey   |           |           |       |
|          | type      | name      | label |
|          | text      | q1        | Q1    |
| {name}   |           |           |       |
|          | id_string | title     |       |
|          | my_id     | My Survey |       |
"""
SURVEY = """
| {name}   |           |           |       |
|          | type      | name      | label |
|          | text      | q1        | Q1    |
| settings |
|          | form_title |
|          | My Form    |
"""


class TestXLS2JSONSheetNameHeuristics(PyxformTestCase):
    err_similar_found = "the following sheets with similar names were found"
    err_survey_required = "You must have a sheet named 'survey'."
    err_choices_required = "There should be a choices sheet in this xlsform."
    err_ext_choices_required = (
        "There should be an external_choices sheet in this xlsform."
    )

    def test_workbook_to_json__case_insensitive__choices(self):
        """Should not warn/error if optional sheets are not lowercase."""
        test_names = ("choices", "Choices", "CHOICES")
        for n in test_names:
            self.assertPyxformXform(
                md=CHOICES.format(name=n),
                warnings_count=0,
            )

    def test_workbook_to_json__case_insensitive__external_choices(self):
        """Should not warn/error if optional sheets are not lowercase."""
        test_names = ("external_choices", "External_Choices", "EXTERNAL_CHOICES")
        for n in test_names:
            self.assertPyxformXform(
                md=EXTERNAL_CHOICES.format(name=n),
                warnings_count=0,
            )

    def test_workbook_to_json__case_insensitive__settings(self):
        """Should not warn/error if optional sheets are not lowercase."""
        test_names = ("settings", "Settings", "SETTINGS")
        for n in test_names:
            self.assertPyxformXform(
                md=SETTINGS.format(name=n),
                warnings_count=0,
            )

    def test_workbook_to_json__case_insensitive__survey(self):
        """Should not warn/error if the survey sheet is not lowercase."""
        test_names = ("survey", "Survey", "SURVEY")
        for n in test_names:
            self.assertPyxformXform(
                md=SURVEY.format(name=n),
                warnings_count=0,
            )

    def test_workbook_to_json__ignore_prefixed_name__choices(self):
        """Should ignore sheet name for spelling if prefixed with underscore."""
        test_names = ("_choice", "_chioces", "_choics")
        for n in test_names:
            self.assertPyxformXform(
                md=CHOICES.format(name=n),
                errored=True,
                error__contains=[self.err_choices_required],
                error__not_contains=[self.err_similar_found, f"'{n}'"],
            )

    def test_workbook_to_json__ignore_prefixed_name__external_choices(self):
        """Should ignore sheet name for spelling if prefixed with underscore."""
        test_names = ("_external_choice", "_extrenal_choices", "_externa_choics")
        for n in test_names:
            self.assertPyxformXform(
                md=EXTERNAL_CHOICES.format(name=n),
                errored=True,
                error__contains=[self.err_ext_choices_required],
                error__not_contains=[self.err_similar_found, f"'{n}'"],
            )

    def test_workbook_to_json__ignore_prefixed_name__settings(self):
        """Should ignore sheet name for spelling if prefixed with underscore."""
        test_names = ("_setting", "_stetings", "_setings")
        for n in test_names:
            self.assertPyxformXform(
                md=SETTINGS.format(name=n),
                warnings_count=0,
            )

    def test_workbook_to_json__ignore_prefixed_name__survey(self):
        """Should ignore sheet name for spelling if prefixed with underscore."""
        test_names = ("_surveys", "_surve", "_sruvey")
        for n in test_names:
            self.assertPyxformXform(
                md=SURVEY.format(name=n),
                errored=True,
                error__contains=[self.err_survey_required],
                error__not_contains=[self.err_similar_found, f"'{n}'"],
            )

    def test_workbook_to_json__misspelled_found__choices(self):
        """Should mention misspellings if similar sheet names found."""
        test_names = ("choice", "chioces", "choics")
        for n in test_names:
            self.assertPyxformXform(
                md=CHOICES.format(name=n),
                errored=True,
                error__contains=[
                    self.err_choices_required,
                    self.err_similar_found,
                    f"'{n}'",
                ],
            )

    def test_workbook_to_json__misspelled_found__choices_exists(self):
        """Should not mention misspellings if the sheet exists."""
        self.assertPyxformXform(
            md="""
            | survey   |               |           |       |
            |          | type          | name      | label |
            |          | select_one l1 | q1        | Q1    |
            | choices  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | chioces  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            """,
            warnings_count=0,
        )

    def test_workbook_to_json__misspelled_found__choices_multiple(self):
        """Should mention misspellings if similar sheet names found."""
        self.assertPyxformXform(
            md="""
            | survey   |               |           |       |
            |          | type          | name      | label |
            |          | select_one l1 | q1        | Q1    |
            | choice   |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | chioces  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            """,
            errored=True,
            error__contains=[
                self.err_choices_required,
                self.err_similar_found,
                "'choice'",
                "'chioces'",
            ],
        )

    def test_workbook_to_json__misspelled_found__external_choices(self):
        """Should mention misspellings if similar sheet names found."""
        test_names = ("external_choice", "extrenal_choices", "externa_choics")
        for n in test_names:
            self.assertPyxformXform(
                md=EXTERNAL_CHOICES.format(name=n),
                errored=True,
                error__contains=[
                    self.err_ext_choices_required,
                    self.err_similar_found,
                    f"'{n}'",
                ],
            )

    def test_workbook_to_json__misspelled_found__external_choices_exists(self):
        """Should not mention misspellings if the sheet exists."""
        self.assertPyxformXform(
            md="""
            | survey   |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | text                   | q1        | Q1    |               |
            |          | select_one_external l1 | q2        | Q2    | q1=${q1}      |
            | external_choices |                |           |       |               |
            |          | list_name              | name      | q1    |               |
            |          | l1                     | 1         | 1     |               |
            |          | l1                     | 2         | 2     |               |
            | extrenal_choices |                |           |       |               |
            |          | list_name              | name      | q1    |               |
            |          | l1                     | 1         | 1     |               |
            |          | l1                     | 2         | 2     |               |
            """,
            warnings_count=0,
        )

    def test_workbook_to_json__misspelled_found__external_choices_multiple(self):
        """Should mention misspellings if similar sheet names found."""
        self.assertPyxformXform(
            md="""
            | survey   |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | text                   | q1        | Q1    |               |
            |          | select_one_external l1 | q2        | Q2    | q1=${q1}      |
            | external_choice |                 |           |       |               |
            |          | list_name              | name      | q1    |               |
            |          | l1                     | 1         | 1     |               |
            |          | l1                     | 2         | 2     |               |
            | extrenal_choices |                |           |       |               |
            |          | list_name              | name      | q1    |               |
            |          | l1                     | 1         | 1     |               |
            |          | l1                     | 2         | 2     |               |
            """,
            errored=True,
            error__contains=[
                self.err_ext_choices_required,
                self.err_similar_found,
                "'external_choice'",
                "'extrenal_choices'",
            ],
        )

    def test_workbook_to_json__misspelled_found__settings(self):
        """Should mention misspellings if similar sheet names found."""
        test_names = ("setting", "stetings", "setings")
        for n in test_names:
            self.assertPyxformXform(
                md=SETTINGS.format(name=n),
                warnings__contains=[self.err_similar_found, f"'{n}'"],
            )

    def test_workbook_to_json__misspelled_found__settings_exists(self):
        """Should not mention misspellings if the sheet exists."""
        self.assertPyxformXform(
            md="""
            | survey   |           |           |       |
            |          | type      | name      | label |
            |          | text      | q1        | Q1    |
            | settings |           |           |       |
            |          | id_string | title     |       |
            |          | my_id     | My Survey |       |
            | stetings |           |           |       |
            |          | id_string | title     |       |
            |          | my_id     | My Survey |       |
            """,
            warnings_count=0,
        )

    def test_workbook_to_json__misspelled_found__settings_multiple(self):
        """Should mention misspellings if similar sheet names found."""
        self.assertPyxformXform(
            md="""
            | survey   |           |           |       |
            |          | type      | name      | label |
            |          | text      | q1        | Q1    |
            | setting  |           |           |       |
            |          | id_string | title     |       |
            |          | my_id     | My Survey |       |
            | stetings |           |           |       |
            |          | id_string | title     |       |
            |          | my_id     | My Survey |       |
            """,
            warnings__contains=[self.err_similar_found, "'setting'", "'stetings'"],
        )

    def test_workbook_to_json__misspelled_found__survey(self):
        """Should mention misspellings if similar sheet names found."""
        test_names = ("surveys", "surve", "sruvey")
        for n in test_names:
            self.assertPyxformXform(
                md=SURVEY.format(name=n),
                errored=True,
                error__contains=[
                    self.err_survey_required,
                    self.err_similar_found,
                    f"'{n}'",
                ],
            )

    def test_workbook_to_json__misspelled_found__survey_exists(self):
        """Should not mention misspellings if the sheet exists."""
        self.assertPyxformXform(
            md="""
            | survey  |           |           |       |
            |         | type      | name      | label |
            |         | text      | q1        | Q1    |
            | surve   |           |           |       |
            |         | type      | name      | label |
            |         | text      | q1        | Q1    |
            """,
            warnings_count=0,
        )

    def test_workbook_to_json__misspelled_found__survey_multiple(self):
        """Should mention misspellings if similar sheet names found."""
        self.assertPyxformXform(
            md="""
            | surveys |           |           |       |
            |         | type      | name      | label |
            |         | text      | q1        | Q1    |
            | Surve   |           |           |       |
            |         | type      | name      | label |
            |         | text      | q1        | Q1    |
            """,
            errored=True,
            error__contains=[
                self.err_survey_required,
                self.err_similar_found,
                "'surveys'",
                "'Surve'",
            ],
        )

    def test_workbook_to_json__misspelled_not_found__choices(self):
        """Should not mention misspellings for dissimilar sheet names."""
        test_names = ("cho", "ices", "choose")
        for n in test_names:
            self.assertPyxformXform(
                md=CHOICES.format(name=n),
                errored=True,
                error__not_contains=[self.err_similar_found, f"'{n}'"],
            )

    def test_workbook_to_json__misspelled_not_found__external_choices(self):
        """Should not mention misspellings for dissimilar sheet names."""
        test_names = ("external", "choices", "eternal_choosey")
        for n in test_names:
            self.assertPyxformXform(
                md=EXTERNAL_CHOICES.format(name=n),
                errored=True,
                error__not_contains=[self.err_similar_found, f"'{n}'"],
            )

    def test_workbook_to_json__misspelled_not_found__settings(self):
        """Should not mention misspellings for dissimilar sheet names."""
        test_names = ("hams", "spetltigs", "stetinsg")
        for n in test_names:
            self.assertPyxformXform(
                md=SETTINGS.format(name=n),
                warnings_count=0,
            )

    def test_workbook_to_json__misspelled_not_found__survey(self):
        """Should not mention misspellings for dissimilar sheet names."""
        test_names = ("hams", "suVVve", "settings")
        for n in test_names:
            self.assertPyxformXform(
                md=SURVEY.format(name=n),
                errored=True,
                error__not_contains=[self.err_similar_found],
            )

    def test_workbook_to_json__multiple_misspellings__all_ok(self):
        """Should not mention misspellings for complete example with correct spelling."""
        self.assertPyxformXform(
            md="""
            | survey   |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | select_one l1          | q1        | Q1    |               |
            |          | select_one_external l2 | q2        | Q2    | q1=${q1}      |
            | choices  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | external_choices |               |           |       |
            |                  | list_name     | name      | q1    |
            |                  | l2            | 1         | 1     |
            |                  | l2            | 2         | 2     |
            | settings |               |           |       |
            |          | id_string     | title     |
            |          | my_id         | My Survey |
            """,
            warnings_count=0,
        )

    def test_workbook_to_json__multiple_misspellings__survey(self):
        """Should mention misspellings in processing order (su, se, ch, ex)."""
        self.assertPyxformXform(
            md="""
            | surveys  |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | select_one l1          | q1        | Q1    |               |
            |          | select_one_external l2 | q2        | Q2    | q1=${q1}      |
            | chooses  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | external_choyces |               |           |       |
            |                  | list_name     | name      | q1    |
            |                  | l2            | 1         | 1     |
            |                  | l2            | 2         | 2     |
            | settyngs |               |           |       |
            |          | id_string     | title     |
            |          | my_id         | My Survey |
            """,
            errored=True,
            warnings__not_contains=[
                self.err_similar_found,
                "'settyngs'",
            ],
            error__contains=[
                self.err_survey_required,
                self.err_similar_found,
                "'surveys'",
            ],
            error__not_contains=[
                self.err_choices_required,
                "'chooses'",
                self.err_ext_choices_required,
                "'external_choyces'",
            ],
        )

    def test_workbook_to_json__multiple_misspellings__choices(self):
        """Should mention misspellings in processing order (su, se, ch, ex)."""
        self.assertPyxformXform(
            md="""
            | survey   |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | select_one l1          | q1        | Q1    |               |
            |          | select_one_external l2 | q2        | Q2    | q1=${q1}      |
            | chooses  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | external_choyces |               |           |       |
            |                  | list_name     | name      | q1    |
            |                  | l2            | 1         | 1     |
            |                  | l2            | 2         | 2     |
            | settings |               |           |       |
            |          | id_string     | title     |
            |          | my_id         | My Survey |
            """,
            errored=True,
            warnings__not_contains=[
                self.err_similar_found,
                "'settyngs'",
            ],
            error__contains=[
                self.err_choices_required,
                "'chooses'",
            ],
            error__not_contains=[
                self.err_survey_required,
                "'survey'",
                # Not raised because the "select_one l1, q1" is checked first.
                self.err_ext_choices_required,
                "'external_choyces'",
            ],
        )

    def test_workbook_to_json__multiple_misspellings__external_choices(self):
        """Should mention misspellings in processing order (su, se, ch, ex)."""
        self.assertPyxformXform(
            md="""
            | survey   |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | select_one l1          | q1        | Q1    |               |
            |          | select_one_external l2 | q2        | Q2    | q1=${q1}      |
            | choices  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | external_choyces |               |           |       |
            |                  | list_name     | name      | q1    |
            |                  | l2            | 1         | 1     |
            |                  | l2            | 2         | 2     |
            | settings |               |           |       |
            |          | id_string     | title     |
            |          | my_id         | My Survey |
            """,
            errored=True,
            warnings__not_contains=[
                self.err_similar_found,
                "'settyngs'",
            ],
            error__contains=[
                self.err_ext_choices_required,
                "'external_choyces'",
            ],
            error__not_contains=[
                self.err_survey_required,
                "'survey'",
                self.err_choices_required,
                "'chooses'",
            ],
        )

    def test_workbook_to_json__multiple_misspellings__settings(self):
        """Should mention misspellings in processing order (su, se, ch, ex)."""
        self.assertPyxformXform(
            md="""
            | survey   |                        |           |       |               |
            |          | type                   | name      | label | choice_filter |
            |          | select_one l1          | q1        | Q1    |               |
            |          | select_one_external l2 | q2        | Q2    | q1=${q1}      |
            | chooses  |               |           |       |
            |          | list_name     | name      | label |
            |          | l1            | 1         | C1    |
            | external_choyces |               |           |       |
            |                  | list_name     | name      | q1    |
            |                  | l2            | 1         | 1     |
            |                  | l2            | 2         | 2     |
            | settyngs |               |           |       |
            |          | id_string     | title     |
            |          | my_id         | My Survey |
            """,
            errored=True,
            warnings__contains=[
                self.err_similar_found,
                "'settyngs'",
            ],
            error__contains=[
                self.err_choices_required,
                "'chooses'",
            ],
            error__not_contains=[
                self.err_survey_required,
                "'survey'",
                # Not raised because the "select_one l1, q1" is checked first.
                self.err_ext_choices_required,
                "'external_choyces",
            ],
        )

    def test_workbook_to_json__optional_sheets_ok(self):
        """Should not warn when valid optional sheet names are provided."""
        self.assertPyxformXform(
            md="""
            | survey   |           |           |       |
            |          | type      | name      | label |
            |          | text      | q1        | Q1    |
            | settings |           |           |       |
            |          | id_string | title     |       |
            |          | my_id     | My Survey |       |
            | choices  |           |           |       |
            |          | list_name | name      | label |
            |          | l1        | c1        | One   |
            """,
            warnings_count=0,
        )

    def test_xls2xform_convert__e2e_row_with_no_column_value(self):
        """Programmatically-created XLSX files may have rows without column values"""
        md = """
        | survey |        |        |        |         |
        |        | type   | name   | label  | hint    |
        |        | text   | state  | State  |         |
        |        | text   | city   | City   | A hint  |
        """
        wb = md_table_to_workbook(md)
        with get_temp_dir() as tmp:
            wb_path = os.path.join(tmp, "empty_cell.xlsx")
            wb.save(wb_path)
            wb.close()
            xls2xform_convert(
                xlsform_path=wb_path,
                xform_path=get_xml_path(wb_path),
            )

            xform_path = os.path.join(tmp, "empty_cell.xml")
            self.assertTrue(os.path.exists(xform_path))

    def test_xls2xform_convert__e2e_with_settings_misspelling(self):
        """Should warn about settings misspelling when running full pipeline."""
        file_name = "extra_sheet_names"
        warnings = xls2xform_convert(
            xlsform_path=os.path.join(example_xls.PATH, file_name + ".xlsx"),
            xform_path=os.path.join(test_output.PATH, file_name + ".xml"),
            validate=False,
            pretty_print=False,
            enketo=False,
        )
        expected = (
            "When looking for a sheet named 'settings', the following sheets "
            "with similar names were found: 'stettings'"
        )
        self.assertIn(expected, "\n".join(warnings))

    def test_xls2xform_convert__e2e_with_extra_columns__does_not_use_excessive_memory(
        self,
    ):
        """Degenerate form with many blank columns"""
        process = psutil.Process(os.getpid())
        pre_mem = process.memory_info().rss
        xls2xform_convert(
            xlsform_path=os.path.join(example_xls.PATH, "extra_columns.xlsx"),
            xform_path=os.path.join(test_output.PATH, "extra_columns.xml"),
        )
        post_mem = process.memory_info().rss
        # in v1.8.0, memory usage grew by over 16x
        self.assertLess(post_mem, pre_mem * 2)

    def test_xlsx_to_dict__extra_sheet_names_are_returned_by_parser(self):
        """Should return all sheet names so that later steps can do spellcheck."""
        d = get_xlsform(os.path.join(example_xls.PATH, "extra_sheet_names.xlsx"))
        self.assertIn("survey", d.sheet_names)
        self.assertIn("my_sheet", d.sheet_names)
        self.assertIn("stettings", d.sheet_names)
        self.assertIn("choices", d.sheet_names)
