from pyxform.errors import ErrorCode
from pyxform.validators.pyxform import question_types as qt

from tests.pyxform_test_case import PyxformTestCase


class TestBackgroundGeopoint(PyxformTestCase):
    """Test background-geopoint question type."""

    def test_error__missing_trigger(self):
        """Should raise an error if the question trigger is empty."""
        md = """
        | survey |
        |        | type                | name          | label      | trigger |
        |        | integer             | temp          | Enter temp |         |
        |        | background-geopoint | temp_geo      |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            errored=True,
            error__contains=[qt.BACKGROUND_GEOPOINT_TRIGGER.format(r=3)],
        )

    def test_error__invalid_trigger(self):
        """Should raise an error if the question trigger does not refer to a question."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger    |
        |        | integer             | temp     | Enter temp |            |
        |        | background-geopoint | temp_geo |            | ${invalid} |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.PYREF_003.value.format(
                    sheet="survey", column="trigger", row="3", q="invalid"
                )
            ],
        )

    def test_error__calculation_exists(self):
        """Should raise an error if a calculation exists for the question."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger | calculation |
        |        | integer             | temp     | Enter temp |         |             |
        |        | background-geopoint | temp_geo |            | ${temp} | 5 * temp    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[qt.BACKGROUND_GEOPOINT_CALCULATION.format(r=3)],
        )

    def test_question_no_group__trigger_no_group(self):
        """Should find geopoint binding, and setgeopoint action on the triggering item."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | integer             | temp     | Enter temp |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:input[@ref='/data/temp']
                  /odk:setgeopoint[@event='xforms-value-changed' and @ref='/data/temp_geo']
                """,
            ],
        )

    def test_question_no_group__trigger_no_group__with_calculate_same_trigger(self):
        """Should find the behaviour is unchanged by a calculate question with same trigger."""
        md = """
        | survey |
        |        | type                | name         | label      | trigger | calculation |
        |        | integer             | temp         | Enter temp |         |             |
        |        | background-geopoint | temp_geo     |            | ${temp} |             |
        |        | calculate           | temp_doubled |            | ${temp} | ${temp} * 2 |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:input[@ref='/data/temp']
                  /odk:setgeopoint[@event='xforms-value-changed' and @ref='/data/temp_geo']
                """,
                # calculate bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/temp_doubled' and @type='string']""",
                """
                /h:html/h:body/x:input[@ref='/data/temp']
                  /x:setvalue[@event='xforms-value-changed'
                    and @ref='/data/temp_doubled'
                    and normalize-space(@value)='/data/temp * 2'
                  ]
                """,
            ],
        )

    def test_question_in_nonrep_group__trigger_in_same_nonrep_group(self):
        """Should find the behaviour is unchanged by nesting in a non-repeating group."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | begin_group         | groupA   |            |         |
        |        | integer             | temp     | Enter temp |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        |        | end_group           |          |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/groupA/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:group[@ref='/data/groupA']
                  /x:input[@ref='/data/groupA/temp']/odk:setgeopoint[
                    @event='xforms-value-changed' and @ref='/data/groupA/temp_geo'
                ]
                """,
            ],
        )

    def test_question_in_nonrep_group__trigger_in_different_nonrep_group(self):
        """Should find the behaviour is unchanged by nesting in different non-repeating groups."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | begin_group         | groupA   |            |         |
        |        | integer             | temp     | Enter temp |         |
        |        | end_group           |          |            |         |
        |        | begin_group         | groupB   |            |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        |        | end_group           |          |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/groupB/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:group[@ref="/data/groupA"]
                  /x:input[@ref="/data/groupA/temp"]
                  /odk:setgeopoint[
                    @event="xforms-value-changed" and @ref="/data/groupB/temp_geo"
                  ]
                """,
            ],
        )

    def test_question_in_rep_group__trigger_in_same_rep_group(self):
        """Should find the behaviour is unchanged by nesting in a repeating group."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | begin_repeat        | groupA   |            |         |
        |        | integer             | temp     | Enter temp |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        |        | end_repeat          |          |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/groupA/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:group[@ref='/data/groupA']
                  /x:repeat[@nodeset='/data/groupA']/x:input[@ref='/data/groupA/temp']
                  /odk:setgeopoint[
                    @event='xforms-value-changed' and @ref='/data/groupA/temp_geo'
                ]
                """,
            ],
        )

    def test_question_in_rep_group__trigger_in_different_rep_group(self):
        """Should find the behaviour is unchanged by nesting in different repeating groups."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | begin_repeat        | groupA   |            |         |
        |        | integer             | temp     | Enter temp |         |
        |        | end_repeat          |          |            |         |
        |        | begin_repeat        | groupB   |            |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        |        | end_repeat          |          |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/groupB/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:group[@ref='/data/groupA']
                  /x:repeat[@nodeset='/data/groupA']/x:input[@ref='/data/groupA/temp']
                  /odk:setgeopoint[
                    @event='xforms-value-changed' and @ref='/data/groupB/temp_geo'
                ]
                """,
            ],
        )

    def test_question_in_nonrep_group__trigger_in_different_rep_group(self):
        """Should find the behaviour is unchanged by nesting in different non/repeating groups."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | begin_repeat        | groupA   |            |         |
        |        | integer             | temp     | Enter temp |         |
        |        | end_repeat          |          |            |         |
        |        | begin_group         | groupB   |            |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        |        | end_group           |          |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/groupB/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:group[@ref='/data/groupA']
                  /x:repeat[@nodeset='/data/groupA']/x:input[@ref='/data/groupA/temp']
                  /odk:setgeopoint[
                    @event='xforms-value-changed' and @ref='/data/groupB/temp_geo'
                ]
                """,
            ],
        )

    def test_question_in_rep_group__trigger_in_different_nonrep_group(self):
        """Should find the behaviour is unchanged by nesting in different non/repeating groups."""
        md = """
        | survey |
        |        | type                | name     | label      | trigger |
        |        | begin_group         | groupA   |            |         |
        |        | integer             | temp     | Enter temp |         |
        |        | end_group           |          |            |         |
        |        | begin_repeat        | groupB   |            |         |
        |        | background-geopoint | temp_geo |            | ${temp} |
        |        | end_repeat          |          |            |         |
        """
        self.assertPyxformXform(
            name="data",
            md=md,
            xml__xpath_match=[
                # background-geopoint bind/control
                """/h:html/h:head/x:model/x:bind[@nodeset='/data/groupB/temp_geo' and @type='geopoint']""",
                """
                /h:html/h:body/x:group[@ref='/data/groupA']
                  /x:input[@ref='/data/groupA/temp']/odk:setgeopoint[
                    @event='xforms-value-changed' and @ref='/data/groupB/temp_geo'
                ]
                """,
            ],
        )
