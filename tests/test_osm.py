"""
Test OSM widgets.
"""

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq

expected_xml_output = """
    <upload mediatype="osm/*" ref="/osm/osm_building">
      <label>Building</label>
      <tag key="name">
        <label>Name</label>
      </tag>
      <tag key="addr:city">
        <label>City</label>
      </tag>
    </upload>"""


class OSMWidgetsTest(PyxformTestCase):
    """
    Test OSM widgets.
    """

    def test_osm_type(self):
        self.assertPyxformXform(
            name="osm",
            md="""
            | survey |                   |              |          |
            |        | type              |   name       | label    |
            |        | osm               | osm_road     | Road     |
            |        | osm building_tags | osm_building | Building |
            | osm    |                   |              |          |
            |        | list name         |  name        | label    |
            |        | building_tags     | name         | Name     |
            |        | building_tags     | addr:city    | City     |

            """,
            xml__contains=[expected_xml_output],
        )

    def test_osm_type_with_list_underscore_name(self):
        self.assertPyxformXform(
            name="osm",
            md="""
            | survey |                   |              |          |
            |        | type              |   name       | label    |
            |        | osm               | osm_road     | Road     |
            |        | osm building_tags | osm_building | Building |
            | osm    |                   |              |          |
            |        | list_name         |  name        | label    |
            |        | building_tags     | name         | Name     |
            |        | building_tags     | addr:city    | City     |

            """,
            xml__contains=[expected_xml_output],
        )

    def test_osm_type_with_select(self):
        """Should find that the OSM tags are output in the body and selects are as normal."""
        md = """
        | survey  |
        |         | type              | name      | label    |
        |         | osm               | osm_road  | Road     |
        |         | osm building_tags | osm_build | Building |
        |         | select_one c1     | q1        | Q1       |
        | osm     |
        |         | list_name     | name      | label |
        |         | building_tags | name      | Name  |
        |         | building_tags | addr:city | City  |
        | choices |
        |         | list_name | name | label |
        |         | c1        | n1   | l1    |
        |         | c1        | n2   | l2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # q1 has data binding, control, and itemset reference.
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.body_label_inline("select1", "q1", "Q1"),
                # q1 has secondary choices instance with inline labels.
                xpc.model_instance_choices_label("c1", (("n1", "l1"), ("n2", "l2"))),
                # osm_road has data binding and control
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_road
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_road' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*' and @ref='/test_name/osm_road' and ./x:label[text()='Road']
                ]
                """,
                # osm_build has data binding and control with tags from building_tags
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_build
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_build' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*'
                  and @ref='/test_name/osm_build'
                  and ./x:label[text()='Building']
                  and ./x:tag[@key='name' and ./x:label/text()='Name']
                  and ./x:tag[@key='addr:city' and ./x:label/text()='City']
                ]
                """,
            ],
            # The OSM list names aren't output anywhere (tags copied inline).
            xml__excludes=["room_tags"],
        )

    def test_osm_type_with_multiple_lists__separate(self):
        """Should find that the OSM tags are output for the corresponding question."""
        md = """
        | survey  |
        |         | type              | name      | label    |
        |         | osm               | osm_road  | Road     |
        |         | osm building_tags | osm_build | Building |
        |         | osm room_tags     | osm_room  | Room     |
        | osm     |
        |         | list_name     | name       | label     |
        |         | building_tags | name       | Name      |
        |         | building_tags | addr:city  | City      |
        |         | room_tags     | room:type  | Type      |
        |         | room_tags     | habitable  | Habitable |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # osm_road has data binding and control
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_road
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_road' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*' and @ref='/test_name/osm_road' and ./x:label[text()='Road']
                ]
                """,
                # osm_build has data binding and control with tags from building_tags
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_build
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_build' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*'
                  and @ref='/test_name/osm_build'
                  and ./x:label[text()='Building']
                  and ./x:tag[@key='name' and ./x:label/text()='Name']
                  and ./x:tag[@key='addr:city' and ./x:label/text()='City']
                ]
                """,
                # osm_room has data binding and control with tags from room_tags
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_room
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_room' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*'
                  and @ref='/test_name/osm_room'
                  and ./x:label[text()='Room']
                  and ./x:tag[@key='room:type' and ./x:label/text()='Type']
                  and ./x:tag[@key='habitable' and ./x:label/text()='Habitable']
                ]
                """,
            ],
            # The OSM list names aren't output anywhere (tags copied inline).
            xml__excludes=["building_tags", "room_tags"],
        )

    def test_osm_type_with_multiple_lists__shared(self):
        """Should find that the OSM tags are output for the corresponding question."""
        md = """
        | survey  |
        |         | type          | name       | label       |
        |         | osm room_tags | osm_resi   | Residential |
        |         | osm room_tags | osm_office | Office      |
        | osm     |
        |         | list_name     | name       | label     |
        |         | room_tags     | room:type  | Type      |
        |         | room_tags     | habitable  | Habitable |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # osm_resi has data binding and control with tags from room_tags
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_resi
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_resi' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*'
                  and @ref='/test_name/osm_resi'
                  and ./x:label[text()='Residential']
                  and ./x:tag[@key='room:type' and ./x:label/text()='Type']
                  and ./x:tag[@key='habitable' and ./x:label/text()='Habitable']
                ]
                """,
                # osm_office has data binding and control with tags from room_tags
                """
                /h:html/h:head/x:model/x:instance/x:test_name[@id='data']/x:osm_office
                """,
                """
                /h:html/h:head/x:model/x:bind[@nodeset='/test_name/osm_office' and @type='binary']
                """,
                """
                /h:html/h:body/x:upload[
                  @mediatype='osm/*'
                  and @ref='/test_name/osm_office'
                  and ./x:label[text()='Office']
                  and ./x:tag[@key='room:type' and ./x:label/text()='Type']
                  and ./x:tag[@key='habitable' and ./x:label/text()='Habitable']
                ]
                """,
            ],
            # The OSM list names aren't output anywhere (tags copied inline).
            xml__excludes=["room_tags"],
        )
