"""
## Geo control traceability

Each test should reference one (or more) requirements from these lists.

- parameter 'reference-geometry':
  - Validation
    - RG001: must match the name of a secondary instance or repeat.
    - RG002: must not match multiple secondary instance names.
    - RG003: must be a nodeset target type that is supported.
  - Behaviour
    - RG004: when the parameter is absent, body control does not have a child itemset.
    - RG005: when the parameter is present, the body control has a child itemset element.
    - RG006: the itemset's nodeset attribute is an instance() lookup for secondary instance targets.
    - RG007: the itemset's nodeset attribute is an path expression for repeat targets.
    - RG008: the nodeset target can be an internal choice list instance.
    - RG009: the nodeset target can be an entity list instance.
    - RG010: the nodeset target can be an repeat.
    - RG011: the nodeset target can be an external file instance.
    - RG012: the nodeset target can be an select_*_from_file instance.
    - RG013: the itemset's label uses itext() when using translated internal choices.
    - RG014: the itemset's @nodeset instance() lookup has a choice filter, if any, appended.
    - RG015: supported nodeset target types can be used with unsupported nodeset target types.
    - RG016: the parameter is not emitted as an attribute of the body control.
"""

from unittest import expectedFailure

from pyxform import constants as co
from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq

GEO_TYPES = ("geoshape", "geotrace", "geopoint")


class GeoWidgetsTest(PyxformTestCase):
    """Test geo widgets class."""

    def test_gps_type(self):
        self.assertPyxformXform(
            name="geo",
            md="""
            | survey |      |          |       |
            |        | type |   name   | label |
            |        | gps  | location | GPS   |
            """,
            xml__contains=["geopoint"],
        )

    def test_gps_alias(self):
        self.assertPyxformXform(
            name="geo_alias",
            md="""
            | survey |          |          |       |
            |        | type     | name     | label |
            |        | geopoint | location | GPS   |
            """,
            xml__contains=["geopoint"],
        )

    def test_geo_widgets_types(self):
        """
        this test could be broken into multiple smaller tests.
        """
        self.assertPyxformXform(
            name="geos",
            md="""
            | survey |              |            |                   |
            |        | type         | name       | label             |
            |        | begin_repeat | repeat     |                   |
            |        | geopoint     | point      | Record Geopoint   |
            |        | note         | point_note | Point ${point}    |
            |        | geotrace     | trace      | Record a Geotrace |
            |        | note         | trace_note | Trace: ${trace}   |
            |        | geoshape     | shape      | Record a Geoshape |
            |        | note         | shape_note | Shape: ${shape}   |
            |        | end_repeat   |            |                   |
            """,
            xml__contains=[
                "<point/>",
                "<point_note/>",
                "<trace/>",
                "<trace_note/>",
                "<shape/>",
                "<shape_note/>",
                '<bind nodeset="/geos/repeat/point" type="geopoint"/>',
                '<bind nodeset="/geos/repeat/point_note" readonly="true()" '
                'type="string"/>',
                '<bind nodeset="/geos/repeat/trace" type="geotrace"/>',
                '<bind nodeset="/geos/repeat/trace_note" readonly="true()" '
                'type="string"/>',
                '<bind nodeset="/geos/repeat/shape" type="geoshape"/>',
                '<bind nodeset="/geos/repeat/shape_note" readonly="true()" '
                'type="string"/>',
            ],
        )


