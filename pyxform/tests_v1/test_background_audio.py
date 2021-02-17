# -*- coding: utf-8 -*-
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
import unittest


class BackgroundAudioTest(PyxformTestCase):
    def test_background_audio(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                   |                 |
            |        | type              |   name          |
            |        | background-audio  |   my_recording  |
            """,
            xml__contains=[
                '<odk:recordaudio event="odk-instance-load" ref="/data/my_recording"/>',
            ],
        )

    @unittest.skip("Required update to Validate to work")
    def test_background_audio_is_valid(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                   |                 |
            |        | type              |   name          |
            |        | background-audio  |   my_recording  |
            """,
            run_odk_validate=True,
        )
