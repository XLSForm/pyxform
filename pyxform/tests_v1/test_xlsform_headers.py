from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class XlsFormHeadersTest(PyxformTestCase):
    def test_label_caps_alternatives(self):
        """
        re: https://github.com/SEL-Columbia/pyxform/issues/76
        Capitalization of 'label' column can lead to confusing errors.
        """
        s1 = self.md_to_pyxform_survey("""
            | survey |      |      |       |
            |        | type | name | label |
            |        | note | q    | Q     |
            """)
        s2 = self.md_to_pyxform_survey("""
            | survey |      |      |       |
            |        | type | name | Label | # <-- note: capital L
            |        | note | q    | Q     |
            """)
        self.assertEqual(s1.to_xml(), s2.to_xml())

    def test_calculate_alias(self):
        self.assertPyxformXform(
            name="calculatealias",
            md="""
            | survey |           |         |         |               |
            |        | type      | name    | label   | calculate     |
            |        | decimal   | amount  | Counter |               |
            |        | calculate | doubled | Doubled | ${amount} * 2 |
            """,
            errored=False,
            debug=True)