class TestParameterIncremental(PyxformTestCase):
    def test_not_emitted_by_default(self):
        """Should find that the parameter is not included as a default control attribute."""
        md = """
        | survey |
        | | type   | name | label |
        | | {type} | q1   | Q1    |
        """
        types = ["geoshape", "geotrace", "geopoint", "integer", "note"]
        for t in types:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        "/h:html/h:body/x:input[@ref='/test_name/q1' and not(@incremental)]",
                    ],
                )

    def test_with_incremental__geoshape_geotrace__ok(self):
        """Should find that the parameter is emitted as a control attribute if specified."""
        md = """
        | survey |
        | | type   | name | label | parameters       |
        | | {type} | q1   | Q1    | incremental=true |
        """
        types = ["geoshape", "geotrace"]
        for t in types:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        f"/h:html/h:head/x:model/x:bind[@nodeset='/test_name/q1' and @type='{t}']",
                        "/h:html/h:body/x:input[@ref='/test_name/q1' and @incremental='true']",
                    ],
                )

    def test_with_incremental__geoshape_geotrace____aliases__ok(self):
        """Should find that the parameter is emitted as a control attribute if specified."""
        md = """
        | survey |
        | | type   | name | label | parameters      |
        | | {type} | q1   | Q1    | incremental={value} |
        """
        types = ["geoshape", "geotrace"]
        values = ["yes", "true()"]
        for t in types:
            for v in values:
                with self.subTest((t, v)):
                    self.assertPyxformXform(
                        md=md.format(type=t, value=v),
                        xml__xpath_match=[
                            f"/h:html/h:head/x:model/x:bind[@nodeset='/test_name/q1' and @type='{t}']",
                            "/h:html/h:body/x:input[@ref='/test_name/q1' and @incremental='true']",
                        ],
                    )

    def test_with_incremental__geoshape_geotrace____wrong_value__error(self):
        """Should raise an error if an unrecognised value is specified."""
        md = """
        | survey |
        | | type   | name | label | parameters          |
        | | {type} | q1   | Q1    | incremental={value} |
        """
        types = ["geoshape", "geotrace"]
        values = ["yeah", "false"]
        for t in types:
            for v in values:
                with self.subTest((t, v)):
                    self.assertPyxformXform(
                        md=md.format(type=t, value=v),
                        errored=True,
                        error__contains=[
                            ErrorCode.SURVEY_003.value.format(
                                sheet=co.SURVEY, column=co.PARAMETERS, row=2
                            )
                        ],
                    )

    def test_with_incremental__geopoint__error(self):
        """Should raise an error if specified for geopoint."""
        md = """
        | survey |
        | | type     | name | label | parameters       |
        | | geopoint | q1   | Q1    | incremental=true |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.SURVEY_005.value.format(
                    row=2,
                    accepted=co.ParametersGeoPoint.value_str_sorted(),
                    rejected="incremental",
                ),
            ],
        )

    def test_with_incremental__wrong_type_with_params__error(self):
        """Should raise an error if specified for other question types with parameters."""
        md = """
        | survey |
        | | type   | name | label | parameters       |
        | | audio  | q1   | Q1    | incremental=true |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.SURVEY_005.value.format(
                    row=2,
                    accepted=co.ParametersAudio.value_str_sorted(),
                    rejected="incremental",
                ),
            ],
        )

    def test_with_incremental__wrong_type_no_params__ok(self):
        """Should not raise an error if specified for other question types without parameters."""
        md = """
        | survey |
        | | type   | name | label | parameters       |
        | | {type} | q1   | Q1    | incremental=true |
        """
        types = ["integer", "note"]
        for t in types:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        "/h:html/h:body/x:input[@ref='/test_name/q1' and not(@incremental)]",
                    ],
                )


