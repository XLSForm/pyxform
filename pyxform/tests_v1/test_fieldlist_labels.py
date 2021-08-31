# -*- coding: utf-8 -*-
"""
Test field-list labels
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class FieldListLabels(PyxformTestCase):
    """Test unlabeled group"""

    def test_unlabeled_group(self):
        warnings = []

        survey = self.md_to_pyxform_survey(
            """
            | survey |             |          |         |
            |        | type        | name     | label   |
            |        | begin_group | my-group |         |
            |        | text        | my-text  | my-text |
            |        | end_group   |          |         |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue("[row : 2] Group has no label" in warnings[0])

    def test_unlabeled_group_alternate_syntax(self):
        warnings = []

        survey = self.md_to_pyxform_survey(
            """
            | survey |             |          |                     |
            |        | type        | name     | label::English (en) |
            |        | begin group | my-group |                     |
            |        | text        | my-text  | my-text             |
            |        | end group   |          |                     |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue("[row : 2] Group has no label" in warnings[0])

    def test_unlabeled_group_fieldlist(self):
        warnings = []

        survey = self.md_to_pyxform_survey(
            """
            | survey |              |           |         |            |
            |        | type         | name      | label   | appearance |
            |        | begin_group  | my-group  |         | field-list |
            |        | text         | my-text   | my-text |            |
            |        | end_group    |           |         |            |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 0)

    def test_unlabeled_group_fieldlist_alternate_syntax(self):
        warnings = []

        survey = self.md_to_pyxform_survey(
            """
            | survey |              |           |         |            |
            |        | type         | name      | label   | appearance |
            |        | begin group  | my-group  |         | field-list |
            |        | text         | my-text   | my-text |            |
            |        | end group    |           |         |            |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 0)

    def test_unlabeled_repeat(self):
        warnings = []

        survey = self.md_to_pyxform_survey(
            """
            | survey |              |           |         |
            |        | type         | name      | label   |
            |        | begin_repeat | my-repeat |         |
            |        | text         | my-text   | my-text |
            |        | end_repeat   |           |         |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue("[row : 2] Repeat has no label" in warnings[0])

    def test_unlabeled_repeat_fieldlist(self):
        warnings = []

        survey = self.md_to_pyxform_survey(
            """
            | survey |              |           |         |            |
            |        | type         | name      | label   | appearance |
            |        | begin_repeat | my-repeat |         | field-list |
            |        | text         | my-text   | my-text |            |
            |        | end_repeat   |           |         |            |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 1)
        self.assertTrue("[row : 2] Repeat has no label" in warnings[0])
