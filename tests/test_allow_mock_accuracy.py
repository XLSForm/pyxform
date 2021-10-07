# -*- coding: utf-8 -*-
from tests.pyxform_test_case import PyxformTestCase


class AllowMockAccuracyTest(PyxformTestCase):
    def test_geopoint(self):
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

    def test_geoshape(self):
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

    def test_geotrace(self):
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

    def test_foo_fails(self):
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
