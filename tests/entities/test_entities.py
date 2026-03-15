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
    - EV016: Reference scope conflict error
    - EV017: Duplicate save_to delimiter error
    - EV018: Entity name invalid identifier error
    - EV019: Entity name invalid period character error
    - EV020: Entity name invalid underscore prefix error
    - EV021: save_to name invalid identifier error
    - EV022: save_to name invalid reserved names error
    - EV023: save_to name invalid underscore prefix error
    - EV024: Entity name missing error
- Behaviour
    - EB001: Dataset column alias
    - EB002: implicit entity_id=0, create_if=0, update_if=0 (create)
    - EB003: implicit entity_id=0, create_if=0, update_if=1 (error, EV011)
    - EB004: implicit entity_id=0, create_if=1, update_if=0 (create / if)
    - EB005: implicit entity_id=0, create_if=1, update_if=1 (error, EV011)
    - EB006: implicit entity_id=1, create_if=0, update_if=0 (update)
    - EB007: implicit entity_id=1, create_if=0, update_if=1 (update / if)
    - EB008: implicit entity_id=1, create_if=1, update_if=0 (error, EV010)
    - EB009: implicit entity_id=1, create_if=1, update_if=1 (upsert / if)
    - EB010: Meta/entity allocations are stable/deterministic
    - EB012: Do not emit entity id setvalue when entity_id present (pyxform/#819)
    - EB013: Emit setvalue for default id
    - EB014: Always emit the instanceID in a survey-level meta block only
    - EB015: Variable reference tokens in the entities sheet are resolved
    - EB016: Variable references for repeats are resolved relative to the entity
    - EB017: Do not emit entities namespace if entities not used
    - EB018: Do not emit entities version if entities not used
    - EB019: Do not emit default instance to load the entity from csv
    - EB020: Allocation is to survey when no references exist for an entity
    - EB021: Allocation to survey meta is compatible with other meta settings
    - EB022: Allocation searches path ancestors only (not children or siblings)
    - EB023: Allocation selects deepest boundary scope (pyxform/#822)
    - EB024: ALlocation is to survey for only one entity not in repeats (pyxform/#825)


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
from pyxform.entities.entities_parsing import ContainerPath, ReferenceSource
from pyxform.errors import ErrorCode, PyXFormError

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.entities import xpe
from tests.xpath_helpers.questions import xpq
from tests.xpath_helpers.settings import xps


class TestEntitiesParsing(PyxformTestCase):
    def test_sheet_name_misspelling__warning(self):
        """Should warn when a name similar to 'entities' is found."""
        # EV001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entitoes |
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label | what |
        | | e1        | E1    | !    |
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
        | | list_name | label | what | why |
        | | e1        | E1    | !    | ?   |
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
        | | list_name | label |
        | | e1        | ${q2} |
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
        | | list_name | label |
        | | e1        | ${q1} |
        | | e1        | ${q2} |
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
        | | list_name | label |
        | | e1        | ${q1} |
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
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q3} |
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
        | | list_name | label |
        | | e1        | ${q1} |
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
        | | list_name | label |
        | | e1        | ${q1} |
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
        | | list_name | label |
        | | e1        | ${q1} |
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
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_003.value.format(row=4)],
        )

    def test_container_as_entity_property__group__no_false_positive__ok(self):
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
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | ${q1} |
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
        | | list_name |
        | | e1        |
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
        | | list_name | create_if   |
        | | e1        | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_005.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_upsert_update_if__error(self):
        """Should raise an error if an entity is in upsert mode but there is no update_if."""
        # EB008 EV010
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | create_if   | entity_id |
        | | e1        | ${q1} != '' | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_006.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_upsert_update_if__with_label__error(self):
        """Should raise an error if an entity is in upsert mode but there is no update_if."""
        # EB008 EV010
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label | create_if   | entity_id |
        | | e1        | ${q1} | ${q1} != '' | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_006.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_entity_id__update__error(self):
        """Should raise an error if an entity is in update mode but there is no entity_id."""
        # EB003 EV011
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | update_if   |
        | | e1        | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_007.value.format(row=2, dataset="e1")],
        )

    def test_missing_entity_entity_id__upsert__error(self):
        """Should raise an error if an entity is in upsert mode but there is no entity_id."""
        # EB005 EV011
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | create_if   | update_if   |
        | | e1        | ${q1} != '' | ${q1} != '' |
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
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q2} |
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
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.ENTITY_008.value.format(row=3)],
        )

    def test_unsolvable_meta_topology__depth_0__saveto_only__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1#e1p1 |
        | | text | q2   | Q2    | e2#e2p1 |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2),
            ],
        )

    def test_unsolvable_meta_topology__depth_0__var_only__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2),
            ],
        )

    def test_unsolvable_meta_topology__depth_0__saveto_and_var__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1#e1p1 |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2),
            ],
        )

    def test_save_to_scope_breach__depth_1_group__save_to_only__ok(self):
        """Should not raise an error if an entity save_to is in more than one group."""
        # ES006 EV014 EV015
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | begin_group | g1   | G1    |         |
        | | text        | q2   | Q2    | e1#e1p2 |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_group__save_and_var__ok(self):
        """Should not raise an error if an entity savsave_to/vare_to is in more than one group."""
        # ES006 EV014 EV015
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | begin_group | g1   | G1    |         |
        | | text        | q2   | Q2    | e1#e1p2 |
        | | end_group   | g1   |       |         |
        | | text        | q3   | Q3    |         |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_group__var_only__ok(self):
        """Should not raise an error if an entity var is in more than one group."""
        # ES006 EV014
        md = """
        | survey |
        | | type        | name | label |
        | | text        | q1   | Q1    |
        | | begin_group | g1   | G1    |
        | | text        | q2   | Q2    |
        | | end_group   | g1   |       |
        | | text        | q3   | Q3    |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_unsolvable_meta_topology__depth_1_group__saveto_only__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | text        | q2   | Q2    | e2#e2p1 |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_group__var_only__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type        | name | label |
        | | begin_group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end_group   | g1   |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q1} |
        | | e3        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey", other_row=3),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_group__saveto_and_var__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | ${q1} |
        | | e3        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey", other_row=3),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__saveto_only__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | text         | q2   | Q2    | e2#e2p1 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1", other_row=2),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__var_only__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q1} |
        | | e3        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1", other_row=2),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__saveto_and_var__error(self):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | ${q1} |
        | | e3        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1", other_row=2),
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
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1", other_row=2),
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
        | | list_name | label |
        | | e1        | ${q1} |
        | | e2        | ${q1} |
        | | e3        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey/r1", other_row=3),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_2_group__saveto_only__error(
        self,
    ):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type            | name | label | save_to |
        | | begin_repeat    | r1   | R1    |         | e1 - q1, q2
        | | text            | q1   | Q1    | e1#e1p1 |
        | |   begin_group   | g1   | G1    |         | e2 - q3, q4; but conflicts q2
        | |     text        | q2   | Q2    | e1#e1p2 |
        | |     begin_group | g2   | G2    |         |
        | |       text      | q3   | Q3    | e2#e2p1 |
        | |     end_group   | g2   |       |         |
        | |     begin_group | g3   | G3    |         |
        | |       text      | q4   | Q4    | e2#e2p2 |
        | |     end_group   | g3   |       |         |
        | |   end_group     | g1   |       |         |
        | | end_repeat      |      |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1", other_row=2),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_2_group__saveto_only__ok(
        self,
    ):
        """Should be able to resolve the above error case by adding a group for e2."""
        # EV014
        md = """
        | survey |
        | | type              | name | label | save_to |
        | | begin_repeat      | r1   | R1    |         | e1 - q1, q2
        | |   text            | q1   | Q1    | e1#e1p1 |
        | |   begin_group     | g1   | G1    |         |
        | |     text          | q2   | Q2    | e1#e1p2 |
        | |     begin_group   | g2   | G2    |         | e2 - q3, q4
        | |       begin_group | g3   | G3    |         |
        | |         text      | q3   | Q3    | e2#e2p1 |
        | |       end_group   | g3   |       |         |
        | |       begin_group | g4   | G4    |         |
        | |         text      | q4   | Q4    | e2#e2p2 |
        | |       end_group   | g4   |       |         |
        | |     end_group     | g2   |       |         |
        | |   end_group       | g1   |       |         |
        | | end_repeat        |      |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1", "/x:r1", create=True, label=True, repeat=True
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[not(@jr:template)]/x:g1/x:g2",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/q2", "e1p2"),
                xpe.model_bind_question_saveto("/r1/g1/g2/g3/q3", "e2p1"),
                xpe.model_bind_question_saveto("/r1/g1/g2/g4/q4", "e2p2"),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_2_group__repeat__saveto_only__ok(
        self,
    ):
        """Should be able to resolve the above error case by adding a repeat for e2."""
        # EV014
        md = """
        | survey |
        | | type              | name | label | save_to |
        | | begin_repeat      | r1   | R1    |         | e1 - q1, q2
        | |   text            | q1   | Q1    | e1#e1p1 |
        | |   begin_group     | g1   | G1    |         |
        | |     text          | q2   | Q2    | e1#e1p2 |
        | |     begin_repeat  | r2   | R2    |         | e2 - q3, q4
        | |       begin_group | g2   | G2    |         |
        | |         text      | q3   | Q3    | e2#e2p1 |
        | |       end_group   | g2   |       |         |
        | |       begin_group | g3   | G3    |         |
        | |         text      | q4   | Q4    | e2#e2p2 |
        | |       end_group   | g3   |       |         |
        | |     end_repeat    | r2   |       |         |
        | |   end_group       | g1   |       |         |
        | | end_repeat        |      |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1", "/x:r1", create=True, label=True, repeat=True
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[not(@jr:template)]/x:g1/x:r2[not(@jr:template)]",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/q2", "e1p2"),
                xpe.model_bind_question_saveto("/r1/g1/r2/g2/q3", "e2p1"),
                xpe.model_bind_question_saveto("/r1/g1/r2/g3/q4", "e2p2"),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_2_group__saveto_and_var__ok(
        self,
    ):
        """Should be able to resolve the above error case by adding a group for e2."""
        # EV014 EB016
        md = """
        | survey |
        | | type              | name | label | save_to |
        | | begin_repeat      | r1   | R1    |         | e1 - q1, q2
        | |   text            | q1   | Q1    | e1#e1p1 |
        | |   begin_group     | g1   | G1    |         |
        | |     text          | q2   | Q2    | e1#e1p2 |
        | |     begin_group   | g2   | G2    |         | e2 - q3, q4
        | |       begin_group | g3   | G3    |         |
        | |         text      | q3   | Q3    | e2#e2p1 |
        | |       end_group   | g3   |       |         |
        | |       begin_group | g4   | G4    |         |
        | |         text      | q4   | Q4    | e2#e2p2 |
        | |       end_group   | g4   |       |         |
        | |     end_group     | g2   |       |         |
        | |   end_group       | g1   |       |         |
        | | end_repeat        |      |       |         |
        | | text              | q5   | Q5    |         | ancestor ref

        | entities |
        | | list_name | label                |
        | | e1        | E1                   |
        | | e2        | concat(${q3}, ${q5}) |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1", "/x:r1", create=True, label=True, repeat=True
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[not(@jr:template)]/x:g1/x:g2",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/q2", "e1p2"),
                xpe.model_bind_question_saveto("/r1/g1/g2/g3/q3", "e2p1"),
                xpe.model_bind_question_saveto("/r1/g1/g2/g4/q4", "e2p2"),
                xpe.model_bind_meta_label(
                    "concat( ../../../g3/q3 ,  /test_name/q5 )", "/r1/g1/g2"
                ),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_3_group__saveto_only__error(
        self,
    ):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type              | name | label | save_to |
        | | begin_repeat      | r1   | R1    |         | e1 - q1, q2
        | | text              | q1   | Q1    | e1#e1p1 |
        | |   begin_group     | g1   | G1    |         |
        | |     text          | q2   | Q2    | e1#e1p2 |
        | |     begin_group   | g2   | G2    |         | e2 - q3, q4
        | |       begin_group | g3   | G3    |         |
        | |         text      | q3   | Q3    | e2#e2p1 |
        | |       end_group   | g3   |       |         |
        | |       begin_group | g4   | G4    |         |
        | |         text      | q4   | Q4    | e2#e2p2 |
        | |       end_group   | g4   |       |         |
        | |       text        | q5   | Q5    | e3#e3p1 | conflict e2 (error)
        | |     end_group     | g2   |       |         |
        | |     text          | q6   | Q6    | e3#e3p2 | conflict e1 (also error)
        | |   end_group       | g1   |       |         |
        | | end_repeat        |      |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        | | e3        | E3    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey/r1", other_row=3),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_3_group__saveto_only__ok(
        self,
    ):
        """Should be able to resolve the above error case by adding a group for e3 and calculate."""
        # EV014
        md = """
        | survey |
        | | type              | name | label | save_to | calculation |
        | | begin_repeat      | r1   | R1    |         |             | e1 - q1, q2
        | | text              | q1   | Q1    | e1#e1p1 |             |
        | |   begin_group     | g1   | G1    |         |             |
        | |     text          | q2   | Q2    | e1#e1p2 |             |
        | |     begin_group   | g2   | G2    |         |             | e2 - q3, q4
        | |       begin_group | g3   | G3    |         |             |
        | |         text      | q3   | Q3    | e2#e2p1 |             |
        | |       end_group   | g3   |       |         |             |
        | |       begin_group | g4   | G4    |         |             |
        | |         text      | q4   | Q4    | e2#e2p2 |             |
        | |       end_group   | g4   |       |         |             |
        | |       text        | q5   | Q5    |         |             | conflict e2
        | |     end_group     | g2   |       |         |             |
        | |     begin_group   | g5   | G5    |         |             |
        | |       text        | q6   | Q6    | e3#e3p1 |             | conflict e3
        | |       calculate   | q7   | Q7    | e3#e3p2 | ${q5}       | conflict e3
        | |     end_group     | g5   |       |         |             |
        | |   end_group       | g1   |       |         |             |
        | | end_repeat        |      |       |         |             |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        | | e3        | E3    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1", "/x:r1", create=True, label=True, repeat=True
                ),
                xpe.model_instance_meta(
                    "e2",
                    "/x:r1[not(@jr:template)]/x:g1/x:g2",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_instance_meta(
                    "e3",
                    "/x:r1[not(@jr:template)]/x:g1/x:g5",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/q2", "e1p2"),
                xpe.model_bind_question_saveto("/r1/g1/g2/g3/q3", "e2p1"),
                xpe.model_bind_question_saveto("/r1/g1/g2/g4/q4", "e2p2"),
                xpe.model_bind_question_saveto("/r1/g1/g5/q6", "e3p1"),
                xpe.model_bind_question_saveto("/r1/g1/g5/q7", "e3p2"),
            ],
        )

    def test_unsolvable_meta_topology__depth_1_repeat__conflict_group__saveto_only__nest_group__error(
        self,
    ):
        """Should raise an error if there is no valid placement for the meta/entity block."""
        # EV014
        md = """
        | survey |
        | | type            | name | label | save_to |
        | | begin_repeat    | r1   | R1    |         | e1 - q1, q2
        | | text            | q1   | Q1    | e1#e1p1 |
        | |   begin_group   | g1   | G1    |         | e2 - q3, q4; but conflicts q2
        | |     begin_group | g2   | G2    |         | should target r1 despite g1/g2
        | |       text      | q2   | Q2    | e1#e1p2 |
        | |     end_group   | g2   |       |         |
        | |     begin_group | g3   | G3    |         |
        | |       text      | q3   | Q3    | e2#e2p1 |
        | |     end_group   | g3   |       |         |
        | |     begin_group | g4   | G4    |         |
        | |       text      | q4   | Q4    | e2#e2p2 |
        | |     end_group   | g4   |       |         |
        | |   end_group     | g1   |       |         |
        | | end_repeat      |      |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey/r1", other_row=2),
            ],
        )

    def test_save_to_scope_breach__depth_1_repeat__error(self):
        """Should raise an error if an entity save_to is in more than one scope."""
        # ES006 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=2, dataset="e1", other_scope="/survey/r1", scope="/survey"
                ),
            ],
        )

    def test_save_to_scope_breach__depth_1_repeat__ancestor_var__ok(self):
        """Should not raise an error if an ancestor variable is outside the repeat scope."""
        # ES006 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p1 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_repeat__save_to_only__ok(self):
        """Should not raise an error if an entity save_to is in more than one group."""
        # ES006 EV014 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g1   | G1    |         |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_group    | g1   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_repeat__save_and_var__ok(self):
        """Should not raise an error if an entity save_to/var is in more than one group."""
        # ES006 EV014 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g1   | G1    |         |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_group    | g1   |       |         |
        | | text         | q3   | Q3    |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_repeat__var_only__ok(self):
        """Should not raise an error if an entity var is in more than one group."""
        # ES006 EV014
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | begin_group  | g1   | G1    |
        | | text         | q2   | Q2    |
        | | end_group    | g1   |       |
        | | text         | q3   | Q3    |
        | | end_repeat   | r1   |       |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_repeat__multiple_lists__ok(self):
        """Should not raise an error if different entity save_tos are in different scopes."""
        # ES006 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e2#e1p1 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_group__multiple_lists__ok(self):
        """Should not raise an error if different entity save_tos are in different scopes."""
        # ES006 EV015
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | begin_group | g1   | G1    |         |
        | | text        | q2   | Q2    | e2#e1p1 |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_repeat__same_scope__ok(self):
        """Should not raise an error if an entity has multiple save_tos in one scope."""
        # ES006 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_1_group__same_scope__ok(self):
        """Should not raise an error if an entity has multiple save_tos in one scope."""
        # ES006 EV015
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | text        | q2   | Q2    | e1#e1p2 |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_2_repeat__error(self):
        """Should raise an error if an entity save_to is in more than one nested scope."""
        # ES006 EV015
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
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=4,
                    dataset="e1",
                    other_scope="/survey/r1/r2",
                    scope="/survey/r1",
                ),
            ],
        )

    def test_save_to_scope_breach__depth_2_group__save_to_only__ok(self):
        """Should not raise an error if an entity save_to is in more than one group."""
        # ES006 EV014 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g2   | G2    |         |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_group    | g2   |       |         |
        | | end_repeat   | r1   |       |         |
        | | end_group    | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_2_group__save_and_var__ok(self):
        """Should not raise an error if an entity save_to/var is in more than one group."""
        # ES006 EV014 EV015
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g2   | G2    |         |
        | | text         | q2   | Q2    | e1#e1p2 |
        | | end_group    | g2   |       |         |
        | | text         | q3   | Q3    |         |
        | | end_repeat   | r1   |       |         |
        | | end_group    | g1   |       |         |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_save_to_scope_breach__depth_2_group__var_only__ok(self):
        """Should not raise an error if an entity var is in more than one group."""
        # ES006 EV014
        md = """
        | survey |
        | | type         | name | label |
        | | begin_group  | g1   | G1    |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | begin_group  | g2   | G2    |
        | | text         | q2   | Q2    |
        | | end_group    | g2   |       |
        | | text         | q3   | Q3    |
        | | end_repeat   | r1   |       |
        | | end_group    | g1   |       |

        | entities |
        | | list_name | label                                 |
        | | e1        | concat(${q1}, " ", ${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_ref_scope_conflict__depth_1_sibling_repeat__saveto_only__error(self):
        """Should raise an error if an entity save_to is in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p1 |
        | | end_repeat   | r1   |       |         |
        | | begin_repeat | r2   | R2    |         |
        | | text         | q3   | Q3    | e1#e1p2 |
        | | end_repeat   | r2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=7, dataset="e1", other_scope="/survey/r1", scope="/survey/r2"
                ),
            ],
        )

    def test_ref_scope_conflict__depth_1_sibling_repeat__var_then_saveto__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    |         |
        | | end_repeat   | r1   |       |         |
        | | begin_repeat | r2   | R2    |         |
        | | text         | q3   | Q3    | e1#e1p1 |
        | | end_repeat   | r2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=7, dataset="e1", other_scope="/survey/r1", scope="/survey/r2"
                ),
            ],
        )

    def test_ref_scope_conflict__depth_1_sibling_repeat__saveto_then_var__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p1 |
        | | end_repeat   | r1   |       |         |
        | | begin_repeat | r2   | R2    |         |
        | | text         | q3   | Q3    |         |
        | | end_repeat   | r2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q3} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_012.value.format(
                    row=2,
                    dataset="e1",
                    other_scope="/survey/r1",
                    scope="/survey/r2",
                    question="q3",
                ),
            ],
        )

    def test_ref_scope_conflict__depth_1_sibling_repeat__var_only__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin_repeat | r1   | R1    |
        | | text         | q2   | Q2    |
        | | end_repeat   | r1   |       |
        | | begin_repeat | r2   | R2    |
        | | text         | q3   | Q3    |
        | | end_repeat   | r2   |       |

        | entities |
        | | list_name | label                     |
        | | e1        | concat(${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_012.value.format(
                    row=2,
                    dataset="e1",
                    other_scope="/survey/r1",
                    scope="/survey/r2",
                    question="q3",
                ),
            ],
        )

    def test_ref_scope_conflict__depth_1_sibling_repeat__var_only__indexed_repeat__error(
        self,
    ):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin_repeat | r1   | R1    |
        | | text         | q2   | Q2    |
        | | end_repeat   | r1   |       |
        | | begin_repeat | r2   | R2    |
        | | text         | q3   | Q3    |
        | | end_repeat   | r2   |       |

        | entities |
        | | list_name | label                                               |
        | | e1        | concat(${q2}, " ", indexed-repeat(${q3}, ${r2}, 1)) |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_012.value.format(
                    row=2,
                    dataset="e1",
                    other_scope="/survey/r1",
                    scope="/survey/r2",
                    question="q3",
                ),
            ],
        )

    def test_ref_scope_conflict__depth_2_asymmetric_lineage__saveto_only__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p1 |
        | | end_repeat   | r1   |       |         |
        | | begin_repeat | r2   | R2    |         |
        | | begin_repeat | r3   | R3    |         |
        | | text         | q3   | Q3    | e1#e1p2 |
        | | end_repeat   | r3   |       |         |
        | | end_repeat   | r2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q3} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=4, dataset="e1", other_scope="/survey/r2/r3", scope="/survey/r1"
                ),
            ],
        )

    def test_ref_scope_conflict__depth_2_asymmetric_lineage__var_then_saveto__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    |         |
        | | end_repeat   | r1   |       |         |
        | | begin_repeat | r2   | R2    |         |
        | | begin_repeat | r3   | R3    |         |
        | | text         | q3   | Q3    | e1#e1p1 |
        | | end_repeat   | r3   |       |         |
        | | end_repeat   | r2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_012.value.format(
                    row=2,
                    dataset="e1",
                    other_scope="/survey/r2/r3",
                    scope="/survey/r1",
                    question="q2",
                ),
            ],
        )

    def test_ref_scope_conflict__depth_2_asymmetric_lineage__saveto_then_var__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q2   | Q2    | e1#e1p1 |
        | | end_repeat   | r1   |       |         |
        | | begin_repeat | r2   | R2    |         |
        | | begin_repeat | r3   | R3    |         |
        | | text         | q3   | Q3    |         |
        | | end_repeat   | r3   |       |         |
        | | end_repeat   | r2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q3} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=4,
                    dataset="e1",
                    other_scope="/survey/r2/r3",
                    scope="/survey/r1",
                    question="q3",
                ),
            ],
        )

    def test_ref_scope_conflict__depth_1_asymmetric_lineage__saveto_only__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016 EB023
        md = """
        | survey |
        | | type             | name | label | save_to |
        | | begin_repeat     | r1   | R1    |         |
        | |   text           | q1   | Q1    | e1p1    |
        | |   begin_group    | g1   | G1    |         |
        | |     text         | q2   | Q2    | e1p2    |
        | |   end_group      | g1   |       |         |
        | | end_repeat       | r1   |       |         |
        | | begin_group      | g2   | G2    |         |
        | |   begin_group    | g3   | G3    |         |
        | |     text         | q3   | Q3    |         |
        | |     begin_repeat | r2   | R2    |         |
        | |       text       | q4   | Q4    | e1p3    |
        | |     end_repeat   | r2   |       |         |
        | |   end_group      | g2   |       |         |
        | | end_group        | g3   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_011.value.format(
                    row=12,
                    dataset="e1",
                    other_scope="/survey/r1",
                    scope="/survey/g2/g3/r2",
                ),
            ],
        )

    def test_ref_scope_conflict__depth_2_asymmetric_lineage__var_only__error(self):
        """Should raise an error if an entity has references in more than one scope lineage."""
        # EV016
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | begin_repeat | r1   | R1    |
        | | text         | q2   | Q2    |
        | | end_repeat   | r1   |       |
        | | begin_repeat | r2   | R2    |
        | | begin_repeat | r3   | R3    |
        | | text         | q3   | Q3    |
        | | end_repeat   | r3   |       |
        | | end_repeat   | r2   |       |

        | entities |
        | | list_name | label                     |
        | | e1        | concat(${q2}, " ", ${q3}) |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_012.value.format(
                    row=2,
                    dataset="e1",
                    other_scope="/survey/r2/r3",
                    scope="/survey/r1",
                    question="q2",
                ),
            ],
        )

    def test_duplicate_save_to_delimiter__error(self):
        """Should raise an error if a save_to has mutliple delimiters."""
        # EV017
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | {case}  |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        cases = ("e1##e1p1", "e1#e1#p1", "##e1p1")
        for case in cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    errored=True,
                    error__contains=[ErrorCode.ENTITY_013.value.format(row=2)],
                )

    def test_dataset_name__xml_identifier__error(self):
        """Should raise an error if the dataset name is not a XML identifier."""
        # ES003 EV018
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | $e1       | E1    |
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
        | | list_name | label |
        | | e.1       | E1    |
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
        | | list_name | label |
        | | __e1      | E1    |
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

    def test_dataset_name__missing__error(self):
        """Should raise an error if the dataset name is missing."""
        # ES003 EV024
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | |           | E1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.NAMES_015.value.format(row=2)],
        )

    def test_dataset_name__missing_multiple__error(self):
        """Should raise an error if the dataset name is missing."""
        # ES003 EV024
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | |           | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.NAMES_015.value.format(row=3)],
        )

    def test_save_to_name__xml_identifier__error(self):
        """Should raise an error if the save_to name is not a XML identifier."""
        # ES005 EV021
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | {case}  |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
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

    def test_list_name_or_dataset_alias__error(self):
        """Should be possible to provide the entity name as 'list_name' or 'dataset'."""
        # EB001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | {case} | label   |
        | | e1     | ${{q1}} |
        """
        cases = ("list_name", "dataset")
        for case in cases:
            with self.subTest(msg=case):
                self.assertPyxformXform(md=md.format(case=case), warnings_count=0)

    def test_no_allocations__single_entity__ok(self):
        """Should not raise an error if a single entity with no references exists."""
        # EV014 EB020
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_no_allocations__multiple_entity__error(self):
        """Should raise an error if a multiple entities with no references exist."""
        # EV014 EB010 EB020
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2)
            ],
        )

    def test_no_allocations__multiple_entity__survey_target__error(self):
        """Should raise an error if a multiple entities with no references exist."""
        # EV014 EB010 EB020
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2)
            ],
        )

    def test_no_allocations__multiple_entity__survey_target_dispersed__error(self):
        """Should raise an error if a multiple entities with no references exist."""
        # EV014 EB010 EB020 EB022
        md = """
        | survey |
        | | type        | name | label |
        | | begin_group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end_group   | g1   |       |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | ${q1} |
        | | e3        | E3    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=4, scope="/survey", other_row=2)
            ],
        )

    def test_no_allocations__multiple_entity__no_sibling_search__error(self):
        """Should raise an error if a multiple entities with no references exist."""
        # EV014 EB020 EB022
        md = """
        | survey |
        | | type        | name | label |
        | | begin_group | g1   | G1    |
        | | text        | q1   | Q1    |
        | | end_group   | g1   |       |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.ENTITY_009.value.format(row=3, scope="/survey", other_row=2)
            ],
        )


