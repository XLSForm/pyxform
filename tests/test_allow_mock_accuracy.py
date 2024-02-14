from tests.pyxform_test_case import PyxformTestCase


class GeoParameterTest(PyxformTestCase):
    def test_geopoint_allow_mock_accuracy(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geopoint  | geopoint    | Geopoint | allow-mock-accuracy=true |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/geopoint" type="geopoint" odk:allow-mock-accuracy="true"/>',
            ],
        )

        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geopoint  | geopoint    | Geopoint | allow-mock-accuracy=false |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/geopoint" type="geopoint" odk:allow-mock-accuracy="false"/>',
            ],
        )

    def test_geoshape_allow_mock_accuracy(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geoshape  | geoshape    | Geoshape | allow-mock-accuracy=true |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/geoshape" type="geoshape" odk:allow-mock-accuracy="true"/>',
            ],
        )

        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geoshape  | geoshape    | Geoshape | allow-mock-accuracy=false |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/geoshape" type="geoshape" odk:allow-mock-accuracy="false"/>',
            ],
        )

    def test_geotrace_allow_mock_accuracy(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geotrace  | geotrace    | Geotrace | allow-mock-accuracy=true |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/geotrace" type="geotrace" odk:allow-mock-accuracy="true"/>',
            ],
        )

        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geotrace  | geotrace    | Geotrace | allow-mock-accuracy=false |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/geotrace" type="geotrace" odk:allow-mock-accuracy="false"/>',
            ],
        )

    def test_foo_allow_mock_accuracy_value_fails(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geopoint  | geopoint    | Geopoint | allow-mock-accuracy=foo |
            """,
            errored=True,
            error__contains=["Invalid value for allow-mock-accuracy."],
        )

        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geoshape  | geoshape    | Geoshape | allow-mock-accuracy=foo |
            """,
            errored=True,
            error__contains=["Invalid value for allow-mock-accuracy."],
        )

        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geotrace  | geotrace    | Geotrace | allow-mock-accuracy=foo |
            """,
            errored=True,
            error__contains=["Invalid value for allow-mock-accuracy."],
        )

    def test_numeric_geopoint_capture_accuracy_is_passed_through(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geopoint  | geopoint    | Geopoint | capture-accuracy=2.5     |
            """,
            xml__xpath_match=[
                "/h:html/h:body/x:input[@accuracyThreshold='2.5' and @ref='/data/geopoint']"
            ],
        )

    def test_string_geopoint_capture_accuracy_errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geopoint  | geopoint    | Geopoint | capture-accuracy=foo     |
            """,
            errored=True,
            error__contains=["Parameter capture-accuracy must have a numeric value"],
        )

    def test_geopoint_warning_accuracy_is_passed_through(self):
        self.assertPyxformXform(
            name="data",
            md="""
        | survey |           |             |          |                          |
        |        | type      | name        | label    | parameters               |
        |        | geopoint  | geopoint    | Geopoint | warning-accuracy=5       |
        """,
            xml__xpath_match=[
                "/h:html/h:body/x:input[@unacceptableAccuracyThreshold='5' and @ref='/data/geopoint']"
            ],
        )

    def test_string_geopoint_warning_accuracy_errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geopoint  | geopoint    | Geopoint | warning-accuracy=foo     |
            """,
            errored=True,
            error__contains=["Parameter warning-accuracy must have a numeric value"],
        )

    def test_geopoint_parameters_combine(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                                                             |
            |        | type      | name        | label    | parameters                                                  |
            |        | geopoint  | geopoint    | Geopoint | warning-accuracy=5.5 capture-accuracy=2 allow-mock-accuracy=true |
            """,
            xml__xpath_match=[
                "/h:html/h:body/x:input[@unacceptableAccuracyThreshold='5.5' and @accuracyThreshold='2' and @ref='/data/geopoint']",
                "/h:html/h:head/x:model/x:bind[@nodeset='/data/geopoint' and @odk:allow-mock-accuracy='true']",
            ],
        )

    def test_geoshape_with_accuracy_parameters_errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geoshape  | geoshape    | Geoshape | warning-accuracy=5       |
            """,
            errored=True,
            error__contains=["invalid parameter(s): 'warning-accuracy'"],
        )

    def test_geotrace_with_accuracy_parameters_errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |             |          |                          |
            |        | type      | name        | label    | parameters               |
            |        | geotrace  | geotrace    | Geotrace | warning-accuracy=5       |
            """,
            errored=True,
            error__contains=["invalid parameter(s): 'warning-accuracy'"],
        )