class TestParameterReferenceGeometryParsing(PyxformTestCase):
    def test_list_name__not_found__error(self):
        """Should raise an error when the list_name is not resolvable."""
        # RG001
        md = """
        | survey |
        | | type   | name | label | parameters            |
        | | {type} | q1   | Q1    | reference-geometry=c1 |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[ErrorCode.SURVEY_006.value.format(row=2)],
                )

    def test_list_name__ambiguous__error(self):
        """Should raise an error when the list_name matches both a choice and entity list_name."""
        # RG002
        md = """
        | survey |
        | | type         | name | label | parameters            |
        | | csv-external | c1   |       |                       |
        | | {type}       | q1   | Q1    | reference-geometry=c1 |

        | choices |
        | | list_name | name | label | geometry |
        | | c1        | n1   | N1    | 123 ...  |

        | entities |
        | | list_name | label |
        | | c1        | E1    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[
                        "The same instance id will be generated for different external instance source URIs"
                    ],
                )

    def test_not_supported__pulldata__error(self):
        """Should raise an error when the secondary instance triggers are not supported."""
        # RG003
        md = """
        | survey |
        | | type          | name | label | parameters            | calculation                            |
        | | {type}        | q1   | Q1    | reference-geometry=c1 |                                        |
        | | calculate     | q2   | Q2    |                       | pulldata('c1', 'name', 'name', 'test') |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[ErrorCode.SURVEY_006.value.format(row=2)],
                )

    def test_not_supported__last_saved__error(self):
        """Should raise an error when the secondary instance triggers are not supported."""
        # RG003
        md = """
        | survey |
        | | type      | name | label | parameters                      | calculation        |
        | | text      | q1   | Q1    |                                 |                    |
        | | calculate | c1   | C1    |                                 | ${{last-saved#q1}} |
        | | {type}    | q2   | Q2    | reference-geometry=__last-saved |                    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[ErrorCode.SURVEY_006.value.format(row=4)],
                )

    def test_not_supported__select_one_external__error(self):
        """Should raise an error when the secondary instance triggers are not supported."""
        # RG003
        md = """
        | survey |
        | | type                   | name | label | parameters            | choice_filter |
        | | {type}                 | q1   | Q1    | reference-geometry=c1 |               |
        | | select_one_external c1 | q2   | Q2    |                       | false()       |

        | external_choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[ErrorCode.SURVEY_006.value.format(row=2)],
                )

    # The search() causes no instance to be emitted but the reference-geometry value is allowed.
    # Ideally this is an error case but detecting it accurately may not be straightforward.
    @expectedFailure
    def test_not_supported__search__error(self):
        """Should raise an error when the secondary instance triggers are not supported."""
        # RG003
        md = """
        | survey |
        | | type          | name | label | parameters            | appearance        |
        | | select_one c1 | q3   | Q3    |                       | search('my_file') |
        | | {type}        | q1   | Q1    | reference-geometry=c1 |                   |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[ErrorCode.SURVEY_006.value.format(row=2)],
                )


