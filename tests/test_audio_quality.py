# -*- coding: utf-8 -*-
from tests.pyxform_test_case import PyxformTestCase


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
                'xmlns:odk="http://www.opendatakit.org/xforms"',
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
                'xmlns:odk="http://www.opendatakit.org/xforms"',
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
                'xmlns:odk="http://www.opendatakit.org/xforms"',
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
                'xmlns:odk="http://www.opendatakit.org/xforms"',
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

    def test_missing(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | audio  | audio    | Audio |                |
            """,
            xml__contains=[
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/audio" type="binary"/>',
            ],
            warnings__contains=["[row : 2] No quality parameter specified for audio. This will soon use an internal recorder in Collect. If you need to use a specific recording app, specify quality=external."]
        )
