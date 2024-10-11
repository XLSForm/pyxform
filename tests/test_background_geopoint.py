from tests.pyxform_test_case import PyxformTestCase


class BackgroundGeopointTest(PyxformTestCase):
    """Test background-geopoint question type."""

    def test_background_geopoint(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                               |
            |        | type                | name          | label                         | trigger   |
            |        | integer             | temp          | Enter the current temperature |           |
            |        | background-geopoint | temp_geo      |                               | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}         |           |
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
            | survey |                     |               |                               |
            |        | type                | name          | label                         | trigger   |
            |        | integer             | temp          | Enter the current temperature |           |
            |        | background-geopoint | temp_geo      |                               |           |
            |        | note                | show_temp_geo | location: ${temp_geo}         |           |
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
            | survey |                     |               |                               |
            |        | type                | name          | label                         | trigger            |
            |        | integer             | temp          | Enter the current temperature |                    |
            |        | background-geopoint | temp_geo      |                               | ${invalid_trigger} |
            |        | note                | show_temp_geo | location: ${temp_geo}         |                    |
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
            | survey |                     |               |                               |             |
            |        | type                | name          | label                         | trigger     | calculation |
            |        | integer             | temp          | Enter the current temperature |             |             |
            |        | background-geopoint | temp_geo      |                               | ${temp}     | 5 * temp    |
            |        | note                | show_temp_geo | location: ${temp_geo}         |             |             |
            """,
            errored=True,
            error__contains=[
                "'temp_geo' is triggered by a geopoint action, please remove the calculation from this question."
            ],
        )

    def test_combined_background_geopoint_and_setvalue(self):
        """Test a form with both a background-geopoint and setvalue triggered by the same question."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                |           |
            |        | type                | name          | label                          | trigger   | calculation |
            |        | integer             | temp          | Enter the current temperature  |           |             |
            |        | background-geopoint | temp_geo      |                                | ${temp}   |             |
            |        | calculate           | temp_doubled  |                                | ${temp}   | ${temp} * 2 |
            |        | note                | show_temp_geo | location: ${temp_geo}          |           |             |
            |        | note                | show_temp     | doubled temp: ${temp_doubled}  |           |             |
            """,
            xml__xpath_match=[
                '/h:html/h:body//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/temp_geo"]',
                '/h:html/h:body//x:setvalue[@event="xforms-value-changed" and @ref="/data/temp_doubled" and normalize-space(@value)="/data/temp * 2"]',
            ],
        )

    def test_setgeopoint_trigger_target_outside_group(self):
        """Verify the correct structure for a setgeopoint trigger and target when neither is in a group."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                |
            |        | type                | name          | label                          | trigger   |
            |        | integer             | temp          | Enter the current temperature  |           |
            |        | background-geopoint | temp_geo      |                                | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}          |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/temp_geo"]',
                '/h:html/h:body//x:input[@ref="/data/show_temp_geo"]/x:label[contains(text(), "location:")]/x:output[@value=" /data/temp_geo "]',
            ],
        )

    def test_setgeopoint_trigger_target_in_non_repeating_group(self):
        """Verify the correct structure for a setgeopoint trigger and target in a non-repeating group."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                 |
            |        | type                | name          | label                           | trigger   |
            |        | begin_group         | groupA        |                                 |           |
            |        | integer             | temp          | Enter the current temperature   |           |
            |        | background-geopoint | temp_geo      |                                 | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}           |           |
            |        | end_group           |               |                                 |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body/x:group[@ref="/data/groupA"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:input[@ref="/data/groupA/temp"]//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/groupA/temp_geo"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:input[@ref="/data/groupA/show_temp_geo"]/x:label[contains(text(), "location:")]/x:output[@value=" /data/groupA/temp_geo "]',
            ],
        )

    def test_setgeopoint_trigger_target_separate_groups(self):
        """Verify the correct structure for a setgeopoint trigger and target in two separate groups."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                 |
            |        | type                | name          | label                           | trigger   |
            |        | begin_group         | groupA        |                                 |           |
            |        | integer             | temp          | Enter the current temperature   |           |
            |        | end_group           |               |                                 |           |
            |        | begin_group         | groupB        |                                 |           |
            |        | background-geopoint | temp_geo      |                                 | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}           |           |
            |        | end_group           |               |                                 |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body/x:group[@ref="/data/groupA"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:input[@ref="/data/groupA/temp"]//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/groupB/temp_geo"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]/x:input[@ref="/data/groupB/show_temp_geo"]/x:label/x:output[@value=" /data/groupB/temp_geo "]',
            ],
        )

    def test_setgeopoint_trigger_target_in_same_repeating_group(self):
        """Verify the correct structure for a setgeopoint trigger and target in the same repeating group."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                 |
            |        | type                | name          | label                           | trigger   |
            |        | begin_repeat        | groupA        |                                 |           |
            |        | integer             | temp          | Enter the current temperature   |           |
            |        | background-geopoint | temp_geo      |                                 | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}           |           |
            |        | end_repeat          |               |                                 |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]/x:input[@ref="/data/groupA/temp"]//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/groupA/temp_geo"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]/x:input[@ref="/data/groupA/show_temp_geo"]/x:label/x:output[@value=" ../temp_geo "]',
            ],
        )

    def test_setgeopoint_trigger_target_in_separate_repeating_groups(self):
        """Verify the correct structure for a setgeopoint trigger and target in separate repeating groups."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                 |
            |        | type                | name          | label                           | trigger   |
            |        | begin_repeat        | groupA        |                                 |           |
            |        | integer             | temp          | Enter the current temperature   |           |
            |        | end_repeat          |               |                                 |           |
            |        | begin_repeat        | groupB        |                                 |           |
            |        | background-geopoint | temp_geo      |                                 | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}           |           |
            |        | end_repeat          |               |                                 |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]/x:input[@ref="/data/groupA/temp"]//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/groupB/temp_geo"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]/x:repeat[@nodeset="/data/groupB"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]/x:repeat[@nodeset="/data/groupB"]/x:input[@ref="/data/groupB/show_temp_geo"]/x:label/x:output[@value=" ../temp_geo "]',
            ],
        )

    def test_setgeopoint_trigger_in_repeating_group_target_in_non_repeating_groups(
        self,
    ):
        """Verify the correct structure for a setgeopoint trigger in a repeating group and a target in a non-repeating group."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                 |
            |        | type                | name          | label                           | trigger   |
            |        | begin_repeat        | groupA        |                                 |           |
            |        | integer             | temp          | Enter the current temperature   |           |
            |        | end_repeat          |               |                                 |           |
            |        | begin_group         | groupB        |                                 |           |
            |        | background-geopoint | temp_geo      |                                 | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}           |           |
            |        | end_group           |               |                                 |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:repeat[@nodeset="/data/groupA"]/x:input[@ref="/data/groupA/temp"]//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/groupB/temp_geo"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]/x:input[@ref="/data/groupB/show_temp_geo"]/x:label/x:output[@value=" /data/groupB/temp_geo "]',
            ],
        )

    def test_setgeopoint_trigger_in_non_repeating_group_target_in_repeating_group(
        self,
    ):
        """Verify the correct structure for a setgeopoint trigger in a non-repeating group and a target in a repeating group."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |                     |               |                                 |
            |        | type                | name          | label                           | trigger   |
            |        | begin_group         | groupA        |                                 |           |
            |        | integer             | temp          | Enter the current temperature   |           |
            |        | end_group           |               |                                 |           |
            |        | begin_repeat        | groupB        |                                 |           |
            |        | background-geopoint | temp_geo      |                                 | ${temp}   |
            |        | note                | show_temp_geo | location: ${temp_geo}           |           |
            |        | end_repeat          |               |                                 |           |
            """,
            xml__xpath_match=[
                '/h:html/h:body/x:group[@ref="/data/groupA"]',
                '/h:html/h:body/x:group[@ref="/data/groupA"]/x:input[@ref="/data/groupA/temp"]//odk:setgeopoint[@event="xforms-value-changed" and @ref="/data/groupB/temp_geo"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]/x:repeat[@nodeset="/data/groupB"]',
                '/h:html/h:body/x:group[@ref="/data/groupB"]/x:repeat[@nodeset="/data/groupB"]/x:input[@ref="/data/groupB/show_temp_geo"]/x:label/x:output[@value=" ../temp_geo "]',
            ],
        )
