# -*- coding: utf-8 -*-
"""
Test translations syntax.
"""
from pyxform.constants import DEFAULT_LANGUAGE_VALUE as DEFAULT_LANG
from pyxform.xls2json import format_missing_translations_survey_msg
from tests.pyxform_test_case import PyxformTestCase


# Label assertions
LABEL_BODY_VALUE_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:label[text()='{value}']
"""
LABEL_BODY_ITEXT_REF_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')" and not(text())]
"""
LABEL_ITEXT_VALUE_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']/x:value[text()='{value}']
"""
LABEL_NO_ITEXT_XPATH = """
/h:html/h:head/x:model[not(x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']/x:value[text()='{value}'])]
"""
# Shortcut of LABEL_ITEXT_VALUE_XPATH + LABEL_BODY_ITEXT_REF_XPATH
LABEL_TRANSLATED_XPATH = """
/h:html
  [h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']/x:value[text()='hello']]
  /h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')" and not(text())]
"""
# Shortcut of LABEL_NO_ITEXT_XPATH + LABEL_BODY_VALUE_XPATH
LABEL_NOT_TRANSLATED_XPATH = """
/h:html
  [not(h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']/x:value[text()='hello'])]
  /h:body/x:input[@ref='/test/n1']/x:label[text()='hello']
"""


# Hint assertions
HINT_BODY_ITEXT_REF_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:hint[@ref="jr:itext('/test/n1:hint')" and not(text())]
"""
HINT_BODY_VALUE_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:hint[text()='{value}']
"""
HINT_ITEXT_VALUE_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']/x:value[text()='{value}']
"""
HINT_NO_ITEXT_XPATH = """
/h:html/h:head/x:model[not(x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']/x:value[text()='{value}'])]
"""
HINT_TRANSLATED_XPATH = """
/h:html
  [h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']/x:value[text()='salutation']]
  /h:body/x:input[@ref='/test/n1']/x:hint[@ref="jr:itext('/test/n1:hint')" and not(text())]
"""
HINT_NOT_TRANSLATED_XPATH = """
/h:html
  [not(h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']/x:value[text()='salutation'])]
  /h:body/x:input[@ref='/test/n1']/x:hint[text()='salutation']
"""

# Other misc
GUIDANCE_TRANSLATED_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']
  /x:value[@form='guidance' and text()='greeting']
"""
IMAGE_TRANSLATED_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']
  /x:value[@form='image' and text()='jr://images/default.jpg']
"""
VIDEO_TRANSLATED_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']
  /x:value[@form='video' and text()='jr://video/default.mkv']
"""
AUDIO_TRANSLATED_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']
  /x:value[@form='audio' and text()='jr://audio/default.mp3']
"""
LANG_MARKED_DEFAULT_XPATH = (
    "/h:html/h:head/x:model/x:itext/x:translation[@default='true()' and @lang='{lang}']"
)
LANG_NOT_MARKED_DEFAULT_XPATH = "/h:html/h:head/x:model/x:itext/x:translation[not(@default='true()') and @lang='{lang}']"
LANG_NO_ITEXT_XPATH = (
    "/h:html/h:head/x:model/x:itext[not(descendant::x:translation[@lang='{lang}'])]"
)


class TestTranslations(PyxformTestCase):
    def test_double_colon_translations(self):
        """Should find translations for a simple form with a label in two languages."""
        md = """
        | survey |      |      |                |               |
        |        | type | name | label::english | label::french |
        |        | note | n1   | hello          | bonjour       |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="english", value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="english"),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="french"),
                # Expected model binding found.
                """/h:html/h:head/x:model
                     /x:bind[@nodeset='/test/n1' and @readonly='true()' and @type='string']
                """,
            ],
            errored=False,
            warnings_count=0,
        )

    def test_no_default__no_translation__label_and_hint(self):
        """Should not find default language translations for only label/hint."""
        md = """
        | survey |      |      |       |            |
        |        | type | name | label | hint       |
        |        | note | n1   | hello | salutation |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_NOT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                HINT_NOT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                # No translations.
                "/h:html/h:head/x:model[not(descendant::x:itext)]",
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__no_translation__label_and_hint_with_image(self):
        """Should find default language translations for label and image but not hint."""
        md = """
        | survey |      |      |       |            |              |
        |        | type | name | label | hint       | media::image |
        |        | note | n1   | hello | salutation | default.jpg  |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                # TODO: is this a bug? Why itext for label/image but not hint?
                HINT_NOT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                IMAGE_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                LANG_MARKED_DEFAULT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__no_translation__label_and_hint_with_guidance(self):
        """Should find default language translations for hint and guidance but not label."""
        md = """
        | survey |      |      |       |            |               |
        |        | type | name | label | hint       | guidance_hint |
        |        | note | n1   | hello | salutation | greeting      |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                # TODO: is this a bug? Why itext for hint/guidance but not label?
                LABEL_NOT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                HINT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                GUIDANCE_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                LANG_MARKED_DEFAULT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__no_translation__label_and_hint_with_media(self):
        """Should find default language translations for all translatables."""
        md = """
        | survey |      |      |       |            |               |              |              |              |
        |        | type | name | label | hint       | guidance_hint | media::image | media::video | media::audio |
        |        | note | n1   | hello | salutation | greeting      | default.jpg  | default.mkv  | default.mp3  |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                HINT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                GUIDANCE_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                IMAGE_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                VIDEO_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                AUDIO_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                LANG_MARKED_DEFAULT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__one_translation__label_and_hint(self):
        """Should find language translations for label and hint."""
        md = """
        | survey |      |      |            |            |
        |        | type | name | label::eng | hint::eng  |
        |        | note | n1   | hello      | salutation |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang="eng"),
                HINT_TRANSLATED_XPATH.format(lang="eng"),
                # TODO: is this a bug? Only one language but not marked default.
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__one_translation__label_and_hint_with_image(self):
        """Should find language translations for label, hint, and image."""
        md = """
        | survey |      |      |            |            |                   |
        |        | type | name | label::eng | hint::eng  | media::image::eng |
        |        | note | n1   | hello      | salutation | default.jpg       |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang="eng"),
                HINT_TRANSLATED_XPATH.format(lang="eng"),
                IMAGE_TRANSLATED_XPATH.format(lang="eng"),
                # TODO: is this a bug? Only one language but not marked default.
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__one_translation__label_and_hint_with_guidance(self):
        """Should find default language translation for hint and guidance but not label."""
        md = """
        | survey |      |      |            |            |                    |
        |        | type | name | label::eng | hint::eng  | guidance_hint::eng |
        |        | note | n1   | hello      | salutation | greeting           |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang="eng"),
                HINT_TRANSLATED_XPATH.format(lang="eng"),
                GUIDANCE_TRANSLATED_XPATH.format(lang="eng"),
                # TODO: is this a bug? Only one language but not marked default.
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_no_default__one_translation__label_and_hint_with_media(self):
        """Should find language translation for label, hint, and all media."""
        md = """
        | survey |      |      |            |            |                    |                   |                   |                   |
        |        | type | name | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::video::eng | media::audio::eng |
        |        | note | n1   | hello      | salutation | greeting           | default.jpg       | default.mkv       | default.mp3       |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang="eng"),
                HINT_TRANSLATED_XPATH.format(lang="eng"),
                GUIDANCE_TRANSLATED_XPATH.format(lang="eng"),
                IMAGE_TRANSLATED_XPATH.format(lang="eng"),
                VIDEO_TRANSLATED_XPATH.format(lang="eng"),
                AUDIO_TRANSLATED_XPATH.format(lang="eng"),
                # TODO: is this a bug? Only one language but not marked default.
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
            errored=False,
        )

    def test_missing_translation_survey__warn__no_default_one_lang(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |       |            |            |
        |        | type | name | label | label::eng | hint       |
        |        | note | n1   | hello | hi there   | salutation |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hi there"),
                HINT_NOT_TRANSLATED_XPATH.format(lang=DEFAULT_LANG),
                LANG_MARKED_DEFAULT_XPATH.format(lang=DEFAULT_LANG),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["eng"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__warn__no_default_two_way(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |            |            |
        |        | type | name | label::eng | hint       |
        |        | note | n1   | hello      | salutation |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                HINT_BODY_VALUE_XPATH.format(value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(
            _in={"hint": ["eng"], "label": ["default"]}
        )
        self.assertIn(expected, observed)

    def test_missing_translation_survey__warn__no_default_with_other_lang(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |            |               |            |
        |        | type | name | label::eng | label::french | hint::eng  |
        |        | note | n1   | hello      | bonjour       | salutation |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                # TODO: is this a bug? French hint has a dash instead of something meaningful.
                HINT_ITEXT_VALUE_XPATH.format(lang="french", value="-"),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="french"),
                LANG_NO_ITEXT_XPATH.format(lang="default"),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__warn__default_with_two_lang(self):
        """Should not warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey |      |      |            |               |            |
        |        | type | name | label::eng | label::french | hint::eng  |
        |        | note | n1   | hello      | bonjour       | salutation |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                HINT_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                # TODO: is this a bug? French hint has a dash instead of something meaningful.
                HINT_ITEXT_VALUE_XPATH.format(lang="french", value="-"),
                LANG_MARKED_DEFAULT_XPATH.format(lang="eng"),
                LANG_NOT_MARKED_DEFAULT_XPATH.format(lang="french"),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__no_warn__default_no_other_lang(self):
        """Should not warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | french           |
        | survey |      |      |                |               |            |
        |        | type | name | label          | label::french | hint       |
        |        | note | n1   | hello          | bonjour       | salutation |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                # TODO: is this a bug? Default label not in translations (i.e. nowhere).
                LABEL_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                HINT_BODY_VALUE_XPATH.format(value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang="french", value="salutation"),
                LANG_MARKED_DEFAULT_XPATH.format(lang="french"),
                # TODO: is this a bug? No default translations.
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertNotIn(expected, observed)


class TranslationsTest(PyxformTestCase):
    """Test XLSForm translations."""

    def test_missing_media_itext(self):
        """Test missing media itext translation

        Fix for https://github.com/XLSForm/pyxform/issues/32
        """
        xform_md = """
        | survey |                                |                    |                                                              |                                               |                 |          |                      |                       |
        |        | name                           | type               | label                                                        | label::Russian                                | label::Kyrgyz   | required | media::audio::Kyrgyz | media::audio::Russian |
        |        | Have_you_received_informed_con | select_one bt7nj36 | A.01 Have you received informed consent from the respondent? | Получили ли вы форму согласия от респондента? | This is Kyrgyz. | true     | something.mp3        | test.mp3              |
        | choices |           |      |       |                |               |
        |         | list name | name | label | label::Russian | label::Kyrgyz |
        |         | bt7nj36   | 0    | No    | Нет            | Нет (ky)      |
        |         | bt7nj36   | 1    | Yes   | Да             | Да (ky)       |
        """
        self.assertPyxformXform(
            name="multi_language_form",
            id_string="multi_language_form",
            md=xform_md,
            errored=False,
            debug=False,
            itext__contains=[
                '<translation default="true()" lang="default">',
                '<text id="/multi_language_form/Have_you_received_informed_con:label">',
                "A.01 Have you received informed consent from the respondent?",
                '<translation lang="Russian">',
                "<value>Получили ли вы форму согласия от респондента?</value>",
                '<value form="audio">jr://audio/test.mp3</value>',
                '<translation lang="Kyrgyz">',
                "<value>This is Kyrgyz.</value>",
                '<value form="audio">jr://audio/something.mp3</value>',
            ],
            itext__excludes=['<value form="audio">jr://audio/-</value>'],
        )
