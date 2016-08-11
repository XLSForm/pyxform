from pyxform_test_case import PyxformTestCase


class ExternalCSVInstancesTest(PyxformTestCase):
    def test_external_csv_instances(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="ecsv",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          |
            |        | select_one_from_file cities.csv              | city           | City           |
            |        | select_multiple_from_file neighbourhoods.csv | neighbourhoods | Neighbourhoods |
            """,  # noqa
            xml__contains=[
                """<instance id="cities" src="jr://file-csv/cities.csv">
        <root>
          <item>
            <name/>
            <label/>
          </item>
        </root>
      </instance>""",  # noqa
                '<select1 ref="/ecsv/city">',
                '<itemset nodeset="instance(\'cities\')/root/item">',
                """<instance id="neighbourhoods" src="jr://file-csv/neighbourhoods.csv">
        <root>
          <item>
            <name/>
            <label/>
          </item>
        </root>
      </instance>""",  # noqa
                '<select ref="/ecsv/neighbourhoods">',
                '<itemset nodeset="instance(\'neighbourhoods\')/root/item">',
            ],
        )

    def test_external_csv_instances_w_choice_filter(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="ecsv",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          | choice_filter |
            |        | select_one_from_file cities.csv              | city           | City           |               |
            |        | select_multiple_from_file neighbourhoods.csv | neighbourhoods | Neighbourhoods | city=${city}  |
            """,  # noqa
            xml__contains=[
                """<instance id="cities" src="jr://file-csv/cities.csv">
        <root>
          <item>
            <name/>
            <label/>
          </item>
        </root>
      </instance>""",  # noqa
                '<select1 ref="/ecsv/city">',
                """<instance id="neighbourhoods" src="jr://file-csv/neighbourhoods.csv">
        <root>
          <item>
            <name/>
            <label/>
          </item>
        </root>
      </instance>""",  # noqa
                '<select ref="/ecsv/neighbourhoods">',
                '<itemset nodeset="instance(\'neighbourhoods\')/root/item[city= /ecsv/city ]">',
            ],
        )


class ExternalXMLInstancesTest(PyxformTestCase):
    def test_external_xml_instances(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="exml",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          |
            |        | select_one_from_file cities.xml              | city           | City           |
            |        | select_multiple_from_file neighbourhoods.xml | neighbourhoods | Neighbourhoods |
            """,  # noqa
            xml__contains=[
                """<instance id="cities" src="jr://file-xml/cities.xml">
        <root>
          <item>
            <name/>
            <label/>
          </item>
        </root>
      </instance>""",  # noqa
                '<select1 ref="/exml/city">',
                '<itemset nodeset="instance(\'cities\')/root/item">',
                """<instance id="neighbourhoods" src="jr://file-xml/neighbourhoods.xml">
        <root>
          <item>
            <name/>
            <label/>
          </item>
        </root>
      </instance>""",  # noqa
                '<select ref="/exml/neighbourhoods">',
                '<itemset nodeset="instance(\'neighbourhoods\')/root/item">',
            ],
        )


class InvalidExternalFileInstancesTest(PyxformTestCase):
    def test_external_other_extension_instances(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="epdf",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          |
            |        | select_one_from_file cities.pdf              | city           | City           |
            |        | select_multiple_from_file neighbourhoods.pdf | neighbourhoods | Neighbourhoods |
            """,  # noqa
            errored=True,
            error_contains=["should be a choices sheet in this xlsform"],
        )

    def test_external_choices_sheet_included_instances(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="epdf",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          |
            |        | select_one_from_file cities.pdf              | city           | City           |
            |        | select_multiple_from_file neighbourhoods.pdf | neighbourhoods | Neighbourhoods |

            | choices |
            |         | list name | name  | label |
            |         | fruits    | apple | Apple |
            """,  # noqa
            errored=True,
            error__contains=["List name not in choices sheet: cities.pdf"],
        )
