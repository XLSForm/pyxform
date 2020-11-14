# -*- coding: utf-8 -*-
"""
Test validators.
"""

import sys
from unittest import TestCase

from pyxform.validators.odk_validate import check_java_version

if sys.version_info >= (3, 3):
    from unittest.mock import patch  # pylint: disable=E0611,E0401
else:
    try:
        from mock import patch
    except ImportError:
        raise ImportError("Pyxform test suite requires the 'mock' library.")

JAVA_7 = """java version "1.7.0_201"
OpenJDK Runtime Environment (IcedTea 2.6.17) (7u211-2.6.17-0ubuntu0.1)
OpenJDK 64-Bit Server VM (build 24.201-b00, mixed mode)
"""
JAVA_8 = """java version "1.8.0_211"
Java(TM) SE Runtime Environment (build 1.8.0_211-b12)
Java HotSpot(TM) 64-Bit Server VM (build 25.211-b12, mixed mode)
"""
OPENJDK_11 = """openjdk version "11.0.3" 2019-04-16
OpenJDK Runtime Environment (build 11.0.3+4)
OpenJDK 64-Bit Server VM (build 11.0.3+4, mixed mode)
"""
OPENJDK_13 = """openjdk version "13" 2019-09-17
OpenJDK Runtime Environment (build 13+33)
OpenJDK 64-Bit Server VM (build 13+33, mixed mode, sharing)
"""
OPENJDK_9_INT = """openjdk version "9-internal"
OpenJDK Runtime Environment (build 9-internal+0-2016-04-14-195246.buildd.src)
OpenJDK 64-Bit Server VM (build 9-internal+0-2016-04-14-195246.buildd.src, mixed mode)
"""
OPENJDK_11_PATCH = """openjdk version "11.0.9.1" 2020-11-04
OpenJDK Runtime Environment (build 11.0.9.1+1-Ubuntu-0ubuntu1.18.04)
OpenJDK 64-Bit Server VM (build 11.0.9.1+1-Ubuntu-0ubuntu1.18.04, mixed mode, sharing)
"""


class TestValidators(TestCase):
    """Test validators."""

    def test_check_java_version(self):
        """Test check_java_version()"""
        mock_func = "pyxform.validators.odk_validate.run_popen_with_timeout"
        with patch(mock_func) as mock_popen:
            mock_popen.side_effect = OSError("[Errno 2] No such file or directory")
            with self.assertRaises(EnvironmentError) as error:
                check_java_version()
            self.assertEqual(
                str(error.exception), "pyxform odk validate dependency: java not found"
            )

        with patch(mock_func) as mock_popen:
            mock_popen.return_value = (0, False, "", JAVA_7)
            with self.assertRaises(EnvironmentError) as error:
                check_java_version()
            self.assertEqual(
                str(error.exception),
                "pyxform odk validate dependency: " "java 8 or newer version not found",
            )

        with patch(mock_func) as mock_popen:
            mock_popen.return_value = (0, False, "", JAVA_8)
            check_java_version()

        with patch(mock_func) as mock_popen:
            mock_popen.return_value = (0, False, "", OPENJDK_11)
            check_java_version()

        with patch(mock_func) as mock_popen:
            mock_popen.return_value = (0, False, "", OPENJDK_13)
            check_java_version()

        with patch(mock_func) as mock_popen:
            mock_popen.return_value = (0, False, "", OPENJDK_9_INT)
            check_java_version()

        with patch(mock_func) as mock_popen:
            mock_popen.return_value = (0, False, "", OPENJDK_11_PATCH)
            check_java_version()
