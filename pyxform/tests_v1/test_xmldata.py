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
            ]
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
            ]
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
            |        | end group   | g1      |                  |
            |        | begin group | g2      |                  |
            |        | xml-data    | mydata2 |                  |
            |        | end group   | g2      |                  |
            |        | begin group | g3      |                  |
            |        | xml-data    | mydata3 |                  |
            |        | end group   | g3      |                  |
            """,
            model__contains=[
                '<instance id="mydata" src="jr://file/mydata.xml"/>',
                '<instance id="mydata1" src="jr://file/mydata1.xml"/>',
                '<instance id="mydata2" src="jr://file/mydata2.xml"/>',
                '<instance id="mydata3" src="jr://file/mydata3.xml"/>'
            ]
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
            |        | end group                            | g1    |       |              |
            |        | begin group                          | g2    |       |              |
            |        | select_one_from_file cities.csv      | city2 | City2 |              |
            |        | end group                            | g2    |       |              |
            |        | begin group                          | g3    |       |              |
            |        | select_multiple_from_file cities.csv | city3 | City3 |              |
            |        | end group                            | g3    |       |              |
            |        | begin group                          | g4    |       |              |
            |        | calculate                            | city4 | City4 | pulldata('fruits', 'name', 'name', 'mango') |
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
            ]
        )

    @skip("Usage scenarios TBA but it might look something like this.")
    def test_external_usage_scenario(self):
        self.assertPyxformXform(
            md="""
            | survey |             |           |                  | 
            |        | type        | name      | label            | bind::type  |  calculation  
            |        | calculate   | external1 |                  | External    |  oc-item(event1(1), form2, item3(1))
            |        | note        | ext_note  | The external value is ${external_1} |     |
            """,
            model__contains=[
                # TODO: not sure what
                ])

