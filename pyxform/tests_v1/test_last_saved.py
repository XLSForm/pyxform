# -*- coding: utf-8 -*-
"""
The last-saved virtual instance can be queried to get values from the last saved instance of the form being authored.
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class LastSavedTest(PyxformTestCase):
    def test_last_saved_in_calculate(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                                    |
            |        | type       | name     | label | calculation                        |
            |        | text       | foo      | Foo   |                                    |
            |        | calculate  | last-foo |       | concat("Foo: ", ${last-saved#foo}) |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "calculate=\"concat(&quot;Foo: &quot;,  instance('__last-saved')/last-saved/foo )\"",
            ],
        )

    def test_last_saved_calculate_self(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                       |
            |        | type       | name     | label | calculation           |
            |        | integer    | foo      | Foo   | ${last-saved#foo} + 1 |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                'calculate=" instance(\'__last-saved\')/last-saved/foo  + 1" nodeset="/last-saved/foo"',
            ],
        )

    def test_last_saved_in_label(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |                                      |
            |        | type       | name     | label                                |
            |        | text       | foo      | Foo was previously ${last-saved#foo} |
            """,
            xml__contains=[
                "<label> Foo was previously <output value=\" instance('__last-saved')/last-saved/foo \"/> </label>",
            ],
        )

    def test_multiple_last_saved_in_calculate(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                                       |
            |        | type       | name     | label | calculation                           |
            |        | integer    | foo      | Foo   |                                       |
            |        | integer    | bar      | Bar   |                                       |
            |        | calculate  | last-sum |       | ${last-saved#foo} + ${last-saved#bar} |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "calculate=\" instance('__last-saved')/last-saved/foo  +  instance('__last-saved')/last-saved/bar \"",
            ],
        )

    def test_last_saved_in_relevant(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                        |
            |        | type       | name     | label | relevant               |
            |        | integer    | foo      | Foo   | ${last-saved#foo} < 12 |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "relevant=\" instance('__last-saved')/last-saved/foo  &lt; 12\"",
            ],
        )

    def test_last_saved_in_readonly(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                        |
            |        | type       | name     | label | readonly               |
            |        | integer    | foo      | Foo   | ${last-saved#foo} < 12 |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "readonly=\" instance('__last-saved')/last-saved/foo  &lt; 12\"",
            ],
        )

    def test_last_saved_in_constraint(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                        |
            |        | type       | name     | label | constraint             |
            |        | integer    | foo      | Foo   | . > ${last-saved#foo}  |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "constraint=\". &gt;  instance('__last-saved')/last-saved/foo \"",
            ],
        )

    def test_last_saved_in_required(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                        |
            |        | type       | name     | label | required               |
            |        | integer    | foo      | Foo   | ${last-saved#foo} < 12 |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "required=\" instance('__last-saved')/last-saved/foo  &lt; 12\"",
            ],
        )

    def test_last_saved_in_default(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                   |
            |        | type       | name     | label | default           |
            |        | integer    | foo      | Foo   | ${last-saved#foo} |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                '<setvalue event="odk-instance-first-load" ref="/last-saved/foo" value=" instance(\'__last-saved\')/last-saved/foo "/>',
            ],
        )

    # This is not really a useful thing to do because we get an unqualified reference. Clients should use the first
    # node in the repeat in an expression like this one where a single value is needed or the full nodeset in an
    # expression where a nodeset is required. An alternative to consider is to generate an expression with position(..).
    def test_last_saved_in_repeat(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |              |           |       |                            |
            |        | type         | name      | label | calculation                |
            |        | begin repeat | my-repeat |       |                            |
            |        | integer      | foo       | Foo   |                            |
            |        | calculate    | bar       |       | ${foo} + ${last-saved#foo} |
            |        | end repeat   | my-repeat |       |                            |
            |        | calculate    | baz       |       | ${foo} + ${last-saved#foo} |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                'calculate=" ../foo  +  instance(\'__last-saved\')/last-saved/my-repeat/foo " nodeset="/last-saved/my-repeat/bar"',
                'calculate=" /last-saved/my-repeat/foo  +  instance(\'__last-saved\')/last-saved/my-repeat/foo " nodeset="/last-saved/baz"',
            ],
        )

    # In repeats, ${} references in choice filters get expanded to relative references using current(). ${last-saved}
    # references should be expanded to absolute references.
    def test_last_saved_in_choice_filter_does_not_use_current_or_relative_ref(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |                |          |       |                                        |
            |        | type           | name     | label | choice_filter                          |
            |        | begin repeat   | repeat   |       |                                        |
            |        | select_one foo | foo      | Foo   | not(selected(${last-saved#foo}, name)) |
            |        | select_one foo | bar      | Bar   | not(selected(${foo}, name))            |
            |        | end repeat     | repeat   |       |                                        |
            | choices|                |          |       |                                        |
            |        | list_name      | name     | label |                                        |
            |        | foo            | a        | A     |                                        |
            """,
            xml__contains=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>',
                "<itemset nodeset=\"instance('foo')/root/item[not(selected( instance('__last-saved')/last-saved/repeat/foo , name))]\">",
                "<itemset nodeset=\"instance('foo')/root/item[not(selected( current()/../foo , name))]\">",
            ],
        )

    # Last saved must refer to an instance of this form definition so we should not allow fields that don't exist in
    # this definition.
    def test_last_saved_errors_when_field_does_not_exist(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |                                   |
            |        | type       | name     | label | calculation                       |
            |        | calculate  | last-foo |       | concat("Foo: ", ${last-saved#foo} |
            """,
            errored=True,
            error__contains=[
                "There has been a problem trying to replace ${last-saved#foo} with the XPath to the survey element named 'foo'. There is no survey element with this name."
            ],
        )

    def test_last_saved_not_generated_without_last_save_call(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |            |          |       |             |
            |        | type       | name     | label | calculation |
            |        | integer    | foo      | Foo   |             |
            |        | calculate  | bar      | Bar   | ${foo} + 4  |
            """,
            xml__excludes=[
                '<instance id="__last-saved" src="jr://instance/last-saved"/>'
            ],
        )

    def test_last_saved_call_and___last_saved_instance_conflict(self):
        self.assertPyxformXform(
            name="last-saved",
            md="""
            | survey |              |              |       |                       |
            |        | type         | name         | label | calculation           |
            |        | xml-external | __last-saved |       |                       |
            |        | integer      | foo          | Foo   |                       |
            |        | calculate    | bar          | Bar   | ${last-saved#foo} + 4 |
            """,
            errored=True,
            error__contains=[
                "The same instance id will be generated for different external instance source URIs. Please check the form.",
                "Instance name: '__last-saved', Existing type: 'external', Existing URI: 'jr://file/__last-saved.xml'",
                "Duplicate type: 'instance', Duplicate URI: 'jr://instance/last-saved', Duplicate context: 'None'.",
            ],
        )
