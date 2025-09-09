"""
Test language warnings.
"""

from pyxform.validators.pyxform import unique_names

from tests.pyxform_test_case import PyxformTestCase


class TestMetadata(PyxformTestCase):
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

    def test_names__survey_named_meta__ok(self):
        """Should find that using the name 'meta' for the survey is OK."""
        md = """
        | survey |
        | | type | name | label |
        | | text | q1   | Q1    |
        """
        self.assertPyxformXform(md=md, name="meta", warnings_count=0)

    def test_names__question_named_meta__in_survey__case_insensitive_ok(self):
        """Should find that using the name 'meta' in a different case is OK."""
        md = """
        | survey |
        | | type | name | label |
        | | text | META | Q1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_names__group_named_meta__in_survey__case_insensitive_ok(self):
        """Should find that using the name 'meta' in a different case is OK."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | META | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_names__repeat_named_meta__in_survey__case_insensitive_ok(self):
        """Should find that using the name 'meta' in a different case is OK."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | META | G1    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_names__question_named_meta__in_survey__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type | name | label |
        | | text | meta | Q1    |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=2)]
        )

    def test_names__group_named_meta__in_survey__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | meta | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=2)]
        )

    def test_names__repeat_named_meta__in_survey__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | meta | G1    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=2)]
        )

    def test_names__question_named_meta__in_group__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | text        | meta | Q1    |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=3)]
        )

    def test_names__group_named_meta__in_group__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type        | name | label |
        | | begin group | g1   | G1    |
        | | begin group | meta | G1    |
        | | text        | q1   | Q1    |
        | | end group   |      |       |
        | | end group   |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=3)]
        )

    def test_names__repeat_named_meta__in_group__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin group  | g1   | G1    |
        | | begin repeat | meta | G1    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=3)]
        )

    def test_names__question_named_meta__in_repeat__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | text         | meta | Q1    |
        | | end group    |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=3)]
        )

    def test_names__group_named_meta__in_repeat__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | begin group  | meta | G1    |
        | | text         | q1   | Q1    |
        | | end group    |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=3)]
        )

    def test_names__repeat_named_meta__in_repeat__error(self):
        """Should find that using the name 'meta' raises an error."""
        md = """
        | survey |
        | | type         | name | label |
        | | begin repeat | r1   | R1    |
        | | begin repeat | meta | G1    |
        | | text         | q1   | Q1    |
        | | end repeat   |      |       |
        | | end repeat   |      |       |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[unique_names.NAMES005.format(row=3)]
        )
