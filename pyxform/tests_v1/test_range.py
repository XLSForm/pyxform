from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class RangeWidgetTest(PyxformTestCase):
    def test_range_type(self):
        # properties column
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

        # parameters column
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | parameters          |
            |        | range  |   level  | Scale | min=1 max=10 step=2 |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="10" ref="/data/level" start="1" step="2">'],
        )

        # attributes column
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | attributes          |
            |        | range  |   level  | Scale | min=1 max=10 step=2 |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="10" ref="/data/level" start="1" step="2">'],
        )

        # mixed case parameters
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | properties          |
            |        | range  |   level  | Scale | Min=3 Max=14 STEP=2 |
            """,
            xml__contains=[
                '<bind nodeset="/data/level" type="int"/>',
                '<range end="14" ref="/data/level" start="3" step="2">'],
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

    def test_range_type_invvalid_parameters(self):
        # 'increment' is an invalid property
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                        |
            |        | type   |   name   | label | properties             |
            |        | range  |   level  | Scale | increment=0.5 max=21.5 |
            """,
            errored=True,
        )
        self.assertPyxformXform(
            debug=True,
            name="data",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | properties          |
            |        | range  |   level  | Scale | min=0.5 max=X step=0.5 |
            """,
            errored=True,
        )
