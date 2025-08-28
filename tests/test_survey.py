from csv import DictReader
from pathlib import Path
from unittest import TestCase

from pyxform import constants as const
from pyxform.question import InputQuestion
from pyxform.section import GroupedSection, RepeatingSection
from pyxform.survey import Survey, share_same_repeat_parent

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


def build_survey_from_path_spec(
    lcar_context: str, target_path: str, source_path: str
) -> tuple[Survey, InputQuestion, InputQuestion]:
    """
    Build a Survey object tree from XPath specifications.

    Naming conventions:
    - Abbreviations:
      - y: Survey
      - a: Lowest Common Ancestor Repeat (LCAR)
      - g: Non-repeating group / GroupedSection
      - r: Repeating group / RepeatingSection
      - t: Target question e.g. `${target}`
      - s: Source question, where the ${} reference is located.
      - o: Outer group, above the LCAR.
    - other misc rules:
      - overall the goal is to have unambiguous paths by using unique element names.
      - groups above or below the LCAR are numbered by depth e.g. `/y/g1o/a/g1t/r2t/t`
      - groups above the LCAR are suffixed with "o".
      - groups below the LCAR that are on the target's path are suffixed with "t".
      - groups below the LCAR that are only on the source's path are suffixed with "s".

    :param lcar_context: The path above the lowest common ancestor repeat.
    :param target_path: The path to the target, including the LCAR.
    :param source_path: The path to the source, including the LCAR.
    """
    target_path = f"{lcar_context}{target_path}".split("/")
    source_path = f"{lcar_context}{source_path}".split("/")

    shared_path_length = 0
    for i, (t, s) in enumerate(zip(target_path, source_path, strict=False)):
        if t != s:
            shared_path_length = i
            break

    shared_path = target_path[:shared_path_length]

    # Objects always present once in paths.
    target = InputQuestion(name="t", type="string")
    source = InputQuestion(name="s", type="string")
    lcar = RepeatingSection(name="a")
    survey = Survey(name="data")
    current_parent = survey

    # Shared path
    for item in shared_path:
        if not item or item == "y":
            continue

        if item[0] == "a":
            new_node = lcar
        elif item[0] == "r":
            new_node = RepeatingSection(name=item)
        else:
            new_node = GroupedSection(name=item)

        current_parent.add_child(new_node)
        current_parent = new_node

    # Target path
    target_parent = current_parent
    for item in target_path[shared_path_length:]:
        if item == "t":
            target_parent.add_child(target)
        else:
            if item[0] == "r":
                new_node = RepeatingSection(name=item)
            else:
                new_node = GroupedSection(name=item)
            target_parent.add_child(new_node)
            target_parent = new_node

    # Source path
    source_parent = current_parent
    for item in source_path[shared_path_length:]:
        if item == "s":
            source_parent.add_child(source)
        else:
            if item[0] == "r":
                new_node = RepeatingSection(name=item)
            else:
                new_node = GroupedSection(name=item)
            source_parent.add_child(new_node)
            source_parent = new_node

    return survey, target, source


class TestShareSameRepeatParent(TestCase):
    """
    Tests of pyxform.survey.share_same_repeat_parent
    """

    def assert_relative_path(
        self,
        lcar_context: str,
        target_path: str,
        source_path: str,
        reference_parent: str,
        out_steps: str,
        out_path: str,
        expect_none: str,
    ):
        """Should find relative XPath elements are calculated accurately."""
        survey, target, source = build_survey_from_path_spec(
            lcar_context=lcar_context,
            target_path=target_path,
            source_path=source_path,
        )
        target_xpath = target.get_xpath()
        source_xpath = source.get_xpath()
        reference_parent = reference_parent == "1"
        expected = int(out_steps), out_path
        expect_none = expect_none == "1"
        msg = (target_xpath, source_xpath, reference_parent, expected, expect_none)

        with self.subTest(msg=msg):
            relation = source.lowest_common_ancestor(
                other=target, group_type=const.REPEAT
            )
            observed = share_same_repeat_parent(
                target=target,
                source=source,
                lcar_steps_source=relation[1],
                lcar=relation[3],
                reference_parent=reference_parent,
            )
            if expect_none:
                # likely bug cases that return (None, None) but should equal expected
                self.assertEqual((None, None), observed, msg=msg)
            else:
                self.assertEqual(expected, observed, msg=msg)

    def test_relative_paths__combinations_max_inner_depth_of_2(self):
        """Should find relative XPath and steps are calculated accurately."""
        path = Path(__file__).parent / "fixtures" / "share_same_repeat_parent_cases.csv"
        with open(path) as f:
            for case in DictReader(f):
                self.assert_relative_path(
                    lcar_context=case["lcar_context"],
                    target_path=case["target_path"],
                    source_path=case["source_path"],
                    reference_parent=case["reference_parent"],
                    out_steps=case["out_steps"],
                    out_path=case["out_path"],
                    expect_none=case["expect_none"],
                )

    def test_relative_paths__outer_gg(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/g1o/g2o",
            "target_path": "/a/t",
            "source_path": "/a/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "1", "out_path": "/t"},
            {"reference_parent": "1", "out_steps": "2", "out_path": "/a/t"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__outer_rr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o/r2o",
            "target_path": "/a/t",
            "source_path": "/a/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "1", "out_path": "/t"},
            {"reference_parent": "1", "out_steps": "1", "out_path": "/t"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__outer_gr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/g1o/r2o",
            "target_path": "/a/t",
            "source_path": "/a/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "1", "out_path": "/t"},
            {"reference_parent": "1", "out_steps": "1", "out_path": "/t"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__separate_ggg(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y",
            "target_path": "/a/g1t/g2t/g3t/t",
            "source_path": "/a/g1s/g2s/g3s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "4", "out_path": "/g1t/g2t/g3t/t"},
            {"reference_parent": "1", "out_steps": "5", "out_path": "/a/g1t/g2t/g3t/t"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__separate_ggr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y",
            "target_path": "/a/g1t/g2t/r3t/t",
            "source_path": "/a/g1s/g2s/r3s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "4", "out_path": "/g1t/g2t/r3t/t"},
            {"reference_parent": "1", "out_steps": "4", "out_path": "/g1t/g2t/r3t/t"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)
