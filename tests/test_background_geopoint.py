from tests.pyxform_test_case import PyxformTestCase


class BackgroundGeopointTest(PyxformTestCase):
    """Test background-geopoint question type."""

    def test_background_geopoint(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |               |                               |
            |        | type               | name          | label                         | trigger   |
            |        | integer            | temp          | Enter the current temperature |           |
            |        | background-geopoint| temp_geo      |                               | ${temp}   |
            |        | note               | show_temp_geo | location: ${temp_geo}         |           |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset="/data/temp_geo" and @type="geopoint"]',
                '/h:html/h:body//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/temp_geo"]',
            ],
        )

    def test_background_geopoint_missing_trigger(self):
        """Test that background-geopoint question raises error when trigger is empty."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |               |                               |
            |        | type               | name          | label                         | trigger   |
            |        | integer            | temp          | Enter the current temperature |           |
            |        | background-geopoint| temp_geo      |                               |           |
            |        | note               | show_temp_geo | location: ${temp_geo}         |           |
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
                | survey |                    |               |                               |
                |        | type               | name          | label                         | trigger            |
                |        | integer            | temp          | Enter the current temperature |                    |
                |        | background-geopoint| temp_geo      |                               | ${invalid_trigger} |
                |        | note               | show_temp_geo | location: ${temp_geo}         |                    |
                """,
            errored=True,
            error__contains=[
                "background-geopoint question 'temp_geo' must have a trigger corresponding to an existing question"
            ],
        )

    def test_background_geopoint_requires_null_calculation(self):
        """Test that background-geopoint raises an error if there is a calculation."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                    |               |                               |             |
            |        | type               | name          | label                         | trigger     | calculation |
            |        | integer            | temp          | Enter the current temperature |             |             |
            |        | background-geopoint| temp_geo      |                               | ${temp}     | 5 * temp    |
            |        | note               | show_temp_geo | location: ${temp_geo}         |             |             |
            """,
            errored=True,
            error__contains=[
                "'temp_geo' is triggered by a geopoint action, please remove the calculation from this question."
            ],
        )
