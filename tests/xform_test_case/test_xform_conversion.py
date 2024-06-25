"""
Some tests for the new (v0.9) spec is properly implemented.
"""

from pathlib import Path

from pyxform.xls2xform import convert

from tests import test_expected_output
from tests.xform_test_case.base import XFormTestCase


class TestXFormConversion(XFormTestCase):
    maxDiff = None

    def test_conversion_vs_expected(self):
        """Should find that conversion results in (an equivalent) expected XML XForm."""
        cases = (
            ("attribute_columns_test.xlsx", True),
            ("flat_xlsform_test.xlsx", True),
            ("or_other.xlsx", True),
            ("pull_data.xlsx", True),
            ("repeat_date_test.xls", True),
            ("survey_no_name.xlsx", False),
            ("widgets.xls", True),
            ("xlsform_spec_test.xlsx", True),
            ("xml_escaping.xls", True),
            ("default_time_demo.xls", True),
        )
        for i, (case, set_name) in enumerate(cases):
            with self.subTest(msg=f"{i}: {case}"):
                self.get_file_path(case)
                expected_output_path = Path(test_expected_output.PATH) / (
                    self.root_filename + ".xml"
                )
                xlsform = Path(self.path_to_excel_file)
                if set_name:
                    result = convert(xlsform=xlsform, warnings=[], form_name=xlsform.stem)
                else:
                    result = convert(xlsform=xlsform, warnings=[])
                with open(expected_output_path, encoding="utf-8") as expected:
                    self.assertXFormEqual(expected.read(), result.xform)
