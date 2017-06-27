from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class OSMWidgetsTest(PyxformTestCase):
    def test_osm_type(self):
        self.assertPyxformXform(
            name="osm",
            run_odk_validate=True,
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
            xml__contains=[
                """
  <h:head>
    <h:title>pyxform_autotesttitle</h:title>
    <model>
      <instance>
        <osm id="pyxform_autotest_id_string">
          <osm_road/>
          <osm_building/>
          <meta>
            <instanceID/>
          </meta>
        </osm>
      </instance>
      <bind nodeset="/osm/osm_road" type="binary"/>
      <bind nodeset="/osm/osm_building" type="binary"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/osm/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <upload mediatype="osm/*" ref="/osm/osm_road">
      <label>Road</label>
    </upload>
    <upload mediatype="osm/*" ref="/osm/osm_building">
      <label>Building</label>
      <tag key="name">
        <label>Name</label>
      </tag>
      <tag key="addr:city">
        <label>City</label>
      </tag>
    </upload>
  </h:body>
</h:html>"""
            ],
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
            xml__contains=[
                """
  <h:head>
    <h:title>pyxform_autotesttitle</h:title>
    <model>
      <instance>
        <osm id="pyxform_autotest_id_string">
          <osm_road/>
          <osm_building/>
          <meta>
            <instanceID/>
          </meta>
        </osm>
      </instance>
      <bind nodeset="/osm/osm_road" type="binary"/>
      <bind nodeset="/osm/osm_building" type="binary"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/osm/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <upload mediatype="osm/*" ref="/osm/osm_road">
      <label>Road</label>
    </upload>
    <upload mediatype="osm/*" ref="/osm/osm_building">
      <label>Building</label>
      <tag key="name">
        <label>Name</label>
      </tag>
      <tag key="addr:city">
        <label>City</label>
      </tag>
    </upload>
  </h:body>
</h:html>"""
            ],
        )
