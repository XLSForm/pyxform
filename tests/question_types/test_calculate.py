"""
Test that any row with a calculation becomes a calculate of the row's type or of type string if the type is "calculate". A hint or label
error should only be thrown for a row without a calculation.
"""

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


class TypedCalculatesTest(PyxformTestCase):
    def test_xls_type_calculate_has_type_string(self):
        self.assertPyxformXform(
            name="calculate-type",
            md="""
            | survey |          |      |             |             |
            |        | type     | name | label       | calculation |
            |        | calculate| a    |             | 2 * 2       |
            """,
            xml__contains=[
                '<bind calculate="2 * 2" nodeset="/calculate-type/a" type="string"/>',
            ],
        )

    def test_xls_type_calculate_with_label_has_no_body(self):
        self.assertPyxformXform(
            name="calculate-type",
            md="""
                | survey |          |      |             |             |
                |        | type     | name | label       | calculation |
                |        | calculate| a    | A           | 2 * 2       |
                """,
            xml__contains=[
                '<bind calculate="2 * 2" nodeset="/calculate-type/a" type="string"/>',
                "<h:body/>",
            ],
        )

    def test_non_calculate_type_with_calculation_is_bind_type(self):
        self.assertPyxformXform(
            name="non-calculate-type",
            md="""
            | survey |          |      |             |             |
            |        | type     | name | label       | calculation |
            |        | integer  | a    |             | 2 * 2       |
            """,
            xml__contains=[
                '<bind calculate="2 * 2" nodeset="/non-calculate-type/a" type="int"/>'
            ],
        )

    def test_non_calculate_type_with_calculation_and_no_label_has_no_control(self):
        self.assertPyxformXform(
            name="no-label",
            md="""
                | survey |          |      |             |             |
                |        | type     | name | label       | calculation |
                |        | integer  | a    |             | 2 * 2       |
                """,
            instance__contains=["<a/>"],
            xml__excludes=["input"],
        )

    def test_non_calculate_type_with_calculation_no_warns(self):
        self.assertPyxformXform(
            md="""
            | survey |           |      |             |      |             |
            |        | type      | name | label       | hint | calculation |
            |        | dateTime  | a    |             |      | now()       |
            |        | integer   | b    |             |      | 1 div 1     |
            |        | note      | note | Hello World |      |             |
            """,
            warnings_count=0,
        )

    def test_non_calculate_type_with_hint_and_no_calculation__no_warning(self):
        self.assertPyxformXform(
            md="""
            | survey |           |      |             |           |             |
            |        | type      | name | label       | hint      | calculation |
            |        | dateTime  | a    |             |           | now()       |
            |        | integer   | b    |             | Some hint |             |
            |        | note      | note | Hello World |           |             |
            """,
            warnings_count=0,
        )

    def test_non_calculate_type_with_calculation_and_dynamic_default_no_warns(self):
        self.assertPyxformXform(
            md="""
            | survey |           |      |             |      |             |         |
            |        | type      | name | label       | hint | calculation | default |
            |        | dateTime  | a    |             |      | now()       |         |
            |        | integer   | b    |             |      | 1 div 1     | $(a)    |
            |        | note      | note | Hello World |      |             |         |
            """,
            warnings_count=0,
        )

    def test_non_calculate_type_with_calculation_and_default_no_warns(self):
        self.assertPyxformXform(
            md="""
            | survey |           |      |             |      |             |         |
            |        | type      | name | label       | hint | calculation | default |
            |        | dateTime  | a    |             |      | now()       |         |
            |        | integer   | b    |             |      | 1 div 1     | 1       |
            |        | note      | note | Hello World |      |             |         |
            """,
            warnings_count=0,
        )

    def test_select_type_with_calculation_and_no_label_has_no_control(self):
        self.assertPyxformXform(
            name="calculate-select",
            md="""
                | survey  |                   |      |       |                  |
                |         | type              | name | label | calculation      |
                |         | select_one yes_no | a    |       | concat('a', 'b') |
                | choices |                   |      |       |                  |
                |         | list_name         | name | label |                  |
                |         | yes_no            | yes  | Yes   |                  |
                |         | yes_no            | no   | No    |                  |
                """,
            xml__contains=[
                '<bind calculate="concat(\'a\', \'b\')" nodeset="/calculate-select/a" type="string"/>'
            ],
            instance__contains=["<a/>"],
            xml__excludes=["<select1>"],
        )

    def test_row_without_label_or_calculation_throws_error(self):
        self.assertPyxformXform(
            name="no-label",
            md="""
        | survey |          |      |             |
        |        | type     | name | label       |
        |        | integer  | a    |             |
        """,
            errored=True,
            error__contains=["The survey element named 'a' has no label or hint."],
        )

    def test_calculate_without_calculation__error(self):
        """Should find an error is raised when a calculate question has no calculation."""
        md = """
        | survey |
        | | type      | name | label | calculation |
        | | calculate | q1   | Q1    |             |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=["[row : 2] Missing calculation."],
        )

    def test_calculate_without_calculation_without_default(self):
        self.assertPyxformXform(
            name="calculate-without-calculation-without-default",
            md="""
        | survey |            |      |             |             |         |
        |        | type       | name | label       | calculation | default |
        |        | calculate  | a    |             |             |         |
        """,
            errored=True,
            error__contains=["Missing calculation"],
        )

    def test_calculate_without_calculation_with_default_without_dynamic_default(self):
        self.assertPyxformXform(
            name="calculate-without-calculation-with-default-without-dynamic-default",
            md="""
        | survey |            |      |             |             |         |
        |        | type       | name | label       | calculation | default |
        |        | calculate  | a    |             |             | foo     |
        """,
            errored=True,
            error__contains=["Missing calculation"],
        )

    def test_calculate_without_calculation_with_dynamic_default(self):
        self.assertPyxformXform(
            name="calculate-without-calculation-with-dynamic-default",
            md="""
        | survey |            |      |             |             |          |
        |        | type       | name | label       | calculation | default  |
        |        | calculate  | a    |             |             | random() |
        """,
            instance__contains=["<a/>"],
        )

    def test_round_function__ok(self):
        """Should find that using the round() function does not raise an ODK Validate error."""
        md = """
        | survey |
        | | type      | name | label | calculation     |
        | | decimal   | q1   | Q1    |                 |
        | | calculate | q2   | Q2    | round(${q1}, 0) |
        """
        self.assertPyxformXform(md=md)

    def test_cascading_select_via_calculate__ok(self):
        """Should find that cascading selects can be done via calculate without error."""
        # Easier with choice_filter, but it could be done this way.
        md = """
        | survey |
        | | type          | name | label | relevant   |  calculation          |
        | | select_one c1 | q1   | Q1    |            |                       |
        | | select_one c2 | q2   | Q2    | ${q1}='n1' |                       |
        | | select_one c3 | q3   | Q3    | ${q1}='n2' |                       |
        | | calculate     | q4   | Q4    |            | if(${q1}='n1', ${q2}, if(${q1}='n2', ${q3}, 'Error')) |
        | | select_one c4 | q5   | Q5    | ${q4}='n3' |                       |
        | | select_one c5 | q6   | Q6    | ${q4}='n4' |                       |
        | | select_one c6 | q7   | Q7    | ${q4}='n5' |                       |
        | | select_one c7 | q8   | Q8    | ${q4}='n6' |                       |
        | | calculate     | q9   | Q9    |            | if(${q4}='n3', ${q5}, if(${q4}='n4', ${q6}, if(${q4}='n5', ${q7}, if(${q4}='n6', ${q8}, 'Error')))) |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        | | c1        | n2   | N2    |
        | | c2        | n3   | N3    |
        | | c2        | n4   | N4    |
        | | c3        | n5   | N5    |
        | | c3        | n6   | N6    |
        | | c4        | n7   | N7    |
        | | c4        | n8   | N8    |
        | | c5        | n9   | N9    |
        | | c5        | n10  | N10   |
        | | c6        | n11  | N11   |
        | | c6        | n12  | N12   |
        | | c7        | n13  | N13   |
        | | c7        | n14  | N14   |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_bind_attr("q2", "relevant", " /test_name/q1 ='n1'"),
                xpq.model_instance_bind_attr("q3", "relevant", " /test_name/q1 ='n2'"),
                xpq.model_instance_bind_attr(
                    "q4",
                    "calculate",
                    "if( /test_name/q1 ='n1',  /test_name/q2 , if( /test_name/q1 ='n2',  /test_name/q3 , 'Error'))",
                ),
                xpq.model_instance_bind_attr("q5", "relevant", " /test_name/q4 ='n3'"),
                xpq.model_instance_bind_attr("q6", "relevant", " /test_name/q4 ='n4'"),
                xpq.model_instance_bind_attr("q7", "relevant", " /test_name/q4 ='n5'"),
                xpq.model_instance_bind_attr("q8", "relevant", " /test_name/q4 ='n6'"),
                xpq.model_instance_bind_attr(
                    "q9",
                    "calculate",
                    "if( /test_name/q4 ='n3',  /test_name/q5 , if( /test_name/q4 ='n4',  /test_name/q6 , if( /test_name/q4 ='n5',  /test_name/q7 , if( /test_name/q4 ='n6',  /test_name/q8 , 'Error'))))",
                ),
            ],
        )
