"""
Test translations syntax.
"""

from dataclasses import dataclass
from os import getpid
from time import perf_counter
from unittest import skip
from unittest.mock import patch

from psutil import Process
from pyxform.constants import CHOICES, SURVEY
from pyxform.constants import DEFAULT_LANGUAGE_VALUE as DEFAULT_LANG
from pyxform.validators.pyxform.translations_checks import (
    OR_OTHER_WARNING,
    format_missing_translations_msg,
)
from pyxform.xls2xform import convert

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


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
        /h:html/h:body/x:{self.question_type}[@ref='/test_name/{self.question_name}']
          /x:label[not(@ref) and text()='{label}']
        """

    def question_hint_in_body(self, hint):
        """The Question hint value is in the body."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test_name/{self.question_name}']
          /x:hint[not(@ref) and text()='{hint}']
        """

    def question_label_references_itext(self):
        """The Question label references an itext entry."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test_name/{self.question_name}']
          /x:label[@ref="jr:itext('/test_name/{self.question_name}:label')" and not(text())]
        """

    def question_hint_references_itext(self):
        """The Question hint references an itext entry."""
        return f"""
        /h:html/h:body/x:{self.question_type}[@ref='/test_name/{self.question_name}']
          /x:hint[@ref="jr:itext('/test_name/{self.question_name}:hint')" and not(text())]
        """

    def question_itext_label(self, lang, label):
        """The Question label value is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{self.question_name}:label']
          /x:value[not(@form) and text()='{label}']
        """

    def question_itext_hint(self, lang, hint):
        """The Question hint value is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{self.question_name}:hint']
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
          /x:text[@id='/test_name/{self.question_name}:{prefix[form][0]}']
          /x:value[@form='{form}' and text()='{prefix[form][1]}{fname}']
        """

    def question_no_itext_label(self, lang, label):
        """There is no itext for the Question label."""
        return f"""
        /h:html/h:head/x:model[not(
          x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{self.question_name}:label']
          /x:value[not(@form) and text()='{label}']
        )]
        """

    def question_no_itext_hint(self, lang, hint):
        """There is no itext for the Question hint."""
        return f"""
        /h:html/h:head/x:model[not(
          x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{self.question_name}:hint']
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
          /x:text[@id='/test_name/{self.question_name}:{prefix[form][0]}'
            and not(descendant::x:value[@form='{form}' and text()='{prefix[form][1]}{fname}'])]
        """

    def constraint_msg_in_bind(self, msg):
        """The Constraint Message is in the model binding."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test_name/{self.question_name}'
          and @jr:constraintMsg='{msg}']
        """

    def constraint_msg_references_itext(self):
        """The Constraint Message references an itext entry."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test_name/{self.question_name}'
          and @jr:constraintMsg="jr:itext('/test_name/{self.question_name}:jr:constraintMsg')"]
        """

    def constraint_msg_itext(self, lang, msg):
        """The Constraint Message is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{self.question_name}:jr:constraintMsg']
          /x:value[not(@form) and text()='{msg}']
        """

    def required_msg_in_bind(self, msg):
        """The Required Message is in the model binding."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test_name/{self.question_name}'
          and @jr:requiredMsg='{msg}']
        """

    def required_msg_references_itext(self):
        """The Required Message references an itext entry."""
        return f"""
        /h:html/h:head/x:model/x:bind[@nodeset='/test_name/{self.question_name}'
          and @jr:requiredMsg="jr:itext('/test_name/{self.question_name}:jr:requiredMsg')"]
        """

    def required_msg_itext(self, lang, msg):
        """The Required Message is in the itext."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{self.question_name}:jr:requiredMsg']
          /x:value[not(@form) and text()='{msg}']
        """


class TestTranslations(PyxformTestCase):
    """Miscellaneous translations behaviour or cases."""

    def test_double_colon_translations(self):
        """Should find translations for a simple form with a label in two languages."""
        md = """
        | survey |      |      |                     |                    |
        |        | type | name | label::english (en) | label::french (fr) |
        |        | note | n1   | hello               | bonjour            |
        """
        xp = XPathHelper(question_type="input", question_name="n1")
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xp.question_label_references_itext(),
                xp.question_itext_label("english (en)", "hello"),
                xp.question_itext_label("french (fr)", "bonjour"),
                xp.language_is_not_default("english (en)"),
                xp.language_is_not_default("french (fr)"),
                xp.language_no_itext(DEFAULT_LANG),
                # Expected model binding found.
                """/h:html/h:head/x:model
                     /x:bind[@nodeset='/test_name/n1' and @readonly='true()' and @type='string']
                """,
            ],
            warnings_count=0,
        )

    def test_spaces_adjacent_to_translation_delimiter(self):
        """Should trim whitespace either side of double-colon '::' delimiter."""
        md = """
        | survey |
        |        | type | name | label::French (fr) | constraint           | constraint_message::French (fr) | constraint_message :: English (en) |
        |        | text | q1   | Q1                 | string-length(.) > 5 | Trop court!                     | Too short!                         |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:itext/x:translation[@lang='French (fr)']
                  /x:text[@id='/test_name/q1:jr:constraintMsg']
                  /x:value[not(@form) and text()='Trop court!']
                """,
                """
                /h:html/h:head/x:model/x:itext/x:translation[@lang='English (en)']
                  /x:text[@id='/test_name/q1:jr:constraintMsg']
                  /x:value[not(@form) and text()='Too short!']
                """,
            ],
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
            md=md,
            xml__xpath_match=[
                xp.question_label_references_itext(),
                xp.question_itext_label(DEFAULT_LANG, q1_default),
                xp.question_itext_label("Russian", q1_russian),
                xp.question_itext_label("Kyrgyz", "This is Kyrgyz."),
                xp.question_no_itext_form(DEFAULT_LANG, "audio", "-"),
                xp.question_itext_form("Russian", "audio", "test.mp3"),
                xp.question_itext_form("Kyrgyz", "audio", "something.mp3"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("yn", ("0", "1")),
                xpc.model_itext_choice_text_label_by_pos("default", "yn", ("No", "Yes")),
                xpc.model_itext_choice_text_label_by_pos("Russian", "yn", ("Нет", "Да")),
                xpc.model_itext_choice_text_label_by_pos(
                    "Kyrgyz", "yn", ("Нет (ky)", "Да (ky)")
                ),
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
                    "image",
                    "video",
                    "audio",
                    "constraint_message",
                    "required_message",
                )
            },
            CHOICES: {
                DEFAULT_LANG: (
                    "image",
                    "video",
                    "audio",
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
            xpq.body_select1_itemset("q1"),
            xpc.model_instance_choices_itext("c1", ("na", "nb")),
            xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
            xpc.model_itext_choice_media_by_pos(
                "eng",
                "c1",
                (
                    (("audio", "la-d.mp3"), ("image", "la-d.jpg"), ("video", "la-d.mkv")),
                    (("audio", "lb-d.mp3"), ("image", "lb-d.jpg"), ("video", "lb-d.mkv")),
                ),
            ),
        ]
        # Warning case
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                *common_xpaths,
                xp.question_itext_label(DEFAULT_LANG, "hello"),
                xp.question_itext_hint(DEFAULT_LANG, "-"),
                xp.question_itext_form(DEFAULT_LANG, "guidance", "-"),
                xp.question_no_itext_form(DEFAULT_LANG, "image", "greeting.jpg"),
                xp.question_no_itext_form(DEFAULT_LANG, "video", "greeting.mkv"),
                xp.question_no_itext_form(DEFAULT_LANG, "audio", "greeting.mp3"),
                xp.constraint_msg_itext(DEFAULT_LANG, "-"),
                xp.required_msg_itext(DEFAULT_LANG, "-"),
                xpc.model_itext_choice_text_label_by_pos(
                    "default", "c1", ("la-d", "lb-d")
                ),
                xpc.model_no_itext_choice_media_by_pos(
                    DEFAULT_LANG,
                    "c1",
                    (
                        (
                            ("audio", "la-d.mp3"),
                            ("image", "la-d.jpg"),
                            ("video", "la-d.mkv"),
                        ),
                        (
                            ("audio", "lb-d.mp3"),
                            ("image", "lb-d.jpg"),
                            ("video", "lb-d.mkv"),
                        ),
                    ),
                ),
                xp.language_is_default(DEFAULT_LANG),
                xp.language_is_not_default("eng"),
            ],
        )
        # default_language set case
        self.assertPyxformXform(
            md=settings + md,
            # TODO: bug - missing default lang translatable/itext values.
            # warnings__contains=[warning],
            xml__xpath_match=[
                *common_xpaths,
                xp.language_is_default("eng"),
                xp.language_no_itext(DEFAULT_LANG),
            ],
        )

    @skip("Slow performance test. Un-skip to run as needed.")
    def test_missing_translations_check_performance(self):
        """
        Should find the translations check costs a fraction of a second for large forms.

        Results with Python 3.10.14 on VM with 2vCPU (i7-7700HQ) 1GB RAM, x questions
        with 2 choices each, average of 10 runs (seconds), with and without the check,
        per question:
        | num   | with   | without | peak RSS MB |
        |   500 | 0.7427 |  0.8133 |          77 |
        |  1000 | 1.7908 |  1.7777 |          94 |
        |  2000 | 5.6719 |  4.8387 |         141 |
        |  5000 | 20.452 |  19.502 |         239 |
        | 10000 | 70.871 |  62.106 |         416 |
        """
        survey_header = """
        | survey |                 |        |                    |                   |
        |        | type            | name   | label::english(en) | label::french(fr) |
        """
        question = """
        |        | select_one c{i} | q{i}   | hello          | bonjour       |
        """
        choices_header = """
        | choices |             |      |                        |
        |         | list name   | name | label | label::eng(en) |
        """
        choice_list = """
        |         | c{i}        | na   | la-d  | la-e       |
        |         | c{i}        | nb   | lb-d  | lb-e       |
        """
        process = Process(getpid())
        for count in (500, 1000, 2000):
            questions = "\n".join(question.format(i=i) for i in range(count))
            choice_lists = "\n".join(choice_list.format(i=i) for i in range(count))
            md = "".join((survey_header, questions, choices_header, choice_lists))

            def run(name, case):
                runs = 0
                results = []
                peak_memory_usage = process.memory_info().rss
                while runs < 10:
                    start = perf_counter()
                    convert(xlsform=case)
                    results.append(perf_counter() - start)
                    peak_memory_usage = max(process.memory_info().rss, peak_memory_usage)
                    runs += 1
                print(
                    name,
                    round(sum(results) / len(results), 4),
                    f"| Peak RSS: {peak_memory_usage}",
                )

            run(name=f"questions={count}, with check (seconds):", case=md)

            with patch(
                "pyxform.xls2json.SheetTranslations.missing_check",
                return_value=[],
            ):
                run(name=f"questions={count}, without check (seconds):", case=md)

    def test_translation_detection__survey_and_choices_columns_present(self):
        """Should identify that the survey is multi-language when first row(s) empty."""
        md = """
        | survey  |                |       |            |            |
        |         | type           | name  | label      | label::en  |
        |         | select_one c0  | f     | f          |            |
        |         | select_one c1  | q1    | Question 1 | Question A |
        | choices |           |      |        |            |           |
        |         | list name | name | label  | label::en  | label::fr |
        |         | c0        | n    | l      |            |           |
        |         | c1        | na   | la     |            |           |
        |         | c1        | nb   | lb     | lb-e       | lb-f      |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_select1_itemset("f"),
                xpq.body_label_inline("select1", "f", "f"),
                xpq.body_select1_itemset("q1"),
                xpq.body_label_itext("select1", "q1"),
                xpq.model_itext_label("q1", DEFAULT_LANG, "Question 1"),
                xpq.model_itext_label("q1", "en", "Question A"),
                xpq.model_itext_label("q1", "fr", "-"),
                xpc.model_instance_choices_label("c0", (("n", "l"),)),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb")
                ),
                xpc.model_itext_choice_text_label_by_pos("en", "c1", ("-", "lb-e")),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("-", "lb-f")),
            ],
        )

    def test_translation_detection__survey_columns_not_present(self):
        """Should identify that the survey is multi-language when only choices translated."""
        md = """
        | survey  |                |       |            |
        |         | type           | name  | label      |
        |         | select_one c0  | f     | f          |
        |         | select_one c1  | q1    | Question 1 |
        | choices |           |      |        |            |           |
        |         | list name | name | label  | label::en  | label::fr |
        |         | c0        | n    | l      |            |           |
        |         | c1        | na   | la     |            |           |
        |         | c1        | nb   | lb     | lb-e       | lb-f      |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_select1_itemset("f"),
                xpq.body_label_inline("select1", "f", "f"),
                xpq.body_select1_itemset("q1"),
                xpq.body_label_inline("select1", "q1", "Question 1"),
                xpc.model_instance_choices_label("c0", (("n", "l"),)),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb")
                ),
                xpc.model_itext_choice_text_label_by_pos("en", "c1", ("-", "lb-e")),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("-", "lb-f")),
            ],
        )

    def test_translation_detection__only_survey_columns_present(self):
        """Should identify that the survey is multi-language when first row(s) empty."""
        md = """
        | survey  |                |       |            |            |
        |         | type           | name  | label      | label::en  |
        |         | select_one c0  | f     | f          |            |
        |         | select_one c1  | q1    | Question 1 | Question A |
        | choices |           |      |        |
        |         | list name | name | label  |
        |         | c0        | n    | l      |
        |         | c1        | na   | la     |
        |         | c1        | nb   | lb     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_select1_itemset("f"),
                xpq.body_label_inline("select1", "f", "f"),
                xpq.body_select1_itemset("q1"),
                xpq.body_label_itext("select1", "q1"),
                xpq.model_itext_label("q1", DEFAULT_LANG, "Question 1"),
                xpq.model_itext_label("q1", "en", "Question A"),
                xpc.model_instance_choices_label("c0", (("n", "l"),)),
                xpc.model_instance_choices_label("c1", (("na", "la"), ("nb", "lb"))),
            ],
        )

    def test_translation_detection__survey_columns_present_with_media(self):
        """Should identify that the survey is multi-language when first row(s) empty."""
        md = """
        | survey  |                |       |            |            |           |
        |         | type           | name  | label      | label::en  | image::en |
        |         | select_one c0  | f     | f          |            |           |
        |         | select_one c1  | q1    | Question 1 | Question A | c1.png    |
        | choices |           |      |        |            |           |
        |         | list name | name | label  | label::en  | label::fr | audio::de |
        |         | c0        | n    | l      |            |           |           |
        |         | c1        | na   | la     |            |           |           |
        |         | c1        | nb   | lb     | lb-e       |           | c1_nb.mp3 |
        |         | c1        | nc   | lc     | lc-e       | lc-f      | c1_nc.mp3 |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_select1_itemset("f"),
                xpq.body_label_inline("select1", "f", "f"),
                xpq.body_select1_itemset("q1"),
                xpq.body_label_itext("select1", "q1"),
                xpq.model_itext_label("q1", DEFAULT_LANG, "Question 1"),
                xpq.model_itext_label(
                    "q1",
                    "en",
                    "Question A",
                ),
                xpq.model_itext_form("q1", "en", "image", "c1.png"),
                xpc.model_instance_choices_label("c0", (("n", "l"),)),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "lc")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "en", "c1", ("-", "lb-e", "lc-e")
                ),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("-", "-", "lc-f")),
                xpc.model_itext_choice_text_label_by_pos("de", "c1", ("-", "-", "-")),
                xpc.model_itext_choice_media_by_pos(
                    "de",
                    "c1",
                    (
                        ((None, None),),
                        (("audio", "c1_nb.mp3"),),
                        (("audio", "c1_nc.mp3"),),
                    ),
                ),
            ],
        )


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
        | survey |      |      |                |               |
        |        | type | name | label::eng(en) | hint::eng(en) |
        |        | note | n1   | hello          | salutation    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng(en)", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng(en)", "salutation"),
                # TODO: is this a bug? Only one language but not marked default.
                self.xp.language_is_not_default("eng(en)"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__one_translation__label_and_hint_with_image(self):
        """Should find language translations for label, hint, and image."""
        md = """
        | survey |      |      |                |               |                       |
        |        | type | name | label::eng(en) | hint::eng(en) | media::image::eng(en) |
        |        | note | n1   | hello          | salutation    | greeting.jpg          |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng(en)", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng(en)", "salutation"),
                self.xp.question_itext_form("eng(en)", "image", "greeting.jpg"),
                self.xp.language_is_not_default("eng(en)"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__one_translation__label_and_hint_with_guidance(self):
        """Should find default language translation for hint and guidance but not label."""
        md = """
        | survey |      |      |                |               |                        |
        |        | type | name | label::eng(en) | hint::eng(en) | guidance_hint::eng(en) |
        |        | note | n1   | hello          | salutation    | greeting               |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng(en)", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng(en)", "salutation"),
                self.xp.question_itext_form("eng(en)", "guidance", "greeting"),
                self.xp.language_is_not_default("eng(en)"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_no_default__one_translation__label_and_hint_all_cols(self):
        """Should find language translation for label, hint, and all translatables."""
        md = """
        | survey |      |      |                |               |                        |                       |                           |                       |                       |                             |                           |
        |        | type | name | label::eng(en) | hint::eng(en) | guidance_hint::eng(en) | media::image::eng(en) | media::big-image::eng(en) | media::video::eng(en) | media::audio::eng(en) | constraint_message::eng(en) | required_message::eng(en) |
        |        | note | n1   | hello          | salutation    | greeting               | greeting.jpg          | greeting.jpg              | greeting.mkv          | greeting.mp3          | check me                    | mandatory                 |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label("eng(en)", "hello"),
                self.xp.question_hint_references_itext(),
                self.xp.question_itext_hint("eng(en)", "salutation"),
                self.xp.question_itext_form("eng(en)", "guidance", "greeting"),
                self.xp.question_itext_form("eng(en)", "image", "greeting.jpg"),
                self.xp.question_itext_form("eng(en)", "big-image", "greeting.jpg"),
                self.xp.question_itext_form("eng(en)", "video", "greeting.mkv"),
                self.xp.question_itext_form("eng(en)", "audio", "greeting.mp3"),
                self.xp.constraint_msg_references_itext(),
                self.xp.constraint_msg_itext("eng(en)", "check me"),
                self.xp.required_msg_references_itext(),
                self.xp.required_msg_itext("eng(en)", "mandatory"),
                self.xp.language_is_not_default("eng(en)"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings_count=0,
        )

    def test_missing_translation__one_lang_simple__warn__no_default(self):
        """Should warn if there's a missing translation and no default_language."""
        md = """
        | survey |      |      |       |                |            |
        |        | type | name | label | label::eng(en) | hint       |
        |        | note | n1   | hello | hi there       | salutation |
        """
        warning = format_missing_translations_msg(_in={SURVEY: {"eng(en)": ["hint"]}})
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_references_itext(),
                self.xp.question_itext_label(DEFAULT_LANG, "hello"),
                self.xp.question_itext_label("eng(en)", "hi there"),
                self.xp.question_hint_in_body("salutation"),
                self.xp.language_is_default(DEFAULT_LANG),
                self.xp.language_is_not_default("eng(en)"),
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
                    "image",
                    "big-image",
                    "video",
                    "audio",
                    "constraint_message",
                    "required_message",
                )
            }
        }
        warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
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
                    "french": ("image",),
                }
            }
        )
        self.assertPyxformXform(
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
            _in={SURVEY: {"default": ("hint", "label"), "french": ("image",)}}
        )
        self.assertPyxformXform(
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
            warnings__not_contains=[OR_OTHER_WARNING],
        )


