from pyxform import constants as co

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe


class TestEntitiesUpdateSurvey(PyxformTestCase):
    """Test entity update specs for entities declared at the survey level"""

    def test_basic_entity_update_building_blocks(self):
        self.assertPyxformXform(
            md="""
            | survey   |              |            |         |
            |          | type         | name       | label   |
            |          | text         | id         | Tree id |
            |          | text         | a          | A       |
            |          | csv-external | trees      |         |
            | entities |              |            |         |
            |          | dataset      | entity_id  |         |
            |          | trees        | ${id}      |         |
            """,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2024_1_0.value),
                # defaults to always updating if an entity_id is specified
                xpe.model_instance_meta("trees", create=False, update=True),
                xpe.model_bind_meta_id(" /test_name/id "),
                xpe.model_bind_meta_baseversion("trees", "/test_name/id"),
                xpe.model_bind_meta_trunkversion("trees", "/test_name/id"),
                xpe.model_bind_meta_branchid("trees", "/test_name/id"),
                xpe.model_no_setvalue_meta_id(),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_entity_id_with_creation_condition_only__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |            |           |
            |          | type    | name       | label     |
            |          | text    | id         | Tree id   |
            |          | text    | a          | A         |
            | entities |         |            |           |
            |          | dataset | entity_id  | create_if |
            |          | trees   | ${id}      | true()    |
            """,
            errored=True,
            error__contains=[
                "The entities sheet can't specify an entity creation condition and an entity_id without also including an update condition."
            ],
        )

    def test_update_condition_without_entity_id__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |            |           |
            |          | type    | name       | label     |
            |          | text    | id         | Tree id   |
            |          | text    | a          | A         |
            | entities |         |            |           |
            |          | dataset | update_if  |           |
            |          | trees   | true()     |           |
            """,
            errored=True,
            error__contains=[
                "The entities sheet is missing the entity_id column which is required when updating entities."
            ],
        )

    def test_update_and_create_conditions_without_entity_id__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |            |            |
            |          | type    | name       | label      |
            |          | text    | id         | Tree id    |
            |          | integer | a          | A          |
            | entities |         |            |            |
            |          | dataset | update_if  | create_if  |
            |          | trees   | ${id} != ''| ${id} = '' |
            """,
            errored=True,
            error__contains=[
                "The entities sheet is missing the entity_id column which is required when updating entities."
            ],
        )

    def test_create_if_with_entity_id_in_entities_sheet__puts_expression_on_bind(self):
        self.assertPyxformXform(
            md="""
            | survey   |              |                      |           |
            |          | type         | name                 | label     |
            |          | text         | id                   | Tree id   |
            |          | text         | a                    | A         |
            |          | csv-external | trees                |           |
            | entities |              |                      |           |
            |          | dataset      | update_if            | entity_id |
            |          | trees        | string-length(a) > 3 | ${id}     |
            """,
            xml__xpath_match=[
                xpe.model_instance_meta("trees", update=True),
                xpe.model_bind_meta_update("string-length(a) > 3"),
                xpe.model_bind_meta_id(" /test_name/id "),
                xpe.model_bind_meta_baseversion("trees", "/test_name/id"),
                xpe.model_no_setvalue_meta_id(),
            ],
        )

    def test_update_and_create_conditions_with_entity_id__puts_both_in_bind_calculations(
        self,
    ):
        self.assertPyxformXform(
            md="""
            | survey   |              |            |            |           |
            |          | type         | name       | label      |           |
            |          | text         | id         | Tree id    |           |
            |          | integer      | a          | A          |           |
            |          | csv-external | trees      |            |           |
            | entities |              |            |            |           |
            |          | dataset      | update_if  | create_if  | entity_id |
            |          | trees        | id != ''   | id = ''    | ${id}     |
            """,
            xml__xpath_match=[
                xpe.model_instance_meta("trees", create=True, update=True),
                xpe.model_bind_meta_update("id != ''"),
                xpe.model_bind_meta_create("id = ''"),
                xpe.model_setvalue_meta_id(),
                xpe.model_bind_meta_id(" /test_name/id "),
                xpe.model_bind_meta_baseversion("trees", "/test_name/id"),
            ],
        )

    def test_entity_id_and_label__updates_label(self):
        self.assertPyxformXform(
            md="""
            | survey   |              |            |         |
            |          | type         | name       | label   |
            |          | text         | id         | Tree id |
            |          | text         | a          | A       |
            |          | csv-external | trees      |         |
            | entities |              |            |         |
            |          | dataset      | entity_id  | label   |
            |          | trees        | ${id}      | a       |
            """,
            xml__xpath_match=[
                xpe.model_instance_meta("trees", update=True, label=True),
                xpe.model_bind_meta_label("a"),
            ],
        )

    def test_save_to_with_entity_id__puts_save_tos_on_bind(self):
        self.assertPyxformXform(
            md="""
            | survey   |              |            |         |         |
            |          | type         | name       | label   | save_to |
            |          | text         | id         | Tree id |         |
            |          | text         | a          | A       | foo     |
            |          | csv-external | trees      |         |         |
            | entities |              |            |         |         |
            |          | dataset      | entity_id  |         |         |
            |          | trees        | ${id}      |         |         |
            """,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/a", "foo"),
            ],
        )
