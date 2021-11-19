# -*- coding: utf-8 -*-
"""
Test translations syntax.
"""
from pyxform.xls2json import format_missing_translations_survey_msg
from tests.pyxform_test_case import PyxformTestCase


class TestTranslations(PyxformTestCase):
    def test_double_colon_translations(self):
        model_contains = (
            """<bind nodeset="/translations/n1"""
            + """" readonly="true()" type="string"/>"""
        )
        self.assertPyxformXform(
            name="translations",
            id_string="transl",
            md="""
            | survey |      |      |                |               |
            |        | type | name | label::english | label::french |
            |        | note | n1   | hello          | bonjour       |
            """,
            errored=False,
            itext__contains=[
                '<translation lang="french">',
                '<text id="/translations/n1:label">',
                "<value>bonjour</value>",
                "</text>",
                "</translation>",
                '<translation lang="english">',
                '<text id="/translations/n1:label">',
                "<value>hello</value>",
                "</text>",
                "</translation>",
            ],
            xml__contains=["""<label ref="jr:itext('/translations/n1:label')"/>"""],
            model__contains=[model_contains],
        )

    def test_missing_translation_survey__warn__no_default_no_other_lang(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |       |               |               |
        |        | type | name | label | label::french | hint          |
        |        | note | n1   | hello | bonjour       | a salutation  |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                # Label is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')"]""",
                # Hint is not translated.
                "/h:html/h:body/x:input[@ref='/test/n1']/x:hint[text()='a salutation']",
                # Default label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@default='true()' and @lang='default']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='hello']",
                # French label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='french']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='bonjour']",
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__warn__no_default_two_way(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |               |               |
        |        | type | name | label::french | hint          |
        |        | note | n1   | bonjour       | a salutation  |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                # Label is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')"]""",
                # Hint is not translated.
                "/h:html/h:body/x:input[@ref='/test/n1']/x:hint[text()='a salutation']",
                # Default label not in translations.
                "/h:html/h:head/x:model/x:itext[not(descendant::x:translation[@lang='default'])]",
                # French label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='french']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='bonjour']",
            ],
        )
        expected = format_missing_translations_survey_msg(
            _in={"hint": ["french"], "label": ["default"]}
        )
        self.assertIn(expected, observed)

    def test_missing_translation_survey__warn__no_default_with_other_lang(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |                |               |               |
        |        | type | name | label::english | label::french | hint::english |
        |        | note | n1   | hello          | bonjour       | a salutation  |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                # Label is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')"]""",
                # Hint is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:hint[@ref="jr:itext('/test/n1:hint')"]""",
                # English label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='english']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='hello']",
                # French label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='french']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='bonjour']",
                # English hint in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='english']"
                + "/x:text[@id='/test/n1:hint']/x:value[text()='a salutation']",
                # French hint in translations but with a dash instead of something meaningful.
                # TODO: is this a bug?
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='french']"
                + "/x:text[@id='/test/n1:hint']/x:value[text()='-']",
            ],
        )
        expected = format_missing_translations_survey_msg(_in={"hint": ["french"]})
        self.assertIn(expected, observed)

    def test_missing_translation_survey__warn__default_with_other_lang(self):
        """Should not warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | english          |
        | survey |      |      |                |               |               |
        |        | type | name | label::english | label::french | hint::english |
        |        | note | n1   | hello          | bonjour       | a salutation  |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                # Label is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')"]""",
                # Hint is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:hint[@ref="jr:itext('/test/n1:hint')"]""",
                # English label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='english' and @default='true()']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='hello']",
                # French label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='french']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='bonjour']",
                # English hint in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='english']"
                + "/x:text[@id='/test/n1:hint']/x:value[text()='a salutation']",
                # French hint in translations but with a dash instead of something meaningful.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@lang='french']"
                + "/x:text[@id='/test/n1:hint']/x:value[text()='-']",
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
        | survey |      |      |                |               |               |
        |        | type | name | label          | label::french | hint          |
        |        | note | n1   | hello          | bonjour       | a salutation  |
        """
        observed = []
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings=observed,
            xml__xpath_match=[
                # Label is translated.
                """/h:html/h:body/x:input[@ref='/test/n1']/x:label[@ref="jr:itext('/test/n1:label')"]""",
                # Hint is not translated.
                "/h:html/h:body/x:input[@ref='/test/n1']/x:hint[text()='a salutation']",
                # Default label not in translations.
                # TODO: is this a bug?
                "/h:html/h:head/x:model/x:itext[not(descendant::x:translation[@lang='default'])]",
                # French label in translations.
                "/h:html/h:head/x:model/x:itext"
                + "/x:translation[@default='true()' and @lang='french']"
                + "/x:text[@id='/test/n1:label']/x:value[text()='bonjour']",
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
