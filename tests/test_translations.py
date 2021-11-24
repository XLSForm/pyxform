# -*- coding: utf-8 -*-
"""
Test translations syntax.
"""
from dataclasses import dataclass

from pyxform.constants import DEFAULT_LANGUAGE_VALUE as DEFAULT_LANG
from pyxform.xls2json import format_missing_translations_survey_msg
from tests.pyxform_test_case import PyxformTestCase

LABEL_BODY_VALUE_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:label[not(@ref) and text()='{value}']
"""
LABEL_BODY_ITEXT_REF_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')" and not(text())]
"""
LABEL_ITEXT_VALUE_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']/x:value[not(@form) and text()='{value}']
"""
LABEL_NO_ITEXT_XPATH = """
/h:html/h:head/x:model[not(x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:label']/x:value[not(@form) and text()='{value}'])]
"""

HINT_BODY_ITEXT_REF_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:hint[@ref="jr:itext('/test/n1:hint')" and not(text())]
"""
HINT_BODY_VALUE_XPATH = """
/h:html/h:body/x:input[@ref='/test/n1']/x:hint[not(@ref) and text()='{value}']
"""
HINT_ITEXT_VALUE_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']/x:value[not(@form) and text()='{value}']
"""
HINT_NO_ITEXT_XPATH = """
/h:html/h:head/x:model[not(x:itext/x:translation[@lang='{lang}']/x:text[@id='/test/n1:hint']/x:value[not(@form) and text()='{value}'])]
"""

_GUIDANCE_KWARGS = {"type": "hint", "form": "guidance", "value": "{value}"}
_AUDIO_KWARGS = {"type": "label", "form": "audio", "value": "jr://audio/greeting.mp3"}
_IMAGE_KWARGS = {"type": "label", "form": "image", "value": "jr://images/greeting.jpg"}
_VIDEO_KWARGS = {"type": "label", "form": "video", "value": "jr://video/greeting.mkv"}
_FORM_ITEXT_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{{lang}}']/x:text[@id='/test/n1:{type}']
  /x:value[@form='{form}' and text()='{value}']
"""
GUIDANCE_ITEXT_XPATH = _FORM_ITEXT_XPATH.format(**_GUIDANCE_KWARGS)
AUDIO_ITEXT_XPATH = _FORM_ITEXT_XPATH.format(**_AUDIO_KWARGS)
IMAGE_ITEXT_XPATH = _FORM_ITEXT_XPATH.format(**_IMAGE_KWARGS)
VIDEO_ITEXT_XPATH = _FORM_ITEXT_XPATH.format(**_VIDEO_KWARGS)

_NO_FORM_ITEXT_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@lang='{{lang}}']
  /x:text[@id='/test/n1:{type}' and not(descendant::x:value[@form='{form}' and text()='{value}'])]
"""
GUIDANCE_NO_ITEXT_XPATH = _NO_FORM_ITEXT_XPATH.format(**_GUIDANCE_KWARGS)
AUDIO_NO_ITEXT_XPATH = _NO_FORM_ITEXT_XPATH.format(**_AUDIO_KWARGS)
IMAGE_NO_ITEXT_XPATH = _NO_FORM_ITEXT_XPATH.format(**_IMAGE_KWARGS)
VIDEO_NO_ITEXT_XPATH = _NO_FORM_ITEXT_XPATH.format(**_VIDEO_KWARGS)

LANG_DEFAULT_TRUE_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[@default='true()' and @lang='{lang}']
"""
LANG_DEFAULT_FALSE_XPATH = """
/h:html/h:head/x:model/x:itext/x:translation[not(@default='true()') and @lang='{lang}']
"""
LANG_NO_ITEXT_XPATH = """
/h:html/h:head/x:model/x:itext[not(descendant::x:translation[@lang='{lang}'])]
"""


class TestTranslations(PyxformTestCase):
    """Miscellaneous translations behaviour or cases."""

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
                LANG_DEFAULT_FALSE_XPATH.format(lang="english"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="french"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                # Expected model binding found.
                """/h:html/h:head/x:model
                     /x:bind[@nodeset='/test/n1' and @readonly='true()' and @type='string']
                """,
            ],
            warnings_count=0,
            debug=True,
        )

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


