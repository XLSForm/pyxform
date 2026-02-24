"""
## Entity feature traceability test suite

Each entities test should reference one (or more) requirements from these lists.

*Entities spec requirements*

- ES001: Namespacing
- ES002: Versioning
- ES003: Creating
- ES004: Updating
- ES005: Properties
- ES006: Multiples

*XLSForm requirements*

- Validation
    - EV001: Sheet name misspelling warning
    - EV002: Unexpected entity column error
    - EV003: Unresolved variable reference error
    - EV004: No entity declarations error
    - EV005: Duplicate entity declarations error
    - EV006: Duplicate save_to error
    - EV007: Container row has save_to error
    - EV008: Unresolved entity save_to prefix error
    - EV009: Missing entity create label error
    - EV010: Missing entity upsert update_if error
    - EV011: Missing entity update/upsert entity_id error
    - EV012: Missing entity save_to prefix error
    - EV014: Unsolvable meta/entity topology error
    - EV015: save_to scope breach error
    - EV016: Entity container scope conflict error
    - EV017: Duplicate save_to delimiter error
    - EV018: Entity name invalid identifier error
    - EV019: Entity name invalid period character error
    - EV020: Entity name invalid underscore prefix error
    - EV021: save_to name invalid identifier error
    - EV022: save_to name invalid reserved names error
    - EV023: save_to name invalid underscore prefix error
- Behaviour
    - EB001: Dataset column alias
    - EB002: implicit entity_id=0, create_if=0, update_if=0 (create)
    - EB003: implicit entity_id=0, create_if=0, update_if=1 (error, EV011)
    - EB004: implicit entity_id=0, create_if=1, update_if=0 (create_if)
    - EB005: implicit entity_id=0, create_if=1, update_if=1 (error, EV011)
    - EB006: implicit entity_id=1, create_if=0, update_if=0 (update)
    - EB007: implicit entity_id=1, create_if=0, update_if=1 (update_if)
    - EB008: implicit entity_id=1, create_if=1, update_if=0 (error, EV010)
    - EB009: implicit entity_id=1, create_if=1, update_if=1 (upsert)
    - EB010: Meta/entity allocations are stable/deterministic
    - EB011: Entities sheet row order used for allocation tie break
    - EB012: Omit setvalue when entity_id present (pyxform/#819)


## Topological constraint solver regression suite

*Path scenarios*

- /s/q1 survey container
- /s/g1/q1 group container
- /s/r1/q1 repeat container
- /s/g1/r1/q1 repeat in group
- /s/r1/g1/q1 group in repeat
- /s/g1/g2/q1 group in group
- /s/r1/r2/q1 repeat in repeat
- /s/r1/g1/r2/q1 repeat in repeat group
- /s/r1/g1/g2/q1 group in repeat group

*Notation*

- tokens:
    - s: survey
    - g: group
    - r: repeat
    - q: question
    - d: dataset
    - p: save_to
    - v: reference
- examples:
    - /s/q1.d1.v1: survey-level question 1 has a reference from dataset 1
    - /s/q2.d2.p1: survey-level question 2 has a save_to property 1 for dataset 2
    - /s/r1/q1.d1.v1: in repeat 1, question 1 has a reference from dataset 1


*Test matrix*

- reference only
    - one dataset
        - each container type, single ref from label, all paths, q1 only
        - each container type, multiple refs from label to same level,
          all paths with q1 and q2 together, cartesian product of paths
        - each container type, multiple refs from label to different levels,
          all paths with q1 and q2 distinct, cartesian product of paths
    - two datasets
        - each container type, multiple refs from label to same level,
          all paths with q1 and q2 together in cartesian product of paths but only
          where there are 2 or more groups in a container scope
        - each container type, multiple refs from label to different levels,
          all paths with q1 and q2 separate in cartesian product of paths but only
          where there are 2 or more groups in a container scope, or where in different scopes
- save_to only
    - as above for "references only" but using save_to to create the linkage
- reference + save_to
    - as above for "references only" but just the "two datasets" cases

*Test matrix schema*

- requestor_1: scenario path - all cases require at least one allocation request
- requestor_2: scenario path - for multiple dataset cases, another allocation request
- expected_error: if an error case then which error code is expected, otherwise "No"
- dataset_1: xpath - where the meta/entity block should be for requestor_1
- dataset_2: xpath - where the meta/entity block should be for requestor_2


*Stress test*

- overall goal: large form with 5k survey rows, 10% containers, saturated with entities.
    - with nesting depth 10, node arity 10 (2 of which branch)
    - B = (c^(d-1)-1)/(c-1) and then T = (B x a) + 1
    - B = branching nodes, c = continuation rate, d = tree depth, a = arity (nodes per branch)
    - For c = 2, d = 10, a = 20: T = (((2^(10-1) - 1)/(2 - 1)) * 10) + 1 = 5111 nodes
    - of which B = 511 (10%) are containers (survey + repeats + groups)
    - container types: 1 survey, 255 repeats, 255 groups
    - 511 entities: 170 by 5x refs, 170 by 5x savetos, 171 by 5x refs + 5x savetos
    - and leaf nodes = 5111 - 511 = 4600 leaf nodes (questions)
- test scaling: linear in arity, exponential in continuation rate or tree depth
- expectations: no errors or warnings, and reasonable processing time and memory usage


## Additional tests

- existing test cases of miscellaneous designs for regressions
"""

