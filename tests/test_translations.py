# -*- coding: utf-8 -*-
"""
Test translations syntax.
"""
import unittest
from dataclasses import dataclass
from time import perf_counter
from unittest.mock import patch

from pyxform.constants import CHOICES
from pyxform.constants import DEFAULT_LANGUAGE_VALUE as DEFAULT_LANG
from pyxform.constants import SURVEY
from pyxform.validators.pyxform.missing_translations_check import (
    format_missing_translations_msg,
)
from tests.pyxform_test_case import PyxformTestCase


@dataclass()
class XPathHelper:
    """
    XPath expressions for translations-related assertions.
    """

    question_type: str
    question_name: str

    @staticmethod
    def language_is_default(lang):
        """The language translation has itext and is marked as the default."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@default='true()' and @lang='{lang}']
        """

    @staticmethod
    def language_is_not_default(lang):
        """The language translation has itext and is not marked as the default."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[not(@default='true()') and @lang='{lang}']
        """

    @staticmethod
    def language_no_itext(lang):
        """The language translation has no itext."""
        return f"""
        /h:html/h:head/x:model/x:itext[not(descendant::x:translation[@lang='{lang}'])]
        """

    def question_label_in_body(self, label):
        """The Question label value is in the body."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:label[not(@ref) and text()='{label}']
        """

    def question_hint_in_body(self, hint):
        """The Question hint value is in the body."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:hint[not(@ref) and text()='{hint}']
        """

    def question_label_references_itext(self):
        """The Question label references an itext entry."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:label[@ref="jr:itext('/test/{self.question_name}:label')" and not(text())]
        """

    def question_hint_references_itext(self):
        """The Question hint references an itext entry."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:hint[@ref="jr:itext('/test/{self.question_name}:hint')" and not(text())]
        """

    def question_itext_label(self, lang, label):
        """The Question label value is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:label']
          /x:value[not(@form) and text()='{label}']
        """

    def question_itext_hint(self, lang, hint):
        """The Question hint value is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:hint']
          /x:value[not(@form) and text()='{hint}']
        """

    def question_itext_form(self, lang, form, fname):
        """There is an alternate form itext for the Question label or hint."""
        prefix = {
            "audio": ("label", "jr://audio/"),
            "image": ("label", "jr://images/"),
            "big-image": ("label", "jr://images/"),
            "video": ("label", "jr://video/"),
            "guidance": ("hint", ""),
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:{prefix[form][0]}']
          /x:value[@form='{form}' and text()='{prefix[form][1]}{fname}']
        """

    def question_no_itext_label(self, lang, label):
        """There is no itext for the Question label."""
        return f"""
        /h:html/h:head/x:model[not(
          x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:label']
          /x:value[not(@form) and text()='{label}']
        )]
        """

    def question_no_itext_hint(self, lang, hint):
        """There is no itext for the Question hint."""
        return f"""
        /h:html/h:head/x:model[not(
          x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:hint']
          /x:value[not(@form) and text()='{hint}']
        )]
        """

    def question_no_itext_form(self, lang, form, fname):
        """There is no alternate form itext for the Question label or hint."""
        prefix = {
            "audio": ("label", "jr://audio/"),
            "image": ("label", "jr://images/"),
            "big-image": ("label", "jr://images/"),
            "video": ("label", "jr://video/"),
            "guidance": ("hint", ""),
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:{prefix[form][0]}'
            and not(descendant::x:value[@form='{form}' and text()='{prefix[form][1]}{fname}'])]
        """

    def choice_value_in_body(self, cname):
        """The Choice label value is in the body."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']/x:item
          /x:value[not(@ref) and text()='{cname}']
        """

    def choice_label_references_itext(self, cname):
        """The Choice label references an itext entry."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']/x:item
          /x:label[@ref="jr:itext('/test/{self.question_name}/{cname}:label')" and not(text())]
        """

    def choice_itext_label(self, lang, cname, label):
        """The Choice label value is in the itext, referenced from the body."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}/{cname}:label']
          /x:value[not(@form) and text()='{label}']
        """

    def choice_itext_form(self, lang, cname, form, fname):
        """There is an alternate form itext for the Choice label, referenced from the body."""
        prefix = {
            "audio": "jr://audio/",
            "image": "jr://images/",
            "big-image": "jr://images/",
            "video": "jr://video/",
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}/{cname}:label']
          /x:value[@form='{form}' and text()='{prefix[form]}{fname}']
        """

    def choice_no_itext_label(self, lang, cname, label):
        """There is no itext for the Choice label."""
        return f"""
        /h:html/h:head/x:model[not(
          x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}/{cname}:label']
          /x:value[not(@form) and text()='{label}']
        )]
        """

    def choice_no_itext_form(self, lang, cname, form, fname):
        """There is no alternate form itext for the Choice label, referenced from the body."""
        prefix = {
            "audio": "jr://audio/",
            "image": "jr://images/",
            "big-image": "jr://images/",
            "video": "jr://video/",
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}/{cname}:label'
            and not(descendant::x:value[@form='{form}' and text()='{prefix[form]}{fname}'])]
        """

    def choice_list_references_itext(self, lname):
        """The Choice list (itemset) references an itext entry and internal instance."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test/{self.question_name}']
          /x:itemset[@nodeset="instance('{lname}')/root/item[{self.question_name} != '']"
            and child::x:label[@ref='jr:itext(itextId)'] and child::x:value[@ref='name']]
        """

    @staticmethod
    def choice_value_in_instance(lname, cname, index):
        """The Choice value is in an internal instance."""
        return f"""
        /h:html/h:head/x:model/x:instance[@id='{lname}']/x:root
          /x:item[child::x:itextId/text()='{lname}-{index}'
            and child::x:name='{cname}' and position()={index}+1]
        """

    @staticmethod
    def choice_instance_itext_label(lang, lname, label, index):
        """The Choice label value is in the itext, referenced from an internal instance."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='{lname}-{index}']
          /x:value[not(@form) and text()='{label}']
        """

    @staticmethod
    def choice_instance_itext_form(lang, lname, form, fname, index):
        """There is an alternate form itext for the Choice label, referenced from an internal instance."""
        prefix = {
            "audio": "jr://audio/",
            "image": "jr://images/",
            "big-image": "jr://images/",
            "video": "jr://video/",
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='{lname}-{index}']
          /x:value[@form='{form}' and text()='{prefix[form]}{fname}']
        """

    def constraint_msg_in_bind(self, msg):
        """The Constraint Message is in the model binding."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test/{self.question_name}'
          and @jr:constraintMsg='{msg}']
        """

    def constraint_msg_references_itext(self):
        """The Constraint Message references an itext entry."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test/{self.question_name}'
          and @jr:constraintMsg="jr:itext('/test/{self.question_name}:jr:constraintMsg')"]
        """

    def constraint_msg_itext(self, lang, msg):
        """The Constraint Message is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:jr:constraintMsg']
          /x:value[not(@form) and text()='{msg}']
        """

    def required_msg_in_bind(self, msg):
        """The Required Message is in the model binding."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test/{self.question_name}'
          and @jr:requiredMsg='{msg}']
        """

    def required_msg_references_itext(self):
        """The Required Message references an itext entry."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test/{self.question_name}'
          and @jr:requiredMsg="jr:itext('/test/{self.question_name}:jr:requiredMsg')"]
        """

    def required_msg_itext(self, lang, msg):
        """The Required Message is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test/{self.question_name}:jr:requiredMsg']
          /x:value[not(@form) and text()='{msg}']
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
        xp = XPathHelper(question_type="input", question_name="n1")
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                xp.question_label_references_itext(),
                xp.question_itext_label("english", "hello"),
                xp.question_itext_label("french", "bonjour"),
                xp.language_is_not_default("english"),
                xp.language_is_not_default("french"),
                xp.language_no_itext(DEFAULT_LANG),
                # Expected model binding found.
                """/h:html/h:head/x:model
                     /x:bind[@nodeset='/test/n1' and @readonly='true()' and @type='string']
                """,
            ],
            warnings_count=0,
        )

    def test_missing_media_itext(self):
        """Test missing media itext translation

        Fix for https://github.com/XLSForm/pyxform/issues/32
        """
        q1_default = "A.01 Have you received informed consent from the respondent?"
        q1_russian = "Получили ли вы форму согласия от респондента?"
        md = f"""
        | survey |       |               |              |                |                 |          |                      |                       |
        |        | name  | type          | label        | label::Russian | label::Kyrgyz   | required | media::audio::Kyrgyz | media::audio::Russian |
        |        | q1    | select_one yn | {q1_default} | {q1_russian}   | This is Kyrgyz. | true     | something.mp3        | test.mp3              |
        | choices |           |      |       |                |               |
        |         | list name | name | label | label::Russian | label::Kyrgyz |
        |         | yn        | 0    | No    | Нет            | Нет (ky)      |
        |         | yn        | 1    | Yes   | Да             | Да (ky)       |
        """
        xp = XPathHelper(question_type="select1", question_name="q1")
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                xp.question_label_references_itext(),
                xp.question_itext_label(DEFAULT_LANG, q1_default),
                xp.question_itext_label("Russian", q1_russian),
                xp.question_itext_label("Kyrgyz", "This is Kyrgyz."),
                xp.question_no_itext_form(DEFAULT_LANG, "audio", "-"),
                xp.question_itext_form("Russian", "audio", "test.mp3"),
                xp.question_itext_form("Kyrgyz", "audio", "something.mp3"),
                xp.choice_value_in_body("0"),
                xp.choice_label_references_itext("0"),
                xp.choice_itext_label(DEFAULT_LANG, "0", "No"),
                xp.choice_itext_label("Russian", "0", "Нет"),
                xp.choice_itext_label("Kyrgyz", "0", "Нет (ky)"),
                xp.choice_value_in_body("1"),
                xp.choice_label_references_itext("1"),
                xp.choice_itext_label(DEFAULT_LANG, "1", "Yes"),
                xp.choice_itext_label("Russian", "1", "Да"),
                xp.choice_itext_label("Kyrgyz", "1", "Да (ky)"),
                xp.language_is_default(DEFAULT_LANG),
                xp.language_is_not_default("Russian"),
                xp.language_is_not_default("Kyrgyz"),
            ],
        )

    def test_missing_translation__one_lang_all_cols(self):
        """Should warn if there's multiple missing translations, with/out default_language."""
        settings = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        """
        md = """
        | survey |               |      |       |            |            |                    |                   |                   |                   |                         |                       |
        |        | type          | name | label | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::video::eng | media::audio::eng | constraint_message::eng | required_message::eng |
        |        | select_one c1 | q1   | hello | hi there   | salutation | greeting           | greeting.jpg      | greeting.mkv      | greeting.mp3      | check me                | mandatory             |
        | choices |           |      |                 |
        |         | list name | name | label | label::eng | media::audio::eng | media::image::eng | media::video::eng |
        |         | c1        | na   | la-d  | la-e       | la-d.mp3          | la-d.jpg          | la-d.mkv          |
        |         | c1        | nb   | lb-d  | lb-e       | lb-d.mp3          | lb-d.jpg          | lb-d.mkv          |
        """
        cols = {
            SURVEY: {
                DEFAULT_LANG: (
                    "hint",
                    "guidance_hint",
                    "media::image",
                    "media::video",
                    "media::audio",
                    "constraint_message",
                    "required_message",
                )
            },
            CHOICES: {
                DEFAULT_LANG: (
                    "media::image",
                    "media::video",
                    "media::audio",
                )
            },
        }
        warning = format_missing_translations_msg(_in=cols)
        xp = XPathHelper(question_type="select1", question_name="q1")
        common_xpaths = [
            xp.question_label_references_itext(),
            xp.question_itext_label("eng", "hi there"),
            xp.question_hint_references_itext(),
            xp.question_itext_hint("eng", "salutation"),
            xp.question_itext_form("eng", "guidance", "greeting"),
            xp.question_itext_form("eng", "image", "greeting.jpg"),
            xp.question_itext_form("eng", "video", "greeting.mkv"),
            xp.question_itext_form("eng", "audio", "greeting.mp3"),
            xp.constraint_msg_references_itext(),
            xp.constraint_msg_itext("eng", "check me"),
            xp.required_msg_references_itext(),
            xp.required_msg_itext("eng", "mandatory"),
            xp.choice_value_in_body("na"),
            xp.choice_value_in_body("nb"),
            xp.choice_label_references_itext("na"),
            xp.choice_label_references_itext("nb"),
            xp.choice_itext_label("eng", "na", "la-e"),
            xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
            xp.choice_itext_form("eng", "na", "image", "la-d.jpg"),
            xp.choice_itext_form("eng", "na", "video", "la-d.mkv"),
            xp.choice_itext_label("eng", "nb", "lb-e"),
            xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
            xp.choice_itext_form("eng", "nb", "image", "lb-d.jpg"),
            xp.choice_itext_form("eng", "nb", "video", "lb-d.mkv"),
        ]
        # Warning case
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=common_xpaths
            + [
                xp.question_itext_label(DEFAULT_LANG, "hello"),
                xp.question_itext_hint(DEFAULT_LANG, "-"),
                xp.question_itext_form(DEFAULT_LANG, "guidance", "-"),
                xp.question_no_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                xp.question_no_itext_form(DEFAULT_LANG, "video", "greeting.mkv"),
                xp.question_no_itext_form(DEFAULT_LANG, "audio", "greeting.mp3"),
                xp.constraint_msg_itext(DEFAULT_LANG, "-"),
                xp.required_msg_itext(DEFAULT_LANG, "-"),
                xp.choice_itext_label(DEFAULT_LANG, "na", "la-d"),
                xp.choice_no_itext_form(DEFAULT_LANG, "na", "audio", "la-d.mp3"),
                xp.choice_no_itext_form(DEFAULT_LANG, "na", "image", "la-d.jpg"),
                xp.choice_no_itext_form(DEFAULT_LANG, "na", "video", "la-d.mkv"),
                xp.choice_itext_label(DEFAULT_LANG, "nb", "lb-d"),
                xp.choice_no_itext_form(DEFAULT_LANG, "nb", "audio", "lb-d.mp3"),
                xp.choice_no_itext_form(DEFAULT_LANG, "nb", "image", "lb-d.jpg"),
                xp.choice_no_itext_form(DEFAULT_LANG, "nb", "video", "lb-d.mkv"),
                xp.language_is_default(DEFAULT_LANG),
                xp.language_is_not_default("eng"),
            ],
        )
        # default_language set case
        self.assertPyxformXform(
            name="test",
            md=settings + md,
            # TODO: bug - missing default lang translatable/itext values.
            # warnings__contains=[warning],
            xml__xpath_match=common_xpaths
            + [xp.language_is_default("eng"), xp.language_no_itext(DEFAULT_LANG)],
        )

    @unittest.skip("Slow performance test. Un-skip to run as needed.")
    def test_missing_translations_check_performance(self):
        """
        Should find the translations check costs a fraction of a second for large forms.

        Results with Python 3.8.9 on VM with 4CPU 8GB RAM, x questions with 2 choices
        each, average of 10 runs (seconds), with and without the check, per question:
        | num  | with   | without |
        |  500 | 1.0192 |  0.9950 |
        | 1000 | 2.0054 |  2.1026 |
        | 2000 | 4.0714 |  4.0926 |
        | 3000 | 6.0266 |  6.2476 |
        """
        survey_header = """
        | survey |                 |        |                |               |
        |        | type            | name   | label::english | label::french |
        """
        question = """
        |        | select_one c{i} | q{i}   | hello          | bonjour       |
        """
        choices_header = """
        | choices |             |      |                    |
        |         | list name   | name | label | label::eng |
        """
        choice_list = """
        |         | c{i}        | na   | la-d  | la-e       |
        |         | c{i}        | nb   | lb-d  | lb-e       |
        """
        for count in (500, 1000, 2000):
            questions = "\n".join((question.format(i=i) for i in range(1, count)))
            choice_lists = "\n".join((choice_list.format(i=i) for i in range(1, count)))
            md = "".join((survey_header, questions, choices_header, choice_lists))

            def run(name):
                runs = 0
                results = []
                while runs < 10:
                    start = perf_counter()
                    self.assertPyxformXform(md=md)
                    results.append(perf_counter() - start)
                    runs += 1
                print(name, sum(results) / len(results))

            run(name=f"questions={count}, with check (seconds):")

            with patch("pyxform.xls2json.missing_translations_check", return_value=[]):
                run(name=f"questions={count}, without check (seconds):")


class TestTranslationsSurvey(PyxformTestCase):
    """Translations behaviour of columns in the Survey sheet."""

    def setUp(self) -> None:
        self.xp = XPathHelper(question_type="input", question_name="n1")

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
                self.xp.question_label_in_body("hello"),
                self.xp.question_no_itext_label(DEFAULT_LANG, "hello"),
                self.xp.question_hint_in_body("salutation"),
                self.xp.question_no_itext_hint(DEFAULT_LANG, "salutation"),
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
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label(DEFAULT_LANG, "hello"),
                # TODO: is this a bug? Why itext for label/image but not hint?
                self.xp.question_hint_in_body("salutation"),
                self.xp.question_no_itext_hint(DEFAULT_LANG, "salutation"),
                self.xp.question_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                self.xp.language_is_default(DEFAULT_LANG),
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
                self.xp.question_label_in_body("hello"),
                self.xp.question_no_itext_label(DEFAULT_LANG, "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint(DEFAULT_LANG, "salutation"),
                self.xp.question_itext_form(DEFAULT_LANG, "guidance", "greeting"),
                self.xp.language_is_default(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__no_translation__label_and_hint_all_cols(self):
        """Should find default language translations for all translatables."""
        md = """
        | survey |      |      |       |            |               |              |              |              |                    |                  |
        |        | type | name | label | hint       | guidance_hint | media::image | media::video | media::audio | constraint_message | required_message |
        |        | note | n1   | hello | salutation | greeting      | greeting.jpg | greeting.mkv | greeting.mp3 | check me           | mandatory        |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label(DEFAULT_LANG, "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint(DEFAULT_LANG, "salutation"),
                self.xp.question_itext_form(DEFAULT_LANG, "guidance", "greeting"),
                self.xp.question_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                self.xp.question_itext_form(DEFAULT_LANG, "video", "greeting.mkv"),
                self.xp.question_itext_form(DEFAULT_LANG, "audio", "greeting.mp3"),
                self.xp.constraint_msg_in_bind("check me"),
                self.xp.required_msg_in_bind("mandatory"),
                self.xp.language_is_default(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__no_translation__image_with_big_image(self):
        """Should find default language translations for image and big-image."""
        md = """
        | survey |      |      |              |                  |
        |        | type | name | media::image | media::big-image |
        |        | note | n1   | greeting.jpg | greeting.jpg     |
        """
        self.assertPyxformXform(
            name="test",
            debug=True,
            md=md,
            xml__xpath_match=[
                self.xp.question_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                self.xp.question_itext_form(DEFAULT_LANG, "big-image", "greeting.jpg"),
                self.xp.language_is_default(DEFAULT_LANG),
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
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                # TODO: is this a bug? Only one language but not marked default.
                self.xp.language_is_not_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
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
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                self.xp.question_itext_form("eng", "image", "greeting.jpg"),
                self.xp.language_is_not_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
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
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                self.xp.question_itext_form("eng", "guidance", "greeting"),
                self.xp.language_is_not_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__one_translation__label_and_hint_all_cols(self):
        """Should find language translation for label, hint, and all translatables."""
        md = """
        | survey |      |      |            |            |                    |                   |                       |                   |                   |                         |                       |
        |        | type | name | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::big-image::eng | media::video::eng | media::audio::eng | constraint_message::eng | required_message::eng |
        |        | note | n1   | hello      | salutation | greeting           | greeting.jpg      | greeting.jpg          | greeting.mkv      | greeting.mp3      | check me                | mandatory             |
        """
        self.assertPyxformXform(
            name="test",
            md=md,
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                self.xp.question_itext_form("eng", "guidance", "greeting"),
                self.xp.question_itext_form("eng", "image", "greeting.jpg"),
                self.xp.question_itext_form("eng", "big-image", "greeting.jpg"),
                self.xp.question_itext_form("eng", "video", "greeting.mkv"),
                self.xp.question_itext_form("eng", "audio", "greeting.mp3"),
                self.xp.constraint_msg_references_itext(),
                self.xp.constraint_msg_itext("eng", "check me"),
                self.xp.required_msg_references_itext(),
                self.xp.required_msg_itext("eng", "mandatory"),
                self.xp.language_is_not_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_missing_translation__one_lang_simple__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |       |            |            |
        |        | type | name | label | label::eng | hint       |
        |        | note | n1   | hello | hi there   | salutation |
        """
        warning = format_missing_translations_msg(_in={SURVEY: {"eng": ["hint"]}})
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label(DEFAULT_LANG, "hello"),
                self.xp.question_itext_label("eng", "hi there"),
                self.xp.question_hint_in_body("salutation"),
                self.xp.language_is_default(DEFAULT_LANG),
                self.xp.language_is_not_default("eng"),
            ],
        )

    def test_missing_translation__one_lang_simple__warn__default(self):
        """Should warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey |      |      |       |            |            |
        |        | type | name | label | label::eng | hint       |
        |        | note | n1   | hello | hi there   | salutation |
        """
        warning = format_missing_translations_msg(_in={SURVEY: {"eng": ["hint"]}})
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hi there"),
                self.xp.question_hint_in_body("salutation"),
                self.xp.question_no_itext_hint("eng", "salutation"),
                self.xp.language_is_default("eng"),
                # TODO: bug - missing default lang translatable/itext values.
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__one_lang_all_cols__warn__no_default(self):
        """Should warn if there's multiple missing translations and no default_language."""
        md = """
        | survey |      |      |       |            |            |                    |                   |                       |                   |                   |                         |                       |
        |        | type | name | label | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::big-image::eng | media::video::eng | media::audio::eng | constraint_message::eng | required_message::eng |
        |        | note | n1   | hello | hi there   | salutation | greeting           | greeting.jpg      | greeting.jpg          | greeting.mkv      | greeting.mp3      | check me                | mandatory             |
        """
        cols = {
            SURVEY: {
                DEFAULT_LANG: (
                    "hint",
                    "guidance_hint",
                    "media::image",
                    "media::big-image",
                    "media::video",
                    "media::audio",
                    "constraint_message",
                    "required_message",
                )
            }
        }
        warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label(DEFAULT_LANG, "hello"),
                self.xp.question_itext_label("eng", "hi there"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                self.xp.question_itext_hint(DEFAULT_LANG, "-"),
                self.xp.question_itext_form("eng", "guidance", "greeting"),
                self.xp.question_itext_form(DEFAULT_LANG, "guidance", "-"),
                self.xp.question_itext_form("eng", "image", "greeting.jpg"),
                self.xp.question_no_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                self.xp.question_itext_form("eng", "big-image", "greeting.jpg"),
                self.xp.question_no_itext_form(DEFAULT_LANG, "big-image", "greeting.jpg"),
                self.xp.question_itext_form("eng", "video", "greeting.mkv"),
                self.xp.question_no_itext_form(DEFAULT_LANG, "video", "greeting.mkv"),
                self.xp.question_itext_form("eng", "audio", "greeting.mp3"),
                self.xp.question_no_itext_form(DEFAULT_LANG, "audio", "greeting.mp3"),
                self.xp.constraint_msg_references_itext(),
                self.xp.constraint_msg_itext("eng", "check me"),
                self.xp.constraint_msg_itext(DEFAULT_LANG, "-"),
                self.xp.required_msg_references_itext(),
                self.xp.required_msg_itext("eng", "mandatory"),
                self.xp.required_msg_itext(DEFAULT_LANG, "-"),
                self.xp.language_is_default(DEFAULT_LANG),
                self.xp.language_is_not_default("eng"),
            ],
        )

    def test_missing_translation__one_lang_all_cols__warn__default(self):
        """Should warn if there's missing translations with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey |      |      |       |            |            |                    |                   |                       |                   |                   |                         |                       |
        |        | type | name | label | label::eng | hint::eng  | guidance_hint::eng | media::image::eng | media::big-image::eng | media::video::eng | media::audio::eng | constraint_message::eng | required_message::eng |
        |        | note | n1   | hello | hi there   | salutation | greeting           | greeting.jpg      | greeting.jpg          | greeting.mkv      | greeting.mp3      | check me                | mandatory             |
        """
        # cols = {
        #     SURVEY: {
        #         DEFAULT_LANG: (
        #             "hint",
        #             "guidance_hint",
        #             "media::image",
        #             "media::video",
        #             "media::audio",
        #             "constraint_message",
        #             "required_message",
        #         )
        #     }
        # }
        # warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            name="test",
            md=md,
            # TODO: bug - missing default lang translatable/itext values.
            # warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hi there"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                self.xp.question_itext_form("eng", "guidance", "greeting"),
                self.xp.question_itext_form("eng", "image", "greeting.jpg"),
                self.xp.question_itext_form("eng", "video", "greeting.mkv"),
                self.xp.question_itext_form("eng", "audio", "greeting.mp3"),
                self.xp.language_is_default("eng"),
                self.xp.constraint_msg_references_itext(),
                self.xp.constraint_msg_itext("eng", "check me"),
                self.xp.required_msg_references_itext(),
                self.xp.required_msg_itext("eng", "mandatory"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__one_lang_overlap__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |            |            |
        |        | type | name | label::eng | hint       |
        |        | note | n1   | hello      | salutation |
        """
        warning = format_missing_translations_msg(
            _in={SURVEY: {"eng": ["hint"], "default": ["label"]}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_hint_in_body("salutation"),
                self.xp.question_no_itext_hint("eng", "salutation"),
                self.xp.question_no_itext_hint(DEFAULT_LANG, "salutation"),
                self.xp.language_is_not_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__one_lang_overlap__warn__default(self):
        """Should warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey |      |      |            |            |
        |        | type | name | label::eng | hint       |
        |        | note | n1   | hello      | salutation |
        """
        warning = format_missing_translations_msg(_in={SURVEY: {"eng": ["hint"]}})
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                # TODO: is this a bug? Default hint gets merged into eng hint.
                self.xp.question_hint_in_body("salutation"),
                self.xp.question_no_itext_hint(DEFAULT_LANG, "salutation"),
                self.xp.question_no_itext_hint("eng", "salutation"),
                self.xp.language_is_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__two_lang__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |            |               |            |
        |        | type | name | label::eng | label::french | hint::eng  |
        |        | note | n1   | hello      | bonjour       | salutation |
        """
        warning = format_missing_translations_msg(_in={SURVEY: {"french": ["hint"]}})
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_itext_label("french", "bonjour"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                # Output of a dash for empty translation is not a bug, it's a reminder /
                # placeholder since XForms spec requires a value for every translation.
                self.xp.question_itext_hint("french", "-"),
                self.xp.language_is_not_default("eng"),
                self.xp.language_is_not_default("french"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__two_lang__warn__default(self):
        """Should warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey |      |      |            |               |            |
        |        | type | name | label::eng | label::french | hint::eng  |
        |        | note | n1   | hello      | bonjour       | salutation |
        """
        warning = format_missing_translations_msg(_in={SURVEY: {"french": ["hint"]}})
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng", "hello"),
                self.xp.question_itext_label("french", "bonjour"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng", "salutation"),
                self.xp.question_itext_hint("french", "-"),
                self.xp.language_is_default("eng"),
                self.xp.language_is_not_default("french"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__issue_157__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |               |              |              |
        |        | type | name | label::french | hint::french | media::image |
        |        | note | n1   | bonjour       | salutation   | greeting.jpg |
        """
        warning = format_missing_translations_msg(
            _in={
                SURVEY: {
                    "default": ("hint", "label"),
                    "french": ("media::image",),
                }
            }
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("french", "bonjour"),
                self.xp.question_itext_label(DEFAULT_LANG, "-"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("french", "salutation"),
                self.xp.question_itext_hint(DEFAULT_LANG, "-"),
                self.xp.question_no_itext_form("french", "audio", "greeting.mp3"),
                self.xp.question_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                self.xp.language_is_not_default("french"),
                self.xp.language_is_default(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__issue_157__warn__default(self):
        """Should warn if there's missing translations with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | french           |
        | survey |      |      |               |              |              |
        |        | type | name | label::french | hint::french | media::image |
        |        | note | n1   | bonjour       | salutation   | greeting.jpg |
        """
        warning = format_missing_translations_msg(
            _in={SURVEY: {"default": ("hint", "label"), "french": ("media::image",)}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("french", "bonjour"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("french", "salutation"),
                self.xp.question_itext_form("french", "image", "greeting.jpg"),
                self.xp.language_is_default("french"),
                # TODO: bug - missing default lang translatable/itext values.
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )


class TestTranslationsChoices(PyxformTestCase):
    """Translations behaviour of columns in the Choices sheet."""

    def setUp(self) -> None:
        self.xp = XPathHelper(question_type="select1", question_name="q1")

    def test_select1__non_dynamic_choices__no_lang__all_columns(self):
        """Should find that when all translatable choices columns are used they appear in itext."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |       |              |              |                  |              |
        |         | list name | name | label | media::audio | media::image | media::big-image | media::video |
        |         | c1        | na   | la    | a.mp3        | a.jpg        | a.jpg            | a.mkv        |
        |         | c1        | nb   | lb    | b.mp3        | b.jpg        | b.jpg            | b.mkv        |
        """
        xpath_match = [
            self.xp.question_label_in_body("Question 1"),
            self.xp.choice_value_in_body("na"),
            self.xp.choice_value_in_body("nb"),
            self.xp.choice_label_references_itext("na"),
            self.xp.choice_label_references_itext("nb"),
            self.xp.choice_itext_label(DEFAULT_LANG, "na", "la"),
            self.xp.choice_itext_form(DEFAULT_LANG, "na", "audio", "a.mp3"),
            self.xp.choice_itext_form(DEFAULT_LANG, "na", "image", "a.jpg"),
            self.xp.choice_itext_form(DEFAULT_LANG, "na", "big-image", "a.jpg"),
            self.xp.choice_itext_form(DEFAULT_LANG, "na", "video", "a.mkv"),
            self.xp.choice_itext_label(DEFAULT_LANG, "nb", "lb"),
            self.xp.choice_itext_form(DEFAULT_LANG, "nb", "audio", "b.mp3"),
            self.xp.choice_itext_form(DEFAULT_LANG, "nb", "image", "b.jpg"),
            self.xp.choice_itext_form(DEFAULT_LANG, "nb", "big-image", "b.jpg"),
            self.xp.choice_itext_form(DEFAULT_LANG, "nb", "video", "b.mkv"),
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
        | choices |           |      |                 |                        |                        |                            |                        |
        |         | list name | name | label::Eng (en) | media::audio::Eng (en) | media::image::Eng (en) | media::big-image::Eng (en) | media::video::Eng (en) |
        |         | c1        | na   | la              | a.mp3                  | a.jpg                  | a.jpg                      | a.mkv                  |
        |         | c1        | nb   | lb              | b.mp3                  | b.jpg                  | b.jpg                      | b.mkv                  |
        """
        xpath_match = [
            self.xp.question_label_in_body("Question 1"),
            self.xp.choice_value_in_body("na"),
            self.xp.choice_value_in_body("nb"),
            self.xp.choice_label_references_itext("na"),
            self.xp.choice_label_references_itext("nb"),
            self.xp.choice_itext_label("Eng (en)", "na", "la"),
            self.xp.choice_itext_form("Eng (en)", "na", "audio", "a.mp3"),
            self.xp.choice_itext_form("Eng (en)", "na", "image", "a.jpg"),
            self.xp.choice_itext_form("Eng (en)", "na", "big-image", "a.jpg"),
            self.xp.choice_itext_form("Eng (en)", "na", "video", "a.mkv"),
            self.xp.choice_itext_label("Eng (en)", "nb", "lb"),
            self.xp.choice_itext_form("Eng (en)", "nb", "audio", "b.mp3"),
            self.xp.choice_itext_form("Eng (en)", "nb", "image", "b.jpg"),
            self.xp.choice_itext_form("Eng (en)", "nb", "big-image", "b.jpg"),
            self.xp.choice_itext_form("Eng (en)", "nb", "video", "b.mkv"),
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
        | choices |           |      |       |              |              |                  |
        |         | list name | name | label | media::audio | media::image | media::big-image | media::video |
        |         | c1        | na   | la    | a.mp3        | a.jpg        | a.jpg            | a.mkv        |
        |         | c1        | nb   | lb    | b.mp3        | b.jpg        | b.jpg            | b.mkv        |
        """
        xpath_match = [
            self.xp.question_label_in_body("Question 1"),
            self.xp.choice_list_references_itext("c1"),
            self.xp.choice_value_in_instance("c1", "na", 0),
            self.xp.choice_value_in_instance("c1", "nb", 1),
            self.xp.choice_instance_itext_label(DEFAULT_LANG, "c1", "la", 0),
            self.xp.choice_instance_itext_form(DEFAULT_LANG, "c1", "audio", "a.mp3", 0),
            self.xp.choice_instance_itext_form(DEFAULT_LANG, "c1", "image", "a.jpg", 0),
            self.xp.choice_instance_itext_form(
                DEFAULT_LANG, "c1", "big-image", "a.jpg", 0
            ),
            self.xp.choice_instance_itext_form(DEFAULT_LANG, "c1", "video", "a.mkv", 0),
            self.xp.choice_instance_itext_label(DEFAULT_LANG, "c1", "lb", 1),
            self.xp.choice_instance_itext_form(DEFAULT_LANG, "c1", "audio", "b.mp3", 1),
            self.xp.choice_instance_itext_form(DEFAULT_LANG, "c1", "image", "b.jpg", 1),
            self.xp.choice_instance_itext_form(
                DEFAULT_LANG, "c1", "big-image", "b.jpg", 1
            ),
            self.xp.choice_instance_itext_form(DEFAULT_LANG, "c1", "video", "b.mkv", 1),
        ]
        self.assertPyxformXform(
            md=md,
            name="test",
            xml__xpath_match=xpath_match,
        )

    def test_select1__dynamic_choices__one_lang__all_columns(self):
        """Should find that when all translatable choices columns are used they appear in itext."""
        md = """
        | survey  |               |       |            |               |
        |         | type          | name  | label      | choice_filter |
        |         | select_one c1 | q1    | Question 1 | q1 != ''      |
        | choices |           |      |                 |                        |                        |                            |                        |
        |         | list name | name | label::Eng (en) | media::audio::Eng (en) | media::image::Eng (en) | media::big-image::Eng (en) | media::video::Eng (en) |
        |         | c1        | na   | la              | a.mp3                  | a.jpg                  | a.jpg                      | a.mkv                  |
        |         | c1        | nb   | lb              | b.mp3                  | b.jpg                  | b.jpg                      | b.mkv                  |
        """
        xpath_match = [
            self.xp.question_label_in_body("Question 1"),
            self.xp.choice_list_references_itext("c1"),
            self.xp.choice_value_in_instance("c1", "na", "0"),
            self.xp.choice_value_in_instance("c1", "nb", "1"),
            self.xp.choice_instance_itext_label("Eng (en)", "c1", "la", 0),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "audio", "a.mp3", 0),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "image", "a.jpg", 0),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "big-image", "a.jpg", 0),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "video", "a.mkv", 0),
            self.xp.choice_instance_itext_label("Eng (en)", "c1", "lb", 1),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "audio", "b.mp3", 1),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "image", "b.jpg", 1),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "big-image", "b.jpg", 1),
            self.xp.choice_instance_itext_form("Eng (en)", "c1", "video", "b.mkv", 1),
        ]
        self.assertPyxformXform(
            md=md,
            name="test",
            xml__xpath_match=xpath_match,
        )

    def test_missing_translation__one_lang_simple__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label | label::eng | media::audio |
        |         | c1        | na   | la-d  | la-e       | la-d.mp3     |
        |         | c1        | nb   | lb-d  | lb-e       | lb-d.mp3     |
        """
        warning = format_missing_translations_msg(
            _in={CHOICES: {"eng": ("media::audio",)}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label(DEFAULT_LANG, "na", "la-d"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_form(DEFAULT_LANG, "na", "audio", "la-d.mp3"),
                self.xp.choice_no_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_label(DEFAULT_LANG, "nb", "lb-d"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_form(DEFAULT_LANG, "nb", "audio", "lb-d.mp3"),
                self.xp.choice_no_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.language_is_default(DEFAULT_LANG),
                self.xp.language_is_not_default("eng"),
            ],
        )

    def test_missing_translation__one_lang_simple__warn__default(self):
        """Should warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label | label::eng | media::audio |
        |         | c1        | na   | la-d  | la-e       | la-d.mp3     |
        |         | c1        | nb   | lb-d  | lb-e       | lb-d.mp3     |
        """
        cols = {CHOICES: {"default": ("label",), "eng": ("media::audio",)}}
        warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.language_is_default("eng"),
                # TODO: bug - missing default lang translatable/itext values.
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__one_lang_all_cols__warn__no_default(self):
        """Should warn if there's multiple missing translations and no default_language."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label | label::eng | media::audio::eng | media::image::eng | media::big-image::eng | media::video::eng |
        |         | c1        | na   | la-d  | la-e       | la-d.mp3          | la-d.jpg          | la-d.jpg              | la-d.mkv          |
        |         | c1        | nb   | lb-d  | lb-e       | lb-d.mp3          | lb-d.jpg          | lb-d.jpg              | lb-d.mkv          |
        """
        cols = {
            CHOICES: {
                DEFAULT_LANG: (
                    "media::image",
                    "media::big-image",
                    "media::video",
                    "media::audio",
                )
            }
        }
        warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label(DEFAULT_LANG, "na", "la-d"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_form("eng", "na", "image", "la-d.jpg"),
                self.xp.choice_itext_form("eng", "na", "big-image", "la-d.jpg"),
                self.xp.choice_itext_form("eng", "na", "video", "la-d.mkv"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "na", "audio", "la-d.mp3"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "na", "image", "la-d.jpg"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "na", "big-image", "la-d.jpg"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "na", "video", "la-d.mkv"),
                self.xp.choice_itext_label(DEFAULT_LANG, "nb", "lb-d"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.choice_itext_form("eng", "nb", "image", "lb-d.jpg"),
                self.xp.choice_itext_form("eng", "nb", "big-image", "lb-d.jpg"),
                self.xp.choice_itext_form("eng", "nb", "video", "lb-d.mkv"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "nb", "audio", "lb-d.mp3"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "nb", "image", "lb-d.jpg"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "nb", "big-image", "lb-d.jpg"),
                self.xp.choice_no_itext_form(DEFAULT_LANG, "nb", "video", "lb-d.mkv"),
                self.xp.language_is_default(DEFAULT_LANG),
                self.xp.language_is_not_default("eng"),
            ],
        )

    def test_missing_translation__one_lang_all_cols__warn__default(self):
        """Should warn if there's missing translations with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label | label::eng | media::audio::eng | media::image::eng | media::big-image::eng | media::video::eng |
        |         | c1        | na   | la-d  | la-e       | la-d.mp3          | la-d.jpg          | la-d.jpg              | la-d.mkv          |
        |         | c1        | nb   | lb-d  | lb-e       | lb-d.mp3          | lb-d.jpg          | lb-d.jpg              | lb-d.mkv          |
        """
        # cols = {
        #     CHOICES: {
        #         DEFAULT_LANG: (
        #             "media::image",
        #             "media::video",
        #             "media::audio",
        #         )
        #     }
        # }
        # warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            name="test",
            md=md,
            # TODO: bug - missing default lang translatable/itext values.
            # warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_form("eng", "na", "image", "la-d.jpg"),
                self.xp.choice_itext_form("eng", "na", "big-image", "la-d.jpg"),
                self.xp.choice_itext_form("eng", "na", "video", "la-d.mkv"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.choice_itext_form("eng", "nb", "image", "lb-d.jpg"),
                self.xp.choice_itext_form("eng", "nb", "big-image", "lb-d.jpg"),
                self.xp.choice_itext_form("eng", "nb", "video", "lb-d.mkv"),
                self.xp.language_is_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__one_lang_overlap__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label::eng | media::audio |
        |         | c1        | na   | la-e       | la-d.mp3     |
        |         | c1        | nb   | lb-e       | lb-d.mp3     |
        """
        warning = format_missing_translations_msg(
            _in={CHOICES: {"eng": ("media::audio",), "default": ("label",)}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                # Output of a dash for empty translation is not a bug, it's a reminder /
                # placeholder since XForms spec requires a value for every translation.
                self.xp.choice_itext_label(DEFAULT_LANG, "na", "-"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_form(DEFAULT_LANG, "na", "audio", "la-d.mp3"),
                self.xp.choice_no_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_label(DEFAULT_LANG, "nb", "-"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_form(DEFAULT_LANG, "nb", "audio", "lb-d.mp3"),
                self.xp.choice_no_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.language_is_default(DEFAULT_LANG),
                self.xp.language_is_not_default("eng"),
            ],
        )

    def test_missing_translation__one_lang_overlap__warn__default(self):
        """Should warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label::eng | media::audio |
        |         | c1        | na   | la-e       | la-d.mp3     |
        |         | c1        | nb   | lb-e       | lb-d.mp3     |
        """
        warning = format_missing_translations_msg(
            _in={CHOICES: {"eng": ("media::audio",), "default": ("label",)}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                # TODO: is this a bug? Default audio gets merged into eng hint.
                self.xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.language_is_default("eng"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__two_lang__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label::eng | label::french | media::audio::eng |
        |         | c1        | na   | la-e       | la-f          | la-d.mp3          |
        |         | c1        | nb   | lb-e       | lb-f          | lb-d.mp3          |
        """
        warning = format_missing_translations_msg(
            _in={CHOICES: {"french": ("media::audio",)}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_label("french", "na", "la-f"),
                self.xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_no_itext_form("french", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_label("french", "nb", "lb-f"),
                self.xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.choice_no_itext_form("french", "na", "audio", "lb-d.mp3"),
                self.xp.language_is_not_default("eng"),
                self.xp.language_is_not_default("french"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    def test_missing_translation__two_lang__warn__default(self):
        """Should warn if there's a missing translation with a default_language."""
        md = """
        | settings |                  |
        |          | default_language |
        |          | eng              |
        | survey  |               |       |            |
        |         | type          | name  | label      |
        |         | select_one c1 | q1    | Question 1 |
        | choices |           |      |                 |
        |         | list name | name | label::eng | label::french | media::audio::eng |
        |         | c1        | na   | la-e       | la-f          | la-d.mp3          |
        |         | c1        | nb   | lb-e       | lb-f          | lb-d.mp3          |
        """
        warning = format_missing_translations_msg(
            _in={CHOICES: {"french": ("media::audio",)}}
        )
        self.assertPyxformXform(
            name="test",
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                self.xp.choice_value_in_body("na"),
                self.xp.choice_value_in_body("nb"),
                self.xp.choice_label_references_itext("na"),
                self.xp.choice_label_references_itext("nb"),
                self.xp.choice_itext_label("eng", "na", "la-e"),
                self.xp.choice_itext_label("french", "na", "la-f"),
                self.xp.choice_itext_form("eng", "na", "audio", "la-d.mp3"),
                self.xp.choice_no_itext_form("french", "na", "audio", "la-d.mp3"),
                self.xp.choice_itext_label("eng", "nb", "lb-e"),
                self.xp.choice_itext_label("french", "nb", "lb-f"),
                self.xp.choice_itext_form("eng", "nb", "audio", "lb-d.mp3"),
                self.xp.choice_no_itext_form("french", "na", "audio", "lb-d.mp3"),
                self.xp.language_is_default("eng"),
                self.xp.language_is_not_default("french"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
        )
