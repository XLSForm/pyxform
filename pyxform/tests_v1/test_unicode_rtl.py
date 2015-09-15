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

    def test_mixed_rtl(self):
        self.assertPyxformXform(
            name='mixed_rtl_test',
            md="""
            | survey |      |            |                      |
            |        | type | name       | label                |
            |        | text | q1         | Q1                   |
            |        | text | urdu_mixed | Q6. صوبہ ؟ ${q1} کیا |
            """,
            xml__contains=[
                '<label>Q6. صوبہ ؟ <output value=" /mixed_rtl_test/q1 "/> کیا</label>',
            ]
        )

    def test_mixed_rtl_multilang(self):
        self.assertPyxformXform(
            name='mixed_rtl_test',
            md="""
            | survey |      |            |                      |            |
            |        | type | name       | label::urdu          | label::eng |
            |        | text | q1         | Question 1           | Q1         |
            |        | text | urdu_mixed | Q6. صوبہ ؟ ${q1} کیا | Q2         |
            """,
            itext__contains=[
                '<value>Q6. صوبہ ؟ <output value=" /mixed_rtl_test/q1 "/> کیا</value>',
            ]
        )
