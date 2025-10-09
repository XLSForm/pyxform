from pyxform.validators.pyxform.unique_names import NAMES001

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


class TestRepeatCount(PyxformTestCase):
    """
    Test usages of the survey repeat_count column.
    """

    def test_single_reference__generated_element_same_name__ok(self):
        """Should not have a name clash, the referenced item should be used directly."""
        md = """
        | survey |
        | | type         | name     | label | repeat_count |
        | | integer      | q1_count | Q1    |              |
        | | begin repeat | r1       | R1    | ${q1_count}  |
        | | text         | q2       | Q2    |              |
        | | end repeat   |          |       |              |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # repeat_count target output as normal
                xpq.model_instance_item("q1_count"),
                xpq.model_instance_bind("q1_count", "int"),
                xpq.body_control("q1_count", "input"),
                # no instance element for generated *_count item
                """
                /h:html/h:head/x:model/x:instance/x:test_name[not(./x:r1_count)]
                """,
                # no binding for generated *_count item
                """
                /h:html/h:head/x:model[not(./x:bind[@nodeset='/test_name/r1_count'])]
                """,
                # repeat references existing count element directly.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[
                  @nodeset='/test_name/r1'
                  and @jr:count=' /test_name/q1_count '
                ]
                """,
            ],
        )

    def test_single_reference__generated_element_different_name__ok(self):
        """Should find that a {repeat_name}_count element is generated for the calculation."""
        md = """
        | survey |
        | | type         | name | label | repeat_count |
        | | integer      | q1   | Q1    |              |
        | | begin repeat | r1   | R1    | ${q1}        |
        | | text         | q2   | Q2    |              |
        | | end repeat   |      |       |              |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # repeat_count target output as normal
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.body_control("q1", "input"),
                # no instance element for generated *_count item
                """
                /h:html/h:head/x:model/x:instance/x:test_name[not(./x:r1_count)]
                """,
                # no binding for generated *_count item
                """
                /h:html/h:head/x:model[not(./x:bind[@nodeset='/test_name/r1_count'])]
                """,
                # repeat references existing count element directly.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[
                  @nodeset='/test_name/r1'
                  and @jr:count=' /test_name/q1 '
                ]
                """,
            ],
        )

    def test_expression__generated_element_same_name__error(self):
        """Should find that a duplicate {repeat_name}_count element raises an error."""
        md = """
        | survey |
        | | type               | name     | label | repeat_count                |
        | | select_multiple l1 | r1_count | Q1    |                             |
        | | begin_repeat       | r1       | R1    | count-selected(${r1_count}) |
        | | text               | q2       | Q2    |                             |
        | | end_repeat         |          |       |                             |

        | choices |
        | | list_name | name | label |
        | | l1        | c1   | C1    |
        | | l1        | c2   | C2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[NAMES001.format(value="r1_count")],
        )

    def test_expression__generated_element_different_name__ok(self):
        """Should find that a {repeat_name}_count element is generated for the calculation."""
        # repro for pyxform 781
        md = """
        | survey |
        | | type               | name | label | repeat_count          |
        | | select_multiple l1 | q1   | Q1    |                       |
        | | begin_repeat       | r1   | R1    | count-selected(${q1}) |
        | | text               | q2   | Q2    |                       |
        | | end_repeat         |      |       |                       |

        | choices |
        | | list_name | name | label |
        | | l1        | c1   | C1    |
        | | l1        | c2   | C2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("r1_count"),
                xpq.model_instance_bind("r1_count", "string"),
                xpq.model_instance_bind_attr(
                    "r1_count", "calculate", "count-selected( /test_name/q1 )"
                ),
                xpq.model_instance_bind_attr("r1_count", "readonly", "true()"),
                # repeat references generated repeat_count element.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[
                  @nodeset='/test_name/r1'
                  and @jr:count=' /test_name/r1_count '
                ]
                """,
            ],
        )

    def test_manual_xpath__generated_element_same_name__error(self):
        """Should find that a duplicate {repeat_name}_count element raises an error."""
        md = """
        | survey |
        | | type               | name     | label | repeat_count                          |
        | | select_multiple l1 | r1_count | Q1    |                                       |
        | | begin_repeat       | r1       | R1    | count-selected( /test_name/r1_count ) |
        | | text               | q2       | Q2    |                                       |
        | | end_repeat         |          |       |                                       |

        | choices |
        | | list_name | name | label |
        | | l1        | c1   | C1    |
        | | l1        | c2   | C2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[NAMES001.format(value="r1_count")],
        )

    def test_manual_xpath__generated_element_different_name__ok(self):
        """Should find that a {repeat_name}_count element is generated for the calculation."""
        md = """
        | survey |
        | | type               | name | label | repeat_count                    |
        | | select_multiple l1 | q1   | Q1    |                                 |
        | | begin_repeat       | r1   | R1    | count-selected( /test_name/q1 ) |
        | | text               | q2   | Q2    |                                 |
        | | end_repeat         |      |       |                                 |

        | choices |
        | | list_name | name | label |
        | | l1        | c1   | C1    |
        | | l1        | c2   | C2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("r1_count"),
                xpq.model_instance_bind("r1_count", "string"),
                xpq.model_instance_bind_attr(
                    "r1_count", "calculate", "count-selected( /test_name/q1 )"
                ),
                xpq.model_instance_bind_attr("r1_count", "readonly", "true()"),
                # repeat references generated repeat_count element.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[
                  @nodeset='/test_name/r1'
                  and @jr:count=' /test_name/r1_count '
                ]
                """,
            ],
        )

    def test_constant_integer__generated_element_same_name__error(self):
        """Should find that a duplicate {repeat_name}_count element raises an error."""
        # Seems strange, but according to pyxform 435 it's a javarosa limitation.
        md = """
        | survey |
        | | type         | name     | label | repeat_count |
        | | integer      | r1_count | Q1    |              |
        | | begin_repeat | r1       | R1    | 2            |
        | | text         | q2       | Q2    |              |
        | | end_repeat   |          |       |              |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[NAMES001.format(value="r1_count")],
        )

    def test_constant_integer__generated_element_different_name__ok(self):
        """Should find that a {repeat_name}_count element is generated for the calculation."""
        # Seems strange, but according to pyxform 435 it's a javarosa limitation.
        md = """
        | survey |
        | | type         | name | label | repeat_count |
        | | integer      | q1   | Q1    |              |
        | | begin_repeat | r1   | R1    | 2            |
        | | text         | q2   | Q2    |              |
        | | end_repeat   |      |       |              |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("r1_count"),
                xpq.model_instance_bind("r1_count", "string"),
                xpq.model_instance_bind_attr("r1_count", "calculate", "2"),
                xpq.model_instance_bind_attr("r1_count", "readonly", "true()"),
                # repeat references generated repeat_count element.
                """
                /h:html/h:body/x:group[@ref='/test_name/r1']/x:repeat[
                  @nodeset='/test_name/r1'
                  and @jr:count=' /test_name/r1_count '
                ]
                """,
            ],
        )
