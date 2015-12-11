from pyxform_test_case import PyxformTestCase


class AliasesTests(PyxformTestCase):
    def test_value_and_name(self):
        '''
        confirm that both 'name' and 'value' both compile to xforms with the
        correct output.
        '''
        for name_alias in ['name', 'value']:
            self.assertPyxformXform(
                name="aliases",
                md="""
                | survey |      |                |            |
                |        | type | %(name_alias)s | label      |
                |        | text | q1             | Question 1 |
                """ % ({
                        u'name_alias': name_alias
                    }),
                instance__contains=[
                    '<q1/>',
                    ],
                model__contains=[
                    '<bind nodeset="/aliases/q1" type="string"/>',
                    ],
                xml__contains=[
                    '<input ref="/aliases/q1">',
                    '<label>Question 1</label>',
                    '</input>',
                    ])

    def test_conflicting_aliased_values_raises_error(self):
        '''
        example:
        an xlsform has {"name": "q_name", "value": "q_value"}
        should not compile because "name" and "value" columns are aliases
        '''
        # TODO: test that this fails for the correct reason
        self.assertPyxformXform(
            # debug=True,
            name="aliases",
            md="""
            | survey |      |        |         |            |
            |        | type | name   | value   | label      |
            |        | text | q_name | q_value | Question 1 |
            """,
            errored=True,
        )