class TestTranslationsChoices(PyxformTestCase):
    """Translations behaviour of columns in the Choices sheet."""

    forms__ab = (
        (
            ("audio", "a.mp3"),
            ("image", "a.jpg"),
            ("big-image", "a.jpg"),
            ("video", "a.mkv"),
        ),
        (
            ("audio", "b.mp3"),
            ("image", "b.jpg"),
            ("big-image", "b.jpg"),
            ("video", "b.mkv"),
        ),
    )
    forms__l_audio = (
        (("audio", "la-d.mp3"),),
        (("audio", "lb-d.mp3"),),
    )

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
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb")
                ),
                xpc.model_itext_choice_media_by_pos(DEFAULT_LANG, "c1", self.forms__ab),
            ],
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
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("Eng (en)", "c1", ("la", "lb")),
                xpc.model_itext_choice_media_by_pos("Eng (en)", "c1", self.forms__ab),
            ],
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
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpc.body_itemset_references_itext("select1", "q1", "c1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb")
                ),
                xpc.model_itext_choice_media_by_pos(DEFAULT_LANG, "c1", self.forms__ab),
            ],
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
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpc.body_itemset_references_itext("select1", "q1", "c1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("Eng (en)", "c1", ("la", "lb")),
                xpc.model_itext_choice_media_by_pos("Eng (en)", "c1", self.forms__ab),
            ],
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
        warning = format_missing_translations_msg(_in={CHOICES: {"eng": ("audio",)}})
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la-d", "lb-d")
                ),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_media_by_pos(
                    DEFAULT_LANG, "c1", self.forms__l_audio
                ),
                xpc.model_no_itext_choice_media_by_pos("eng", "c1", self.forms__l_audio),
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
        |         | list name | name | label::eng | media::audio |
        |         | c1        | na   | la-e       | la-d.mp3     |
        |         | c1        | nb   | lb-e       | lb-d.mp3     |
        """
        cols = {CHOICES: {"default": ("label",), "eng": ("audio",)}}
        warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_media_by_pos("eng", "c1", self.forms__l_audio),
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
        cols = {CHOICES: {DEFAULT_LANG: ("image", "big-image", "video", "audio")}}
        warning = format_missing_translations_msg(_in=cols)
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la-d", "lb-d")
                ),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_media_by_pos(
                    "eng",
                    "c1",
                    (
                        (
                            ("audio", "la-d.mp3"),
                            ("image", "la-d.jpg"),
                            ("big-image", "la-d.jpg"),
                            ("video", "la-d.mkv"),
                        ),
                        (
                            ("audio", "lb-d.mp3"),
                            ("image", "lb-d.jpg"),
                            ("big-image", "lb-d.jpg"),
                            ("video", "lb-d.mkv"),
                        ),
                    ),
                ),
                xpc.model_no_itext_choice_media_by_pos(
                    DEFAULT_LANG,
                    "c1",
                    (
                        (
                            ("audio", "la-d.mp3"),
                            ("image", "la-d.jpg"),
                            ("big-image", "la-d.jpg"),
                            ("video", "la-d.mkv"),
                        ),
                        (
                            ("audio", "lb-d.mp3"),
                            ("image", "lb-d.jpg"),
                            ("big-image", "la-d.jpg"),
                            ("video", "lb-d.mkv"),
                        ),
                    ),
                ),
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
            md=md,
            # TODO: bug - missing default lang translatable/itext values.
            # warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_media_by_pos(
                    "eng",
                    "c1",
                    (
                        (
                            ("audio", "la-d.mp3"),
                            ("image", "la-d.jpg"),
                            ("big-image", "la-d.jpg"),
                            ("video", "la-d.mkv"),
                        ),
                        (
                            ("audio", "lb-d.mp3"),
                            ("image", "lb-d.jpg"),
                            ("big-image", "lb-d.jpg"),
                            ("video", "lb-d.mkv"),
                        ),
                    ),
                ),
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
            _in={CHOICES: {"eng": ("audio",), "default": ("label",)}}
        )
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                # Output of a dash for empty translation is not a bug, it's a reminder /
                # placeholder since XForms spec requires a value for every translation.
                xpc.model_itext_choice_text_label_by_pos(DEFAULT_LANG, "c1", ("-", "-")),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_media_by_pos(
                    DEFAULT_LANG, "c1", self.forms__l_audio
                ),
                xpc.model_no_itext_choice_media_by_pos("eng", "c1", self.forms__l_audio),
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
            _in={CHOICES: {"eng": ("audio",), "default": ("label",)}}
        )
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                # TODO: is this a bug? Default audio gets merged into eng hint.
                xpc.model_itext_choice_media_by_pos("eng", "c1", self.forms__l_audio),
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
        warning = format_missing_translations_msg(_in={CHOICES: {"french": ("audio",)}})
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_text_label_by_pos(
                    "french", "c1", ("la-f", "lb-f")
                ),
                xpc.model_itext_choice_media_by_pos("eng", "c1", self.forms__l_audio),
                xpc.model_no_itext_choice_media_by_pos(
                    "french", "c1", self.forms__l_audio
                ),
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
        warning = format_missing_translations_msg(_in={CHOICES: {"french": ("audio",)}})
        self.assertPyxformXform(
            md=md,
            warnings__contains=[warning],
            xml__xpath_match=[
                self.xp.question_label_in_body("Question 1"),
                xpq.body_select1_itemset("q1"),
                xpc.model_instance_choices_itext("c1", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("eng", "c1", ("la-e", "lb-e")),
                xpc.model_itext_choice_text_label_by_pos(
                    "french", "c1", ("la-f", "lb-f")
                ),
                xpc.model_itext_choice_media_by_pos("eng", "c1", self.forms__l_audio),
                xpc.model_no_itext_choice_media_by_pos(
                    "french", "c1", self.forms__l_audio
                ),
                self.xp.language_is_default("eng"),
                self.xp.language_is_not_default("french"),
                self.xp.language_no_itext(DEFAULT_LANG),
            ],
            warnings__not_contains=[OR_OTHER_WARNING],
        )

    def test_choice_name_containing_dash_output_itext(self):
        """Should output itext when list_name contains a dash (itextId separator)."""
        md = """
        | survey  |                      |       |            |
        |         | type                 | name  | label:en   | label:fr |
        |         | select_one with_us   | q0    | Q1 EN      | Q1 FR    |
        |         | select_one with-dash | q1    | Q2 EN      | Q2 FR    |
        | choices |           |      |          |
        |         | list name | name | label:en | label:fr |
        |         | with_us   | na   | l1a-en   | l1a-fr   |
        |         | with_us   | nb   | l1b-en   | l1b-fr   |
        |         | with-dash | na   | l2a-en   | l2a-fr   |
        |         | with-dash | nb   | l2b-en   | l2b-fr   |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "en", "with_us", ("l1a-en", "l1b-en")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "en", "with-dash", ("l2a-en", "l2b-en")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "with_us", ("l1a-fr", "l1b-fr")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "with-dash", ("l2a-fr", "l2b-fr")
                ),
            ],
        )


