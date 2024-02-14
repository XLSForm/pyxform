"""
Some tests for the new (v0.9) spec is properly implemented.
"""
import os

import pyxform

from tests import test_expected_output
from tests.xform_test_case.base import XFormTestCase


class AttributeColumnsTest(XFormTestCase):
    maxDiff = None

    def test_conversion(self):
        filename = "attribute_columns_test.xlsx"
        self.get_file_path(filename)
        expected_output_path = os.path.join(
            test_expected_output.PATH, self.root_filename + ".xml"
        )

        # Do the conversion:
        warnings = []
        json_survey = pyxform.xls2json.parse_file_to_json(
            self.path_to_excel_file,
            default_name="attribute_columns_test",
            warnings=warnings,
        )
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(self.output_path, warnings=warnings)
        # print warnings
        # Compare with the expected output:
        with open(expected_output_path, encoding="utf-8") as expected, open(
            self.output_path, encoding="utf-8"
        ) as observed:
            self.assertXFormEqual(expected.read(), observed.read())
