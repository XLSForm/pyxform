from pyxform import constants as co

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe


class TestEntitiesUpdateRepeat(PyxformTestCase):
    """
    Test entity update specs for entities declared in a repeat.

    These tests feature 'csv-external | [entity list name]' in order to include an
    instance for the entity data, and thereby satisfy a ODK Validate check that instance()
    expressions refer to an instance that exists in the form. Per:
    https://docs.getodk.org/entities-quick-reference/#using-entity-data
    """

    def test_basic_usage__ok(self):
        """Should find that the entity repeat has a meta block and the bindings target it."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |
        | | csv-external | e1    |       |         |

        | entities |
        |          | list_name | label | repeat | entity_id |
        |          | e1        | ${q1} | ${r1}  | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    template=True,
                    update=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    update=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "q1e"),
                xpe.model_bind_meta_id(" ../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../q1", "/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.model_no_setvalue_meta_id("/r1"),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_minimal_fields__ok(self):
        """Should find that omitting all optional entity fields is OK."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |
        | | csv-external | e1    |       |

        | entities |
        | | list_name | repeat | entity_id |
        | | e1        | ${r1}  | ${q1}     |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_update_if__ok(self):
        """Should find that the update_if expression targets the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |
        | | csv-external | e1    |       |         |

        | entities |
        | | list_name | label | repeat | entity_id | update_if  |
        | | e1        | ${q1} | ${r1}  | ${q1}     | ${q1} = '' |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[xpe.model_bind_meta_update(" ../../q1  = ''", "/r1")],
        )

    def test_all_fields__ok(self):
        """Should find that using all entity fields at once is OK."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |
        | | csv-external | e1    |       |         |

        | entities |
        | | list_name | label | repeat | entity_id | create_if  | update_if  |
        | | e1        | ${q1} | ${r1}  | ${q1}     | ${q1} = '' | ${q1} = '' |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    template=True,
                    create=True,
                    update=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    create=True,
                    update=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "q1e"),
                xpe.model_bind_meta_id(" ../../q1 ", "/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../q1", "/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
            ],
        )
