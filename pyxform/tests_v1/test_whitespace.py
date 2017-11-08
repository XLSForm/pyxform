from pyxform.tests_v1.pyxform_test_case import PyxformTestCase

class WhitespaceTest(PyxformTestCase):
    def test_over_trim(self):
        self.assertPyxformXform(
            name='issue96',
            md="""
            | survey  |                 |             |       |
            |         | type            | label       | name  |
            |         | text            | Ignored     | var   |
            |         | note            | ${var} text | label |
            """,
            xml__contains=[
                '<label><output value=" /issue96/var "/> text </label>',
            ])
