from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
from pyxform.xls2json_backends import xls_value_to_unicode
import xlrd


class RoundCalculationTest(PyxformTestCase):
    def test_non_existent_itext_reference(self):
        self.assertPyxformXform(
            name="ecsv",
            md="""
            | survey |             |                |         |                     |
            |        | type        | name           | label   | calculation         |
            |        | decimal     | amount         | Counter |                     |
            |        | calculate   | rounded        | Rounded | round(${amount}, 0) |
            """,  # noqa
            xml__contains=[
                """<instance>"""
            ],
            run_odk_validate=True)


class TestXLIntValueConversion(PyxformTestCase):
    """
    Test external choices sheet with numeric values is processed successfully.

    The test ensures that the integer values within the external choices sheet
    are returned as they were initially received.
    """
    def test_xls_int_to_csv(self):
        """Test that the float value obtained from xlrd module
        is converted back to its int value."""
        value = 32.0
        value_type = xlrd.XL_CELL_NUMBER
        datemode = 1
        csv_data = xls_value_to_unicode(value, value_type, datemode)
        expected_output = "32"
        self.assertEqual(csv_data, expected_output)

        """Test that the decimal value is not changed during conversion."""
        value = 46.9
        value_type = xlrd.XL_CELL_NUMBER
        datemode = 1
        csv_data = xls_value_to_unicode(value, value_type, datemode)
        expected_output = "46.9"
        self.assertEqual(csv_data, expected_output)
