from __future__ import print_function
from unittest import TestCase
from pyxform.xls2json_backends import convert_file_to_csv_string
from pyxform.tests import utils


class BackendUtilsTests(TestCase):
    def test_xls_to_csv(self):
        specify_other_xls = utils.path_to_text_fixture("specify_other.xls")
        converted_xls = convert_file_to_csv_string(specify_other_xls)
        specify_other_csv = utils.path_to_text_fixture("specify_other.csv")
        converted_csv = convert_file_to_csv_string(specify_other_csv)
        print("csv:")
        print(converted_csv)
        print("xls:")
        print(converted_xls)
        self.assertEqual(converted_csv, converted_xls)

