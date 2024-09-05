from pyxform import constants as co

from tests.pyxform_test_case import PyxformTestCase


class EntitiesUpdateTest(PyxformTestCase):
    def test_basic_entity_update_building_blocks(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |            |         |
            |          | type         | name       | label   |
            |          | text         | id         | Tree id |
            |          | text         | a          | A       |
            |          | csv-external | trees      |         |
            | entities |              |            |         |
            |          | dataset      | entity_id  |         |
            |          | trees        | ${id}      |         |
            """,
            xml__xpath_match=[
                "/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity",
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@dataset = "trees"]',
                # defaults to always updating if an entity_id is specified
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@update = "1"]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@id = ""]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@id" and @type = "string" and @readonly = "true()" and @calculate = " /data/id "]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@baseVersion = ""]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@baseVersion" and @type = "string" and @readonly = "true()" and @calculate = "instance(\'trees\')/root/item[name= /data/id ]/__version"]',
                '/h:html/h:head/x:model[@entities:entities-version = "2023.1.0"]',
            ],
            xml__xpath_count=[
                ("/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity/x:label", 0),
                ("/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity/@create", 0),
                ("/h:html/h:head/x:model/x:setvalue", 0),
            ],
            xml__contains=['xmlns:entities="http://www.opendatakit.org/xforms/entities"'],
        )

    def test_entity_id_with_creation_condition_only__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |            |           |
            |          | type    | name       | label     |
            |          | text    | id         | Tree id   |
            |          | text    | a          | A         |
            | entities |         |            |           |
            |          | dataset | entity_id  | create_if |
            |          | trees   | ${id}      | true()    |
            """,
            errored=True,
            error__contains=[
                "The entities sheet can't specify an entity creation condition and an entity_id without also including an update condition."
            ],
        )

    def test_update_condition_without_entity_id__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |            |           |
            |          | type    | name       | label     |
            |          | text    | id         | Tree id   |
            |          | text    | a          | A         |
            | entities |         |            |           |
            |          | dataset | update_if  |           |
            |          | trees   | true()     |           |
            """,
            errored=True,
            error__contains=[
                "The entities sheet is missing the entity_id column which is required when updating entities."
            ],
        )

    def test_update_and_create_conditions_without_entity_id__errors(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |         |            |            |
            |          | type    | name       | label      |
            |          | text    | id         | Tree id    |
            |          | integer | a          | A          |
            | entities |         |            |            |
            |          | dataset | update_if  | create_if  |
            |          | trees   | ${id} != ''| ${id} = '' |
            """,
            errored=True,
            error__contains=[
                "The entities sheet is missing the entity_id column which is required when updating entities."
            ],
        )

    def test_create_if_with_entity_id_in_entities_sheet__puts_expression_on_bind(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |                      |           |
            |          | type         | name                 | label     |
            |          | text         | id                   | Tree id   |
            |          | text         | a                    | A         |
            |          | csv-external | trees                |           |
            | entities |              |                      |           |
            |          | dataset      | update_if            | entity_id |
            |          | trees        | string-length(a) > 3 | ${id}     |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@update" and @calculate = "string-length(a) > 3"]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@update = "1"]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@id" and @type = "string" and @readonly = "true()" and @calculate = " /data/id "]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@baseVersion = ""]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@baseVersion" and @type = "string" and @readonly = "true()" and @calculate = "instance(\'trees\')/root/item[name= /data/id ]/__version"]',
            ],
            xml__xpath_count=[("/h:html/h:head/x:model/x:setvalue", 0)],
        )

    def test_update_and_create_conditions_with_entity_id__puts_both_in_bind_calculations(
        self,
    ):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |            |            |           |
            |          | type         | name       | label      |           |
            |          | text         | id         | Tree id    |           |
            |          | integer      | a          | A          |           |
            |          | csv-external | trees      |            |           |
            | entities |              |            |            |           |
            |          | dataset      | update_if  | create_if  | entity_id |
            |          | trees        | id != ''   | id = ''    | ${id}     |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@update" and @calculate = "id != \'\'"]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@update = "1"]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@create" and @calculate = "id = \'\'"]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@create = "1"]',
                '/h:html/h:head/x:model/x:setvalue[@event = "odk-instance-first-load" and @type = "string" and @ref = "/data/meta/entity/@id" and @value = "uuid()"]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@id" and @type = "string" and @readonly = "true()" and @calculate = " /data/id "]',
                '/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity[@baseVersion = ""]',
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/@baseVersion" and @type = "string" and @readonly = "true()" and @calculate = "instance(\'trees\')/root/item[name= /data/id ]/__version"]',
            ],
        )

    def test_entity_id_and_label__updates_label(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |            |         |
            |          | type         | name       | label   |
            |          | text         | id         | Tree id |
            |          | text         | a          | A       |
            |          | csv-external | trees      |         |
            | entities |              |            |         |
            |          | dataset      | entity_id  | label   |
            |          | trees        | ${id}      | a       |
            """,
            xml__xpath_match=[
                "/h:html/h:head/x:model/x:instance/x:data/x:meta/x:entity/x:label",
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/meta/entity/label" and @type = "string" and @readonly = "true()" and @calculate = "a"]',
            ],
        )

    def test_save_to_with_entity_id__puts_save_tos_on_bind(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |            |         |         |
            |          | type         | name       | label   | save_to |
            |          | text         | id         | Tree id |         |
            |          | text         | a          | A       | foo     |
            |          | csv-external | trees      |         |         |
            | entities |              |            |         |         |
            |          | dataset      | entity_id  |         |         |
            |          | trees        | ${id}      |         |         |
            """,
            xml__xpath_match=[
                '/h:html/h:head/x:model/x:bind[@nodeset = "/data/a" and @entities:saveto = "foo"]'
            ],
        )

    def test_entities_offline_opt_in__yes(self):
        """Should find offline spec version and trunk/branch props/binds, if opted-in."""
        self.assertPyxformXform(
            md="""
            | survey   |
            |          | type | name | label   |
            |          | text | id   | Tree id |
            |          | text | q1   | Q1      |
            | entities |
            |          | dataset | entity_id | offline |
            |          | trees   | ${id}     | yes     |
            """,
            xml__xpath_match=[
                f"""
                  /h:html/h:head/x:model[
                    @entities:entities-version = "{co.ENTITIES_OFFLINE_VERSION}"
                  ]
                """,
                """
                  /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[
                    @trunkVersion = ''
                    and @branchId = ''
                  ]
                """,
                """
                  /h:html/h:head/x:model/x:bind[
                    @nodeset = '/test_name/meta/entity/@trunkVersion'
                    and @calculate = "instance('trees')/root/item[name= /test_name/id ]/__trunkVersion"
                    and @type = 'string'
                    and @readonly = 'true()'
                  ]
                """,
                """
                  /h:html/h:head/x:model/x:bind[
                    @nodeset = '/test_name/meta/entity/@branchId'
                    and @calculate = "instance('trees')/root/item[name= /test_name/id ]/__branchId"
                    and @type = 'string'
                    and @readonly = 'true()'
                  ]
                """,
            ],
        )

    def test_entities_offline_opt_in__no(self):
        """Should not find update spec version and trunk/branch props/binds, if not opted-in."""
        cases = (
            """
            | entities |
            |          | dataset | entity_id |
            |          | trees   | ${id}     |
            """,
            """
            | entities |
            |          | dataset | entity_id | offline |
            |          | trees   | ${id}     | no      |
            """,
        )
        survey = """
        | survey   |
        |          | type | name | label   |
        |          | text | id   | Tree id |
        |          | text | q1   | Q1      |
        """
        for i, case in enumerate(cases):
            with self.subTest(msg=i):
                self.assertPyxformXform(
                    md=survey + case,
                    xml__xpath_match=[
                        f"""
                          /h:html/h:head/x:model[
                            @entities:entities-version = "{co.ENTITIES_UPDATE_VERSION}"
                          ]
                        """,
                        """
                          /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[
                            not(@trunkVersion)
                            and not(@branchId)
                          ]
                        """,
                        """
                          /h:html/h:head/x:model[
                            not(x:bind[@nodeset = '/test_name/meta/entity/@trunkVersion'])
                          ]
                        """,
                        """
                          /h:html/h:head/x:model[
                            not(x:bind[@nodeset = '/test_name/meta/entity/@branchId'])
                          ]
                        """,
                    ],
                )
