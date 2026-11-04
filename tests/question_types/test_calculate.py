"""
## Calculate traceability.

The scope of this test module is the "calculate" question type, and other question types
with a user-specified "calculation" (which behave similarly to the "calculate" type, and
not to be confused with the column alias "calculate" for "calculation").

Each test should reference one (or more) requirements from these lists.

- Validation
  - CV001: a calculate question must have a calculation and/or a dynamic default.
  - CV002: a calculate/non-calculate question may have a static default.
  - CV003: a calculate question may have control content (label, hint, media, etc).
- Behaviour
  - CB001: for a calculate/non-calculate question, the calculation is emitted in a calculate binding.
  - CB002: for a calculate question, the bind data type is "string".
  - CB003: for a non-calculate question, the bind data type is the question data type.
  - CB004: for a calculate/non-calculate question, a static default is emitted in the primary instance.
  - CB005: for a calculate/non-calculate question, a dynamic default is emitted in a setvalue.
  - CB006: for a calculate question, no control element is emitted.
  - CB007: for a non-calculate question, a control element is emitted only if control content is provided.
"""

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


class TestCalculateParsing(PyxformTestCase):
    def test_calculate__no_calculation__error(self):
        """Should raise an error when no calculation or dynamic default is provided."""
        # CV001
        md = """
        | survey |
        | | type      | name |
        | | calculate | q1   |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=["[row : 2] Missing calculation."],
        )

    def test_calculate__no_calculation__with_static_default__error(self):
        """Should raise an error when no calculation or dynamic default is provided."""
        # CV001
        md = """
        | survey |
        | | type      | name | default |
        | | calculate | q1   | foo     |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=["[row : 2] Missing calculation."],
        )

    def test_calculate__no_calculation__with_dynamic_default__ok(self):
        """Should find that a calculation is not required when a dynamic default is provided."""
        # CV001
        md = """
        | survey |
        | | type      | name | default |
        | | calculate | q1   | 2 * 2   |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_calculate__with_static_default__ok(self):
        """Should find that a calculation may have a static default."""
        # CV002
        md = """
        | survey |
        | | type      | name | calculation | default |
        | | calculate | q1   | 2 * 2       | 3       |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_calculate__with_label__ok(self):
        """Should find that a calculation may have control content."""
        # CV003
        md = """
        | survey |
        | | type      | name | label | calculation |
        | | calculate | q1   | Q1    | 2 * 2       |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

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


class TestCalculateOutput(PyxformTestCase):
    def test_calculate(self):
        """Should find that the bind is string, with the calculation, and no control."""
        # CB001 CB002 CB006
        md = """
        | survey |
        || type      | name | calculation |
        || calculate | q1   | 2 * 2       |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_calculate__with_control_content(self):
        """Should find that no control is emitted."""
        # CB001 CB002 CB006
        md = """
        | survey |
        || type      | name | calculation | {key} |
        || calculate | q1   | 2 * 2       | {val} |
        """
        cases = (
            ("label", "Q1"),
            ("hint", "Q1"),
            ("audio", "Q1.mp3"),
            ("label::English (en)", "Q1"),
        )
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md,
                    xml__xpath_match=[
                        xpq.model_instance_item("q1"),
                        xpq.model_instance_bind("q1", "string"),
                        xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                        xpq.body_empty(),
                    ],
                    warnings_count=0,
                )

    def test_calculate__with_static_default(self):
        """Should find that the static default is in the instance, and the calculation is in a bind."""
        # CB001 CB002 CB004 CB006
        md = """
        | survey |
        || type      | name | calculate | default  |
        || calculate | q1   | 2 * 2     | 3        |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1", "3"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_calculate__with_dynamic_default(self):
        """Should find that the dynamic default is in a setvalue, and the calculation is in a bind."""
        # CB001 CB002 CB005 CB006
        md = """
        | survey |
        || type      | name | calculate | default  |
        || calculate | q1   | 2 * 2     | random() |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.setvalue(
                    path="""h:head/x:model""",
                    ref="/test_name/q1",
                    event="odk-instance-first-load",
                    value="random()",
                ),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_calculate__with_dynamic_default__no_calculation(self):
        """Should find that the default is in a setvalue."""
        # CB001 CB002 CB005 CB006
        md = """
        | survey |
        || type      | name | default  |
        || calculate | q1   | random() |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.setvalue(
                    path="""h:head/x:model""",
                    ref="/test_name/q1",
                    event="odk-instance-first-load",
                    value="random()",
                ),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_non_calculate__integer(self):
        """Should find that the bind is the question type, with the calculation, and no control."""
        # CB001 CB003 CB007
        md = """
        | survey |
        || type      | name | calculation |
        || integer   | q1   | 2 * 2       |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_non_calculate__integer__with_label(self):
        """Should find that the label is in a control."""
        # CB001 CB003 CB007
        md = """
        | survey |
        || type      | name | label | calculation |
        || integer   | q1   | Q1    | 2 * 2       |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.body_label_inline("input", "q1", "Q1"),
            ],
            warnings_count=0,
        )

    def test_non_calculate__integer__with_static_default(self):
        """Should find that the static default is in the instance, and the calculation is in a bind."""
        # CB001 CB003 CB004 CB007
        md = """
        | survey |
        || type      | name | calculation | default |
        || integer   | q1   | 2 * 2       | 3       |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1", "3"),
                xpq.model_instance_bind("q1", "int"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_non_calculate__integer__with_dynamic_default(self):
        """Should find that the dynamic default is in a setvalue, and the calculation is in a bind."""
        # CB001 CB003 CB005 CB007
        md = """
        | survey |
        || type    | name | calculate | default  |
        || integer | q1   | 2 * 2     | random() |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.model_instance_bind_attr("q1", "calculate", "2 * 2"),
                xpq.setvalue(
                    path="""h:head/x:model""",
                    ref="/test_name/q1",
                    event="odk-instance-first-load",
                    value="random()",
                ),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_non_calculate__integer__with_dynamic_default__no_calculation(self):
        """Should find that the default is in a setvalue."""
        # CB003 CB005 CB007
        md = """
        | survey |
        || type    | name | label | default  |
        || integer | q1   | Q1    | random() |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.setvalue(
                    path="""h:head/x:model""",
                    ref="/test_name/q1",
                    event="odk-instance-first-load",
                    value="random()",
                ),
                xpq.body_label_inline("input", "q1", "Q1"),
            ],
            warnings_count=0,
        )

    def test_non_calculate__select(self):
        """Should find that the bind is the question type, with the calculation, and no control."""
        # CB001 CB003 CB007
        md = """
        | survey |
        || type          | name | calculation      |
        || select_one c1 | q1   | concat('a', 'b') |

        | choices |
        || list_name | name | label |
        || c1        | n1   | N1    |
        || c1        | n2   | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "concat('a', 'b')"),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )

    def test_non_calculate__select__with_label(self):
        """Should find that the label is in a control."""
        # CB001 CB003 CB007
        md = """
        | survey |
        || type          | name | label | calculation      |
        || select_one c1 | q1   | Q1    | concat('a', 'b') |

        | choices |
        || list_name | name | label |
        || c1        | n1   | N1    |
        || c1        | n2   | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "concat('a', 'b')"),
                xpq.body_label_inline("select1", "q1", "Q1"),
                xpq.body_select1_itemset("q1"),
            ],
            warnings_count=0,
        )

    def test_non_calculate__select__with_static_default(self):
        """Should find that the static default is in the instance, and the calculation is in a bind."""
        # CB001 CB003 CB004 CB007
        md = """
        | survey |
        || type          | name | label | calculation      | default |
        || select_one c1 | q1   | Q1    | concat('n', '1') | n1      |

        | choices |
        || list_name | name | label |
        || c1        | n1   | N1    |
        || c1        | n2   | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1", "n1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "concat('n', '1')"),
                xpq.body_label_inline("select1", "q1", "Q1"),
                xpq.body_select1_itemset("q1"),
            ],
            warnings_count=0,
        )

    def test_non_calculate__select__with_dynamic_default(self):
        """Should find that the dynamic default is in a setvalue, and the calculation is in a bind."""
        # CB001 CB003 CB005 CB007
        md = """
        | survey |
        || type          | name | label | calculation      | default          |
        || select_one c1 | q1   | Q1    | concat('n', '1') | concat('n', '2') |

        | choices |
        || list_name | name | label |
        || c1        | n1   | N1    |
        || c1        | n2   | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.model_instance_bind_attr("q1", "calculate", "concat('n', '1')"),
                xpq.setvalue(
                    path="""h:head/x:model""",
                    ref="/test_name/q1",
                    event="odk-instance-first-load",
                    value="concat('n', '2')",
                ),
                xpq.body_label_inline("select1", "q1", "Q1"),
                xpq.body_select1_itemset("q1"),
            ],
            warnings_count=0,
        )

    def test_non_calculate__select__with_dynamic_default__no_calculation(self):
        """Should find that the default is in a setvalue."""
        # CB003 CB005 CB007
        md = """
        | survey |
        || type          | name | label | default          |
        || select_one c1 | q1   | Q1    | concat('n', '1') |

        | choices |
        || list_name | name | label |
        || c1        | n1   | N1    |
        || c1        | n2   | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.setvalue(
                    path="""h:head/x:model""",
                    ref="/test_name/q1",
                    event="odk-instance-first-load",
                    value="concat('n', '1')",
                ),
                xpq.body_label_inline("select1", "q1", "Q1"),
                xpq.body_select1_itemset("q1"),
            ],
            warnings_count=0,
        )
