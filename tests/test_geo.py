"""
Test geo widgets.
"""

from pyxform import constants as co
from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase


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
        values = ["", "yeah", "false"]
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

    def test_with_incremental__wrong_type_with_params__error(self):
        """Should raise an error if specified for other question types with parameters."""
        md = """
        | survey |
        | | type   | name | label | parameters       |
        | | {type} | q1   | Q1    | incremental=true |
        """
        types = ["geopoint", "audio"]
        for t in types:
            with self.subTest(t):
                self.assertPyxformXform(
                    md=md.format(type=t),
                    errored=True,
                    error__contains=[
                        "The following are invalid parameter(s): 'incremental'."
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
