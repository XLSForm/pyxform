# -*- coding: utf-8 -*-
from tests.pyxform_test_case import PyxformTestCase


class EntitiesTest(PyxformTestCase):
    def test_dataset_in_entities_sheet__adds_meta_entity_block(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__xpath_match=["/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity"],
        )

    def test_multiple_dataset_rows_in_entities_sheet__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |      |       |
            |          | type    | name | label |
            |          | text    | a    | A     |
            | entities |         |      |       |
            |          | dataset |      |       |
            |          | trees   |      |       |
            |          | shovels |      |       |
            """,
            errored=True,
            error__contains=[
                "This version of pyxform only supports declaring a single entity per form. Please make sure your entities sheet only declares one entity."
            ],
        )

    def test_dataset_in_entities_sheet__adds_dataset_attribute_to_entity(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@dataset = "trees"]'
            ],
        )

    def test_dataset_with_reserved_prefix__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | __sweet | a     |       |
            """,
            errored=True,
            error__contains=[
                "Invalid dataset name: '__sweet' starts with reserved prefix __."
            ],
        )

    def test_dataset_with_invalid_xml_name__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | $sweet  | a     |       |
            """,
            errored=True,
            error__contains=[
                "Invalid dataset name: '$sweet'. Dataset names must begin with a letter, colon, or underscore. Other characters can include numbers or dashes."
            ],
        )

    def test_dataset_with_period_in_name__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | s.w.eet | a     |       |
            """,
            errored=True,
            error__contains=[
                "Invalid dataset name: 's.w.eet'. Dataset names may not include periods."
            ],
        )

    def test_worksheet_name_close_to_entities__produces_warning(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entitoes |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            warnings__contains=[
                "When looking for a sheet named 'entities', the following sheets with similar names were found: 'entitoes'."
            ],
        )

    def test_dataset_in_entities_sheet__defaults_to_always_creating(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@create = "1"]'
            ],
        )

    def test_create_if_in_entities_sheet__puts_expression_on_bind(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |                      |       |
            |          | type    | name                 | label |
            |          | text    | a                    | A     |
            | entities |         |                      |       |
            |          | dataset | create_if            | label |
            |          | trees   | string-length(a) > 3 | a     |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@create" and @calculate = "string-length(a) > 3"]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@create = "1"]',
            ],
        )

    def test_dataset_in_entities_sheet__adds_id_attribute_and_model_nodes_to_entity(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@id = ""]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@id" and @type = "string" and @readonly = "true()"]',
                '/h:html/h:head/x:model/x:setvalue[@event = "odk-instance-first-load" and @type = "string" and @ref = "/data/meta/entity/@id" and @value = "uuid()"]',
            ],
        )

    def test_label_in_entities_sheet__adds_label_and_bind_to_entity(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__xpath_match=[
                "/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity/x:label",
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/label" and @type = "string" and @readonly = "true()" and @calculate = "a"]',
            ],
        )

    def test_label_and_create_if_in_entities_sheet__expand_node_selectors_to_xpath(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |                         |
            |          | type    | name  | label                   |
            |          | text    | a     | A                       |
            | entities |         |       |                         |
            |          | dataset | label | create_if               |
            |          | trees   | ${a}  | string-length(${a}) > 3 |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@create" and @calculate = "string-length( /data/a ) > 3"]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/label" and @type = "string" and @readonly = "true()" and @calculate = " /data/a "]',
            ],
        )

    def test_entity_label__required(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset |       |       |
            |          | trees   |       |       |
            """,
            errored=True,
            error__contains=["The entities sheet is missing the required label column."],
        )

    def test_dataset_in_entities_sheet__adds_entities_namespace(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_entities_namespace__omitted_if_no_entities_sheet(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            """,
            xml__excludes=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_dataset_in_entities_sheet__adds_entities_version(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            | entities |         |       |       |
            |          | dataset | label |       |
            |          | trees   | a     |       |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model[@entities:entities-version = "2022.1.0"]'
            ],
        )

    def test_entities_version__omitted_if_no_entities_sheet(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |
            |          | type    | name  | label |
            |          | text    | a     | A     |
            """,
            xml__excludes=['entities:entities-version = "2022.1.0"'],
        )

    def test_saveto_column__added_to_xml(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | foo     |
            | entities |         |       |       |         |
            |          | dataset | label |       |         |
            |          | trees   | a     |       |         |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/a" and @entities:saveto = "foo"]'
            ],
        )

    def test_saveto_without_entities_sheet__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | foo     |
            """,
            errored=True,
            error__contains=[
                "To save entity properties using the save_to column, you must add an entities sheet and declare an entity."
            ],
        )

    def test_name_in_saveto_column__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | name    |
            | entities |         |       |       |         |
            |          | dataset | label |       |         |
            |          | trees   | a     |       |         |
            """,
            errored=True,
            error__contains=[
                "[row : 2] Invalid save_to name: the entity property name 'name' is reserved."
            ],
        )

    def test_label_in_saveto_column__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | label   |
            | entities |         |       |       |         |
            |          | dataset | label |       |         |
            |          | trees   | a     |       |         |
            """,
            errored=True,
            error__contains=[
                "[row : 2] Invalid save_to name: the entity property name 'label' is reserved."
            ],
        )

    def test_system_prefix_in_saveto_column__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | __a     |
            | entities |         |       |       |         |
            |          | dataset | label |       |         |
            |          | trees   | a     |       |         |
            """,
            errored=True,
            error__contains=[
                "[row : 2] Invalid save_to name: the entity property name '__a' starts with reserved prefix __."
            ],
        )

    def test_invalid_xml_identifier_in_saveto_column__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |       |       |         |
            |          | type    | name  | label | save_to |
            |          | text    | a     | A     | $a      |
            | entities |         |       |       |         |
            |          | dataset | label |       |         |
            |          | trees   | a     |       |         |
            """,
            errored=True,
            error__contains=[
                "[row : 2] Invalid save_to name: '$a'. Entity property names must begin with a letter, colon, or underscore. Other characters can include numbers, dashes, and periods."
            ],
        )

    def test_saveto_on_group__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |             |       |       |         |
            |          | type        | name  | label | save_to |
            |          | begin_group | a     | A     | a       |
            |          | end_group   |       |       |         |
            | entities |             |       |       |         |
            |          | dataset     | label |       |         |
            |          | trees       | a     |       |         |
            """,
            errored=True,
            error__contains=[
                "[row : 2] Groups and repeats can't be saved as entity properties."
            ],
        )
