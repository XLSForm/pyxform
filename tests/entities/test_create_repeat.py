from pyxform import constants as co

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe


class TestEntitiesCreateRepeat(PyxformTestCase):
    """Test entity create specs for entities declared in a repeat"""

    def test_basic_usage__ok(self):
        """Should find that the entity repeat has a meta block and the bindings target it."""
        md = """
        | survey |              |       |       |         |
        |        | type         | name  | label | save_to |
        |        | begin_repeat | r1    | R1    |         |
        |        | text         | q1    | Q1    | q1e     |
        |        | end_repeat   |       |       |         |

        | entities |
        |          | list_name | label |
        |          | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    template=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "q1e"),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_minimal_fields__ok(self):
        """Should find that omitting all optional entity fields is OK."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_setvalue_meta_id("/r1"),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_create_if__ok(self):
        """Should find that the create_if expression targets the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | create_if  |
        | | e1        | ${q1} | ${q1} = '' |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_bind_meta_create(" ../../../q1  = ''", "/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_other_controls_before__ok(self):
        """Should find that having other control types before the entity repeat is OK."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |
        | | begin_group  | g1    | G1    |
        | | text         | q2    | Q2    |
        | | end_group    |       |       |
        | | begin_repeat | r2    | R2    |
        | | text         | q3    | Q3    |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q3} |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r2",
                    repeat=True,
                    template=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r2",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_meta_id(meta_path="/r2"),
                xpe.model_setvalue_meta_id("/r2"),
                xpe.model_bind_meta_label(" ../../../q3 ", "/r2"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r2']", "/r2"
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_other_controls_after__ok(self):
        """Should find that having other control types after the entity repeat is OK."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |
        | | begin_group  | g1    | G1    |
        | | text         | q2    | Q2    |
        | | end_group    |       |       |
        | | begin_repeat | r2    | R2    |
        | | text         | q3    | Q3    |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
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
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_other_controls_before_and_after__ok(self):
        """Should find that having other control types before or after the entity repeat is OK."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |
        | | begin_group  | g1    | G1    |
        | | text         | q2    | Q2    |
        | | end_group    |       |       |
        | | begin_repeat | r2    | R2    |
        | | text         | q3    | Q3    |
        | | end_repeat   |       |       |
        | | begin_group  | g2    | G2    |
        | | text         | q4    | Q4    |
        | | end_group    |       |       |
        | | begin_repeat | r3    | R3    |
        | | text         | q5    | Q5    |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q3} |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r2",
                    repeat=True,
                    template=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r2",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_meta_id(meta_path="/r2"),
                xpe.model_setvalue_meta_id("/r2"),
                xpe.model_bind_meta_label(" ../../../q3 ", "/r2"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r2']", "/r2"
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_question_without_saveto_in_entity_repeat__ok(self):
        """Should find that including a question with no save_to in the entity repeat is OK."""
        md = """
        | survey |              |       |       |         |
        |        | type         | name  | label | save_to |
        |        | begin_repeat | r1    | R1    |         |
        |        | text         | q1    | Q1    | p1      |
        |        | text         | q2    | Q2    |         |
        |        | end_repeat   |       |       |         |

        | entities |
        |          | list_name | label |
        |          | e1        | ${q1} |
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
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "p1"),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
                # repeat model instance question
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:r1[@jr:template='']/x:q2
                """,
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:r1[not(@jr:template='')]/x:q2
                """,
                # repeat bind question no saveto
                """
                /h:html/h:head/x:model/x:bind[
                  @nodeset='/test_name/r1/q2'
                  and not(@entities:saveto)
                ]
                """,
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_repeat_without_saveto_in_entity_repeat__ok(self):
        """Should find that including a repeat with no save_to in the entity repeat is OK."""
        md = """
        | survey |              |       |       |         |
        |        | type         | name  | label | save_to |
        |        | begin_repeat | r1    | R1    |         |
        |        | text         | q1    | Q1    | p1      |
        |        | begin_repeat | r2    | R2    |         |
        |        | text         | q2    | Q2    |         |
        |        | end_repeat   |       |       |         |
        |        | end_repeat   |       |       |         |

        | entities |
        |          | list_name | label |
        |          | e1        | ${q1} |
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
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "p1"),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
                # repeat template for adjacent repeat doesn't get meta block
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:r1[
                  @jr:template=''
                  and ./x:q1
                  and ./x:r2[not(./x:meta)]
                ]
                """,
                # repeat default for adjacent repeat doesn't get meta block
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:r1[
                  not(@jr:template)
                  and ./x:q1
                  and ./x:r2[not(./x:meta)]
                ]
                """,
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_saveto_question_in_nested_group__ok(self):
        """Should find that putting a save_to question in a group inside the entity repeat is OK."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | begin_group  | g1    | G1    |         |
        | | text         | q1    | Q1    | p1      |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]/x:g1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/g1/q1", "p1"),
                xpe.model_bind_meta_id(meta_path="/r1/g1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1/g1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1/g1"
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_entity_repeat_in_group__ok(self):
        """Should find that putting the entity repeat inside a group is OK."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_group  | g1    | G1    |         |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | p1      |
        | | end_repeat   |       |       |         |
        | | end_group    |       |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:g1/x:r1",
                    repeat=True,
                    template=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:g1/x:r1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/g1/r1/q1", "p1"),
                xpe.model_bind_meta_id(meta_path="/g1/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/g1/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:group/x:repeat[@nodeset='/test_name/g1/r1']", "/g1/r1"
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_somewhat_ambiguous_repeat_nesting_references(self):
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | begin_group  | g1    | G1    |
        | | text         | q1    | Q1    |
        | | begin_repeat | r2    | R2    |
        | | begin_group  | g2    | G2    |
        | | text         | q2    | Q2    |
        | | begin_group  | g3    | G3    |
        | | text         | q3    | Q3    |
        | | end_group    |       |       |
        | | end_group    |       |       |
        | | end_repeat   |       |       |
        | | end_group    |       |       |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label                |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                # no save_to in this test
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2/g3"),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../../q1 , " ",  ../../../../q2 , " ",  ../../../q3 )""",
                    "/r1/g1/r2/g2/g3",
                ),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2/g3",
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_somewhat_ambiguous_repeat_nesting_references_with_saveto(self):
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | begin_group  | g1    | G1    |         |
        | | text         | q1    | Q1    |         |
        | | begin_repeat | r2    | R2    |         |
        | | begin_group  | g2    | G2    |         |
        | | text         | q2    | Q2    |         |
        | | begin_group  | g3    | G3    |         |
        | | text         | q3    | Q3    |         |
        | | text         | q4    | Q4    | p1      |
        | | end_group    |       |       |         |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/g1/r2/g2/g3/q4", "p1"),
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2/g3"),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../../q1 , " ",  ../../../../q2 , " ",  ../../../q3 )""",
                    "/r1/g1/r2/g2/g3",
                ),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2/g3",
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_somewhat_ambiguous_repeat_nesting_references_with_saveto_and_competing_lists(
        self,
    ):
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | begin_group  | g1    | G1    |         |
        | | text         | q1    | Q1    |         |
        | | begin_repeat | r2    | R2    |         |
        | | begin_group  | g2    | G2    |         |
        | | text         | q2    | Q2    | e1#e1p1 |
        | | begin_group  | g3    | G3    |         |
        | | text         | q3    | Q3    |         |
        | | text         | q4    | Q4    | e2#e2p1 |
        | | end_group    |       |       |         |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        | | e2        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/g1/r2/g2/q2", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/r2/g2/g3/q4", "e2p1"),
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2"),
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2/g3"),
                xpe.model_setvalue_meta_id("/r1/g1/r2/g2"),
                xpe.model_setvalue_meta_id("/r1/g1/r2/g2/g3"),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../q1 , " ",  ../../../q2 , " ",  ../../../g3/q3 )""",
                    "/r1/g1/r2/g2",
                ),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../../q1 , " ",  ../../../../q2 , " ",  ../../../q3 )""",
                    "/r1/g1/r2/g2/g3",
                ),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2",
                ),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2/g3",
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 4),
            ],
        )

    def test_somewhat_ambiguous_repeat_nesting_references_with_saveto_and_many_competing_lists(
        self,
    ):
        md = """
        | survey |
        | | type         | name  | label | save_to | meta gets what
        | | begin_repeat | r1    | R1    |         |
        | | begin_group  | g1    | G1    |         |
        | | text         | q1    | Q1    |         |
        | | begin_repeat | r2    | R2    |         | e4 (spare slot in R2 scope)
        | | begin_group  | g2    | G2    |         | e1 (pinned by saveto)
        | | text         | q2    | Q2    | e1#e1p1 |
        | | begin_group  | g3    | G3    |         | e3 (another spare slot in R2 scope)
        | | begin_group  | g4    | G4    |         | e2 (pinned to container by saveto)
        | | text         | q3    | Q3    |         |
        | | text         | q4    | Q4    | e2#e2p1 |
        | | end_group    |       |       |         |
        | | end_group    |       |       |         |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label                                 | create_if  |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) | ${q1} = '' |
        | | e2        | concat(${q1}, " ", ${q2}, " ", ${q3}) | |
        | | e3        | concat(${q1}, " ", ${q2}, " ", ${q3}) | |
        | | e4        | concat(${q1}, " ", ${q2}, " ", ${q3}) | |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
                xpe.model_bind_meta_instanceid(),
                # model entity x12 (r1 template + r2 template, r1 template + r2, r1 + r2)
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2/x:g3/x:g4",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3/x:g4",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3/x:g4",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e3",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e3",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e3",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]/x:g2/x:g3",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e4",
                    "/x:r1[@jr:template='']/x:g1/x:r2[@jr:template='']",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e4",
                    "/x:r1[@jr:template='']/x:g1/x:r2[not(@jr:template)]",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e4",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]",
                    template=None,
                    repeat=True,
                    create=True,
                    label=True,
                ),
                # saveto x2
                xpe.model_bind_question_saveto("/r1/g1/r2/g2/q2", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/r2/g2/g3/g4/q4", "e2p1"),
                # model bind meta/entity/@id x4
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2"),
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2"),
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2/g3"),
                xpe.model_bind_meta_id(meta_path="/r1/g1/r2/g2/g3/g4"),
                # model setvalue meta/entity/@id x4
                xpe.model_setvalue_meta_id("/r1/g1/r2"),
                xpe.model_setvalue_meta_id("/r1/g1/r2/g2"),
                xpe.model_setvalue_meta_id("/r1/g1/r2/g2/g3"),
                xpe.model_setvalue_meta_id("/r1/g1/r2/g2/g3/g4"),
                # model bind meta/entity/label x4
                xpe.model_bind_meta_label(
                    """concat( ../../../../q1 , " ",  ../../../g2/q2 , " ",  ../../../g2/g3/g4/q3 )""",
                    "/r1/g1/r2",
                ),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../q1 , " ",  ../../../q2 , " ",  ../../../g3/g4/q3 )""",
                    "/r1/g1/r2/g2",
                ),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../../q1 , " ",  ../../../../q2 , " ",  ../../../g4/q3 )""",
                    "/r1/g1/r2/g2/g3",
                ),
                xpe.model_bind_meta_label(
                    """concat( ../../../../../../../q1 , " ",  ../../../../../q2 , " ",  ../../../q3 )""",
                    "/r1/g1/r2/g2/g3/g4",
                ),
                # body repeat setvalue x4
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2",
                ),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2",
                ),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2/g3",
                ),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat/x:group/x:group/x:repeat[@nodeset='/test_name/r1/g1/r2']",
                    "/r1/g1/r2/g2/g3/g4",
                ),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 8),
                ("/h:html/h:head/x:model/x:instance/x:test_name//x:entity", 12),
            ],
        )

    def test_bad_sibling_repeats_savetos(self):
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | e1#p1   |
        | | end_repeat   |       |       |         |
        | | begin_repeat | r2    | R2    |         |
        | | text         | q2    | Q2    | e1#p2   |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label                     |
        | | e1        | concat(${q1}, " ", ${q2}) |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                "Scope Breach for 'e1': subscriber trying to switch scope at same level"
            ],
        )

    def test_bad_sibling_repeats_saveto(self):
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | e1#p1   |
        | | end_repeat   |       |       |         |
        | | begin_repeat | r2    | R2    |         |
        | | text         | q2    | Q2    |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label                     |
        | | e1        | concat(${q1}, " ", ${q2}) |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                "Scope Breach for 'e1': subscriber trying to switch scope at same level"
            ],
        )

    def test_bad_sibling_repeats(self):
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    |         |
        | | end_repeat   |       |       |         |
        | | begin_repeat | r2    | R2    |         |
        | | text         | q2    | Q2    |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label                     |
        | | e1        | concat(${q1}, " ", ${q2}) |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                "Scope Breach for 'e1': subscriber trying to switch scope at same level"
            ],
        )
