from pyxform import constants as co

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe


class TestEntitiesCreateSurvey(PyxformTestCase):
    """Test entity create specs for entities declared at the survey level"""

    def test_multiple_dataset_rows_in_entities_sheet__ok(self):
        self.assertPyxformXform(
            md="""
            | survey |
            | | type        | name | label | save_to |
            | | begin group | g1   | G1    |         |
            | | text        | q1   | Q1    | e1#a1   |
            | | end group   | g1   |       |         |
            | | text        | q2   | Q2    | e2#a1   |
            | |
            | entities |
            | | dataset | label |
            | | e1      | ${q1} |
            | | e2      | ${q1} |
            """,
            warnings_count=0,
        )

    def test_entities_namespace__omitted_if_no_entities_sheet(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            """,
            xml__excludes=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_entities_version__omitted_if_no_entities_sheet(self):
        self.assertPyxformXform(
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            """,
            xml__xpath_match=[xpe.model_no_entities_version()],
        )

    def test_saveto_column__added_to_xml(self):
        self.assertPyxformXform(
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | foo     |
            | entities |         |       |       |         |
            |          | dataset | label |       |         |
            |          | trees   | a     |       |         |
            """,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/a", "foo"),
            ],
        )

    def test_saveto_in_group__works(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |             |        |       |         |
            |          | type        | name   | label | save_to |
            |          | begin_group | a      | A     |         |
            |          | text        | size   | Size  | size    |
            |          | end_group   |        |       |         |
            | entities |             |        |       |         |
            |          | dataset     | label  |       |         |
            |          | trees       | ${size}|       |         |
            """,
            warnings_count=0,
        )

    def test_entities_columns__all_expected(self):
        self.assertPyxformXform(
            md="""
            | survey   |              |       |            |
            |          | type         | name  | label      |
            |          | text         | id    | Treid      |
            |          | text         | a     | A          |
            |          | csv-external | trees |            |
            | entities |              |       |            |
            |          | dataset      | label | update_if  | create_if  | entity_id |
            |          | trees        | a     | id != ''   | id = ''    | ${a}      |
            """,
            warnings_count=0,
        )
