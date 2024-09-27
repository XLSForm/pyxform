from tests.pyxform_test_case import PyxformTestCase


class BackgroundGeopointTest(PyxformTestCase):
    """Test background-geopoint question type."""

    def test_background_geopoint(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |             |                |
            |        | type               | name        | label          | trigger   |
            |        | integer            | temp        | Enter the current temperature |        |
            |        | background-geopoint| temp_geo    |                | ${temp}   |
            |        | note               | show_temp_geo | location: ${temp_geo} |        |
            """,
            xml__contains=[
                '<bind nodeset="/data/temp_geo" type="geopoint"/>',
                '<odk:setgeopoint event="xforms-value-changed" ref="/data/temp_geo"/>',
            ],
        )

    def test_background_geopoint_missing_trigger(self):
        """Test that background-geopoint question raises error when trigger is empty."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |             |                |
            |        | type               | name        | label          | trigger   |
            |        | integer            | temp        | Enter the current temperature |        |
            |        | background-geopoint| temp_geo    |                |  |
            |        | note               | show_temp_geo | location: ${temp_geo} |        |
            """,
            errored=True,
            error__contains=[
                "background-geopoint question 'temp_geo' must have a non-null trigger"
            ],
        )

    def test_invalid_trigger_background_geopoint(self):
        self.assertPyxformXform(
            name="data",
            md="""
                | survey |                    |             |                |
                |        | type               | name        | label          | trigger   |
                |        | integer            | temp        | Enter the current temperature |        |
                |        | background-geopoint| temp_geo    |                | ${invalid_trigger} |
                |        | note               | show_temp_geo | location: ${temp_geo} |        |
                """,
            errored=True,
            error__contains=[
                "Trigger 'invalid_trigger' for background-geopoint question 'temp_geo' does not correspond to an existing question"
            ],
        )

    def test_background_geopoint_requires_null_calculation(self):
        """Test that background-geopoint raises an error if there is a calculation."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |             |                |  |
            |        | type               | name        | label          | trigger     | calculation |
            |        | integer            | temp        | Enter the current temperature |        |             |
            |        | background-geopoint| temp_geo    |                | ${temp}     | 5 * temp |
            |        | note               | show_temp_geo | location: ${temp_geo} |        |             |
            """,
            errored=True,
            error__contains=[
                "'temp_geo' is triggered by a geopoint action, so the calculation must be null."
            ],
        )
