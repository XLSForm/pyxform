"""
Test field-list labels
"""

from tests.pyxform_test_case import PyxformTestCase


class FieldListLabels(PyxformTestCase):
    """Test unlabeled group"""

    def test_unlabeled_group(self):
        self.assertPyxformXform(
            md="""
            | survey |             |          |         |
            |        | type        | name     | label   |
            |        | begin_group | my-group |         |
            |        | text        | my-text  | my-text |
            |        | end_group   |          |         |
            """,
            warnings_count=1,
            warnings__contains=["[row : 2] Group has no label"],
        )

    def test_unlabeled_group_alternate_syntax(self):
        self.assertPyxformXform(
            md="""
            | survey |             |          |                     |
            |        | type        | name     | label::English (en) |
            |        | begin group | my-group |                     |
            |        | text        | my-text  | my-text             |
            |        | end group   |          |                     |
            """,
            warnings_count=1,
            warnings__contains=["[row : 2] Group has no label"],
        )

    def test_unlabeled_group_fieldlist(self):
        self.assertPyxformXform(
            md="""
            | survey |              |           |         |            |
            |        | type         | name      | label   | appearance |
            |        | begin_group  | my-group  |         | field-list |
            |        | text         | my-text   | my-text |            |
            |        | end_group    |           |         |            |
            """,
            warnings_count=0,
            xml__xpath_match=[
                """
                /h:html/h:body/x:group[
                  @ref = '/test_name/my-group' and @appearance='field-list'
                ]
                """
            ],
        )

    def test_unlabeled_group_fieldlist_alternate_syntax(self):
        self.assertPyxformXform(
            md="""
            | survey |              |           |         |            |
            |        | type         | name      | label   | appearance |
            |        | begin group  | my-group  |         | field-list |
            |        | text         | my-text   | my-text |            |
            |        | end group    |           |         |            |
            """,
            warnings_count=0,
        )

    def test_unlabeled_repeat(self):
        self.assertPyxformXform(
            md="""
            | survey |              |           |         |
            |        | type         | name      | label   |
            |        | begin_repeat | my-repeat |         |
            |        | text         | my-text   | my-text |
            |        | end_repeat   |           |         |
            """,
            warnings_count=1,
            warnings__contains=["[row : 2] Repeat has no label"],
        )

    def test_unlabeled_repeat_fieldlist(self):
        self.assertPyxformXform(
            md="""
            | survey |              |           |         |            |
            |        | type         | name      | label   | appearance |
            |        | begin_repeat | my-repeat |         | field-list |
            |        | text         | my-text   | my-text |            |
            |        | end_repeat   |           |         |            |
            """,
            warnings_count=1,
            warnings__contains=["[row : 2] Repeat has no label"],
        )