class TestTranslationsSurvey(PyxformTestCase):
    """Translations behaviour of columns in the Survey sheet."""

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
                LABEL_BODY_VALUE_XPATH.format(value="hello"),
                LABEL_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                HINT_BODY_VALUE_XPATH.format(value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                # No translations.
                "/h:html/h:head/x:model[not(descendant::x:itext)]",
            ],
            warnings_count=0,
        )

    def test_no_default__no_translation__label_and_hint_with_image(self):
        """Should find default language translations for label and image but not hint."""
        md = """
        | survey |      |      |       |            |              |
        |        | type | name | label | hint       | media::image |
        |        | note | n1   | hello | salutation | greeting.jpg |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                # TODO: is this a bug? Why itext for label/image but not hint?
                HINT_BODY_VALUE_XPATH.format(value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                IMAGE_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                LANG_DEFAULT_TRUE_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
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
                LABEL_BODY_VALUE_XPATH.format(value="hello"),
                LABEL_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                GUIDANCE_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="greeting"),
                LANG_DEFAULT_TRUE_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__no_translation__label_and_hint_all_cols(self):
        """Should find default language translations for all translatables."""
        md = """
        | survey |      |      |       |            |               |              |              |              |
        |        | type | name | label | hint       | guidance_hint | media::image | media::video | media::audio |
        |        | note | n1   | hello | salutation | greeting      | greeting.jpg | greeting.mkv | greeting.mp3 |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                GUIDANCE_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="greeting"),
                IMAGE_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                VIDEO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                AUDIO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                LANG_DEFAULT_TRUE_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
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
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                # TODO: is this a bug? Only one language but not marked default.
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__one_translation__label_and_hint_with_image(self):
        """Should find language translations for label, hint, and image."""
        md = """
        | survey |      |      |            |            |                   |
        |        | type | name | label::eng | hint::eng  | media::image::eng |
        |        | note | n1   | hello      | salutation | greeting.jpg      |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                IMAGE_ITEXT_XPATH.format(lang="eng"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
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
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                GUIDANCE_ITEXT_XPATH.format(lang="eng", value="greeting"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__one_translation__label_and_hint_all_cols(self):
        """Should find language translation for label, hint, and all translatables."""
        md = """
        | survey |      |      |            |            |                    |                   |                   |                   |
        |        | type | name | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::video::eng | media::audio::eng |
        |        | note | n1   | hello      | salutation | greeting           | greeting.jpg      | greeting.mkv      | greeting.mp3      |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                GUIDANCE_ITEXT_XPATH.format(lang="eng", value="greeting"),
                IMAGE_ITEXT_XPATH.format(lang="eng"),
                VIDEO_ITEXT_XPATH.format(lang="eng"),
                AUDIO_ITEXT_XPATH.format(lang="eng"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_missing_translation_survey__one_lang_simple__warn__no_default(self):
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
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hi there"),
                HINT_BODY_VALUE_XPATH.format(value="salutation"),
                LANG_DEFAULT_TRUE_XPATH.format(lang=DEFAULT_LANG),
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["eng"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__one_lang_simple__no_warn__default(self):
        """Should not warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
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
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hi there"),
                HINT_BODY_VALUE_XPATH.format(value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang="eng", value="salutation"),
                LANG_DEFAULT_TRUE_XPATH.format(lang="eng"),
                # TODO: is this a bug? No default lang itext (missing label).
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["eng"]})
        self.assertNotIn(expected, observed)

    def test_missing_translation_survey__one_lang_all_cols__warn__no_default(self):
        """Should warn if there's multiple missing translations and no default_language."""
        md = """
        | survey |      |      |       |            |            |                    |                   |                   |                   |
        |        | type | name | label | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::video::eng | media::audio::eng |
        |        | note | n1   | hello | hi there   | salutation | greeting           | greeting.jpg      | greeting.mkv      | greeting.mp3      |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hi there"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                HINT_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="-"),
                GUIDANCE_ITEXT_XPATH.format(lang="eng", value="greeting"),
                GUIDANCE_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="-"),
                IMAGE_ITEXT_XPATH.format(lang="eng"),
                IMAGE_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                VIDEO_ITEXT_XPATH.format(lang="eng"),
                VIDEO_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                AUDIO_ITEXT_XPATH.format(lang="eng"),
                AUDIO_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                LANG_DEFAULT_TRUE_XPATH.format(lang=DEFAULT_LANG),
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
            ],
        )
        cols = {
            c: [DEFAULT_LANG]
            for c in ("hint", "guidance_hint", "image", "video", "audio")
        }
        expected = format_missing_translations_survey_msg(_in=cols)
        self.assertIn(expected, observed)

    def test_missing_translation_survey__one_lang_all_cols__no_warn__default(self):
        """Should not warn if there's missing translations with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey |      |      |       |            |            |                    |                   |                   |                   |
        |        | type | name | label | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::video::eng | media::audio::eng |
        |        | note | n1   | hello | hi there   | salutation | greeting           | greeting.jpg      | greeting.mkv      | greeting.mp3      |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hi there"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                GUIDANCE_ITEXT_XPATH.format(lang="eng", value="greeting"),
                IMAGE_ITEXT_XPATH.format(lang="eng"),
                VIDEO_ITEXT_XPATH.format(lang="eng"),
                AUDIO_ITEXT_XPATH.format(lang="eng"),
                LANG_DEFAULT_TRUE_XPATH.format(lang="eng"),
                # TODO: is this a bug? No default lang itext (missing label, hint).
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        cols = {
            c: [DEFAULT_LANG]
            for c in ("hint", "guidance_hint", "image", "video", "audio")
        }
        expected = format_missing_translations_survey_msg(_in=cols)
        self.assertNotIn(expected, observed)

    def test_missing_translation_survey__one_lang_overlap__warn__no_default(self):
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
                HINT_NO_ITEXT_XPATH.format(lang="eng", value="salutation"),
                HINT_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG, value="salutation"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(
            _in={"hint": ["eng"], "label": ["default"]}
        )
        self.assertIn(expected, observed)

    def test_missing_translation_survey__one_lang_overlap__no_warn__default(self):
        """Should not warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
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
                HINT_NO_ITEXT_XPATH.format(lang="eng", value="salutation"),
                LANG_DEFAULT_TRUE_XPATH.format(lang="eng"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["eng"]})
        self.assertNotIn(expected, observed)

    def test_missing_translation_survey__two_lang__warn__no_default(self):
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
                LANG_DEFAULT_FALSE_XPATH.format(lang="eng"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="french"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__two_lang__no_warn__default(self):
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
                LABEL_ITEXT_VALUE_XPATH.format(lang="eng", value="hello"),
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="eng", value="salutation"),
                HINT_ITEXT_VALUE_XPATH.format(lang="french", value="-"),
                LANG_DEFAULT_TRUE_XPATH.format(lang="eng"),
                LANG_DEFAULT_FALSE_XPATH.format(lang="french"),
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertNotIn(expected, observed)

    def test_missing_translation_survey__issue_157__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |               |              |              |
        |        | type | name | label::french | hint::french | media::image |
        |        | note | n1   | bonjour       | salutation   | greeting.jpg |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                LABEL_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="-"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="french", value="salutation"),
                HINT_ITEXT_VALUE_XPATH.format(lang=DEFAULT_LANG, value="-"),
                IMAGE_NO_ITEXT_XPATH.format(lang="french"),
                IMAGE_ITEXT_XPATH.format(lang=DEFAULT_LANG),
                LANG_DEFAULT_FALSE_XPATH.format(lang="french"),
                LANG_DEFAULT_TRUE_XPATH.format(lang=DEFAULT_LANG),
            ],
        )
        expected = format_missing_translations_survey_msg(
            _in={"hint": ["default"], "image": ["french"], "label": ["default"]}
        )
        self.assertIn(expected, observed)

    def test_missing_translation_survey__issue_157__no_warn__default(self):
        """Should not warn if there's missing translations with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | french           |
        | survey |      |      |               |              |              |
        |        | type | name | label::french | hint::french | media::image |
        |        | note | n1   | bonjour       | salutation   | greeting.jpg |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                LABEL_BODY_ITEXT_REF_XPATH,
                LABEL_ITEXT_VALUE_XPATH.format(lang="french", value="bonjour"),
                HINT_BODY_ITEXT_REF_XPATH,
                HINT_ITEXT_VALUE_XPATH.format(lang="french", value="salutation"),
                IMAGE_ITEXT_XPATH.format(lang="french"),
                LANG_DEFAULT_TRUE_XPATH.format(lang="french"),
                # TODO: is this a bug? No default lang itext (missing image).
                LANG_NO_ITEXT_XPATH.format(lang=DEFAULT_LANG),
            ],
            debug=True,
        )
        expected = format_missing_translations_survey_msg(
            _in={"hint": ["default"], "image": ["french"], "label": ["default"]}
        )
        self.assertNotIn(expected, observed)


