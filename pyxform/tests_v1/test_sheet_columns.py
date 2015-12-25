from pyxform_test_case import PyxformTestCase


class InvalidSurveyColumnsTests(PyxformTestCase):
    def test_missing_name(self):
        '''
        every question needs a name (or alias of name)
        '''
        self.assertPyxformXform(
            name='invalidcols',
            ss_structure={'survey': [{'type': 'text',
                                      'label': 'label'}]},
            errored=True,
            error__contains=['no name'],
        )

    def test_missing_name_but_has_alias_of_name(self):
        self.assertPyxformXform(
            name='invalidcols',
            ss_structure={'survey': [{'value': 'q1',
                                      'type': 'text',
                                      'label': 'label'}]},
            errored=False,
        )

    def test_missing_label(self):
        self.assertPyxformXform(
            name="invalidcols",
            ss_structure={'survey': [{'type': 'text',
                                      'name': 'q1'}]},
            errored=True,
            error__contains=['no label or hint'],
        )


class InvalidChoiceSheetColumnsTests(PyxformTestCase):
    def _simple_choice_ss(self, choice_sheet=[]):
        return {'survey': [{'type': 'select_one l1',
                            'name': 'l1choice',
                            'label': 'select one from list l1'}],
                'choices': choice_sheet}

    def test_valid_choices_sheet_passes(self):
        self.assertPyxformXform(
            name='valid_choices',
            ss_structure=self._simple_choice_ss([
                {'list_name': 'l1',
                    'name': 'c1',
                    'label': 'choice 1'},
                {'list_name': 'l1',
                    'name': 'c2',
                    'label': 'choice 2'}]),
            errored=False,
            )

    def test_invalid_choices_sheet_fails(self):
        self.assertPyxformXform(
            name='missing_name',
            ss_structure=self._simple_choice_ss([
                {'list_name': 'l1',
                    'label': 'choice 1'},
                {'list_name': 'l1',
                    'label': 'choice 2'},
                ]),
            errored=True,
            error__contains=['option with no name'],
            )

    def test_missing_list_name(self):
        self.assertPyxformXform(
            name='missing_list_name',
            ss_structure=self._simple_choice_ss([
                {'bad_column': 'l1',
                    'name': 'l1c1',
                    'label': 'choice 1'},
                {'bad_column': 'l1',
                    'name': 'l1c1',
                    'label': 'choice 2'},
                ]),
            debug=True,
            errored=True,
            # some basic keywords that should be in the error:
            error__contains=[
                'choices',
                'name',
                'list name',
            ])


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
''' # uncomment when re-implemented
    # TODO: test that this fails for the correct reason
    def test_conflicting_aliased_values_raises_error(self):
        # example:
        # an xlsform has {"name": "q_name", "value": "q_value"}
        # should not compile because "name" and "value" columns are aliases

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
'''