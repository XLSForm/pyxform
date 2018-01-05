from unittest2 import TestCase

from pyxform.tests.utils import prep_class_config
from pyxform.validators.error_cleaner import ErrorCleaner


class TestValidatorUtil(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls)

    def test_cleanup_error_message(self):
        test_str = self.config.get(
            self.cls_name, "test_cleanup_error_message_test")
        expected_str = self.config.get(
            self.cls_name, "test_cleanup_error_message_expected")
        self.assertEqual(
            ErrorCleaner.odk_validate(test_str), expected_str.strip())

    def test_do_not_over_trim_javarosa_errors(self):
        test_str = self.config.get(
            self.cls_name, "test_do_not_over_trim_javarosa_errors_test")
        # Unescape tabs in string
        test_str = test_str.replace("\n\\t", "\n\t")
        expected_str = self.config.get(
            self.cls_name, "test_do_not_over_trim_javarosa_errors_expected")
        self.assertEqual(
            ErrorCleaner.odk_validate(test_str), expected_str.strip())

    def test_single_line_error_still_output(self):
        """Should emit errors that are a single line of text."""
        test_str = self.config.get(
            self.cls_name, "test_single_line_error_still_output_test")
        expected_str = self.config.get(
            self.cls_name, "test_single_line_error_still_output_expected")
        self.assertEqual(
            ErrorCleaner.odk_validate(test_str), expected_str.strip())

    def test_jarfile_error_returned_asis(self):
        """Should return a jarfile error as-is, to avoid tokenising the path."""
        test_str = self.config.get(
            self.cls_name, "test_jarfile_error_returned_asis_test")
        expected_str = self.config.get(
            self.cls_name, "test_jarfile_error_returned_asis_expected")
        self.assertEqual(
            ErrorCleaner.odk_validate(test_str), expected_str.strip())
