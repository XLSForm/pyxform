from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
from pyxform.tests_v1.pyxform_test_case import PyxformTestError
try:
    from unittest import skip
except ImportError:
    from unittest2 import skip


class ExternalInstanceTests(PyxformTestCase):

    def test_external_single_ok(self):
        """Simplest possible example to include an external instance."""
        self.assertPyxformXform(
            md="""
            | survey |             |           |                  |
            |        | type        | name      | label            |
            |        | xml-data    | mydata    |                  |
            """,
            model__contains=[
                '<instance id="mydata" src="jr://file/mydata.xml"/>'
            ],
            run_odk_validate=True
        )

    def test_external_two_in_section_duplicate_raises(self):
        """Duplicate external instances in the same section raises an error."""
        with self.assertRaises(PyxformTestError) as ctx:
            self.assertPyxformXform(
                md="""
                | survey |             |           |                  |
                |        | type        | name      | label            |
                |        | xml-data    | mydata    |                  |
                |        | xml-data    | mydata    |                  |
                """,
                model__contains=[])
        # This is caught first by existing validation rule.
        self.assertIn("There are two survey elements named 'mydata'",
                      repr(ctx.exception))

    def test_external_two_in_section_unique_ok(self):
        """Two unique external instances in the same section is OK."""
        self.assertPyxformXform(
            md="""
            | survey |             |           |                  |
            |        | type        | name      | label            |
            |        | xml-data    | mydata    |                  |
            |        | xml-data    | mydata2   |                  |
            """,
            model__contains=[
                '<instance id="mydata" src="jr://file/mydata.xml"/>',
                '<instance id="mydata2" src="jr://file/mydata2.xml"/>'
            ],
            run_odk_validate=True
        )

    def test_external_multi_group_duplicate_raises(self):
        """Duplicate external instances anywhere raises an error."""
        with self.assertRaises(PyxformTestError) as ctx:
            self.assertPyxformXform(
                md="""
                | survey |             |         |                  |
                |        | type        | name    | label            |
                |        | xml-data    | mydata  |                  |
                |        | begin group | g1      |                  |
                |        | xml-data    | mydata  |                  |
                |        | end group   | g1      |                  |
                |        | begin group | g2      |                  |
                |        | xml-data    | mydata  |                  |
                |        | end group   | g2      |                  |
                """,
                model__contains=[])
        self.assertIn("Instance names must be unique", repr(ctx.exception))

    def test_external_multi_group_duplicate_raises_helpfully(self):
        """Duplicate external instances anywhere raises a helpful error."""
        with self.assertRaises(PyxformTestError) as ctx:
            self.assertPyxformXform(
                md="""
                | survey |             |         |                  |
                |        | type        | name    | label            |
                |        | xml-data    | mydata  |                  |
                |        | begin group | g1      |                  |
                |        | xml-data    | mydata  |                  |
                |        | end group   | g1      |                  |
                |        | begin group | g2      |                  |
                |        | xml-data    | mydata2 |                  |
                |        | end group   | g2      |                  |
                |        | begin group | g3      |                  |
                |        | xml-data    | mydata3 |                  |
                |        | end group   | g3      |                  |
                """,
                model__contains=[])
        self.assertIn("The name 'mydata' was found 2 time(s)",
                      repr(ctx.exception))

    def test_external_multi_group_unique_ok(self):
        """Unique external instances anywhere is OK."""
        self.assertPyxformXform(
            md="""
            | survey |             |         |                  |
            |        | type        | name    | label            |
            |        | xml-data    | mydata  |                  |
            |        | begin group | g1      |                  |
            |        | xml-data    | mydata1 |                  |
            |        | note        | note1   | It's note-able   |
            |        | end group   | g1      |                  |
            |        | begin group | g2      |                  |
            |        | note        | note2   | It's note-able   |
            |        | xml-data    | mydata2 |                  |
            |        | end group   | g2      |                  |
            |        | begin group | g3      |                  |
            |        | note        | note3   | It's note-able   |
            |        | xml-data    | mydata3 |                  |
            |        | end group   | g3      |                  |
            """,
            model__contains=[
                '<instance id="mydata" src="jr://file/mydata.xml"/>',
                '<instance id="mydata1" src="jr://file/mydata1.xml"/>',
                '<instance id="mydata2" src="jr://file/mydata2.xml"/>',
                '<instance id="mydata3" src="jr://file/mydata3.xml"/>'
            ],
            run_odk_validate=True
        )

    def test_instance_names_other_sources_duplicate_raises(self):
        """Duplicate instances with other sources present raises an error."""
        with self.assertRaises(PyxformTestError) as ctx:
            self.assertPyxformXform(
                md="""
                | survey |                                      |      |       |
                |        | type                                 | name | label | calculation  |
                |        | begin group                          | g1   |       |              |
                |        | xml-data                             | city |       |              |
                |        | end group                            | g1   |       |              |
                |        | xml-data                             | city |       |              |
                |        | begin group                          | g2   |       |              |
                |        | select_one_from_file cities.csv      | city | City  |              |
                |        | end group                            | g2   |       |              |
                |        | begin group                          | g3   |       |              |
                |        | select_multiple_from_file cities.csv | city | City  |              |
                |        | end group                            | g3   |       |              |
                |        | begin group                          | g4   |       |              |
                |        | calculate                            | city | City  | pulldata('fruits', 'name', 'name', 'mango') |
                |        | end group                            | g4   |       |              |
                """,
                model__contains=[])
        self.assertIn("The name 'city' was found 2 time(s)",
                      repr(ctx.exception))

    def test_instance_names_other_sources_unique_ok(self):
        """Unique instances with other sources present are OK."""
        self.assertPyxformXform(
            md="""
            | survey |                                      |       |       |
            |        | type                                 | name  | label | calculation  |
            |        | begin group                          | g1    |       |              |
            |        | xml-data                             | city1 |       |              |
            |        | note                                 | note1 | Note  |              |
            |        | end group                            | g1    |       |              |
            |        | begin group                          | g2    |       |              |
            |        | select_one_from_file cities.csv      | city2 | City2 |              |
            |        | end group                            | g2    |       |              |
            |        | begin group                          | g3    |       |              |
            |        | select_multiple_from_file cities.csv | city3 | City3 |              |
            |        | end group                            | g3    |       |              |
            |        | begin group                          | g4    |       |              |
            |        | calculate                            | city4 | City4 | pulldata('fruits', 'name', 'name', 'mango') |
            |        | note                                 | note4 | Note  |              |
            |        | end group                            | g4    |       |              |
            """,
            model__contains=[
                '<instance id="city1" src="jr://file/city1.xml"/>',
"""
      <instance id="cities" src="jr://file-csv/cities.csv">
        <root>
          <item>
            <name>_</name>
            <label>_</label>
          </item>
        </root>
      </instance>
""",
                '<instance id="fruits" src="jr://file-csv/fruits.csv"/>'
            ],
            run_odk_validate=True
        )

    def test_one_instance_per_external_select(self):
        """Using a select from file should output 1 instance: #88 bug test"""
        md = """
            | survey  |                                      |       |       |                                    |
            |         | type                                 | name  | label | choice_filter                      |
            |         | select_one_from_file states.csv      | state | State |                                    |
            |         | select_one_from_file cities.csv      | city  | City  | state=/select_from_file_test/State |
            |         | select_one regular                   | test  | Test  |                                    |
            | choices |                                      |       |       |                                    |
            |         | list_name                            | name  | label |                                    |
            |         | states                               | name  | label |                                    |
            |         | cities                               | name  | label |                                    |
            |         | regular                              | 1     | Pass  |                                    |
            |         | regular                              | 2     | Fail  |                                    |
            """
        self.assertPyxformXform(
            md=md,
            model__contains=[
"""
      <instance id="states" src="jr://file-csv/states.csv">
        <root>
          <item>
            <name>_</name>
            <label>_</label>
          </item>
        </root>
      </instance>
""",
"""
      <instance id="cities" src="jr://file-csv/cities.csv">
        <root>
          <item>
            <name>_</name>
            <label>_</label>
          </item>
        </root>
      </instance>
""",
"""
      <instance id="regular">
        <root>
          <item>
            <itextId>static_instance-regular-0</itextId>
            <name>1</name>
          </item>
          <item>
            <itextId>static_instance-regular-1</itextId>
            <name>2</name>
          </item>
        </root>
      </instance>
"""
            ],
            run_odk_validate=True
        )
        survey = self.md_to_pyxform_survey(md_raw=md)
        xml = survey._to_pretty_xml()
        unwanted_extra_states = \
