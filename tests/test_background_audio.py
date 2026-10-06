from tests.pyxform_test_case import PyxformTestCase


class BackgroundAudioTest(PyxformTestCase):
    def test_background_audio(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                  |              |
            |        | type             | name         |
            |        | background-audio | my_recording |
            """,
            xml__contains=[
                '<bind nodeset="/data/my_recording" type="binary"/>',
                '<odk:recordaudio event="odk-instance-load" ref="/data/my_recording"/>',
            ],
        )

    def test_background_audio_voice_only(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                  |              |                      |
            |        | type             | name         | parameters           |
            |        | background-audio | my_recording | quality=voice-only |
            """,
            xml__contains=[
                '<odk:recordaudio event="odk-instance-load" ref="/data/my_recording" odk:quality="voice-only"/>',
            ],
        )

    def test_background_audio_low(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                  |              |                      |
            |        | type             | name         | parameters           |
            |        | background-audio | my_recording | quality=low |
            """,
            xml__contains=[
                '<odk:recordaudio event="odk-instance-load" ref="/data/my_recording" odk:quality="low"/>',
            ],
        )

    def test_background_audio_normal(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                  |              |                      |
            |        | type             | name         | parameters           |
            |        | background-audio | my_recording | quality=normal |
            """,
            xml__contains=[
                '<odk:recordaudio event="odk-instance-load" ref="/data/my_recording" odk:quality="normal"/>',
            ],
        )

    def test_external_quality_fails(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                  |              |                      |
            |        | type             | name         | parameters           |
            |        | background-audio | my_recording | quality=external |
            """,
            errored=True,
            error__contains=["Invalid value for quality."],
        )

    def test_foo_quality_fails(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                  |              |                      |
            |        | type             | name         | parameters           |
            |        | background-audio | my_recording | quality=foo |
            """,
            errored=True,
            error__contains=["Invalid value for quality."],
        )

    def test_label_ignored_if_specified(self):
        """Should find that the control output is hidden even if a label is specified."""
        md = """
        | survey |
        | | type             | name | label |
        | | background-audio | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_count=[
                # No control output with this ref.
                ("/h:html/h:body//*[@ref='/test_name/q1']", 0),
                # No control with the specified label.
                ("/h:html/h:body//*[text()='Q1']", 0),
            ],
        )
