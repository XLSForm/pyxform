#!/usr/bin/python
# -*- coding: utf-8 -*-
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class DoubleColonTranslations(PyxformTestCase):
    def test_langs(self):
        model_contains = """<bind nodeset="/translations/n1""" + \
                         """" readonly="true()" type="string"/>"""
        self.assertPyxformXform(
            name='translations',
            id_string='transl',
            md="""
            | survey |      |      |                |               |
            |        | type | name | label::english | label::french |
            |        | note | n1   | hello          | bonjour       |
            """,
            errored=False,
            itext__contains=[
                '<translation lang="french">',
                '<text id="/translations/n1:label">',
                '<value>bonjour</value>',
                '</text>',
                '</translation>',
                '<translation lang="english">',
                '<text id="/translations/n1:label">',
                '<value>hello</value>',
                '</text>',
                '</translation>',
            ],
            xml__contains=[
                """<label ref="jr:itext('/translations/n1:label')"/>""",
            ],
            model__contains=[model_contains],
        )
