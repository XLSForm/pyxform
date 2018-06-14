from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class RangeWidgetTest(PyxformTestCase):
    def test_rank(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |              |          |       |
            |        | type         | name     | label |
            |        | rank mylist  | order    | Rank  |
            | choices|              |          |       |
            |        | list_name    | name     | label |
            |        | mylist       | a        | A     |
            |        | mylist       | b        | B     |
            """,
            xml__contains=[
                '<rank ref="/data/order">',
                '<label>Rank</label>',
                '<label>A</label>',
                '<value>a</value>',
                '<label>B</label>',
                '<value>b</value>'
            ]
        )


    def test_rank_filter(self):
        self.assertPyxformXform(
            name="data",
            debug=True,
            md="""
            | survey |              |          |       |               |
            |        | type         | name     | label | choice_filter |
            |        | rank mylist  | order    | Rank  | color='blue'  |
            | choices|              |          |       |
            |        | list_name    | name     | label | color |
            |        | mylist       | a        | A     | red   |
            |        | mylist       | b        | B     | blue  |
           """,
            xml__contains=[
                """<instance id="mylist">
        <root>
          <item>
            <itextId>static_instance-mylist-0</itextId>
            <color>red</color>
            <name>a</name>
          </item>
          <item>
            <itextId>static_instance-mylist-1</itextId>
            <color>blue</color>
            <name>b</name>
          </item>
        </root>
      </instance>""",
                """<rank ref="/data/order">
      <label>Rank</label>
      <itemset nodeset="instance('mylist')/root/item[color='blue']">
        <value ref="name"/>
        <label ref="jr:itext(itextId)"/>
      </itemset>
    </rank>"""
            ]
        )


    def test_rank_translations(self):
        self.assertPyxformXform(
            name="data",
            debug=True,
            md="""
            | survey |              |          |       |                    |
            |        | type         | name     | label | label::French (fr) |
            |        | rank mylist  | order    | Rank  | Ranger             |
            | choices|              |          |       |
            |        | list_name    | name     | label | label::French (fr) |
            |        | mylist       | a        | A     |  À                 |
            |        | mylist       | b        | B     |  É                 |
            """,
            xml__contains=[
                """<translation lang="French (fr)">
          <text id="/data/order:label">
            <value>Ranger</value>
          </text>
          <text id="/data/order/a:label">
            <value>À</value>
          </text>
          <text id="/data/order/b:label">
            <value>É</value>
          </text>
        </translation>""",
        """<rank ref="/data/order">
      <label ref="jr:itext('/data/order:label')"/>
      <item>
        <label ref="jr:itext('/data/order/a:label')"/>
        <value>a</value>
      </item>
      <item>
        <label ref="jr:itext('/data/order/b:label')"/>
        <value>b</value>
      </item>
    </rank>"""
            ]
        )