class TestParameterReferenceGeometryOutput(PyxformTestCase):
    def test_not_emitted_by_default(self):
        """Should find that a child itemset is not emitted."""
        # RG004
        md = """
        | survey |
        | | type   | name | label |
        | | {type} | q1   | Q1    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_bind("q1", t),
                        """
                        /h:html/h:body/x:input[
                          @ref='/test_name/q1'
                          and count(@*) = 1
                          and not(./x:itemset)
                        ]
                        """,
                    ],
                )

    def test_choices_sheet__ok(self):
        """Should find that a child itemset is emitted, with default value/label."""
        # RG005 RG006 RG008 RG016
        md = """
        | survey |
        | | type   | name | label | parameters            |
        | | {type} | q1   | Q1    | reference-geometry=c1 |

        | choices |
        | | list_name | name | label | geometry |
        | | c1        | n1   | N1    | 123 ...  |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("c1"),
                        xpq.model_instance_bind("q1", t),
                        xpq.body_itemset(
                            q_name="q1",
                            nodeset="instance('c1')/root/item",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_choices_sheet__translated__ok(self):
        """Should find that a child itemset is emitted, with translations label."""
        # RG005 RG006 RG008 RG013 RG016
        md = """
        | survey |
        | | type   | name | label | parameters            |
        | | {type} | q1   | Q1    | reference-geometry=c1 |

        | choices |
        | | list_name | name | label::English (en) | geometry |
        | | c1        | n1   | N1                  | 123 ...  |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("c1"),
                        xpq.model_instance_bind("q1", t),
                        xpq.body_itemset(
                            q_name="q1",
                            nodeset="instance('c1')/root/item",
                            label_ref="jr:itext(itextId)",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_choices_sheet__choice_filter__ok(self):
        """Should find that a child itemset is emitted, with a choice_filter predicate."""
        # RG005 RG006 RG008 RG014 RG016
        md = """
        | survey |
        | | type   | name | label | parameters            | choice_filter  |
        | | text   | q1   | Q1    |                       |                |
        | | {type} | q2   | Q2    | reference-geometry=c1 | name = ${{q1}} |

        | choices |
        | | list_name | name | label | geometry |
        | | c1        | n1   | N1    | 123 ...  |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("c1"),
                        xpq.model_instance_bind("q2", t),
                        xpq.body_itemset(
                            q_name="q2",
                            nodeset="instance('c1')/root/item[name =  /test_name/q1 ]",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_entity_list__ok(self):
        """Should find that a child itemset is emitted, with default value/label."""
        # RG005 RG006 RG009 RG016
        md = """
        | survey |
        | | type         | name | label | parameters            |
        | | csv-external | e1   |       |                       |
        | | {type}       | q1   | Q1    | reference-geometry=e1 |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("e1"),
                        xpq.model_instance_bind("q1", t),
                        xpq.body_itemset(
                            q_name="q1",
                            nodeset="instance('e1')/root/item",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_entity_list__choice_filter__ok(self):
        """Should find that a child itemset is emitted, with a choice_filter predicate."""
        # RG005 RG006 RG009 RG014 RG016
        md = """
        | survey |
        | | type         | name | label | parameters            | choice_filter |
        | | csv-external | e1   |       |                       |               |
        | | {type}       | q1   | Q1    | reference-geometry=e1 | region = 1    |

        | entities |
        | | list_name | label |
        | | e1        | E1    |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("e1"),
                        xpq.model_instance_bind("q1", t),
                        xpq.body_itemset(
                            q_name="q1",
                            nodeset="instance('e1')/root/item[region = 1]",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_pyxform_reference__ok(self):
        """Should find that a child itemset is emitted, with geometry value/label."""
        # RG005 RG007 RG010 RG016
        md = """
        | survey |
        | | type         | name     | label | parameters                 |
        | | begin_repeat | r1       | R1    |                            |
        | | text         | geometry | Q1    |                            |
        | | end_repeat   | r1       |       |                            |
        | | {type}       | q2       | Q2    | reference-geometry=${{r1}} |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_item("r1[not(@jr:template)]"),
                        xpq.model_instance_bind("q2", t),
                        xpq.body_itemset(
                            q_name="q2",
                            nodeset="/test_name/r1[./geometry != '']",
                            value_ref="geometry",
                            label_ref="geometry",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_pyxform_reference__choice_filter__ok(self):
        """Should find that a child itemset is emitted, with a choice_filter predicate."""
        # RG005 RG007 RG010 RG014 RG016
        md = """
        | survey |
        | | type         | name     | label | parameters                 | choice_filter |
        | | begin_repeat | r1       | R1    |                            |               |
        | | geopoint     | geometry | Q1    |                            |               |
        | | text         | q2       | Q2    |
        | | end_repeat   | r1       |       |                            |               |
        | | {type}       | q3       | Q3    | reference-geometry=${{r1}} | ${{q2}} = 1   |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_item("r1[not(@jr:template)]"),
                        xpq.model_instance_bind("q3", t),
                        xpq.body_itemset(
                            q_name="q3",
                            nodeset="/test_name/r1[ ./q2  = 1]",
                            value_ref="geometry",
                            label_ref="geometry",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_pyxform_reference__inside_repeat__ok(self):
        """Should find that a child itemset is emitted, with geometry value/label."""
        # RG005 RG007 RG010 RG016
        md = """
        | survey |
        | | type         | name     | label | parameters                 |
        | | begin_repeat | r1       | R1    |                            |
        | | {type}       | geometry | Q1    | reference-geometry=${{r1}} |
        | | end_repeat   | r1       |       |                            |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_item("r1[not(@jr:template)]"),
                        xpq.model_instance_bind("r1/geometry", t),
                        xpq.body_itemset(
                            q_name="r1/geometry",
                            nodeset="/test_name/r1[./geometry != '']",
                            value_ref="geometry",
                            label_ref="geometry",
                            extra_q_assertions="and not(@reference-geometry)",
                            body_path="/x:group/x:repeat",
                        ),
                    ],
                )

    def test_external_file__ok(self):
        """Should find that a child itemset is emitted, with default value/label."""
        # RG005 RG006 RG011 RG016
        md = """
        | survey |
        | | type   | name | label | parameters            |
        | | {ext}  | x1   |       |                       |
        | | {type} | q2   | Q2    | reference-geometry=x1 |
        """
        for t in GEO_TYPES:
            for ext in co.EXTERNAL_INSTANCE_TYPES:
                with self.subTest((t, ext)):
                    self.assertPyxformXform(
                        md=md.format(type=t, ext=ext),
                        xml__xpath_match=[
                            xpq.model_instance_exists("x1"),
                            xpq.model_instance_bind("q2", t),
                            xpq.body_itemset(
                                q_name="q2",
                                nodeset="instance('x1')/root/item",
                                extra_q_assertions="and not(@reference-geometry)",
                            ),
                        ],
                    )

    def test_external_file__choice_filter__ok(self):
        """Should find that a child itemset is emitted, with a choice_filter predicate."""
        # RG005 RG006 RG011 RG014 RG016
        md = """
        | survey |
        | | type   | name | label | parameters            | choice_filter |
        | | {ext}  | x1   |       |                       |               |
        | | {type} | q2   | Q2    | reference-geometry=x1 | region = 1    |
        """
        for t in GEO_TYPES:
            for ext in co.EXTERNAL_INSTANCE_TYPES:
                with self.subTest((t, ext)):
                    self.assertPyxformXform(
                        md=md.format(type=t, ext=ext),
                        xml__xpath_match=[
                            xpq.model_instance_exists("x1"),
                            xpq.model_instance_bind("q2", t),
                            xpq.body_itemset(
                                q_name="q2",
                                nodeset="instance('x1')/root/item[region = 1]",
                                extra_q_assertions="and not(@reference-geometry)",
                            ),
                        ],
                    )

    def test_select_from_file__ok(self):
        """Should find that a child itemset is emitted, with default value/label."""
        # RG005 RG006 RG012 RG016
        md = """
        | survey |
        | | type                         | name | label | parameters            |
        | | select_one_from_file s1{ext} | q1   | Q1    |                       |
        | | {type}                       | q2   | Q2    | reference-geometry=s1 |
        """
        for t in GEO_TYPES:
            for ext in co.EXTERNAL_INSTANCE_EXTENSIONS:
                with self.subTest((t, ext)):
                    self.assertPyxformXform(
                        md=md.format(type=t, ext=ext),
                        xml__xpath_match=[
                            xpq.model_instance_exists("s1"),
                            xpq.model_instance_bind("q2", t),
                            xpq.body_itemset(
                                q_name="q2",
                                nodeset="instance('s1')/root/item",
                                extra_q_assertions="and not(@reference-geometry)",
                            ),
                        ],
                    )

    def test_select_from_file__choice_filter__ok(self):
        """Should find that a child itemset is emitted, with a choice_filter predicate."""
        # RG005 RG006 RG012 RG014 RG016
        md = """
        | survey |
        | | type                         | name | label | parameters            | choice_filter |
        | | select_one_from_file s1{ext} | q1   | Q1    |                       |               |
        | | {type}                       | q2   | Q2    | reference-geometry=s1 | region = 1    |
        """
        for t in GEO_TYPES:
            for ext in co.EXTERNAL_INSTANCE_EXTENSIONS:
                with self.subTest((t, ext)):
                    self.assertPyxformXform(
                        md=md.format(type=t, ext=ext),
                        xml__xpath_match=[
                            xpq.model_instance_exists("s1"),
                            xpq.model_instance_bind("q2", t),
                            xpq.body_itemset(
                                q_name="q2",
                                nodeset="instance('s1')/root/item[region = 1]",
                                extra_q_assertions="and not(@reference-geometry)",
                            ),
                        ],
                    )

    def test_select_from_file__params_value_label__ok(self):
        """Should find that a child itemset is emitted, with default value/label."""
        # RG005 RG006 RG012 RG016
        md = """
        | survey |
        | | type                         | name | label | parameters            |
        | | select_one_from_file s1{ext} | q1   | Q1    | value=v, label=l      |
        | | {type}                       | q2   | Q2    | reference-geometry=s1 |
        """
        for t in GEO_TYPES:
            for ext in co.EXTERNAL_INSTANCE_EXTENSIONS:
                with self.subTest((t, ext)):
                    self.assertPyxformXform(
                        md=md.format(type=t, ext=ext),
                        xml__xpath_match=[
                            xpq.model_instance_exists("s1"),
                            # The "select from file" params are separate to reference-geometry.
                            xpq.body_itemset(
                                q_name="q1",
                                q_type="select1",
                                nodeset="instance('s1')/root/item",
                                value_ref="v",
                                label_ref="l",
                            ),
                            xpq.model_instance_bind("q2", t),
                            xpq.body_itemset(
                                q_name="q2",
                                nodeset="instance('s1')/root/item",
                                extra_q_assertions="and not(@reference-geometry)",
                            ),
                        ],
                    )

    def test_select_one_external__ok(self):
        """Should find that a child itemset is emitted, with default value/label."""
        # RG005 RG006 RG011 RG015 RG016
        # select_one_external doesn't generate an instance, so the csv-external does that,
        # and the file name "itemsets.csv" is the hard-coded file name  external_choices.
        md = """
        | survey |
        | | type                    | name     | label | parameters                  | choice_filter  | relevant |
        | | csv-external            | itemsets |       |                             |                |          |
        | | select_one_external c1  | q1       | Q1    |                             | false()        | false()  |
        | | {type}                  | q2       | Q2    | reference-geometry=itemsets |                |          |

        | external_choices |
        | | list_name | name | label | geometry |
        | | c1        | n1   | N1    | 123 ...  |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("itemsets"),
                        xpq.model_instance_bind("q2", t),
                        xpq.body_itemset(
                            q_name="q2",
                            nodeset="instance('itemsets')/root/item",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )

    def test_select_one_external__choice_filter__ok(self):
        """Should find that a child itemset is emitted, with a choice_filter predicate."""
        # RG005 RG006 RG011 RG014 RG015 RG016
        md = """
        | survey |
        | | type                    | name     | label | parameters                  | choice_filter  | relevant |
        | | csv-external            | itemsets |       |                             |                |          |
        | | select_one_external c1  | q1       | Q1    |                             | false()        | false()  |
        | | {type}                  | q2       | Q2    | reference-geometry=itemsets | name = 'n1'    |          |

        | external_choices |
        | | list_name | name | label | geometry |
        | | c1        | n1   | N1    | 123 ...  |
        """
        for t in GEO_TYPES:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    xml__xpath_match=[
                        xpq.model_instance_exists("itemsets"),
                        xpq.model_instance_bind("q2", t),
                        xpq.body_itemset(
                            q_name="q2",
                            nodeset="instance('itemsets')/root/item[name = 'n1']",
                            extra_q_assertions="and not(@reference-geometry)",
                        ),
                    ],
                )
