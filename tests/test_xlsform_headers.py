"""
Test XLSForm headers syntax.
"""

from tests.pyxform_test_case import PyxformTestCase


class XlsFormHeadersTest(PyxformTestCase):
    def test_label_caps_alternatives(self):
        """
        re: https://github.com/SEL-Columbia/pyxform/issues/76
        Capitalization of 'label' column can lead to confusing errors.
        """
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | label |
            |        | note | q    | Q     |
            """,
            xml__xpath_match=["/h:html/h:body/x:input[./x:label='Q']"],
        )
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | Label | # <-- note: capital L
            |        | note | q    | Q     |
            """,
            xml__xpath_match=["/h:html/h:body/x:input[./x:label='Q']"],
        )

    def test_calculate_alias(self):
        self.assertPyxformXform(
            name="calculatealias",
            md="""
            | survey |           |         |         |               |
            |        | type      | name    | label   | calculate     |
            |        | decimal   | amount  | Counter |               |
            |        | calculate | doubled | Doubled | ${amount} * 2 |
            """,
        )

    def test_form_id_variant(self):
        md = """
        | survey   |      |             |       |
        |          | type | name        | label |
        |          | text | member_name | name  |
        | settings |                                   |                        |             |
        |          | id_string                         | version                | form_id     |
        |          | get_option_from_two_repeat_answer | vWvvk3GYzjXcJQyvTWELej | AUTO-v2-jef |
        """
        self.assertPyxformXform(
            md=md,
            # setting 'id_string' is ignored.
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance/x:test_name[
                    @id='AUTO-v2-jef'
                    and @version='vWvvk3GYzjXcJQyvTWELej'
                  ]
                """
            ],
        )