"""
      <instance id="regular">
        <root>
          <item>
            <itextId>static_instance-states-0</itextId>
            <name>1</name>
          </item>
        </root>
      </instance>
"""
        self.assertNotIn(unwanted_extra_states, xml)
        unwanted_extra_cities = \
            """
                  <instance id="regular">
                    <root>
                      <item>
                        <itextId>static_instance-cities-0</itextId>
                        <name>1</name>
                      </item>
                    </root>
                  </instance>
            """
        self.assertNotIn(unwanted_extra_cities, xml)

    def test_no_duplicate_with_pulldata(self):
        """Using xml-data and pulldata should not output 2 instances."""
        md = """
            | survey |                                      |        |       |              |
            |        | type                                 | name   | label | calculation  |
            |        | begin group                          | g1     |       |              |
            |        | xml-data                             | fruits |       |              |
            |        | calculate                            | f_csv  | City  | pulldata('fruits', 'name', 'name', 'mango') |
            |        | note                                 | note   | Fruity! ${f_csv} |   |
            |        | end group                            | g1     |       |              |
            """
        self.assertPyxformXform(
            md=md,
            model__contains=[
                '<instance id="fruits" src="jr://file/fruits.xml"/>',
            ],
            run_odk_validate=True
        )
        survey = self.md_to_pyxform_survey(md_raw=md)
        xml = survey._to_pretty_xml()
        unwanted_extra_fruits = \
            '<instance id="fruits" src="jr://file-csv/fruits.csv"/>'
        self.assertNotIn(unwanted_extra_fruits, xml)