class TestTranslationsOrOther(PyxformTestCase):
    """Translations behaviour with or_other."""

    def test_specify_other__with_translations(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label      | label::eng |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        | choices |           |      |       |            |           |
        |         | list name | name | label | label::eng | label::fr | media::image::eng |
        |         | c1        | na   | la    | la-e       | la-f      | a.jpg             |
        |         | c1        | nb   | lb    | lb-e       |           | b.jpg             |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "eng", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("la-f", "-", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                xpq.body_select1_itemset("q1"),
                """
                /h:html/h:body/x:input[@ref='/test_name/q1_other']/
                  x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_translations_only(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label::en  | label::fr  |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        | choices |           |      |            |           |
        |         | list name | name | label::en  | label::fr |
        |         | c1        | na   | la-e       | la-f      |
        |         | c1        | nb   | lb-e       |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "en", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("la-f", "-", "Other")
                ),
                """
                /h:html/h:head/x:model/x:itext[
                  not(descendant::x:translation[@lang='default'])
                ]
                """,
                xpq.body_select1_itemset("q1"),
                """
                /h:html/h:body/x:input[@ref='/test_name/q1_other']/
                  x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_media_only(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |
        |         | type                   | name  | label      |
        |         | select_one c1 or_other | q1    | Question 1 |
        | choices |           |      |       |              |
        |         | list name | name | label | media::image |
        |         | c1        | na   | la    | a.jpg        |
        |         | c1        | nb   | lb    | b.jpg        |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                xpq.body_select1_itemset("q1"),
                """
                /h:html/h:body/x:input[@ref='/test_name/q1_other']/
                  x:label[text() = 'Specify other.']
                """,
            ],
        )

    def test_specify_other__with_translations_only__existing_other_choice(self):
        """Should not add an extra "other" choice if already defined for some reason."""
        # Blank translations for existing "other" choices are not replaced with "Other".
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label::en  | label::fr  |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        | choices |           |       |            |           |
        |         | list name | name  | label::en  | label::fr |
        |         | c1        | na    | la-e       | la-f      |
        |         | c1        | nb    | lb-e       |           |
        |         | c1        | other | Other      |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "en", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("la-f", "-", "-")),
                """
                /h:html/h:head/x:model/x:itext[
                  not(descendant::x:translation[@lang='default'])
                ]
                """,
                xpq.body_select1_itemset("q1"),
                """
                /h:html/h:body/x:input[@ref='/test_name/q1_other']/
                  x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_translations_only__missing_first_translation(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        # xls2json validation would raise an error if a choice has no label at all.
        md = """
        | survey  |                        |       |            |            |           |
        |         | type                   | name  | label      | label::eng | label::fr |
        |         | select_one c1 or_other | q1    | Question 1 | Question A | QA fr     |
        | choices |           |      |       |            |           |
        |         | list name | name | label | label::eng | label::fr |
        |         | c1        | na   | la    | la-e       | la-f      |
        |         | c1        | nb   | lb    | lb-e       |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "eng", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("la-f", "-", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                xpq.body_select1_itemset("q1"),
                """
                /h:html/h:body/x:input[@ref='/test_name/q1_other']/
                  x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_translations__with_group(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label      | label::eng |
        |         | begin group            | g1    | Group 1    | Group 1    |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        |         | end group              | g1    |            |            |
        | choices |           |      |       |            |           |
        |         | list name | name | label | label::eng | label::fr |
        |         | c1        | na   | la    |            |           |
        |         | c1        | nb   | lb    | lb-e       | lb-f      |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "eng", "c1", ("-", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("-", "lb-f", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                xpq.body_group_select1_itemset("g1", "q1"),
                """
                /h:html/h:body/x:group[@ref='/test_name/g1']
                  /x:input[@ref='/test_name/g1/q1_other']
                  /x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_translations__with_repeat(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label      | label::eng |
        |         | begin repeat           | r1    | Repeat 1   | Repeat 1   |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        |         | end repeat             | r1    |            |            |
        | choices |           |      |       |            |           |
        |         | list name | name | label | label::eng | label::fr |
        |         | c1        | na   | la    | la-e       | la-f      |
        |         | c1        | nb   | lb    | lb-e       |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "eng", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("la-f", "-", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                xpq.body_repeat_select1_itemset("r1", "q1"),
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']
                  /x:repeat[@nodeset='/test_name/r1']
                  /x:input[@ref='/test_name/r1/q1_other']
                  /x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_translations__with_nested_group(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label      | label::eng |
        |         | begin group            | g1    | Group 1    | Group 1    |
        |         | begin group            | g2    | Group 2    | Group 2    |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        |         | end group              | g2    |            |            |
        |         | end group              | g1    |            |            |
        | choices |           |      |       |            |           |
        |         | list name | name | label | label::eng | label::fr |
        |         | c1        | na   | la    | la-e       | la-f      |
        |         | c1        | nb   | lb    | lb-e       |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "eng", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("la-f", "-", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                """
                /h:html/h:body/x:group[@ref='/test_name/g1']
                  /x:group[@ref='/test_name/g1/g2']/x:select1[
                    @ref = '/test_name/g1/g2/q1'
                    and ./x:itemset
                    and not(./x:item)
                  ]
                """,
                """
                /h:html/h:body/x:group[@ref='/test_name/g1']
                  /x:group[@ref='/test_name/g1/g2']
                  /x:input[@ref='/test_name/g1/g2/q1_other']
                  /x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__with_translations__with_nested_repeat(self):
        """Should add an "other" choice to the itemset instance and an itext label."""
        md = """
        | survey  |                        |       |            |            |
        |         | type                   | name  | label      | label::eng |
        |         | begin group            | g1    | Group 1    | Group 1    |
        |         | begin repeat           | r1    | Repeat 1   | Repeat 1   |
        |         | select_one c1 or_other | q1    | Question 1 | Question A |
        |         | end repeat             | r1    |            |            |
        |         | end group              | g1    |            |            |
        | choices |           |      |       |            |           |
        |         | list name | name | label | label::eng | label::fr |
        |         | c1        | na   | la    | la-e       | la-f      |
        |         | c1        | nb   | lb    | lb-e       |           |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpc.model_itext_choice_text_label_by_pos(
                    "eng", "c1", ("la-e", "lb-e", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("la-f", "-", "Other")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    DEFAULT_LANG, "c1", ("la", "lb", "Other")
                ),
                """
                /h:html/h:body/x:group[@ref='/test_name/g1']
                  /x:group[@ref='/test_name/g1/r1']
                  /x:repeat[@nodeset='/test_name/g1/r1']
                  /x:select1[
                    @ref = '/test_name/g1/r1/q1'
                    and ./x:itemset
                    and not(./x:item)
                  ]
                """,
                """
                /h:html/h:body/x:group[@ref='/test_name/g1']
                  /x:group[@ref='/test_name/g1/r1']
                  /x:repeat[@nodeset='/test_name/g1/r1']
                  /x:input[@ref='/test_name/g1/r1/q1_other']
                  /x:label[text() = 'Specify other.']
                """,
            ],
            warnings__contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__no_translations(self):
        """Should add an "other" choice to the itemset instance, but not use itext."""
        md = """
        | survey  |                        |       |            |
        |         | type                   | name  | label      |
        |         | select_one c1 or_other | q1    | Question 1 |
        | choices |           |      |       |
        |         | list name | name | label |
        |         | c1        | na   | la    |
        |         | c1        | nb   | lb    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model[not(descendant::x:itext)]
                """,
                xpc.model_instance_choices_label(
                    "c1", (("na", "la"), ("nb", "lb"), ("other", "Other"))
                ),
                xpq.body_select1_itemset("q1"),
                """
                /h:html/h:body/x:input[@ref='/test_name/q1_other']/
                  x:label[text() = 'Specify other.']
                """,
            ],
            warnings__not_contains=[OR_OTHER_WARNING],
        )

    def test_specify_other__choice_filter(self):
        """Should raise an error since these features are unsupported together."""
        md = """
        | survey  |                        |       |            |
        |         | type                   | name  | label      | choice_filter |
        |         | text                   | q0    | Question 0 |               |
        |         | select_one c1 or_other | q1    | Question 1 | ${q0} = cf    |
        | choices |           |      |       |
        |         | list name | name | label | cf |
        |         | c1        | na   | la    | 1  |
        |         | c1        | nb   | lb    | 2  |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=["[row : 3] Choice filter not supported with or_other."],
        )
