#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pyxform_test_case import PyxformTestCase


class UnicodeRtl(PyxformTestCase):
    def test_unicode_snowman(self):
        self.assertPyxformXform(
            md="""
            | survey |      |         |       |
            |        | type | name    | label |
            |        | text | snowman | ☃     |
            """,
            errored=False,
            xml__contains=[
                '<label>☃</label>',
            ],
        )
