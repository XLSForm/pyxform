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

    def test_form_id_variant(self):
        md = """
| survey       |                    |                |                |
|              | type               | name           | label          |
|              | text               | member_name    | name           |
| settings     |                    |              |                        |             |
|              | id_string                         | version                | form_id     |
|              | get_option_from_two_repeat_answer | vWvvk3GYzjXcJQyvTWELej | AUTO-v2-jef |
""" 
        kwargs = {
            u'name': u'None',
            u'title': u'AUTO-v2-jef',
            u'id_string': u'AUTO-v2-jef',
        }

        survey = self.md_to_pyxform_survey(md, kwargs=kwargs, autoname=False)

        self.assertEqual(survey.id_string, "AUTO-v2-jef")
        self.assertEqual(survey.version, "vWvvk3GYzjXcJQyvTWELej")
