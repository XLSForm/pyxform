# -*- coding: utf-8 -*-
"""
Test whitespace around output variables in XForms.
"""
from tests.pyxform_test_case import PyxformTestCase


class WhitespaceTest(PyxformTestCase):
    def test_over_trim(self):
        self.assertPyxformXform(
            name="issue96",
            md="""
            | survey  |                 |             |       |
            |         | type            | label       | name  |
            |         | text            | Ignored     | var   |
            |         | note            | ${var} text | label |
            """,
            xml__contains=['<label><output value=" /issue96/var "/> text </label>'],
        )

    def test_values_without_whitespaces_are_processed_successfully(self):
        md = """
            | survey  |                 |             |       |
            |         | type            | label       | name  |
            |         | text            | Ignored     | Var   |
            | settings       |                    |            |                                                   |
            |                | id_string          | public_key | submission_url                                    |
            |                | tutorial_encrypted | MIIB       | https://odk.ona.io/random_person/submission       |
          """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=True,
            xml__xpath_contains=[
                """
                /h:html/h:head/x:model/x:submission[
                  @action='https://odk.ona.io/random_person/submission'
                  and @method='post'
                  and @base64RsaPublicKey='MIIB'
                ]
                """
            ],
        )
