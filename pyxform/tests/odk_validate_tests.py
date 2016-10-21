from pyxform.odk_validate import _cleanup_errors

from unittest2 import TestCase
from pyxform.tests.utils import prep_class_config


class ODKValidateTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls)

    def test_cleanup_error_message(self):
        test_str = self.config.get(
            self.cls_name, "test_cleanup_error_message_test")
        expected_str = self.config.get(
            self.cls_name, "test_cleanup_error_message_expected")
        self.assertEqual(_cleanup_errors(test_str), expected_str.strip())

    def test_do_not_over_trim_javarosa_errors(self):
        test_str = self.config.get(
            self.cls_name, "test_do_not_over_trim_javarosa_errors_test")
        # Unescape tabs in string
        test_str = test_str.replace("\n\\t", "\n\t")
        expected_str = self.config.get(
            self.cls_name, "test_do_not_over_trim_javarosa_errors_expected")
        self.assertEqual(_cleanup_errors(test_str), expected_str.strip())