from pyxform import constants as co
from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe


class TestEntitiesParsing(PyxformTestCase):
    def test_sheet_name_misspelling__warning(self):
        """Should warn when a name similar to 'entities' is found."""
        # EV001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entitoes |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=1,
            warnings__contains=[
                ErrorCode.NAMES_013.value.format(
                    sheet=co.ENTITIES, candidates="'entitoes'"
                )
            ],
        )

    def test_unexpected_column__single__error(self):
        """Should raise an error when an unsupported column name is found on the entities sheet."""
        # EV002
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label | what |
        | | e1      | E1    | !    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.HEADER_005.value.format(columns="'what'")],
        )

    def test_unexpected_column__multiple__error(self):
        """Should raise an error when unsupported columns are found on the entities sheet."""
        # EV002
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label | what | why |
        | | e1      | E1    | !    | ?   |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.HEADER_005.value.format(columns="'what', 'why'")],
        )

    def test_unresolved_variable_reference__error(self):
        """Should raise an error when an entities variable reference name is not found."""
        # EV003
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.PYREF_003.value.format(
                    sheet="entities", row=2, column="label", q="q2"
                )
            ],
        )

    def test_no_entity_declarations__error(self):
        """Should raise an error when an a save_to value appears but there are no entities."""
        # EV004
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1p1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_001.value.format(row=2)],
        )

    def test_duplicate_entity_declaration__error(self):
        """Should raise an error when more than one entity uses the same name."""
        # EV005
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1#e1p1 |
        | | text | q2   | Q2    | e2#e2p1 |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e1      | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.NAMES_014.value.format(row=3)],
        )

    def test_duplicate_entity_property__single_entity__error(self):
        """Should raise an error when multiple rows attempt to save_to the same entity property."""
        # EV006
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1p1    |
        | | text | q2   | Q2    | e1p1    |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_002.value.format(row=3, saveto="e1p1", other_row=2)
            ],
        )

    def test_duplicate_entity_property__multiple_entity__error(self):
        """Should raise an error when multiple rows attempt to save_to the same entity property."""
        # EV006
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1#e1p1 |
        | | text | q2   | Q2    | e1#e1p2 |
        | | text | q3   | Q3    | e2#e1p1 |
        | | text | q4   | Q4    | e2#e1p1 |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q3} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                # This verifies check scoping since otherwise the error would be row 4 + 1
                ErrorCode.ENTITY_002.value.format(row=5, saveto="e1p1", other_row=4)
            ],
        )

    def test_container_row_has_save_to__begin_group__error(self):
        """Should raise an error when a begin_group has a save_to value."""
        # EV007
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    | e1p1    |
        | | text        | q1   | Q1    |         |
        | | end_group   |      |       |         |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_003.value.format(row=2)],
        )

    def test_container_row_has_save_to__end_group__error(self):
        """Should raise an error when a end_group has a save_to value."""
        # EV007
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    |         |
        | | end_group   |      |       | e1p1    |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_003.value.format(row=4)],
        )

    def test_container_row_has_save_to__begin_repeat__error(self):
        """Should raise an error when a begin_repeat has a save_to value."""
        # EV007
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | g1   | G1    | e1p1    |
        | | text         | q1   | Q1    |         |
        | | end_repeat   |      |       |         |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_003.value.format(row=2)],
        )

    def test_container_row_has_save_to__end_repeat__error(self):
        """Should raise an error when a end_repeat has a save_to value."""
        # EV007
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | g1   | G1    |         |
        | | text         | q1   | Q1    |         |
        | | end_repeat   |      |       | e1p1    |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_003.value.format(row=4)],
        )

    def test_container_as_entity_property__group__no_false_positive(self):
        """Should not raise an error when a valid type contains a container type."""
        # EV007
        md = """
        | survey |
        | | type              | name | label | save_to |
        | | select_one {case} | q1   | Q1    | e1p1    |

        | choices |
        | | list_name | name | label |
        | | {case}    | n1   | N1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        cases = ("group", "my_group1", "repeat", "my_repeat1")
        for case in cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(md=md.format(case=case), warnings_count=0)

    def test_missing_entity_declaration__error(self):
        """Should raise an error if there are entities defined but not the one referenced."""
        # EV008
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e2#e1p1 |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_004.value.format(row=2, dataset="e2")],
        )

    def test_missing_entity_create_label__create_if_present__error(self):
        """Should raise an error if an entity is in create mode but there is no label."""
        # EV009
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset |
        | | e1      |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_005.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_create_label__entity_id_not_present__error(self):
        """Should raise an error if an entity is in create mode but there is no label."""
        # EV009
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | create_if   |
        | | e1      | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_005.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_upsert_update_if__error(self):
        """Should raise an error if an entity is in upsert mode but there is no update_if."""
        # EV010
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | create_if   | entity_id |
        | | e1      | ${q1} != '' | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_006.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_upsert_update_if__with_label__error(self):
        """Should raise an error if an entity is in upsert mode but there is no update_if."""
        # EV010
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label | create_if   | entity_id |
        | | e1      | ${q1} | ${q1} != '' | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_006.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_entity_id__update__error(self):
        """Should raise an error if an entity is in update mode but there is no entity_id."""
        # EV011
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | update_if   |
        | | e1      | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_007.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_entity_id__upsert__error(self):
        """Should raise an error if an entity is in upsert mode but there is no entity_id."""
        # EV011
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | create_if   | update_if   |
        | | e1      | ${q1} != '' | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_007.value.format(row=2, dataset="e1")],
        )

    def test_missing_save_to_prefix__bad_row_first__error(self):
        """Should raise an error if 2 or more entities but a save_to is not prefixed."""
        # EV012
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1p1    |
        | | text | q2   | Q2    | e2#e2p1 |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_008.value.format(row=2)],
        )

    def test_missing_save_to_prefix__bad_row_second__error(self):
        """Should raise an error if 2 or more entities but a save_to is not prefixed."""
        # EV012
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1#e1p1 |
        | | text | q2   | Q2    | e2p1    |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_008.value.format(row=3)],
        )

    def test_unsolvable_meta_topology__depth_0__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey"),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_group__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type        | name | label |
        | | begin_group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end_group   | g1   |       |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q1} |
        | | e3      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey"),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1"),
            ],
        )

    def test_unsolvable_meta_topology__depth_2_group__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | begin_group  | g1   | G1    |
        | | text         | q1   | Q1    |
        | | end_group    | g1   |       |
        | | end_repeat   | r1   |       |

        | entities |
        | | dataset | label |
        | | e1      | ${q1} |
        | | e2      | ${q1} |
        | | e3      | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey/r1"),
            ],
        )

    def test_save_to_scope_breach__depth_1_repeat__error(self):
        """Should raise an error if an entity save_to is in more than one scope."""
        # EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_010.value.format(row=4, dataset="e1", other_row=2),
            ],
        )

    def test_save_to_scope_breach__depth_1_repeat__ok(self):
        """Should not raise an error if different entity save_tos are in different scopes."""
        # EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e2#e1p1 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        | | e2      | E2    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_group__ok(self):
        """Should not raise an error if the entity save_tos are in the same scope."""
        # EV015
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | begin_group | g1   | g1    |         |
        | | text        | q2   | Q2    | e1#e1p2 |
        | | end_group   | g1   |       |         |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_2_repeat__error(self):
        """Should raise an error if an entity save_to is in more than one nested scope."""
        # EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p1 |
        | | begin_repeat | r2   | R2    |         |
        | | text         | q3   | Q3    | e1#e1p2 |
        | | end_repeat   | r2   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_010.value.format(row=6, dataset="e1", other_row=4),
            ],
        )

    def test_dataset_name__xml_identifier__error(self):
        """Should raise an error if the dataset name is not a XML identifier."""
        # ES003 EV018
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | $e1     | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.NAMES_008.value.format(
                    sheet=co.ENTITIES, row=2, column=co.EntityColumns.DATASET.value
                )
            ],
        )

    def test_dataset_name__period__error(self):
        """Should raise an error if the dataset name contains a period."""
        # ES003 EV019
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e.1     | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.NAMES_011.value.format(
                    sheet=co.ENTITIES, row=2, column=co.EntityColumns.DATASET.value
                )
            ],
        )

    def test_dataset_name__reserved_prefix__error(self):
        """Should raise an error if the dataset name has the reserved prefix."""
        # ES003 EV020
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | __e1    | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.NAMES_010.value.format(
                    sheet=co.ENTITIES, row=2, column=co.EntityColumns.DATASET.value
                )
            ],
        )

    def test_save_to_name__xml_identifier__error(self):
        """Should raise an error if the save_to name is not a XML identifier."""
        # ES005 EV021
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | {case}  |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        cases = ("$e1p1", "e1#", "e1#$e1p1")
        for case in cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    errored=True,
                    error__contains=[
                        ErrorCode.NAMES_008.value.format(
                            sheet=co.SURVEY, row=2, column=co.ENTITIES_SAVETO
                        )
                    ],
                )

    def test_save_to_name__reserved_name__error(self):
        """Should raise an error if the save_to name is a reserved name."""
        # ES005 EV022
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | {case}  |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        cases = ("name", "naMe", "label", "lAbEl")
        for case in cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    errored=True,
                    error__contains=[
                        ErrorCode.NAMES_012.value.format(
                            sheet=co.SURVEY, row=2, column=co.ENTITIES_SAVETO
                        )
                    ],
                )

    def test_save_to_name__reserved_prefix__error(self):
        """Should raise an error if the save_to name has the reserved prefix."""
        # ES005 EV023
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | __e1p1  |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.NAMES_010.value.format(
                    sheet=co.SURVEY, row=2, column=co.ENTITIES_SAVETO
                )
            ],
        )


class TestEntitiesOutput(PyxformTestCase):
    def test_namespace__exists(self):
        """Should find namespace definition in XForm when entities used."""
        # ES001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_namespace__used_outside_main_instance(self):
        """Should find namespace prefix is used outside of the main instance."""
        # ES001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2024_1_0.value),
            ],
        )

    def test_namespace__not_used_in_main_instance(self):
        """Should find namespace prefix not used for additions to the main instance."""
        # ES001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity"""
            ],
        )

    def test_version__2024_1_0(self):
        """Should find that forms using compatible features are 2024.1.0."""
        # ES002
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2024_1_0.value),
            ],
        )

    def test_version__2025_1_0(self):
        """Should find that forms using compatible features are 2025.1.0."""
        # ES002
        md = """
        | survey |
        | | type         | name  | label | save_to |
        | | begin_repeat | r1    | R1    |         |
        | | text         | q1    | Q1    | e1p1    |
        | | end_repeat   |       |       |         |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_entities_version(co.EntityVersion.v2025_1_0.value),
            ],
        )

    def test_create__container_survey__child_of_meta(self):
        """Should find that the entity element is a direct child of meta."""
        # ES003
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity"""
            ],
        )

    def test_create__container_survey__id_attribute__exists(self):
        """Should find that the entity element has an 'id' attribute."""
        # ES003
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[@id]"""
            ],
        )

    def test_create__container_survey__id_attribute__has_uuid(self):
        """Should find that the entity element has an 'id' with uuid."""
        # ES003
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[xpe.model_setvalue_meta_id()],
        )

    def test_create__container_survey__dataset_attribute__exists(self):
        """Should find that the entity element has an 'dataset' attribute."""
        # ES003
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[@dataset]"""
            ],
        )

    def test_create__container_survey__dataset_attribute__has_dataset(self):
        """Should find that the entity element has an 'dataset' attribute with name."""
        # ES003
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | dataset | label |
        | | e1      | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[@dataset='e1']"""
            ],
        )
