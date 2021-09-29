from tests.pyxform_test_case import PyxformTestCase


class TestSurvey(PyxformTestCase):
    """
    Tests for the Survey class.
    """

    def test_many_xpath_references_do_not_hit_64_recursion_limit__one_to_one(self):
        """Should be able to pipe a question into one note more than 64 times."""
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |          |
            |        | type | name | label | relevant |
            |        | text | q1   | Q1    |          |
            |        | note | n    | {n}   |          |
            |        | text | q2   | Q2    | {r}      |
            """.format(
                n="q1 = ${q1} " * 250, r=" or ".join(["${q1} = 'y'"] * 250)
            ),
        )

    def test_many_xpath_references_do_not_hit_64_recursion_limit__many_to_one(self):
        """Should be able to pipe more than 64 questions into one note."""
        tmpl_q = "|        | text | q{0}   | Q{0}    |"
        tmpl_n = "q{0} = ${{q{0}}} "
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | label |
            {q}
            |        | note | n    | {n}  |
            """.format(
                q="\n".join((tmpl_q.format(i) for i in range(1, 250))),
                n=" ".join((tmpl_n.format(i) for i in range(1, 250))),
            ),
        )

    def test_many_xpath_references_do_not_hit_64_recursion_limit__many_to_many(self):
        """Should be able to pipe more than 64 questions into 64 notes."""
        tmpl_q = "|        | text | q{0} | Q{0}    |"
        tmpl_n = "|        | note | n{0} | q{0} = ${{q{0}}} |"
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | label |
            {q}
            {n}
            """.format(
                q="\n".join((tmpl_q.format(i) for i in range(1, 250))),
                n="\n".join((tmpl_n.format(i) for i in range(1, 250))),
            ),
        )
