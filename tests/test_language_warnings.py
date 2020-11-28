# -*- coding: utf-8 -*-
"""
Test language warnings.
"""
import os
import tempfile

from tests.pyxform_test_case import PyxformTestCase


class LanguageWarningTest(PyxformTestCase):
    """
    Test language warnings.
    """

    def test_label_with_valid_subtag_should_not_warn(self):
        survey = self.md_to_pyxform_survey(
            """
            | survey |      |         |                     |
            |        | type | name    | label::English (en) |
            |        | note | my_note | My note             |
            """
        )

        warnings = []
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        survey.print_xform_to_file(tmp.name, warnings=warnings)

        self.assertTrue(len(warnings) == 0)
        os.unlink(tmp.name)

    def test_label_with_no_subtag_should_warn(self):
        survey = self.md_to_pyxform_survey(
            """
            | survey |      |         |                     |
            |        | type | name    | label::English      |
            |        | note | my_note | My note             |
            """
        )

        warnings = []
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        survey.print_xform_to_file(tmp.name, warnings=warnings)

        self.assertTrue(len(warnings) == 1)
        self.assertTrue(
            "do not contain valid machine-readable codes: English. Learn more"
            in warnings[0]
        )
        os.unlink(tmp.name)

    def test_label_with_unknown_subtag_should_warn(self):
        survey = self.md_to_pyxform_survey(
            """
            | survey |      |         |                       |
            |        | type | name    | label::English (schm) |
            |        | note | my_note | My note               |
            """
        )

        warnings = []
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        survey.print_xform_to_file(tmp.name, warnings=warnings)

        self.assertTrue(len(warnings) == 1)
        self.assertTrue(
            "do not contain valid machine-readable codes: English (schm). Learn more"
            in warnings[0]
        )
        os.unlink(tmp.name)

    def test_default_language_only_should_not_warn(self):
        survey = self.md_to_pyxform_survey(
            """
            | survey |                 |         |        |               |
            |        | type            | name    | label  | choice_filter |
            |        | select_one opts | opt     | My opt | fake = 1      |
            | choices|                 |         |        |               |
            |        | list_name       | name    | label  | fake          |
            |        | opts            | opt1    | Opt1   | 1             |
            |        | opts            | opt2    | Opt2   | 1             |
            """
        )

        warnings = []
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        survey.print_xform_to_file(tmp.name, warnings=warnings)
        self.assertTrue(len(warnings) == 0)
        os.unlink(tmp.name)

    def test_incomplete_translations(self):
        survey = self.md_to_pyxform_survey(
            """
            | survey |                 |                 |                      |                     |                    |              |                      |                                  |
            |        | type            | name            | label                | label::English (en) | hint::Spanish (es) | media::image | choice_filter        | constraint                       | constraint_message::Spanish (es) |
            |        | select_one opts | option_question | My opt               | My opt in English   | elige su opcion    | opt.jpg      | option_question != ''|                                  |                                  |
            |        | note            | splain          | splain               |                     | explique su elecn  |              |                      | string-length(.) > 1             | demasiado corto                  |                                  |
            | choices|                 |                 |                      |                     |                    |              |                      |                                  |                                  |
            |        | list_name       | name            | label::English (en)  | label::Spanish (es) |                    |              |                      |                                  |                                  |
            |        | opts            | opt1            | Opt1                 | Opc1                |                    |              |                      |                                  |                                  |
            |        | opts            | opt2            | Opt2                 | Opc2                |                    |              |                      |                                  
            """
        )
                      
        warnings = []
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close() 
        survey.print_xform_to_file(tmp.name, warnings=warnings)
        self.assertTrue(len(warnings) == 8)
        self.assertIn('Translation for English (en) missing for: jr:constraintMsg', warnings)
        self.assertIn('Translation for English (en) missing for: image', warnings)
        self.assertIn('Translation for English (en) missing for: hint', warnings)
        self.assertIn('Translation for Spanish (es) missing for: image', warnings)
        self.assertIn('Translation for Spanish (es) missing for: label', warnings)
        self.assertIn('There is no default language set, and no language specified for: choice label for opts, Set a default language in the settings tab, or specifiy the language of this column.', warnings)
        self.assertIn('There is no default language set, and no language specified for: hint, Set a default language in the settings tab, or specifiy the language of this column.', warnings)
        self.assertIn('There is no default language set, and no language specified for: jr:constraintMsg, Set a default language in the settings tab, or specifiy the language of this column.', warnings)
        os.unlink(tmp.name)