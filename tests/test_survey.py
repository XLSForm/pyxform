from pyxform.question import InputQuestion
from pyxform.survey import Survey

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
            """.format(n="q1 = ${q1} " * 250, r=" or ".join(["${q1} = 'y'"] * 250)),
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
                q="\n".join(tmpl_q.format(i) for i in range(1, 250)),
                n=" ".join(tmpl_n.format(i) for i in range(1, 250)),
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
                q="\n".join(tmpl_q.format(i) for i in range(1, 250)),
                n="\n".join(tmpl_n.format(i) for i in range(1, 250)),
            ),
        )

    def test_autoplay_attribute_added_to_question_body_control(self):
        """Should add the autoplay attribute when specified for a question."""
        md = """
        | survey |
        |        | type  | name | label      | audio       | autoplay |
        |        | text  | feel | Song feel? | amazing.mp3 | audio    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:body/x:input[@ref='/test_name/feel' and @autoplay='audio']
                """
            ],
        )

    def test_xpath_dict_initialised_once(self):
        """Should be able to convert a valid form to XML repeatedly with the same result."""
        s = Survey(name="guest_list")
        s.add_children(
            [
                InputQuestion(name="q1", type="text", label="Your first name?"),
                InputQuestion(name="q2", type="text", label="${q1}, last name?"),
            ]
        )
        s._setup_xpath_dictionary()
        # If the dict is re-initialised, "duplicate" elements will be found, which
        # results in the value being set to None.
        self.assertFalse(any(i for i in s._xpath.values() if i is None))
        # Due to the pyxform reference, _var_repl_function() raises an error for None,
        # so calling to_xml() twice would trigger a "duplicates" error.
        self.assertEqual(s.to_xml(validate=False), s.to_xml(validate=False))
