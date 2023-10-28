from pyxform.validators.pyxform.android_package_name import validate_android_package_name
from tests.pyxform_test_case import PyxformTestCase


class TestAndroidPackageNameValidator(PyxformTestCase):
    def test_empty_package_name(self):
        result = validate_android_package_name("")
        self.assertEqual(
            result, "Parameter 'app' has an invalid Android package name - package name is missing."
        )

    def test_blank_package_name(self):
        result = validate_android_package_name(" ")
        self.assertEqual(
            result, "Parameter 'app' has an invalid Android package name - package name is missing."
        )

    def test_missing_separator(self):
        result = validate_android_package_name("comexampleapp")
        self.assertEqual(
            result,
            "Parameter 'app' has an invalid Android package name - the package name must have at least one '.' separator.",
        )

    def test_invalid_start_with_underscore(self):
        result = validate_android_package_name("_com.example.app")
        expected_error = "Parameter 'app' has an invalid Android package name - the character '_' cannot be the first character in a package name segment."
        self.assertEqual(result, expected_error)

    def test_invalid_start_with_digit(self):
        result = validate_android_package_name("1com.example.app")
        expected_error = "Parameter 'app' has an invalid Android package name - a digit cannot be the first character in a package name segment."
        self.assertEqual(result, expected_error)

    def test_invalid_character(self):
        result = validate_android_package_name("com.example.app$")
        expected_error = "Parameter 'app' has an invalid Android package name - the package name can only include letters (a-z, A-Z), numbers (0-9), dots (.), and underscores (_)."
        self.assertEqual(result, expected_error)

    def test_package_name_segment_with_zero_length(self):
        result = validate_android_package_name("com..app")
        expected_error = (
            "Parameter 'app' has an invalid Android package name - package segments must be of non-zero length."
        )
        self.assertEqual(result, expected_error)

    def test_separator_as_last_char_in_package_name(self):
        result = validate_android_package_name("com.example.app.")
        expected_error = "Parameter 'app' has an invalid Android package name - the package name cannot end in a '.' separator."
        self.assertEqual(result, expected_error)

    def test_valid_package_name(self):
        package_names = (
            "com.zenstudios.zenpinball",
            "com.outfit7.talkingtom",
            "com.zeptolab.ctr2.f2p.google",
            "com.ea.game.pvzfree_row",
            "com.rovio.angrybirdsspace.premium",
        )

        for case in package_names:
            result = validate_android_package_name(case)
            self.assertIsNone(result)
