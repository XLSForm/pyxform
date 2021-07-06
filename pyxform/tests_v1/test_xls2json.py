from pyxform import xls2json
from pyxform.errors import PyXFormError
from typing import TYPE_CHECKING
import unittest


if TYPE_CHECKING:
    from typing import Any, Dict


def get_survey(sheet_name: str) -> "Dict[str, Any]":
    return {
        sheet_name: [
            {"type": "text", "name": "q1"},
            {"type": "text", "name": "q2"},
            {"type": "text", "name": "q3"},
        ]
    }


def get_choices(sheet_name: str) -> "Dict[str, Any]":
    return {
        sheet_name: [
            {"list_name": "l1", "name": "c1", "label": "choice 1"},
            {"list_name": "l1", "name": "c2", "label": "choice 2"},
        ]
    }


def get_settings(sheet_name: str) -> "Dict[str, Any]":
    return {sheet_name: [{"id_string": "my_id", "title": "My Survey"},]}


def get_expected_dict() -> "Dict[str, Any]":
    return {
        "type": "survey",
        "name": "None",
        "title": None,
        "id_string": None,
        "sms_keyword": None,
        "default_language": "default",
        "children": [
            {"name": "q1", "type": "text"},
            {"name": "q2", "type": "text"},
            {"name": "q3", "type": "text"},
            {
                "name": "meta",
                "type": "group",
                "control": {"bodyless": True},
                "children": [
                    {
                        "name": "instanceID",
                        "bind": {"readonly": "true()", "jr:preload": "uid"},
                        "type": "calculate",
                    }
                ],
            },
        ],
    }


class TestXLS2JSONSheetNameHeuristics(unittest.TestCase):

    err_msg = "The following sheets with similar names were found"

    def test_workbook_to_json__case_insensitive_survey_sheet(self):
        """Should not warn/error if the survey sheet is not lowercase."""
        test_names = ("survey", "Survey", "SURVEY")
        for n in test_names:
            test_dict = get_survey(sheet_name=n)
            warnings = []
            observed = xls2json.workbook_to_json(
                workbook_dict=test_dict, warnings=warnings
            )
            self.assertDictEqual(get_expected_dict(), observed)
            observed = [i for i in warnings if self.err_msg in i]
            self.assertEqual(0, len(observed), observed)

    def test_workbook_to_json__misspelled_survey_found(self):
        """Should mention misspellings if similar sheet names found."""
        test_names = ("surveys", "surve", "sruvey")
        for n in test_names:
            test_dict = get_survey(sheet_name=n)
            with self.assertRaises(PyXFormError) as e:
                xls2json.workbook_to_json(workbook_dict=test_dict)
            self.assertIn(self.err_msg, e.exception.args[0])

    def test_workbook_to_json__misspelled_survey_not_found(self):
        """Should not mention misspellings for dissimilar sheet names."""
        test_names = ("hams", "suVVve", "settings")
        for n in test_names:
            test_dict = get_survey(sheet_name=n)
            with self.assertRaises(PyXFormError) as e:
                xls2json.workbook_to_json(workbook_dict=test_dict)
            self.assertNotIn(self.err_msg, e.exception.args[0])

    def test_workbook_to_json__optional_sheets_ok(self):
        """Should not warn when optional sheet names are provided."""
        test_dict = get_survey(sheet_name="survey")
        test_dict.update(get_choices(sheet_name="choices"))
        test_dict.update(get_settings(sheet_name="settings"))
        warnings = []
        xls2json.workbook_to_json(workbook_dict=test_dict, warnings=warnings)
        observed = [i for i in warnings if self.err_msg in i]
        self.assertEqual(0, len(observed), observed)

    def test_workbook_to_json__case_insensitive_optional_sheets(self):
        """Should not warn/error if optional sheets are not lowercase."""
        test_names = ("settings", "Settings", "SETTINGS")
        for n in test_names:
            test_dict = get_survey(sheet_name="survey")
            test_dict.update(get_settings(sheet_name=n))
            warnings = []
            xls2json.workbook_to_json(workbook_dict=test_dict, warnings=warnings)
            observed = [i for i in warnings if self.err_msg in i]
            self.assertEqual(0, len(observed), observed)

    def test_workbook_to_json__misspelled_settings_found(self):
        """Should mention misspellings if similar sheet names found."""
        test_names = ("setting", "stetings", "setings")
        for n in test_names:
            test_dict = get_survey(sheet_name="survey")
            test_dict.update(get_settings(sheet_name=n))
            warnings = []
            xls2json.workbook_to_json(workbook_dict=test_dict, warnings=warnings)
            observed = [i for i in warnings if self.err_msg in i]
            self.assertEqual(1, len(observed), observed)

    def test_workbook_to_json__misspelled_settings_not_found(self):
        """Should not mention misspellings for dissimilar sheet names."""
        test_names = ("hams", "spetltigs", "stetinsg")
        for n in test_names:
            test_dict = get_survey(sheet_name="survey")
            test_dict.update(get_settings(sheet_name=n))
            warnings = []
            xls2json.workbook_to_json(workbook_dict=test_dict, warnings=warnings)
            observed = [i for i in warnings if self.err_msg in i]
            self.assertEqual(0, len(observed), observed)

    def test_workbook_to_json__ignore_optional_prefixed_name_for_spelling(self):
        """Should not mention misspellings for prefixed similar sheet names."""
        test_names = ("_setting", "_stetings", "_setings")
        for n in test_names:
            test_dict = get_survey(sheet_name="survey")
            test_dict.update(get_settings(sheet_name=n))
            warnings = []
            xls2json.workbook_to_json(workbook_dict=test_dict, warnings=warnings)
            observed = [i for i in warnings if self.err_msg in i]
            self.assertEqual(0, len(observed), observed)

    def test_workbook_to_json__ignore_survey_prefixed_name_for_spelling(self):
        """Should not mention misspellings for prefixed similar sheet names."""
        test_names = ("_surveys", "_surve", "_sruvey")
        for n in test_names:
            test_dict = get_survey(sheet_name=n)
            with self.assertRaises(PyXFormError) as e:
                xls2json.workbook_to_json(workbook_dict=test_dict)
            self.assertNotIn(self.err_msg, e.exception.args[0])
