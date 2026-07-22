"""
Test setgeopoint widget.
"""

from tests.pyxform_test_case import PyxformTestCase


class SetGeopointTest(PyxformTestCase):
    """Test setgeopoint widget class."""

    def test_setgeopoint(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                |             |          |
            |        | type           | name        | label    |
            |        | start-geopoint | my-location | my label |
            """,
            xml__contains=[
                '<bind nodeset="/data/my-location" type="geopoint"/>',
                '<odk:setgeopoint event="odk-instance-first-load" ref="/data/my-location"/>',
                "",
            ],
        )

    def test_label_ignored_if_specified(self):
        """Should find that the control output is hidden even if a label is specified."""
        md = """
        | survey |
        | | type           | name | label |
        | | start-geopoint | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_count=[
                # No control output with this ref.
                ("/h:html/h:body//*[@ref='/test_name/q1']", 0),
                # No control with the specified label.
                ("/h:html/h:body//*[text()='Q1']", 0),
            ],
        )
