from pyxform_test_case import PyxformTestCase


class LabelTests(PyxformTestCase):
    def test_label_whitespace_preserved(self):
        '''
        https://github.com/XLSForm/pyxform/issues/50

        confirms the behavior of stripping out whitespace
        at the beginning and end of labels.
        '''
        label_with_newlines_wrap = '\n'.join(['', ' * line 1', ' * line 2'])
        self.assertPyxformXform(
            ss_structure={
                'survey': [
                  {
                    'type': 'note',
                    'name': 'n1',
                    'label': label_with_newlines_wrap,
                  }
                ],
                'settings': [{
                    'clean_text_values': 'false()',
                  }
                ]
            },
            xml__contains=[
                label_with_newlines_wrap,
                ]
            )

class HintTests(PyxformTestCase):
    def test_label_whitespace_preserved(self):
        '''
        https://github.com/XLSForm/pyxform/issues/50

        confirms the behavior of stripping out whitespace
        at the beginning and end of hints.
        '''
        whitespace_hint = '\n'.join(['', ' * hint l1', ' * hint l2', ''])
        self.assertPyxformXform(
            ss_structure={
                'survey': [
                  {
                    'type': 'note',
                    'name': 'n1',
                    'label': 'label 1',
                    'hint': whitespace_hint,
                  }
                ],
                'settings': [{
                    'clean_text_values': 'false()',
                  }
                ]
            },
            xml__contains=[
                whitespace_hint,
                ]
            )