class TestEntitiesOutput(PyxformTestCase):
    def test_namespace__entities_not_used__not_exists(self):
        """Should not find the entities namespace definition when entities not used."""
        # ES001 EB017
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__excludes=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_namespace__entities_used__exists(self):
        """Should find namespace definition in XForm when entities used."""
        # ES001
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
            ],
        )

    def test_version__not_entities__not_exists(self):
        """Should not find the entities version when entities not used."""
        # ES002 EB018
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[xpe.model_no_entities_version()],
        )

    def test_version__2024_1_0(self):
        """Should find that forms using compatible features are 2024.1.0."""
        # ES002
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[xps.instance_meta_survey_element(name="entity")],
        )

    def test_create__container_survey__child_of_meta__other_settings(self):
        """Should find that the meta for an unreferenced entity works with settings."""
        # ES003 EB021
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |

        | settings |
        | | instance_name |
        | | my_form       |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xps.instance_meta_survey_element(name="entity"),
                xps.instance_meta_survey_element(name="instanceName"),
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
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
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
        | | list_name | label |
        | | e1        | E1    |
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
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
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
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
            ],
        )

    def test_implicit_create_mode__survey(self):
        """Should find that when no entity_id is provided, the entity is in create mode."""
        # ES003 EB002 EB013 EB014 EB019
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_no_instance_csv("e1"),
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", create=True, label=True),
                xpe.model_bind_meta_label("E1"),
                xpe.model_bind_meta_id(),
                xpe.model_setvalue_meta_id(),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 1),
            ],
        )

    def test_implicit_create_mode__repeat(self):
        """Should find that when no entity_id is provided, the entity is in create mode."""
        # ES003 EB002 EB013 EB014 EB015 EB016 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_no_instance_csv("e1"),
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, create=True, label=True
                ),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_implicit_create_mode__create_if__survey(self):
        """Should find that when no entity_id is provided, the entity is in create mode."""
        # ES003 EB004 EB013 EB014 EB015
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |

        | entities |
        | | list_name | label | create_if  |
        | | e1        | E1    | ${q1} = '' |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", create=True, label=True),
                xpe.model_bind_meta_label("E1"),
                xpe.model_bind_meta_id(),
                xpe.model_setvalue_meta_id(),
                xpe.model_bind_meta_create(" /test_name/q1  = ''"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 1),
            ],
        )

    def test_implicit_create_mode__create_if__repeat(self):
        """Should find that when no entity_id is provided, the entity is in create mode."""
        # ES003 EB004 EB013 EB014 EB015 EB016
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |

        | entities |
        | | list_name | label | create_if  |
        | | e1        | ${q1} | ${q1} = '' |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, create=True, label=True
                ),
                xpe.model_bind_meta_label(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_id(meta_path="/r1"),
                xpe.model_setvalue_meta_id("/r1"),
                xpe.body_repeat_setvalue_meta_id(
                    "/x:group/x:repeat[@nodeset='/test_name/r1']", "/r1"
                ),
                xpe.model_bind_meta_create(" ../../../q1  = ''", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_implicit_update_mode__instance_required__error(self):
        """Should find that when an update mode, an instance for the entity is required."""
        # ES004 EB006 EB012 EB014 EB015 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=True,
            odk_validate_error__contains=[
                "Error evaluating field",
                "The problem was located in Calculate expression for ${entity}",
                "XPath evaluation: Instance referenced by instance(e1)/root",
                "does not exist",
            ],
        )

    def test_implicit_update_mode__entity_id__survey(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__entity_id__repeat(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015 EB016 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", "/x:r1", repeat=True, update=True),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, template=True, update=True
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__entity_id__with_csv_instance__survey(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | csv-external | e1   |       |
        | | text         | q1   | Q1    |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_csv("e1"),
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__entity_id__with_csv_instance__repeat(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015 EB016 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | csv-external | e1   |       |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_csv("e1"),
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", "/x:r1", repeat=True, update=True),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, template=True, update=True
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__entity_id__with_label__survey(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | label |
        | | e1        | ${q1}     | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True, label=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
                xpe.model_bind_meta_label("E1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__entity_id__with_label__repeat(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015 EB016
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | label |
        | | e1        | ${q1}     | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, update=True, label=True
                ),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, template=True, update=True, label=True
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_label("E1", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__entity_id__with_other_setvalue__survey(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015
        md = """
        | survey |
        | | type         | name | label | default |
        | | text         | q1   | Q1    | uuid()  |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
                xpq.setvalue(
                    "h:head/x:model", "/test_name/q1", "odk-instance-first-load", "uuid()"
                ),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 1),
            ],
        )

    def test_implicit_update_mode__entity_id__with_other_setvalue__repeat(self):
        """Should find that when an entity_id is provided, the entity is in update mode."""
        # ES004 EB006 EB012 EB014 EB015 EB016
        md = """
        | survey |
        | | type         | name | label | default |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | uuid()  |
        | | end_repeat   | r1   |       |         |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | entity_id |
        | | e1        | ${q1}     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", "/x:r1", repeat=True, update=True),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, template=True, update=True
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
                xpq.setvalue(
                    "h:head/x:model",
                    "/test_name/r1/q1",
                    "odk-instance-first-load",
                    "uuid()",
                ),
                xpq.setvalue(
                    "h:body/x:group/x:repeat[@nodeset='/test_name/r1']",
                    "/test_name/r1/q1",
                    "odk-new-repeat",
                    "uuid()",
                ),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 2),
            ],
        )

    def test_implicit_update_mode__update_if__survey(self):
        """Should find that when an update_if is provided, the condition is emitted."""
        # ES004 EB007 EB012 EB014 EB015
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | update_if   |
        | | e1        | ${q1}     | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
                xpe.model_bind_meta_update(" /test_name/q1  != ''"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_update_mode__update_if__repeat(self):
        """Should find that when an update_if is provided, the condition is emitted."""
        # ES004 EB007 EB012 EB014 EB015 EB016
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | update_if   |
        | | e1        | ${q1}     | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", "/x:r1", repeat=True, update=True),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, template=True, update=True
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_update(" ../../../q1  != ''", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_upsert_mode__survey(self):
        """Should find that entity_id, create_if, and update_if are provided, the entity is in upsert mode."""
        # ES004 EB009 EB012 EB014 EB015 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | update_if   | create_if   |
        | | e1        | ${q1}     | ${q1} != '' | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True, create=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
                xpe.model_bind_meta_update(" /test_name/q1  != ''"),
                xpe.model_bind_meta_create(" /test_name/q1  != ''"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_upsert_mode__repeat(self):
        """Should find that entity_id, create_if, and update_if are provided, the entity is in upsert mode."""
        # ES004 EB009 EB012 EB014 EB015 EB016 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | update_if   | create_if   |
        | | e1        | ${q1}     | ${q1} != '' | ${q1} != '' |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, update=True, create=True
                ),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, template=True, update=True, create=True
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_update(" ../../../q1  != ''", "/r1"),
                xpe.model_bind_meta_create(" ../../../q1  != ''", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_upsert_mode__with_label__survey(self):
        """Should find that entity_id, create_if, and update_if are provided, the entity is in upsert mode."""
        # ES004 EB009 EB012 EB014 EB015 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | text         | q1   | Q1    |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | update_if   | create_if   | label |
        | | e1        | ${q1}     | ${q1} != '' | ${q1} != '' | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta("e1", update=True, create=True, label=True),
                xpe.model_bind_meta_id(" /test_name/q1 "),
                xpe.model_bind_meta_baseversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_trunkversion("e1", "/test_name/q1"),
                xpe.model_bind_meta_branchid("e1", "/test_name/q1"),
                xpe.model_bind_meta_update(" /test_name/q1  != ''"),
                xpe.model_bind_meta_create(" /test_name/q1  != ''"),
                xpe.model_bind_meta_label("E1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_implicit_upsert_mode__with_label__repeat(self):
        """Should find that entity_id, create_if, and update_if are provided, the entity is in upsert mode."""
        # ES004 EB009 EB012 EB014 EB015 EB016 EB019
        md = """
        | survey |
        | | type         | name | label |
        | | begin_repeat | r1   | R1    |
        | | text         | q1   | Q1    |
        | | end_repeat   | r1   |       |
        | | csv-external | e1   |       |

        | entities |
        | | list_name | entity_id | update_if   | create_if   | label |
        | | e1        | ${q1}     | ${q1} != '' | ${q1} != '' | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_meta_instanceid(),
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, update=True, create=True, label=True
                ),
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1",
                    repeat=True,
                    template=True,
                    update=True,
                    create=True,
                    label=True,
                ),
                xpe.model_bind_meta_id(" ../../../q1 ", "/r1"),
                xpe.model_bind_meta_baseversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_trunkversion("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_branchid("e1", "current()/../../../q1", "/r1"),
                xpe.model_bind_meta_update(" ../../../q1  != ''", "/r1"),
                xpe.model_bind_meta_create(" ../../../q1  != ''", "/r1"),
                xpe.model_bind_meta_label("E1", "/r1"),
            ],
            xml__xpath_count=[
                ("/h:html//x:setvalue", 0),
            ],
        )

    def test_save_to__create__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1p1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/q1", "e1p1"),
            ],
        )

    def test_save_to__create__group(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
            ],
        )

    def test_save_to__create__repeat(self):
        """Should find the saveto binding is output for save_to in a repeat container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
            ],
        )

    def test_save_to__create__repeat_group(self):
        """Should find the saveto binding is output for save_to in nested group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | begin_group  | g1   | G1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_group    | g1   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/g1/q1", "e1p1"),
            ],
        )

    def test_save_to__create__group_repeat(self):
        """Should find the saveto binding is output for save_to in nested repeat container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_repeat   | r1   |       |         |
        | | end_group    | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/r1/q1", "e1p1"),
            ],
        )

    def test_save_to__update__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | text         | q1   | Q1    | e1p1    |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | label | entity_id |
        | | e1        | E1    | uuid()    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/q1", "e1p1"),
            ],
        )

    def test_save_to__update__group(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_group    | g1   |       |         |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | label | entity_id |
        | | e1        | E1    | uuid()    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
            ],
        )

    def test_save_to__update__repeat(self):
        """Should find the saveto binding is output for save_to in a repeat container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_repeat   | r1   |       |         |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | label | entity_id |
        | | e1        | E1    | uuid()    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
            ],
        )

    def test_save_to__update__repeat_group(self):
        """Should find the saveto binding is output for save_to in nested group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | begin_group  | g1   | G1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_group    | g1   |       |         |
        | | end_repeat   | r1   |       |         |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | label | entity_id |
        | | e1        | E1    | uuid()    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/g1/q1", "e1p1"),
            ],
        )

    def test_save_to__update__group_repeat(self):
        """Should find the saveto binding is output for save_to in nested repeat container."""
        # ES004 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_repeat   | r1   |       |         |
        | | end_group    | g1   |       |         |
        | | csv-external | e1   |       |         |

        | entities |
        | | list_name | label | entity_id |
        | | e1        | E1    | uuid()    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/r1/q1", "e1p1"),
            ],
        )

    def test_save_to__multiple_properties__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005
        md = """
        | survey |
        | | type | name | label | save_to |
        | | text | q1   | Q1    | e1p1    |
        | | text | q2   | Q2    | e1p2    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/q1", "e1p1"),
                xpe.model_bind_question_saveto("/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__group(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__repeat(self):
        """Should find the saveto binding is output for save_to in a repeat container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | text         | q2   | Q2    | e1p2    |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__repeat_group(self):
        """Should find the saveto binding is output for save_to in nested group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | begin_group  | g1   | G1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | text         | q2   | Q2    | e1p2    |
        | | end_group    | g1   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__group_repeat(self):
        """Should find the saveto binding is output for save_to in nested repeat container."""
        # ES004 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | text         | q2   | Q2    | e1p2    |
        | | end_repeat   | r1   |       |         |
        | | end_group    | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/r1/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__split_groups__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | end_group   | g1   |       |         |
        | | begin_group | g2   | G2    |         |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g2/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__split_groups__survey__with_var(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005
        # pyxform/#826 repro
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g1   |       |         |
        | | begin_group | g2   | G2    |         |
        | | text        | q3   | Q3    | e1p3    |
        | | text        | q4   | Q4    | e1p4    |
        | | end_group   | g2   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/q2", "e1p2"),
                xpe.model_bind_question_saveto("/g2/q3", "e1p3"),
                xpe.model_bind_question_saveto("/g2/q4", "e1p4"),
                xpe.model_bind_meta_label(" /test_name/g1/q1 ", ""),
            ],
        )

    def test_save_to__multiple_properties__split_groups__group(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | begin_group | g2   | G2    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | end_group   | g2   |       |         |
        | | begin_group | g3   | G3    |         |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g3   |       |         |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
                xpe.model_bind_question_saveto("/g1/g2/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/g3/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__split_groups__repeat(self):
        """Should find the saveto binding is output for save_to in a repeat container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | begin_group  | g1   | G1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | end_group    | g1   |       |         |
        | | begin_group  | g2   | G2    |         |
        | | text         | q2   | Q2    | e1p2    |
        | | end_group    | g2   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1", "/x:r1", repeat=True, create=True, label=True
                ),
                xpe.model_bind_question_saveto("/r1/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g2/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__uneven_groups__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | text        | q1   | Q1    | e1p1    |
        | | begin_group | g1   | G1    |         |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
                xpe.model_bind_question_saveto("/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__uneven_groups__group(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | begin_group | g2   | G2    |         |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g2   |       |         |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/g2/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_properties__uneven_groups__group__with_var(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005
        # pyxform/#823 repro
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | begin_group | g2   | G2    |         |
        | | text        | q2   | Q2    | e1p2    |
        | | end_group   | g2   |       |         |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q2} |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", repeat=None, create=True, label=True),
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/g2/q2", "e1p2"),
                xpe.model_bind_meta_label(" /test_name/g1/g2/q2 ", ""),
            ],
        )

    def test_save_to__multiple_properties__uneven_groups__repeat(self):
        """Should find the saveto binding is output for save_to in a repeat container."""
        # ES003 ES005
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1p1    |
        | | begin_group  | g2   | G2    |         |
        | | text         | q2   | Q2    | e1p2    |
        | | end_group    | g2   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g2/q2", "e1p2"),
            ],
        )

    def test_save_to__multiple_entities__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005 ES006
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | begin_group | g1   | G1    |         |
        | | text        | q2   | Q2    | e2#e2p1 |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/q2", "e2p1"),
            ],
        )

    def test_save_to__multiple_entities__group(self):
        """Should find the saveto binding is output for save_to in a group container."""
        # ES003 ES005 ES006
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1#e1p1 |
        | | begin_group | g2   | G2    |         |
        | | text        | q2   | Q2    | e2#e2p1 |
        | | end_group   | g2   |       |         |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/g2/q2", "e2p1"),
            ],
        )

    def test_save_to__multiple_entities__repeat(self):
        """Should find the saveto binding is output for save_to in a repeat container."""
        # ES003 ES005 ES006
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g1   | G1    |         |
        | | text         | q2   | Q2    | e2#e2p1 |
        | | end_group    | g1   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/q2", "e2p1"),
            ],
        )

    def test_save_to__multiple_entities__repeat_group(self):
        """Should find the saveto binding is output for save_to in nested group container."""
        # ES003 ES005 ES006
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_repeat | r1   | R1    |         |
        | | begin_group  | g1   | G1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g2   | G1    |         |
        | | text         | q2   | Q2    | e2#e2p1 |
        | | end_group    | g2   |       |         |
        | | end_group    | g1   |       |         |
        | | end_repeat   | r1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/r1/g1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/r1/g1/g2/q2", "e2p1"),
            ],
        )

    def test_save_to__multiple_entities__group_repeat(self):
        """Should find the saveto binding is output for save_to in nested repeat container."""
        # ES004 ES005 ES006
        md = """
        | survey |
        | | type         | name | label | save_to |
        | | begin_group  | g1   | G1    |         |
        | | begin_repeat | r1   | R1    |         |
        | | text         | q1   | Q1    | e1#e1p1 |
        | | begin_group  | g2   | G1    |         |
        | | text         | q2   | Q2    | e2#e2p1 |
        | | end_group    | g2   |       |         |
        | | end_repeat   | r1   |       |         |
        | | end_group    | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        | | e2        | E2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_bind_question_saveto("/g1/r1/q1", "e1p1"),
                xpe.model_bind_question_saveto("/g1/r1/g2/q2", "e2p1"),
            ],
        )

    def test_var__multiple_var__cross_boundary__before(self):
        """Should find the deepest scope preferenced and outside vars resolve to one item."""
        # ES005 EB016 EB023
        md = """
        | survey |
        | | type          | name | label |
        | | begin_group   | g1   | G1    |
        | |   begin_group | g2   | G2    |
        | |     text      | q2   | Q2    |
        | |   end_group   | g2   |       |
        | | end_group     | g1   |       |
        | | begin_repeat  | r1   | R1    |
        | |   text        | q1   | Q1    |
        | | end_repeat    | r1   |       |

        | entities |
        | | list_name | label                |
        | | e1        | concat(${q1}, ${q2}) |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_meta_label(
                    "concat( ../../../q1 ,  /test_name/g1/g2/q2 )", "/r1"
                ),
            ],
        )

    def test_var__multiple_var__cross_boundary__after(self):
        """Should find the deepest scope preferenced and outside vars resolve to one item."""
        # ES005 EB016 EB023
        # pyxform/#822 repro
        md = """
        | survey |
        | | type          | name | label |
        | | begin_repeat  | r1   | R1    |
        | |   text        | q1   | Q1    |
        | | end_repeat    | r1   |       |
        | | begin_group   | g1   | G1    |
        | |   begin_group | g2   | G2    |
        | |     text      | q2   | Q2    |
        | |   end_group   | g2   |       |
        | | end_group     | g1   |       |

        | entities |
        | | list_name | label                |
        | | e1        | concat(${q1}, ${q2}) |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta(
                    "e1",
                    "/x:r1[not(@jr:template)]",
                    create=True,
                    label=True,
                    repeat=True,
                ),
                xpe.model_bind_meta_label(
                    "concat( ../../../q1 ,  /test_name/g1/g2/q2 )", "/r1"
                ),
            ],
        )

    def test_single_entity__no_repeats__survey(self):
        """Should find the saveto binding is output for save_to in a survey container."""
        # ES003 ES005 EB024
        # pyxform/#825 repro
        md = """
        | survey |
        | | type        | name | label | save_to |
        | | begin_group | g1   | G1    |         |
        | | text        | q1   | Q1    | e1p1    |
        | | end_group   | g1   |       |         |

        | entities |
        | | list_name | label |
        | | e1        | ${q1} |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpe.model_instance_meta("e1", "", create=True, repeat=None, label=True),
                xpe.model_bind_question_saveto("/g1/q1", "e1p1"),
                xpe.model_bind_meta_label(" /test_name/g1/q1 ", ""),
            ],
        )


class TestReferenceSource(PyxformTestCase):
    def test_missing_property_and_question_name__error(self):
        """Should raise an error if both property_name and question_name are None."""
        with self.assertRaises(PyXFormError) as err:
            ReferenceSource(path=ContainerPath.default(), row=1)
        self.assertEqual(
            err.exception.args[0], ErrorCode.INTERNAL_002.value.format(path="/survey")
        )
