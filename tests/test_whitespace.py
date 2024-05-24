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

    def test_whitespace_output_permutations(self):
        """Should find expected whitespace before/after/between output variables."""
        md = """
        | survey |              |      |
        |        | type         | name | label                |
        |        | text         | A    | None                 |
        |        | text         | B1   | Before {0}           |
        |        | text         | C1   | {0} After            |
        |        | text         | D1   | Before x2 {0} {0}    |
        |        | text         | E1   | {0} {0} After x2     |
        |        | text         | F1   | {0} Between {0}      |
        |        | text         | G1   | Wrap {0} in text     |
        |        | text         | H1   | Wrap {0} in {0} text |
        |        | text         | I1   | Wrap {0} in {0}      |
        """
        xp = "/h:html/h:body/x:input[@ref='/test_name/{}']/x:label"
        test_cases = ("A", "B1")
        for case in test_cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    md=md.format(f"${{{case}}}"),
                    xml__xpath_exact=[
                        (xp.format("A"), {"<label>None</label>"}),
                        (
                            xp.format("B1"),
                            {
                                f"""<label> Before <output value=" /test_name/{case} "/> </label>"""
                            },
                        ),
                        (
                            xp.format("C1"),
                            {
                                f"""<label><output value=" /test_name/{case} "/> After </label>"""
                            },
                        ),
                        (
                            xp.format("D1"),
                            {
                                f"""<label> Before x2 <output value=" /test_name/{case} "/> <output value=" /test_name/{case} "/> </label>"""
                            },
                        ),
                        (
                            xp.format("E1"),
                            {
                                f"""<label><output value=" /test_name/{case} "/> <output value=" /test_name/{case} "/> After x2 </label>"""
                            },
                        ),
                        (
                            xp.format("F1"),
                            {
                                f"""<label><output value=" /test_name/{case} "/> Between <output value=" /test_name/{case} "/> </label>"""
                            },
                        ),
                        (
                            xp.format("G1"),
                            {
                                f"""<label> Wrap <output value=" /test_name/{case} "/> in text </label>"""
                            },
                        ),
                        (
                            xp.format("H1"),
                            {
                                f"""<label> Wrap <output value=" /test_name/{case} "/> in <output value=" /test_name/{case} "/> text </label>"""
                            },
                        ),
                        (
                            xp.format("I1"),
                            {
                                f"""<label> Wrap <output value=" /test_name/{case} "/> in <output value=" /test_name/{case} "/> </label>"""
                            },
                        ),
                    ],
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
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:submission[
                  @action='https://odk.ona.io/random_person/submission'
                  and @method='post'
                  and @base64RsaPublicKey='MIIB'
                ]
                """
            ],
        )
