from pyxform import constants as co
from pyxform.entities import entities_parsing as ep
from pyxform.errors import ErrorCode

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
        |          | list_name | label | repeat |
        |          | e1        | ${q1} | ${r1}  |
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
                xpe.model_bind_question_saveto("/r1/q1", "q1e"),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_instanceid(),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
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

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_create_if__ok(self):
        """Should find that the create_if expression targets the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat | create_if  |
        | | e1        | ${q1} | ${r1}  | ${q1} = '' |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[xpe.model_bind_meta_create(" ../../q1  = ''", "/r1")],
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
        | | list_name | label | repeat |
        | | e1        | ${q3} | ${r2}  |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

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
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

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
        | | list_name | label | repeat |
        | | e1        | ${q3} | ${r2}  |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_question_without_saveto_in_entity_repeat__ok(self):
        """Should find that including a question with no save_to in the entity repeat is OK."""
        md = """
        | survey |              |       |       |         |
        |        | type         | name  | label | save_to |
        |        | begin_repeat | r1    | R1    |         |
        |        | text         | q1    | Q1    | q1e     |
        |        | text         | q2    | Q2    |         |
        |        | end_repeat   |       |       |         |

        | entities |
        |          | list_name | label | repeat |
        |          | e1        | ${q1} | ${r1}  |
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
        )

    def test_repeat_without_saveto_in_entity_repeat__ok(self):
        """Should find that including a repeat with no save_to in the entity repeat is OK."""
        md = """
        | survey |              |       |       |         |
        |        | type         | name  | label | save_to |
        |        | begin_repeat | r1    | R1    |         |
        |        | text         | q1    | Q1    | q1e     |
        |        | begin_repeat | r2    | R2    |         |
        |        | text         | q2    | Q2    |         |
        |        | end_repeat   |       |       |         |
        |        | end_repeat   |       |       |         |

        | entities |
        |          | list_name | label | repeat |
        |          | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
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
        )

    def test_saveto_question_in_nested_group__ok(self):
        """Should find that putting a save_to question in a group inside the entity repeat is OK."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | begin_group  | g1    | G1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_group    |       |       |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
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
                    label=True,
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_question_saveto("/r1/g1/q1", "q1e"),
                xpe.model_bind_meta_label(" ../../../g1/q1 ", "/r1"),
            ],
        )

    def test_entity_repeat_in_group__ok(self):
        """Should find that putting the entity repeat inside a group is OK."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_group  | g1    | G1    |         |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |
        | | end_group    |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            xml__xpath_match=[
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
                xpe.model_bind_question_saveto("/g1/r1/q1", "q1e"),
                xpe.model_bind_meta_label(" ../../../q1 ", "/g1/r1"),
            ],
        )

    def test_entity_repeat_is_not_a_single_reference__error(self):
        """Should raise an error if the entity repeat is not a reference."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label   | repeat |
        | | e1        | ${{q1}} | {case} |
        """
        # Looks like a single reference but fails to parse.
        cases_pyref = ("${.a}", "${a }", "${ }")
        for case in cases_pyref:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    errored=True,
                    error__contains=[
                        ErrorCode.PYREF_001.value.format(
                            sheet="entities", column="repeat", row=2, value=case
                        )
                    ],
                )
        # Doesn't parse, or isn't a single reference.
        cases = (".", "r1", "${r1}a", "${r1}${r2}", "${last-saved#r1}", "${}")
        for case in cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    errored=True,
                    error__contains=[ep.ENTITY001.format(value=case)],
                )

    def test_entity_repeat_not_found__error(self):
        """Should raise an error if the entity repeat was not found in the survey sheet."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r2}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY002.format(value="r2")]
        )

    def test_entity_repeat_is_a_group__error(self):
        """Should raise an error if the entity repeat is not a repeat."""
        md = """
        | survey |
        | | type        | name  | label | save_to |
        | | begin_group | g1    | G1    |         |
        | | text        | q1    | Q1    | q1e     |
        | | end_group   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${g1}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY003.format(value="g1")]
        )

    def test_entity_repeat_is_a_loop__error(self):
        """Should raise an error if the entity repeat is not a repeat."""
        md = """
        | survey |
        | | type               | name  | label | save_to |
        | | begin_loop over c1 | l1    | L1    |         |
        | | text               | q1    | Q1    | q1e     |
        | | end_loop           |       |       |         |

        | choices |
        | | list_name | name | label |
        | | c1        | o1   | l1    |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${l1}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY003.format(value="l1")]
        )

    def test_entity_repeat_in_repeat__error(self):
        """Should raise an error if the entity repeat is inside a repeat."""
        md = """
        | survey |
        | | type         | name  | label |
        | | begin_repeat | r1    | R1    |
        | | begin_repeat | r2    | R2    |
        | | text         | q1    | Q1    |
        | | end_repeat   |       |       |
        | | end_repeat   |       |       |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r2}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY004.format(value="r2")]
        )

    def test_saveto_question_not_in_entity_repeat_no_entity_repeat__error(
        self,
    ):
        """Should raise an error if a save_to question is not in the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r2}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY006.format(row=3, value="q1e")]
        )

    def test_saveto_question_not_in_entity_repeat_in_survey__error(self):
        """Should raise an error if a save_to question is not in the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | text         | q1    | Q1    | q1e     |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q2    | Q2    |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY006.format(row=2, value="q1e")]
        )

    def test_saveto_question_not_in_entity_repeat_in_group__error(self):
        """Should raise an error if a save_to question is not in the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_group  | g1    | G1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_group    |       |       |         |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q2    | Q2    |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY006.format(row=3, value="q1e")]
        )

    def test_saveto_question_not_in_entity_repeat_in_repeat__error(self):
        """Should raise an error if a save_to question is not in the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |
        | | begin_repeat | r2    | R2    |         |
        | | text         | q2    | Q2    |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r2}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY006.format(row=3, value="q1e")]
        )

    def test_saveto_question_in_nested_repeat__error(self):
        """Should raise an error if a save_to question is in a repeat inside the entity repeat."""
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | begin_repeat | r2    | R2    |         |
        | | text         | q1    | Q1    | q1e     |
        | | end_repeat   |       |       |         |
        | | end_repeat   |       |       |         |

        | entities |
        | | list_name | label | repeat |
        | | e1        | ${q1} | ${r1}  |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ep.ENTITY005.format(row=4, value="q1e")]
        )
