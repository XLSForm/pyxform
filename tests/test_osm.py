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
                xpq.model_instance_item("osm_road"),
                xpq.model_instance_bind("osm_road", "binary"),
                xpq.body_label_inline("upload", "osm_road", "Road"),
                # osm_build has data binding and control with tags from building_tags
                xpq.model_instance_item("osm_build"),
                xpq.model_instance_bind("osm_build", "binary"),
                xpq.body_label_inline("upload", "osm_build", "Building"),
                xpq.body_upload_tags(
                    "osm_build", (("name", "Name"), ("addr:city", "City"))
                ),
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
                xpq.model_instance_item("osm_road"),
                xpq.model_instance_bind("osm_road", "binary"),
                xpq.body_label_inline("upload", "osm_road", "Road"),
                # osm_build has data binding and control with tags from building_tags
                xpq.model_instance_item("osm_build"),
                xpq.model_instance_bind("osm_build", "binary"),
                xpq.body_label_inline("upload", "osm_build", "Building"),
                xpq.body_upload_tags(
                    "osm_build", (("name", "Name"), ("addr:city", "City"))
                ),
                # osm_room has data binding and control with tags from room_tags
                xpq.model_instance_item("osm_room"),
                xpq.model_instance_bind("osm_room", "binary"),
                xpq.body_label_inline("upload", "osm_room", "Room"),
                xpq.body_upload_tags(
                    "osm_room", (("room:type", "Type"), ("habitable", "Habitable"))
                ),
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
                xpq.model_instance_item("osm_resi"),
                xpq.model_instance_bind("osm_resi", "binary"),
                xpq.body_label_inline("upload", "osm_resi", "Residential"),
                xpq.body_upload_tags(
                    "osm_resi", (("room:type", "Type"), ("habitable", "Habitable"))
                ),
                # osm_office has data binding and control with tags from room_tags
                xpq.model_instance_item("osm_office"),
                xpq.model_instance_bind("osm_office", "binary"),
                xpq.body_label_inline("upload", "osm_office", "Office"),
                xpq.body_upload_tags(
                    "osm_office", (("room:type", "Type"), ("habitable", "Habitable"))
                ),
            ],
            # The OSM list names aren't output anywhere (tags copied inline).
            xml__excludes=["room_tags"],
        )
