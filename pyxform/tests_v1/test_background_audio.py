# -*- coding: utf-8 -*-
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class AuditTest(PyxformTestCase):
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
