from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq


def xp_model_instance_with_csv_src_no_items(iid: str) -> str:
    return f"""
      /h:html/h:head/x:model/x:instance[
        @id='{iid}' and @src='jr://file-csv/{iid}.csv' and not(./x:root/x:item)
      ]
    """


def xp_body_select_search_appearance(
    qname: str, appearance: str = "search('my_file')"
) -> str:
    """The select has a 'search' appearance attribute."""
    return f"""
          /h:html/h:body/x:select1[
            @ref='/test_name/{qname}'
            and @appearance="{appearance}"
          ]
        """


def xp_body_select_config_choice_inline(qname: str, cvname: str, clname: str) -> str:
    """The inline choice item has an inline (non-translated) label."""
    return f"""
          /h:html/h:body/x:select1[@ref='/test_name/{qname}']/x:item[
            ./x:value/text()='{cvname}'
            and ./x:label/text()='{clname}'
          ]
        """


def xp_body_select_config_choice_itext(qname: str, cname: str, cvname: str) -> str:
    """The inline choice item has an itext (translated) label."""
    return f"""
          /h:html/h:body/x:select1[@ref='/test_name/{qname}']/x:item[
            ./x:value/text()='{cvname}'
            and ./x:label[@ref="jr:itext('{cname}-0')"]
          ]
        """


