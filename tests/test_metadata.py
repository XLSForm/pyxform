"""
Test language warnings.
"""

from tests.pyxform_test_case import PyxformTestCase


class MetadataTest(PyxformTestCase):
    """
    Test metadata and related warnings.
    """

    def test_metadata_bindings(self):
        self.assertPyxformXform(
            name="metadata",
            md="""
            | survey |             |             |       |
            |        | type        | name        | label |
            |        | deviceid    | deviceid    |       |
            |        | phonenumber | phonenumber |       |
            |        | start       | start       |       |
            |        | end         | end         |       |
            |        | today       | today       |       |
            |        | username    | username    |       |
            |        | email       | email       |       |
            """,
            xml__contains=[
                'jr:preload="property" jr:preloadParams="deviceid"',
                'jr:preload="property" jr:preloadParams="phonenumber"',
                'jr:preload="timestamp" jr:preloadParams="start"',
                'jr:preload="timestamp" jr:preloadParams="end"',
                'jr:preload="date" jr:preloadParams="today"',
                'jr:preload="property" jr:preloadParams="username"',
                'jr:preload="property" jr:preloadParams="email"',
            ],
        )

    def test_simserial_deprecation_warning(self):
        self.assertPyxformXform(
            md="""
            | survey |              |                       |                                     |
            |        | type         | name                  | label                               |
            |        | simserial    | simserial             |                                     |
            |        | note         | simserial_test_output | simserial_test_output: ${simserial} |
            """,
            warnings_count=1,
            warnings__contains=[
                "[row : 2] simserial is no longer supported on most devices. "
                "Only old versions of Collect on Android versions older than 11 still support it."
            ],
        )

    def test_subscriber_id_deprecation_warning(self):
        self.assertPyxformXform(
            md="""
            | survey |              |                          |                                            |
            |        | type         | name                     | label                                      |
            |        | subscriberid | subscriberid             | sub id - extra warning generated w/o this  |
            |        | note         | subscriberid_test_output | subscriberid_test_output: ${subscriberid}  |
            """,
            warnings_count=1,
            warnings__contains=[
                "[row : 2] subscriberid is no longer supported on most devices. "
                "Only old versions of Collect on Android versions older than 11 still support it."
            ],
        )
