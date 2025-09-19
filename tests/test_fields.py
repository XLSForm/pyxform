"""
Test duplicate survey question field name.
"""

from pyxform.validators.pyxform import unique_names

from tests.pyxform_test_case import PyxformTestCase


class TestQuestionParsing(PyxformTestCase):
    """
    Test XLSForm Fields
    """

    def test_names__question_basic_case__ok(self):
        """Should find that a single unique question name is ok."""
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_different_names_same_context__ok(self):
        """Should find that questions with unique names in the same context is ok."""
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |
        | | text | q2   | Q2    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_question_in_different_group_context__ok(self):
        """Should find that a question name can be the same as another question in a different context."""
        md = """
        | survey |
        | | type        | name | label |
        | | text        | q1   | Q1    |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_question_in_different_repeat_context__ok(self):
        """Should find that a question name can be the same as another question in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_group_in_different_group_context__ok(self):
        """Should find that a question name can be the same a group in a different context."""
        md = """
        | survey |
        | | type        | name | label |
        | | text        | q1   | Q1    |
        | | begin group | g1   | G1    |
        | | begin group | q1   | G1    |
        | | text        | q2   | Q1    |
        | | end group   |      |       |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_group_in_different_repeat_context__ok(self):
        """Should find that a question name can be the same a group in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin repeat | r1   | R1    |
        | | begin group  | q1   | G1    |
        | | text         | q2   | Q1    |
        | | end group    |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_repeat_in_different_group_context__ok(self):
        """Should find that a question name can be the same a repeat in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin group  | g1   | G1    |
        | | begin repeat | q1   | G1    |
        | | text         | q2   | Q1    |
        | | end repeat   |      |       |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_repeat_in_different_repeat_context__ok(self):
        """Should find that a question name can be the same a repeat in a different context."""
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin repeat | r1   | R1    |
        | | begin repeat | q1   | G1    |
        | | text         | q2   | Q1    |
        | | end repeat   |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
        )

    def test_names__question_same_as_survey_root__ok(self):
        """Should find that a question name can be the same as the survey root."""
        md = """
        | survey |
        | | type | name | label |
        | | text | data | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            name="data",
            warnings_count=0,
        )

    def test_names__question_same_as_survey_root_case_insensitive__ok(self):
        """Should find that a question name can be the same (CI) as the survey root."""
        md = """
        | survey |
        | | type | name | label |
        | | text | DATA | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            name="data",
            warnings_count=0,
        )

    def test_names__question_same_as_question_in_same_context_in_survey__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |
        | | text | q1   | Q2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=3, value="q1")],
        )

    def test_names__question_same_as_group_in_same_context_in_survey__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | text        | q1   | Q1    |
        | | begin group | q1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=3, value="q1")],
        )

    def test_names__question_same_as_repeat_in_same_context_in_survey__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin repeat | q1   | G2    |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=3, value="q1")],
        )

    def test_names__question_same_as_question_in_same_context_in_group__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | text        | q1   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=4, value="q1")],
        )

    def test_names__question_same_as_group_in_same_context_in_group__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | begin group | q1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=4, value="q1")],
        )

    def test_names__question_same_as_repeat_in_same_context_in_group__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | text         | q1   | Q1    |
        | | begin repeat | q1   | G2    |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=4, value="q1")],
        )

    def test_names__question_same_as_question_in_same_context_in_repeat__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | text         | q1   | Q2    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=4, value="q1")],
        )

    def test_names__question_same_as_group_in_same_context_in_repeat__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | begin group  | q1   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=4, value="q1")],
        )

    def test_names__question_same_as_repeat_in_same_context_in_repeat__error(self):
        """Should find that a duplicate question name raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | begin repeat | q1   | G2    |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[unique_names.NAMES001.format(row=4, value="q1")],
        )

    def test_names__question_same_as_question_in_same_context_in_survey__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | text        | q1   | Q1    |
        | | text        | Q1   | Q2    |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=3, value="Q1")]
        )

    def test_names__question_same_as_group_in_same_context_in_survey__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | text        | q1   | Q1    |
        | | begin group | Q1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=3, value="Q1")]
        )

    def test_names__question_same_as_repeat_in_same_context_in_survey__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin repeat | Q1   | G2    |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=3, value="Q1")]
        )

    def test_names__question_same_as_question_in_same_context_in_group__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | text        | Q1   | Q2    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=4, value="Q1")]
        )

    def test_names__question_same_as_group_in_same_context_in_group__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | begin group | Q1   | G2    |
        | | text        | q2   | Q2    |
        | | end group   |      |       |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=4, value="Q1")]
        )

    def test_names__question_same_as_repeat_in_same_context_in_group__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | text         | q1   | Q1    |
        | | begin repeat | Q1   | G2    |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=4, value="Q1")]
        )

    def test_names__question_same_as_question_in_same_context_in_repeat__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | text         | Q1   | Q2    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=4, value="Q1")]
        )

    def test_names__question_same_as_group_in_same_context_in_repeat__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | begin group  | Q1   | G2    |
        | | text         | q2   | Q2    |
        | | end group    |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=4, value="Q1")]
        )

    def test_names__question_same_as_repeat_in_same_context_in_repeat__case_insensitive_warning(
        self,
    ):
        """Should find that a duplicate question name (CI) raises a warning."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | begin repeat | Q1   | G2    |
        | | text         | q2   | Q2    |
        | | end repeat   |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, warnings__contains=[unique_names.NAMES002.format(row=4, value="Q1")]
        )
