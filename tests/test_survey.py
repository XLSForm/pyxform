from csv import DictReader
from pathlib import Path
from unittest import TestCase

from pyxform import constants as const
from pyxform.question import InputQuestion
from pyxform.section import GroupedSection, RepeatingSection
from pyxform.survey import Survey, get_path_relative_to_lcar

from tests.pyxform_test_case import PYXFORM_TESTS_RUN_ODK_VALIDATE, PyxformTestCase


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
      - "at" indicates that the reference target is an ancestor repeat of the source.

    :param lcar_context: The path above the lowest common ancestor repeat.
    :param target_path: The path to the target, including the LCAR.
    :param source_path: The path to the source, including the LCAR.
    """
    target_path = f"{lcar_context}{target_path}".split("/")
    source_path = f"{lcar_context}{source_path}".split("/")

    shared_path_length = 0
    for i, (t, s) in enumerate(zip(target_path, source_path, strict=False)):
        shared_path_length = i
        if t != s:
            break

    # Objects always present once in paths.
    survey = Survey(name="data")
    target_name = target_path[-1]
    if target_name == "t":
        lcar = RepeatingSection(name="a")
        target = InputQuestion(name=target_name, label="target", type="string")
    elif target_name == "at":
        lcar = RepeatingSection(name=target_name)
        target = lcar
        shared_path_length += 1
    else:
        raise ValueError(f"Unknown target_name: {target_name}")

    source = InputQuestion(name="s", label=f"source ${{{target_name}}}", type="string")
    current_parent = survey
    shared_path = target_path[:shared_path_length]

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
            if not item:
                continue
            elif item[0] == "r":
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
            if not item:
                continue
            elif item[0] == "r":
                new_node = RepeatingSection(name=item)
            else:
                new_node = GroupedSection(name=item)
            source_parent.add_child(new_node)
            source_parent = new_node

    return survey, target, source


class TestGetPathRelativeToLCAR(TestCase):
    """
    Tests of pyxform.survey.get_path_relative_to_lcar
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

        if PYXFORM_TESTS_RUN_ODK_VALIDATE:
            with self.subTest(msg=f"ODK Validate: {msg}"):
                survey.to_xml(validate=True)

        with self.subTest(msg=f"Output Test: {msg}"):
            relation = source.lowest_common_ancestor(
                other=target, group_type=const.REPEAT
            )
            observed = get_path_relative_to_lcar(
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
        path = Path(__file__).parent / "fixtures" / "get_path_relative_to_lcar_cases.csv"
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

    def test_relative_paths__source_under_target__outer_r(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "2", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "3", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_rr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o/r2o",
            "target_path": "/at",
            "source_path": "/at/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "2", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "3", "out_path": "/r2o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_gr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/g1o/r2o",
            "target_path": "/at",
            "source_path": "/at/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "2", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "3", "out_path": "/r2o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_r__inner_r(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/r1s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "3", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "4", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_r__inner_rr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/r1s/r2s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "4", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "5", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_r__inner_rg(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/r1s/g2s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "4", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "5", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_r__inner_g(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/g1s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "3", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "4", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_r__inner_gg(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/g1s/g2s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "4", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "5", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)

    def test_relative_paths__source_under_target__outer_r__inner_gr(self):
        """Should find relative XPath and steps are calculated accurately."""
        topo = {
            "lcar_context": "/y/r1o",
            "target_path": "/at",
            "source_path": "/at/g1s/r2s/s",
            "expect_none": "0",
        }
        cases = (
            {"reference_parent": "0", "out_steps": "4", "out_path": "/at"},
            {"reference_parent": "1", "out_steps": "5", "out_path": "/r1o/at"},
        )
        for case in cases:
            self.assert_relative_path(**topo, **case)


class TestReferencesToAncestorRepeat(PyxformTestCase):
    """
    References cases that involve a repeat, but don't fit with the above tests using
    'assert_relative_path', since the target is not inside a repeat, and so the expected
    XPath is an absolute path (not relative).
    """

    def test_references__source_under_target(self):
        """Should find the XPath reference path is absolute."""
        # Repro case for pyxform/#791
        # The position() predicate approach shown here is the only workaround for unsupported
        # 'preceding-sibling' and 'following-sibling' axes in javarosa/Collect. In practical
        # terms this example sets the default for a question using the previous repeat response.
        md = """
        | survey |
        | | type         | name | label  | default     |
        | | begin_repeat | t    | target |             |
        | | begin group  | g1t  | g1t    |             |
        | | date         | s    | source | ${t}[position() = position(current()/../..) - 1]/g1t/s |
        | | end group    | g1t  |        |             |
        | | end_repeat   | t    |        |             |
        | | begin_repeat | t2   | t2     |             |
        | | text         | s2   | s2     | ${t2}[position() = position(current()/..) - 1]/s2 |
        | | end_repeat   | t2   |        |             |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/t/g1t/s'
                  and @value=' /test_name/t [position() = position(current()/../..) - 1]/g1t/s'
                ]
                """,
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/t2/s2'
                  and @value=' /test_name/t2 [position() = position(current()/..) - 1]/s2'
                ]
                """,
            ],
        )

    def test_references__source_under_target_repeat(self):
        """Should find the XPath reference path is absolute."""
        md = """
        | survey |
        | | type         | name | label | default   |
        | | begin_repeat | t    | t     |           |
        | | text         | s    | s     | ${t}[1]/s |
        | | end_repeat   |      |       |           |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/t/s'
                  and @value=' /test_name/t [1]/s'
                ]
                """
            ],
        )

    def test_references__source_under_target_repeat__inner_g(self):
        """Should find the XPath reference path is absolute."""
        md = """
        | survey |
        | | type         | name | label | default   |
        | | begin_repeat | t    | t     |           |
        | | begin_group  | g1s  | g1s   |           |
        | | text         | s    | s     | ${t}[1]/s |
        | | end_group    |      |       |           |
        | | end_repeat   |      |       |           |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/t/g1s/s'
                  and @value=' /test_name/t [1]/s'
                ]
                """
            ],
        )

    def test_references__source_under_target_repeat__inner_r(self):
        """Should find the XPath reference path is absolute."""
        md = """
        | survey |
        | | type         | name | label | default   |
        | | begin_repeat | t    | t     |           |
        | | begin_repeat | r1s  | r1s   |           |
        | | text         | s    | s     | ${t}[1]/s |
        | | end_repeat   |      |       |           |
        | | end_repeat   |      |       |           |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/t/r1s/s'
                  and @value=' /test_name/t [1]/s'
                ]
                """
            ],
        )

    def test_references__source_under_target_repeat__outer_g(self):
        """Should find the XPath reference path is absolute."""
        md = """
        | survey |
        | | type         | name | label | default   |
        | | begin_group  | g1o  | g1o   |           |
        | | begin_repeat | t    | t     |           |
        | | text         | s    | s     | ${t}[1]/s |
        | | end_repeat   |      |       |           |
        | | end_group    |      |       |           |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/g1o/t/s'
                  and @value=' /test_name/g1o/t [1]/s'
                ]
                """
            ],
        )

    def test_references__source_under_target_repeat__outer_g__inner_g(self):
        """Should find the XPath reference path is absolute."""
        md = """
        | survey |
        | | type         | name | label | default   |
        | | begin_group  | g1o  | g1o   |           |
        | | begin_repeat | t    | t     |           |
        | | begin_group  | g1s  | g1s   |           |
        | | text         | s    | s     | ${t}[1]/s |
        | | end_group    |      |       |           |
        | | end_repeat   |      |       |           |
        | | end_group    |      |       |           |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/g1o/t/g1s/s'
                  and @value=' /test_name/g1o/t [1]/s'
                ]
                """
            ],
        )

    def test_references__source_under_target_repeat__outer_g__inner_r(self):
        """Should find the XPath reference path is absolute."""
        md = """
        | survey |
        | | type         | name | label | default   |
        | | begin_group  | g1o  | g1o   |           |
        | | begin_repeat | t    | t     |           |
        | | begin_repeat | r1s  | r1s   |           |
        | | text         | s    | s     | ${t}[1]/s |
        | | end_repeat   |      |       |           |
        | | end_repeat   |      |       |           |
        | | end_group    |      |       |           |
            """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:setvalue[
                  @ref='/test_name/g1o/t/r1s/s'
                  and @value=' /test_name/g1o/t [1]/s'
                ]
                """
            ],
        )
