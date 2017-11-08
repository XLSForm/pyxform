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

    def test_empty_label_squashing(self):
        self.assertPyxformXform(
            name='empty_label',
            debug=True,
            ss_structure={'survey': [
                    { 'type':'note', 'label':'', 'name':'label' } ] },
            xml__contains=[
                '<label></label>',
            ])
