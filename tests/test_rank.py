"""
Test rank widget.
"""

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


class RangeWidgetTest(PyxformTestCase):
    def test_rank(self):
        self.assertPyxformXform(
            md="""
            | survey |              |          |       |
            |        | type         | name     | label |
            |        | rank mylist  | order    | Rank  |
            | choices|              |          |       |
            |        | list_name    | name     | label |
            |        | mylist       | a        | A     |
            |        | mylist       | b        | B     |
            """,
            xml__xpath_match=[
                xpc.model_instance_choices_label("mylist", (("a", "A"), ("b", "B"))),
                xpq.body_odk_rank_itemset("order"),  # also an implicit test for xmlns:odk
                "/h:html/h:head/x:model/x:bind[@nodeset='/test_name/order' and @type='odk:rank']",
            ],
        )

    def test_rank_filter(self):
        self.assertPyxformXform(
            name="data",
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
                'xmlns:odk="http://www.opendatakit.org/xforms"',
                '<bind nodeset="/data/order" type="odk:rank"/>',
                '<instance id="mylist">',
                "<color>red</color>",
                "<name>a</name>",
                "<color>blue</color>",
                "<name>b</name>",
                """<odk:rank ref="/data/order">
      <label>Rank</label>
      <itemset nodeset="instance('mylist')/root/item[color='blue']">
        <value ref="name"/>
        <label ref="label"/>
      </itemset>
    </odk:rank>""",
            ],
        )

    def test_rank_translations(self):
        """Should find itext/translations for rank, using itemset method."""
        self.assertPyxformXform(
            md="""
            | survey |              |          |       |                    |
            |        | type         | name     | label | label::French (fr) |
            |        | rank mylist  | order    | Rank  | Ranger             |
            | choices|              |          |       |
            |        | list_name    | name     | label | label::French (fr) |
            |        | mylist       | a        | A     |  AA                |
            |        | mylist       | b        | B     |  BB                |
            """,
            xml__xpath_match=[
                xpc.model_instance_choices_itext("mylist", ("a", "b")),
                xpq.body_odk_rank_itemset("order"),  # also an implicit test for xmlns:odk
                "/h:html/h:head/x:model/x:bind[@nodeset='/test_name/order' and @type='odk:rank']",
                # All itemset translations.
                xpc.model_itext_choice_text_label_by_pos("default", "mylist", ("A", "B")),
                xpc.model_itext_choice_text_label_by_pos(
                    "French (fr)", "mylist", ("AA", "BB")
                ),
                # No non-itemset translations.
                xpc.model_itext_no_text_by_id("default", "/test_name/order/a:label"),
                xpc.model_itext_no_text_by_id("default", "/test_name/order/b:label"),
                xpc.model_itext_no_text_by_id("French (fr)", "/test_name/order/a:label"),
                xpc.model_itext_no_text_by_id("French (fr)", "/test_name/order/b:label"),
            ],
        )
