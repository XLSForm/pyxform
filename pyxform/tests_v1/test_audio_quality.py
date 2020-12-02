# -*- coding: utf-8 -*-
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class AudioQualityTest(PyxformTestCase):
    def test_voice_only(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | audio  | audio    | Audio | quality=voice-only |
            """,
            xml__contains=[
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/audio" type="binary" odk:quality="voice-only"/>',
            ],
        )

    def test_low(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | audio  | audio    | Audio | quality=low |
            """,
            xml__contains=[
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/audio" type="binary" odk:quality="low"/>',
            ],
        )

    def test_normal(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | audio  | audio    | Audio | quality=normal |
            """,
            xml__contains=[
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/audio" type="binary" odk:quality="normal"/>',
            ],
        )

    def test_external(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | audio  | audio    | Audio | quality=external |
            """,
            xml__contains=[
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/audio" type="binary" odk:quality="external"/>',
            ],
        )

    def test_foo_fails(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | audio  | audio    | Audio | quality=foo |
            """,
            errored=True,
            error__contains=["Invalid value for quality."],
        )
