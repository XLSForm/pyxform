
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TestMismatchInBrackets(PyxformTestCase):
    def test_non_existent_itext_reference(self):
        self.assertPyxformXform(
            name="ecsv",
            md="""
            | survey |             |                |         |                     | relevant             |
            |        | type        | name           | label   | calculation         |                      |
            |        | decimal     | amount         | Counter |                     |                      |
            |        | integer     | divisor        | divisor |                     |                      |
            |        | calculate   | rounded        | Rounded | round(${amount}, 0) |${amount -> ${divisor}|
            """,  # noqa
            xml__contains=[
                """<instance>"""
            ],
            run_odk_validate=True,
            debug=True)
