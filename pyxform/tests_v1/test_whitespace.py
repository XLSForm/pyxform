from pyxform.tests_v1.pyxform_test_case import PyxformTestCase

class WhitespaceTest(PyxformTestCase):
    def test_over_trim_before(self):
        self.assertPyxformXform(
            name='issue96_issue146',
            ss_structure={'survey': [
                    { 'type':'text', 'label':'Ignored',    'name':'var'   },
                    { 'type':'note', 'label':'${var} end', 'name':'label' } ] },
            xml__contains=[
                '<label><output value=" /issue96_issue146/var "/> end</label>',
            ])

    def test_over_trim_middle(self):
        self.assertPyxformXform(
            name='issue96_issue146',
            ss_structure={'survey': [
                    { 'type':'text', 'label':'Ignored',          'name':'var'   },
                    { 'type':'note', 'label':'start ${var} end', 'name':'label' } ] },
            xml__contains=[
                '<label>start <output value=" /issue96_issue146/var "/> end</label>',
            ])

    def test_over_trim_after(self):
        self.assertPyxformXform(
            name='issue96_issue146',
            ss_structure={'survey': [
                    { 'type':'text', 'label':'Ignored',      'name':'var'   },
                    { 'type':'note', 'label':'start ${var}', 'name':'label' } ] },
            xml__contains=[
                '<label>start <output value=" /issue96_issue146/var "/></label>',
            ])
