from pyxform.tests_v1.pyxform_test_case import PyxformTestCase

class WhitespaceTest(PyxformTestCase):
    def test_over_trim_before(self):
        self.assertPyxformXform(
            name='issue96',
            md="""
            | survey  |                 |            |       |
            |         | type            | label      | name  |
            |         | text            | Ignored    | var   |
            |         | note            | ${var} end | label |
            """,
            xml__contains=[
                '<label><output value=" /issue96/var "/> end </label>',
            ])

    def test_over_trim_middle(self):
        self.assertPyxformXform(
            name='issue96',
            md="""
            | survey  |                 |                  |       |
            |         | type            | label            | name  |
            |         | text            | Ignored          | var   |
            |         | note            | start ${var} end | label |
            """,
            xml__contains=[
                '<label> start <output value=" /issue96/var "/> end </label>',
            ])

    def test_over_trim_after(self):
        self.assertPyxformXform(
            name='issue96',
            md="""
            | survey  |                 |              |       |
            |         | type            | label        | name  |
            |         | text            | Ignored      | var   |
            |         | note            | start ${var} | label |
            """,
            xml__contains=[
                '<label> start <output value=" /issue96/var "/> </label>',
            ])
