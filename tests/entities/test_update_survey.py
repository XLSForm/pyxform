from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe


class TestEntitiesUpdateSurvey(PyxformTestCase):
    """Test entity update specs for entities declared at the survey level"""

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