class TestTranslations(PyxformTestCase):
    """
    Translations behaviour with the search() appearance.

    The search() appearance is a Collect-only feature, so ODK Validate is run for these
    tests to try and ensure that the output will be accepted by Collect. In particular,
    the search() appearance requires in-line (body) items for choices.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.run_odk_validate = True

    def test_shared_choice_list(self):
        """Should include translation for search() items, when sharing the choice list"""
        md = """
        | survey  |               |       |            |           |                   |
        |         | type          | name  | label::en  | label::fr | appearance        |
        |         | select_one c1 | q1    | Question 1 | Chose 1   | search('my_file') |
        |         | select_one c1 | q2    | Question 2 | Chose 2   | search('my_file', 'matches', 'filtercol', 'x1') |
        | choices |               |       |           |           |
        |         | list_name     | name  | label::en | label::fr |
        |         | c1            | id    | label_en  | label_fr  |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_itext("q1", "c1", "id"),
                xp_body_select_search_appearance(
                    "q2", "search('my_file', 'matches', 'filtercol', 'x1')"
                ),
                xp_body_select_config_choice_itext("q2", "c1", "id"),
                xpc.model_itext_choice_text_label_by_pos("en", "c1", ("label_en",)),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("label_fr",)),
            ],
            xml__xpath_count=[(xpq.model_instance_exists("c1"), 0)],
        )

    def test_usage_with_other_selects(self):
        """Should include translation for search() items, when used with other selects"""
        md = """
        | survey  |               |       |            |           |                   |
        |         | type          | name  | label::en  | label::fr | appearance        |
        |         | select_one c1 | q1    | Question 1 | Chose 1   | search('my_file') |
        |         | select_one c2 | q2    | Question 2 | Chose 2   |                   |
        | choices |               |       |            |           |
        |         | list_name     | name  | label::en | label::fr |
        |         | c1            | id    | label_en  | label_fr  |
        |         | c2            | na    | la-e      | la-f      |
        |         | c2            | nb    | lb-e      | lb-f      |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_itext("q1", "c1", "id"),
                xpc.model_itext_choice_text_label_by_pos("en", "c1", ("label_en",)),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("label_fr",)),
                xpc.model_instance_choices_itext("c2", ("na", "nb")),
                xpc.model_itext_choice_text_label_by_pos("en", "c2", ("la-e", "lb-e")),
                xpc.model_itext_choice_text_label_by_pos("fr", "c2", ("la-f", "lb-f")),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("c1"), 0),
            ],
        )

    def test_usage_with_other_selects__invalid_list_reuse_by_non_search_question(self):
        """By design, q2 won't pull data but the test is to document output behaviour."""
        md = """
        | survey  |               |       |            |           |                   |
        |         | type          | name  | label::en  | label::fr | appearance        |
        |         | select_one c1 | q1    | Question 1 | Chose 1   | search('my_file') |
        |         | select_one c1 | q2    | Question 2 | Chose 2   |                   |
        | choices |               |       |           |
        |         | list_name     | name  | label     |
        |         | c1            | id    | label     |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=["Question 'q1' uses the 'search' appearance"],
        )

    def test_single_question_usage(self):
        """Should include translation for search() items, edge case of single question"""
        md = """
        | survey  |               |       |            |           |                   |
        |         | type          | name  | label::en  | label::fr | appearance        |
        |         | select_one c1 | q1    | Question 1 | Chose 1   | search('my_file') |
        | choices |               |       |           |           |
        |         | list_name     | name  | label::en | label::fr |
        |         | c1            | id    | label_en  | label_fr  |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_itext("q1", "c1", "id"),
                xpc.model_itext_choice_text_label_by_pos("en", "c1", ("label_en",)),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1", ("label_fr",)),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("c1"), 0),
            ],
        )

    def test_additional_static_choices(self):
        """Should include translation for search() items, when adding static choices"""
        md = """
        | survey  |               |       |            |           |                   |
        |         | type          | name  | label::en  | label::fr | appearance        |
        |         | select_one c1 | q1    | Question 1 | Chose 1   | search('my_file') |
        | choices |               |       |           |           |
        |         | list_name     | name  | label::en | label::fr |
        |         | c1            | id    | label_en  | label_fr  |
        |         | c1            | 0     | l0-e      | l0-f      |
        |         | c1            | 1     | l1-e      | l1-f      |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_itext("q1", "c1", "id"),
                xpc.model_itext_choice_text_label_by_pos(
                    "en", "c1", ("label_en", "l0-e", "l1-e")
                ),
                xpc.model_itext_choice_text_label_by_pos(
                    "fr", "c1", ("label_fr", "l0-f", "l1-f")
                ),
            ],
            xml__xpath_count=[(xpq.model_instance_exists("c1"), 0)],
        )

    def test_name_clashes(self):
        """Should include translation for search() items, avoids any name clashes."""
        md = """
        | survey  |                 |       |            |           |                   |
        |         | type            | name  | label::en  | label::fr | appearance        |
        |         | select_one c1-0 | c1-0  | Question 1 | Chose 1   | search('my_file') |
        | choices |               |       |            |           |
        |         | list_name     | name  | label::en  | label::fr |
        |         | c1-0          | id    | label_en   | label_fr  |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_body_select_search_appearance("c1-0"),
                xp_body_select_config_choice_itext("c1-0", "c1-0", "id"),
                xpc.model_itext_choice_text_label_by_pos("en", "c1-0", ("label_en",)),
                xpc.model_itext_choice_text_label_by_pos("fr", "c1-0", ("label_fr",)),
            ],
            xml__xpath_count=[(xpq.model_instance_exists("c1"), 0)],
        )

    def test_search_and_select_xlsx(self):
        """Test to replace the old XLSX-based test fixture, 'search_and_select.xlsx'"""
        md = """
        | survey  |                   |            |                |                  |
        |         | type              | name       | label          | appearance       |
        |         | select_one fruits | fruit      | Choose a fruit | search('fruits') |
        |         | note              | note_fruit | The fruit ${fruit} pulled from csv | |
        | choices |               |          |       |
        |         | list_name     | name     | label |
        |         | fruits        | name_key | name  |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                "/h:html/h:head/x:model[not(descendant::x:itext)]",
                """
                /h:html/h:body/x:select1[
                  @ref='/test_name/fruit'
                  and @appearance="search('fruits')"
                ]/x:item[
                  ./x:value/text()='name_key'
                  and ./x:label/text()='name'
                ]
                """,
                xpq.model_instance_bind("fruit", "string"),
                xpq.model_instance_bind("note_fruit", "string"),
                "/h:html/h:body/x:input[@ref='/test_name/note_fruit']",
            ],
            xml__xpath_count=[(xpq.model_instance_exists("c1"), 0)],
        )


class TestSecondaryInstances(PyxformTestCase):
    """
    Test behaviour of the search() appearance with other sources of secondary instances.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.run_odk_validate = True

    def test_pulldata_same_file(self):
        """Should generate pulldata instance, and search elements in the body only."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | calculation |
        |         | select_one s1 | q1   | Q1    | search('my_file') |             |
        |         | calculate     | p1   |       |                   | pulldata('my_file', 'this', 'that', ${q1}) |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "p1",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_pulldata_same_file__multiple_search(self):
        """Should generate pulldata instance, and search elements in the body only."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | calculation |
        |         | select_one s1 | q1   | Q1    | search('my_file') |             |
        |         | calculate     | p1   |       |                   | pulldata('my_file', 'this', 'that', ${q1}) |
        |         | select_one s1 | q2   | Q2    | search('my_file') |             |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "p1",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
                xp_body_select_search_appearance("q2"),
                xp_body_select_config_choice_inline("q2", "na", "la"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_pulldata_same_file__multiple_search__translation(self):
        """Should generate pulldata instance, and search elements in the body and itext."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | calculation |
        |         | select_one s1 | q1   | Q1    | search('my_file') |             |
        |         | calculate     | p1   |       |                   | pulldata('my_file', 'this', 'that', ${q1}) |
        |         | select_one s1 | q2   | Q2    | search('my_file') |             |
        | choices |           |      |           |
        |         | list_name | name | label::en |
        |         | s1        | na   | la        |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "p1",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xp_body_select_search_appearance("q1"),
                xpc.model_itext_choice_text_label_by_pos("en", "s1", ("la",)),
                xp_body_select_config_choice_itext("q1", "s1", "na"),
                xp_body_select_search_appearance("q2"),
                xp_body_select_config_choice_itext("q2", "s1", "na"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_pulldata_same_file__multiple_search_and_pulldata(self):
        """Should generate pulldata instances, and search elements in the body only."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | calculation |
        |         | select_one s1 | q1   | Q1    | search('my_file') |             |
        |         | calculate     | p1   |       |                   | pulldata('my_file', 'this', 'that', ${q1}) |
        |         | select_one s1 | q2   | Q2    | search('my_file') |             |
        |         | calculate     | p2   |       |                   | pulldata('my_file', 'this', 'that', ${q2}) |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "p1",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xpq.model_instance_bind_attr(
                    "p2",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q2 )",
                ),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
                xp_body_select_search_appearance("q2"),
                xp_body_select_config_choice_inline("q2", "na", "la"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_pulldata_same_file__multiple_search__different_config(self):
        """Should generate pulldata instance, and search elements in the body only."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | calculation |
        |         | select_one s1 | q1   | Q1    | search('my_file') |             |
        |         | calculate     | p1   |       |                   | pulldata('my_file', 'this', 'that', ${q1}) |
        |         | select_one s2 | q2   | Q2    | search('my_file') |             |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        |         | s2        | nb   | lb    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "p1",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
                xp_body_select_search_appearance("q2"),
                xp_body_select_config_choice_inline("q2", "nb", "lb"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
                (xpq.model_instance_exists("s2"), 0),
            ],
        )

    def test_pulldata_same_file__multiple_search__static_choice(self):
        """Should generate pulldata instance, and search elements in the body only."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | calculation |
        |         | select_one s1 | q1   | Q1    | search('my_file') |             |
        |         | calculate     | p1   |       |                   | pulldata('my_file', 'this', 'that', ${q1}) |
        |         | select_one s1 | q2   | Q2    | search('my_file') |             |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        |         | s1        | 0    | lb    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "p1",
                    "calculate",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
                xp_body_select_config_choice_inline("q1", "0", "lb"),
                xp_body_select_search_appearance("q2"),
                xp_body_select_config_choice_inline("q2", "na", "la"),
                xp_body_select_config_choice_inline("q2", "0", "lb"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_pulldata_same_file__constraint(self):
        """Should generate pulldata instance, and search elements in the body only."""
        md = """
        | survey  |               |      |       |                   |             |
        |         | type          | name | label | appearance        | constraint  |
        |         | select_one s1 | q1   | Q1    | search('my_file') | pulldata('my_file', 'this', 'that', ${q1}) |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xpq.model_instance_bind_attr(
                    "q1",
                    "constraint",
                    "pulldata('my_file', 'this', 'that',  /test_name/q1 )",
                ),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_xmlexternal_same_file(self):
        """Should generate xml-external instance, and search elements in the body only."""
        md = """
        | survey  |               |         |       |                   |
        |         | type          | name    | label | appearance        |
        |         | select_one s1 | q1      | Q1    | search('my_file') |
        |         | xml-external  | my_file |       |                   |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance[
                    @id='my_file' and @src='jr://file/my_file.xml' and not(./x:root/x:item)
                  ]
                """,
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_csvexternal_same_file(self):
        """Should generate csv-external instance, and search elements in the body only."""
        md = """
        | survey  |               |         |       |                   |
        |         | type          | name    | label | appearance        |
        |         | select_one s1 | q1      | Q1    | search('my_file') |
        |         | csv-external  | my_file |       |                   |
        | choices |           |      |       |
        |         | list_name | name | label |
        |         | s1        | na   | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_select_from_file__search_on_different_question(self):
        """Should generate select-from-file instance, and search elements in the body only."""
        md = """
        | survey  |                                  |      |       |                   |
        |         | type                             | name | label | appearance        |
        |         | select_one s1                    | q1   | Q1    | search('my_file') |
        |         | select_one_from_file my_file.csv | q2   | Q2    |                   |
        | choices |           |       |       |
        |         | list_name | name  | label |
        |         | s1        | na    | la    |
        """
        self.assertPyxformXform(
            md=md,
            run_odk_validate=self.run_odk_validate,
            xml__xpath_match=[
                xp_model_instance_with_csv_src_no_items("my_file"),
                xp_body_select_search_appearance("q1"),
                xp_body_select_config_choice_inline("q1", "na", "la"),
                xpq.body_select1_itemset("q2"),
            ],
            xml__xpath_count=[
                (xpq.model_instance_exists("s1"), 0),
            ],
        )

    def test_select_from_file__search_on_same_question(self):
        """Should raise an error, since this combination is not supported."""
        md = """
        | survey  |                                  |      |       |                   |
        |         | type                             | name | label | appearance        |
        |         | select_one_from_file my_file.csv | q1   | Q1    | search('my_file') |
        | choices |           |       |       |
        |         | list_name | name  | label |
        |         | my_file   | na    | la    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                "Question 'q1' is a select from file type, with a 'search' appearance."
            ],
        )
