# -*- coding: utf-8 -*-
"""
Test select one external syntax.
"""
import codecs
import os

import unittest2 as unittest

import pyxform
from pyxform.tests.utils import XFormTestCase
from pyxform.utils import sheet_to_csv

DIR = os.path.dirname(__file__)


class MainTest(XFormTestCase):

    maxDiff = None

    def runTest(self):
        for filename in ["select_one_external.xlsx"]:
            self.get_file_path(filename)
            expected_output_path = os.path.join(
                DIR, "test_expected_output", self.root_filename + ".xml"
            )

            output_csv = os.path.join(DIR, "test_output", self.root_filename + ".csv")
            # Do the conversion:
            json_survey = pyxform.xls2json.parse_file_to_json(self.path_to_excel_file)

            self.assertTrue(
                sheet_to_csv(self.path_to_excel_file, output_csv, "external_choices")
            )
            self.assertFalse(
                sheet_to_csv(self.path_to_excel_file, output_csv, "non-existant sheet")
            )

            survey = pyxform.create_survey_element_from_dict(json_survey)

            survey.print_xform_to_file(self.output_path)

            # Compare with the expected output:
            with codecs.open(
                expected_output_path, "rb", encoding="utf-8"
            ) as expected_file:
                with codecs.open(
                    self.output_path, "rb", encoding="utf-8"
                ) as actual_file:
                    self.assertXFormEqual(expected_file.read(), actual_file.read())


if __name__ == "__main__":
    unittest.main()
