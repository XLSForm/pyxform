# -*- coding: utf-8 -*-
from tests.pyxform_test_case import PyxformTestCase


class EntitiesTest(PyxformTestCase):
    def test_dataset_in_entities_sheet__adds_meta_entity_block(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |      |       |
            |          | type    | name | label |
            |          | text    | a    | A     |
            | entities |         |      |       |
            |          | dataset |      |       |
            |          | trees   |      |       |
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