@dataclass()
class XPathHelper:
    question_type: str
    question_name: str

    def question_label_in_body(self, label):
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:label[not(@ref) and text()='{label}']
        """

    def question_label_references_itext(self):
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:label[@ref="jr:itext('/test/{self.question_name}:label')" and not(text())]
        """

    def choice_value_in_body(self, cname):
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']/x:item
          /x:value[not(@ref) and text()='{cname}']
        """

    def choice_label_references_itext(self, cname):
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']/x:item
          /x:label[@ref="jr:itext('/test/{self.question_name}/{cname}:label')" and not(text())]
        """

    def choice_label_itext_label(self, lang, cname, label):
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}/{cname}:label']
          /x:value[not(@form) and text()='{label}']
        """

    def choice_label_itext_form(self, lang, cname, form, fname):
        prefix = {
            "audio": "jr://audio/",
            "image": "jr://images/",
            "video": "jr://video/",
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}/{cname}:label']
          /x:value[@form='{form}' and text()='{prefix[form]}{fname}']
        """

    def choice_list_references_itext(self, lname):
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:itemset[@nodeset="instance('{lname}')/root/item[{self.question_name} != '']"
            and child::x:label[@ref='jr:itext(itextId)'] and child::x:value[@ref='name']]
        """

    @staticmethod
    def choice_value_in_instance(lname, cname, index):
        return f"""
        /h:html/h:head/x:model/x:instance[@id='{lname}']/x:root
          /x:item[child::x:itextId/text()='{lname}-{index}'
            and child::x:name='{cname}' and position()={index}+1]
        """

    @staticmethod
    def choice_label_itext_label_instance(lang, lname, label, index):
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='{lname}-{index}']
          /x:value[not(@form) and text()='{label}']
        """

    @staticmethod
    def choice_label_itext_form_instance(lang, lname, form, fname, index):
        prefix = {
            "audio": "jr://audio/",
            "image": "jr://images/",
            "video": "jr://video/",
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='{lname}-{index}']
          /x:value[@form='{form}' and text()='{prefix[form]}{fname}']
        """


class TestTranslationsChoices(PyxformTestCase):
    """Translations behaviour of columns in the Choices sheet."""

    def test_select1__non_dynamic_choices__no_lang__all_columns(self):
        """Should find that when all translatable choices columns are used they appear in itext."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |       |              |              |              |
        |         | list name | name | label | media::audio | media::image | media::video |
        |         | c1        | na   | la    | a.mp3        | a.jpg        | a.mkv        |
        |         | c1        | nb   | lb    | b.mp3        | b.jpg        | b.mkv        |
        """
        xp = XPathHelper(question_type="select1", question_name="q1")
        lang = DEFAULT_LANG
        xpath_match = [
            xp.question_label_in_body("Question 1"),
            xp.choice_value_in_body("na"),
            xp.choice_value_in_body("nb"),
            xp.choice_label_references_itext("na"),
            xp.choice_label_references_itext("nb"),
            xp.choice_label_itext_label(lang, "na", "la"),
            xp.choice_label_itext_form(lang, "na", "audio", "a.mp3"),
            xp.choice_label_itext_form(lang, "na", "image", "a.jpg"),
            xp.choice_label_itext_form(lang, "na", "video", "a.mkv"),
            xp.choice_label_itext_label(lang, "nb", "lb"),
            xp.choice_label_itext_form(lang, "nb", "audio", "b.mp3"),
            xp.choice_label_itext_form(lang, "nb", "image", "b.jpg"),
            xp.choice_label_itext_form(lang, "nb", "video", "b.mkv"),
        ]
        self.assertPyxformXform(
            md=md,
            name="test",
            xml__xpath_match=xpath_match,
        )

    def test_select1__non_dynamic_choices__one_lang__all_columns(self):
        """Should find that when all translatable choices columns are used they appear in itext."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |                        |                        |                        |
        |         | list name | name | label::Eng (en) | media::audio::Eng (en) | media::image::Eng (en) | media::video::Eng (en) |
        |         | c1        | na   | la              | a.mp3                  | a.jpg                  | a.mkv                  |
        |         | c1        | nb   | lb              | b.mp3                  | b.jpg                  | b.mkv                  |
        """
        xp = XPathHelper(question_type="select1", question_name="q1")
        lang = "Eng (en)"
        xpath_match = [
            xp.question_label_in_body("Question 1"),
            xp.choice_value_in_body("na"),
            xp.choice_value_in_body("nb"),
            xp.choice_label_references_itext("na"),
            xp.choice_label_references_itext("nb"),
            xp.choice_label_itext_label(lang, "na", "la"),
            xp.choice_label_itext_form(lang, "na", "audio", "a.mp3"),
            xp.choice_label_itext_form(lang, "na", "image", "a.jpg"),
            xp.choice_label_itext_form(lang, "na", "video", "a.mkv"),
            xp.choice_label_itext_label(lang, "nb", "lb"),
            xp.choice_label_itext_form(lang, "nb", "audio", "b.mp3"),
            xp.choice_label_itext_form(lang, "nb", "image", "b.jpg"),
            xp.choice_label_itext_form(lang, "nb", "video", "b.mkv"),
        ]
        self.assertPyxformXform(
            md=md,
            name="test",
            xml__xpath_match=xpath_match,
        )

    def test_select1__dynamic_choices__no_lang__all_columns(self):
        """Should find that when all translatable choices columns are used they appear in itext."""
        md = """
        | survey  |               |       |            |               |
        |         | type          | name  | label      | choice_filter |
        |         | select_one c1 | q1    | Question 1 | q1 != ''      |
        | choices |           |      |       |              |              |              |
        |         | list name | name | label | media::audio | media::image | media::video |
        |         | c1        | na   | la    | a.mp3        | a.jpg        | a.mkv        |
        |         | c1        | nb   | lb    | b.mp3        | b.jpg        | b.mkv        |
        """
        xp = XPathHelper(question_type="select1", question_name="q1")
        lang = DEFAULT_LANG
        xpath_match = [
            xp.question_label_in_body("Question 1"),
            xp.choice_list_references_itext("c1"),
            xp.choice_value_in_instance("c1", "na", 0),
            xp.choice_value_in_instance("c1", "nb", 1),
            xp.choice_label_itext_label_instance(lang, "c1", "la", 0),
            xp.choice_label_itext_form_instance(lang, "c1", "audio", "a.mp3", 0),
            xp.choice_label_itext_form_instance(lang, "c1", "image", "a.jpg", 0),
            xp.choice_label_itext_form_instance(lang, "c1", "video", "a.mkv", 0),
            xp.choice_label_itext_label_instance(lang, "c1", "lb", 1),
            xp.choice_label_itext_form_instance(lang, "c1", "audio", "b.mp3", 1),
            xp.choice_label_itext_form_instance(lang, "c1", "image", "b.jpg", 1),
            xp.choice_label_itext_form_instance(lang, "c1", "video", "b.mkv", 1),
        ]
        self.assertPyxformXform(
            md=md,
            name="test",
            xml__xpath_match=xpath_match,
        )

    def test_select1__dynamic_choices__one_lang__all_columns(self):
        """ "Should find that when all translatable choices columns are used they appear in itext."""
        md = """
        | survey  |               |       |            |               |
        |         | type          | name  | label      | choice_filter |
        |         | select_one c1 | q1    | Question 1 | q1 != ''      |
        | choices |           |      |                 |                        |                        |                        |
        |         | list name | name | label::Eng (en) | media::audio::Eng (en) | media::image::Eng (en) | media::video::Eng (en) |
        |         | c1        | na   | la              | a.mp3                  | a.jpg                  | a.mkv                  |
        |         | c1        | nb   | lb              | b.mp3                  | b.jpg                  | b.mkv                  |
        """
        xp = XPathHelper(question_type="select1", question_name="q1")
        lang = "Eng (en)"
        xpath_match = [
            xp.question_label_in_body("Question 1"),
            xp.choice_list_references_itext("c1"),
            xp.choice_value_in_instance("c1", "na", "0"),
            xp.choice_value_in_instance("c1", "nb", "1"),
            xp.choice_label_itext_label_instance(lang, "c1", "la", 0),
            xp.choice_label_itext_form_instance(lang, "c1", "audio", "a.mp3", 0),
            xp.choice_label_itext_form_instance(lang, "c1", "image", "a.jpg", 0),
            xp.choice_label_itext_form_instance(lang, "c1", "video", "a.mkv", 0),
            xp.choice_label_itext_label_instance(lang, "c1", "lb", 1),
            xp.choice_label_itext_form_instance(lang, "c1", "audio", "b.mp3", 1),
            xp.choice_label_itext_form_instance(lang, "c1", "image", "b.jpg", 1),
            xp.choice_label_itext_form_instance(lang, "c1", "video", "b.mkv", 1),
        ]
        self.assertPyxformXform(
            md=md,
            name="test",
            xml__xpath_match=xpath_match,
        )
