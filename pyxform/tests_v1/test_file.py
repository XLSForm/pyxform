from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class FileWidgetTest(PyxformTestCase):
    def test_file_type(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |        |               |
            |        | type   | name   | label         |
            |        | file   | file   | Attach a file |
            """,
            xml__contains=[
                '<upload mediatype="application/*"'],
        )