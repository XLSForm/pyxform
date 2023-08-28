# -*- coding: utf-8 -*-
"""
Test validators.
"""
from unittest import TestCase
from unittest.mock import patch

from pyxform.validators.odk_validate import check_java_available

mock_func = "shutil.which"
msg = "Form validation failed because Java (8+ required) could not be found."


class TestValidatorsUtil(TestCase):
    """Test validators.util"""

    def test_check_java_available__found(self):
        """Should not raise an error when Java is found."""
        with patch(mock_func) as mocked:
            mocked.return_value = "/usr/bin/java"
            check_java_available()

    def test_check_java_available__not_found(self):
        """Should raise an error when java is not found."""
        with patch(mock_func) as mocked:
            mocked.return_value = None
            with self.assertRaises(EnvironmentError) as error:
                check_java_available()
            self.assertIn(msg, str(error.exception))
