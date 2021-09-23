# -*- coding: utf-8 -*-
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


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
                'xmlns:orx="http://openrosa.org/xforms"',
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
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/geopoint" type="geopoint" odk:allow-mock-accuracy="false"/>',
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
