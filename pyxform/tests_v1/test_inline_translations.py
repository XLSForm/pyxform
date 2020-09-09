# -*- coding: utf-8 -*-
"""
Testing inlining translation when no translation is specified.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class InlineTranslationsTest(PyxformTestCase):
    def test_inline_translations(self):
        """
        Dynamic choice (marked with choice filter) should inline the labels instead of using
        itext fields. There should be no itext definition in the model.
        """
        self.assertPyxformXform(
            md="""
               | survey  |                   |          |            |               |
               |         | type              | name     | label      | choice_filter |
               |         | select_one states | state    | State Name | state != ''   |
               | choices |                   |          |            |
               |         | list name         | name     | label      |
               |         | states            | option a | a          |
               |         | states            | option b | b          |
               |         | states            | option c | c          |
               """,
            name="data",
            id_string="some-id",
            model__contains=[
                "<label>a</label>",
                "<label>b</label>",
                "<label>c</label>",
            ],
            model__excludes=[
                '<text id="states-0">',
                '<text id="states-1">',
                '<text id="states-2">',
                "<itextId>states-0</itextId>",
                "<itextId>states-1</itextId>",
                "<itextId>states-2</itextId>",
            ],
            xml__contains=['<label ref="label"/>'],
            xml__excludes=['<label ref="jr:itext(itextId)"/>'],
        )

    def test_multiple_translations(self):
        """
        Dynamic choice with potential translation should generate itext fields.
        """
        self.assertPyxformXform(
            md="""
               | survey  |                   |          |            |               |
               |         | type              | name     | label      | choice_filter |
               |         | select_one states | state    | State Name | state != ''   |
               | choices |                   |          |            |
               |         | list name         | name     | label::English(en)|
               |         | states            | option a | a                 |
               |         | states            | option b | b                 |
               |         | states            | option c | c                 |
               """,
            name="data",
            id_string="some-id",
            model__contains=[
                '<text id="states-0">',
                '<text id="states-1">',
                '<text id="states-2">',
                "<itextId>states-0</itextId>",
                "<itextId>states-1</itextId>",
                "<itextId>states-2</itextId>",
            ],
            model__excludes=[
                "<label>a</label>",
                "<label>b</label>",
                "<label>c</label>",
            ],
            xml__contains=['<label ref="jr:itext(itextId)"/>'],
            xml__excludes=['<label ref="label"/>'],
        )

    def test_select_with_media_and_choice_filter_and_no_translations_generates_media(
        self,
    ):
        """
        Selects with media and choice filter should generate itext fields for the media.
        """
        xform_md = """
        | survey |                    |                 |                                 |                           |
        |        | type               | name            | label                           | choice_filter             |
        |        | select_one consent | consent         | Would you like to participate ? |                           |
        |        | select_one mood    | enumerator_mood | How are you feeling today ?     | selected(${consent}, 'y') |
        | choices |
        |         | list_name | name | label | media::image |
        |         | mood      | h    | Happy | happy.jpg    |
        |         | mood      | s    | Sad   | sad.jpg      |
        |         | consent   | y    | Yes   |              |
        |         | consent   | n    | No    |              |
        """
        self.assertPyxformXform(
            name="data",
            id_string="some-id",
            md=xform_md,
            errored=False,
            debug=False,
            model__contains=[
                '<text id="mood-0">',
                '<text id="mood-1">',
                "<itextId>mood-0</itextId>",
                "<itextId>mood-1</itextId>",
            ],
            model__excludes=[
                '<text id="/data/enumerator_mood/h:label">',
                '<text id="/data/enumerator_mood/s:label">',
            ],
            xml__contains=['<label ref="jr:itext(itextId)"/>'],
            xml__excludes=['<label ref="label"/>'],
        )

    def test_select_with_choice_filter_and_translations_generates_single_translation(
        self,
    ):
        """
        Selects with choice filter and translations should only have a single itext entry.
        """
        xform_md = """
        | survey |                    |      |       |               |
        |        | type               | name | label | choice_filter |
        |        | select_one list    | foo  | Foo   | name != "     |
        | choices |
        |         | list_name | name | label | image | label::French |
        |         | list      | a    | A     | a.jpg | Ah            |
        |         | list      | b    | B     | b.jpg | Bé            |
        |         | list      | c    | C     | c.jpg | Cé            |
        """
        self.assertPyxformXform(
            name="data",
            id_string="some-id",
            md=xform_md,
            errored=False,
            debug=False,
            itext__contains=[
                '<text id="list-0">',
                '<text id="list-1">',
                '<text id="list-2">',
            ],
            itext__excludes=[
                '<text id="/data/foo/a:label">',
                '<text id="/data/foo/b:label">',
                '<text id="/data/foo/c:label">',
            ],
        )
