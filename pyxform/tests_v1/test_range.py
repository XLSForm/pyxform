from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class RangeWidgetTest(PyxformTestCase):
    def test_range_type(self):
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | properties          |
            |        | range  |   level  | Scale | min=1 max=10 step=1 |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="10" ref="/data/level" start="1" step="1">'],
        )

    def test_range_type_defaults(self):
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | properties          |
            |        | range  |   level  | Scale |                     |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="10" ref="/data/level" start="1" step="1">'],
        )

        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | properties          |
            |        | range  |   level  | Scale | max=20              |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="20" ref="/data/level" start="1" step="1">'],
        )

        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | range  |   level  | Scale |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="10" ref="/data/level" start="1" step="1">'],
        )

    def test_range_type_float(self):
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | properties          |
            |        | range  |   level  | Scale | min=0.5 max=5.0 step=0.5 |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="decimal"/>',
                '<range end="5.0" ref="/data/level" start="0.5" step="0.5">'],
        )
