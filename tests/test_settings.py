from pyxform import constants as co
from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.choices import xpc
from tests.xpath_helpers.questions import xpq
from tests.xpath_helpers.settings import xps


class TestSettings(PyxformTestCase):
    """
    Test form settings.

    Use the documented setting name, even if it's an alias.
    """

    def test_form_title(self):
        """Should find the title set in the XForm."""
        md = """
        | settings |
        |          | form_title |
        |          | My Form    |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[xps.form_title("My Form")],
        )

    def test_form_id(self):
        """Should find the instance id set in the XForm."""
        md = """
        | settings |
        |          | form_id |
        |          | my_form |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[xps.form_id("my_form")],
        )

    def test_name__from_sheet__valid_characters(self):
        """Should allow a custom name with valid characters."""
        md = """
        | settings |
        | | name             |
        | | master-form_v2.1 |

        | survey |
        | | type  | name | label |
        | | text  | q1   | hello |
        """
        self.assertPyxformXform(md=md, xml__xpath_match=[xps.name("master-form_v2.1")])

    def test_name__from_sheet__invalid_characters__error(self):
        """Should raise an error if the form_name is not a valid name."""
        md = """
        | settings |
        | | name         |
        | | bad@filename |

        | survey |
        | | type  | name | label |
        | | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.NAMES_008.value.format(sheet=co.SETTINGS, row=1, column=co.NAME)
            ],
        )

    def test_name__from_file__valid_characters(self):
        """Should allow a custom form_name with valid characters."""
        md = """
        | survey |
        | | type  | name | label |
        | | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            name="master-form_v2.1",
            xml__xpath_match=[xps.name("master-form_v2.1")],
        )

    def test_name__from_file__invalid_characters__error(self):
        """Should raise an error if the form_name is not a valid name."""
        md = """
        | survey |
        | | type  | name | label |
        | | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            name="bad@filename",
            errored=True,
            error__contains=[ErrorCode.NAMES_009.value.format(name="form_name")],
        )

    def test_clean_text_values__yes(self):
        """Should find clean_text_values=yes (default) collapses survey sheet whitespace."""
        md = """
        | survey  |                    |      |       |             |
        |         | type               | name | label | calculation |
        |         | integer            | q1   | Q1    | string-length('abc  def') |
        |         | select_one c1      | q2   | Q2    |             |
        |         | select_multiple c2 | q3   | Q3    |             |
        | choices  |
        |          | list_name | name | label |
        |          | c1        | a  b | c  1  |
        |          | c2        | b    | c  2  |
        | settings |                   |
        |          | clean_text_values |
        |          | yes               |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_bind_attr(
                    "q1",
                    "calculate",
                    "string-length('abc def')",
                ),
                xpc.model_instance_choices_label("c1", (("a  b", "c  1"),)),
                xpc.model_instance_choices_label("c2", (("b", "c  2"),)),
            ],
        )

    def test_clean_text_values__no(self):
        """Should find clean_text_values=no leaves survey sheet whitespace as-is."""
        md = """
        | survey  |                    |      |       |             |
        |         | type               | name | label | calculation |
        |         | integer            | q1   | Q1    | string-length('abc  def') |
        |         | select_one c1      | q2   | Q2    |             |
        |         | select_multiple c2 | q3   | Q3    |             |
        | choices  |
        |          | list_name | name | label |
        |          | c1        | a  b | c  1  |
        |          | c2        | b    | c  2  |
        | settings |                   |
        |          | clean_text_values |
        |          | no                |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_bind_attr(
                    "q1",
                    "calculate",
                    "string-length('abc  def')",
                ),
                xpc.model_instance_choices_label("c1", (("a  b", "c  1"),)),
                xpc.model_instance_choices_label("c2", (("b", "c  2"),)),
            ],
        )

    def test_instance_name_from_reference(self):
        """Should find a binding to set the instance name from the reference."""
        md = """
        | settings |
        | | instance_name |
        | | ${q1}         |

        | survey |
        | | type  | name | label |
        | | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:bind[
                  @calculate=' /test_name/q1 '
                  and @nodeset='/test_name/meta/instanceName'
                  and @type='string'
                ]
                """
            ],
        )

    def test_instance_name_from_reference__name_not_found__error(self):
        """Should raise an error if the referenced name is not in the survey sheet."""
        md = """
        | settings |
        | | instance_name |
        | | ${q2}         |

        | survey |
        | | type  | name | label |
        | | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.PYREF_003.value.format(
                    sheet="settings", column="instance_name", row=2, q="q2"
                )
            ],
        )

    def test_instance_id__exists_in_survey_meta_by_default(self):
        """Should find an instanceID child in the survey-level meta element."""
        md = """
        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:instanceID
                """,
                """
                /h:html/h:head/x:model/x:bind[
                  @nodeset='/test_name/meta/instanceID'
                  and @type='string'
                  and @readonly='true()'
                  and @jr:preload='uid'
                ]
                """,
            ],
        )

    def test_instance_id__bind_can_be_modified_with_setting(self):
        """Should find that the instance_id bind can be changed via instance_id setting."""
        md = """
        | settings |
        | | instance_id |
        | | x           |

        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:instanceID
                """,
                """
                /h:html/h:head/x:model/x:bind[
                  @nodeset='/test_name/meta/instanceID'
                  and @type='string'
                  and @readonly='true()'
                  and @jr:preload='x'
                ]
                """,
            ],
        )

    def test_instance_id__can_be_excluded_with_omit_instanceID__no_meta(self):
        """Should find that instanceID can be excluded with omit_instanceID setting.."""
        md = """
        | settings |
        | | omit_instanceID |
        | | yes             |

        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                # The meta block is not emitted if it would be empty.
                """
                /h:html/h:head/x:model/x:instance/x:test_name[not(./x:meta)]
                """,
                """
                /h:html/h:head/x:model[not(./x:bind[@nodeset='/test_name/meta/instanceID'])]
                """,
            ],
        )

    def test_instance_id__can_be_excluded_with_omit_instanceID__with_meta(self):
        """Should find that instanceID can be excluded with omit_instanceID setting.."""
        md = """
        | settings |
        | | omit_instanceID | instance_name |
        | | yes             | x             |

        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:meta[not(./x:instanceID)]
                """,
                """
                /h:html/h:head/x:model[not(./x:bind[@nodeset='/test_name/meta/instanceID'])]
                """,
            ],
        )

    def test_instance_id__can_be_used_as_reference_variable(self):
        """Should find that ${instanceID} resolves to the survey-level meta child."""
        md = """
        | survey |
        | | type  | name | label         | calculation   | read_only |
        | | text  | q1   | ${instanceID} |               |           |
        | | text  | q2   | Q2            | ${instanceID} | yes       |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:instanceID
                """,
                """
                /h:html/h:body/x:input[@ref='/test_name/q1']/x:label/x:output[
                  @value=' /test_name/meta/instanceID '
                ]
                """,
                """
                /h:html/h:head/x:model/x:bind[
                  @nodeset='/test_name/q2'
                  and @type='string'
                  and @readonly='true()'
                  and @calculate=' /test_name/meta/instanceID '
                ]
                """,
            ],
        )

    def test_instance_id__can_be_used_as_reference_variable__error(self):
        """Should find that ${instanceID} resolves to the survey-level meta child."""
        md = """
        | settings |
        | | omit_instanceID |
        | | yes             |

        | survey |
        | | type  | name | label         | calculation   | read_only |
        | | text  | q1   | ${instanceID} |               |           |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                ErrorCode.PYREF_003.value.format(
                    sheet="survey", column="label", row=2, q="instanceID"
                ),
            ],
        )

    def test_style__no_default_output(self):
        """Should find that no default style is set."""
        md = """
        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=["""/h:html/h:body[not(@class)]"""],
        )

    def test_style__output_body_class_attribute(self):
        """Should find that the 'style' setting is output as a body 'class' attribute."""
        md = """
        | settings |
        | | style      |
        | | theme-grid |

        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=["""/h:html/h:body[@class='theme-grid']"""],
        )

    def test_style__output_body_class_attribute_verbatim(self):
        """Should find that the 'style' setting has no processing or validation."""
        md = r"""
        | settings |
        | | style      |
        | | theme-grids\n\n |

        | survey |
        | | type  | name | label |
        | | text  | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[r"""/h:html/h:body[@class='theme-grids\n\n']"""],
        )


class TestNamespaces(PyxformTestCase):
    """Test namespaces, for the XForm and in relation to settings that can be namespaced."""

    def test_standard_namespaces(self):
        """Should find the standard namespaces in the XForm output."""
        md = """
        | survey |      |      |       |
        |        | type | name | label |
        |        | note | q    | Q     |
        """
        # re: https://github.com/XLSForm/pyxform/issues/14
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                "/h:html[namespace::*[name()='']='http://www.w3.org/2002/xforms']",
                "/h:html[namespace::h='http://www.w3.org/1999/xhtml']",
                "/h:html[namespace::jr='http://openrosa.org/javarosa']",
                "/h:html[namespace::orx='http://openrosa.org/xforms']",
                "/h:html[namespace::xsd='http://www.w3.org/2001/XMLSchema']",
            ],
        )

    def test_custom_xml_namespaces(self):
        """Should find any custom namespaces in the XForm."""
        md = """
        | settings |            |
        |          | namespaces |
        |          | esri="http://esri.com/xforms" enk="http://enketo.org/xforms" naf="http://nafundi.com/xforms" |
        | survey   |      |      |       |
        |          | type | name | label |
        |          | note | q    | Q     |
        """
        # re: https://github.com/XLSForm/pyxform/issues/65
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                "/h:html[namespace::*[name()='']='http://www.w3.org/2002/xforms']",
                "/h:html[namespace::h='http://www.w3.org/1999/xhtml']",
                "/h:html[namespace::jr='http://openrosa.org/javarosa']",
                "/h:html[namespace::orx='http://openrosa.org/xforms']",
                "/h:html[namespace::xsd='http://www.w3.org/2001/XMLSchema']",
                "/h:html[namespace::esri='http://esri.com/xforms']",
                "/h:html[namespace::enk='http://enketo.org/xforms']",
                "/h:html[namespace::naf='http://nafundi.com/xforms']",
            ],
        )

    def test_custom_namespaced_instance_attribute(self):
        md = """
        | settings |            |
        |          | namespaces |
        |          | ex="http://example.com/xforms" |
        | survey  |         |            |       |                        |
        |         | type    | name       | label | instance::ex:duration |
        |         | trigger | my_trigger | T1    | 10                     |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                "/h:html[namespace::ex='http://example.com/xforms']",
                """
                  /h:html/h:head/x:model/x:instance/x:test_name/x:my_trigger/@*[
                    local-name()='duration'
                    and namespace-uri()='http://example.com/xforms'
                    and .='10'
                  ]
                """,
            ],
        )

    def test_instance_xmlns__is_set__custom_namespace(self):
        """Should find the instance_xmlns value in the instance xmlns attribute."""
        md = """
        | settings |
        |          | instance_xmlns            |
        |          | http://example.com/xforms |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance/*[
                    namespace-uri()='http://example.com/xforms'
                    and local-name()='test_name'
                    and @id='data'
                  ]
                """
            ],
        )

    def test_instance_xmlns__not_set__xforms_namespace(self):
        """Should find the XForms namespace for the instance element."""
        md = """
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance/*[
                    namespace-uri()='http://www.w3.org/2002/xforms'
                    and local-name()='test_name'
                    and @id='data'
                  ]
                """
            ],
        )

    def test_primary_instance_attribute__xforms_namespace(self):
        """Should find the instance attribute in the default namespace."""
        md = """
        | settings |
        |          | attribute::xyz |
        |          | 1234           |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance/x:test_name/@*[
                    namespace-uri()=''
                    and local-name()='xyz'
                    and .='1234'
                  ]
                """
            ],
        )

    def test_primary_instance_attribute__custom_namespace(self):
        """Should find the instance attribute in the custom namespace."""
        md = """
        | settings |
        |          | attribute::ex:xyz | namespaces                     |
        |          | 1234              | ex="http://example.com/xforms" |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                "/h:html[namespace::ex='http://example.com/xforms']",
                """
                  /h:html/h:head/x:model/x:instance/x:test_name/@*[
                    namespace-uri()='http://example.com/xforms'
                    and local-name()='xyz'
                    and .='1234'
                  ]
                """,
            ],
        )

    def test_primary_instance_attribute__multiple(self):
        """Should find the multiple instance attributes in the default namespace."""
        md = """
        | settings |
        |          | attribute::xyz | attribute::abc |
        |          | 1234           | 5678           |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                  /h:html/h:head/x:model/x:instance/x:test_name/@*[
                    namespace-uri()=''
                    and local-name()='xyz'
                    and .='1234'
                  ]
                """,
                """
                  /h:html/h:head/x:model/x:instance/x:test_name/@*[
                    namespace-uri()=''
                    and local-name()='abc'
                    and .='5678'
                  ]
                """,
            ],
        )


class TestSubmission(PyxformTestCase):
    """Test settings that configure the submission element."""

    def test_client_editable__active(self):
        """Should find the odk:client-editable attribute in the submission config."""
        md = """
        | settings |
        || client_editable |
        || {case}          |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("yes", "true")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        xps.submission_where("@odk:client-editable = 'true'"),
                    ],
                )

    def test_client_editable__inactive__explicit(self):
        """Should not find a submission config containing odk:client-editable."""
        md = """
        | settings |
        || client_editable |
        || {case}          |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("no", "false")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        """/h:html/h:head/x:model[not(./x:submission/@odk:client-editable)]""",
                    ],
                )

    def test_client_editable__inactive__implicit(self):
        """Should not find a submission config containing odk:client-editable."""
        md = """
        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model[not(./x:submission/@odk:client-editable)]""",
            ],
        )

    def test_client_editable__inactive__explicit__submission(self):
        """Should not find the odk:client-editable attribute in the submission config."""
        md = """
        | settings |
        || client_editable | auto_send |
        || {case}          | true      |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("no", "false")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        xps.submission_where("not(@odk:client-editable = 'true')"),
                    ],
                )

    def test_auto_send__active(self):
        """Should find the orx:auto-send attribute in the submission config."""
        md = """
        | settings |
        || auto_send |
        || {case}    |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("yes", "true")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        xps.submission_where("@orx:auto-send = 'true'"),
                    ],
                )

    def test_auto_send__inactive__explicit(self):
        """Should not find a submission config containing orx:auto-send."""
        md = """
        | settings |
        || auto_send |
        || {case}    |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("no", "false")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        """/h:html/h:head/x:model[not(./x:submission/@orx:auto-send)]""",
                    ],
                )

    def test_auto_send__inactive__implicit(self):
        """Should not find a submission config containing orx:auto-send."""
        md = """
        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model[not(./x:submission/@orx:auto-send)]""",
            ],
        )

    def test_auto_send__inactive__explicit__submission(self):
        """Should not find the orx:auto-send attribute in the submission config."""
        md = """
        | settings |
        || auto_send | client_editable |
        || {case}    | true            |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("no", "false")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        xps.submission_where("not(@orx:auto-send)"),
                    ],
                )

    def test_auto_delete__active(self):
        """Should find the orx:auto-delete attribute in the submission config."""
        md = """
        | settings |
        || auto_delete |
        || {case}      |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("yes", "true")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        xps.submission_where("@orx:auto-delete = 'true'"),
                    ],
                )

    def test_auto_delete__inactive__explicit(self):
        """Should not find a submission config containing orx:auto-delete."""
        md = """
        | settings |
        || auto_delete |
        || {case}      |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("no", "false")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        """/h:html/h:head/x:model[not(./x:submission/@orx:auto-delete)]""",
                    ],
                )

    def test_auto_delete__inactive__implicit(self):
        """Should not find a submission config containing orx:auto-delete."""
        md = """
        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """/h:html/h:head/x:model[not(./x:submission/@orx:auto-delete)]""",
            ],
        )

    def test_auto_delete__inactive__explicit__submission(self):
        """Should not find the orx:auto-delete attribute in the submission config."""
        md = """
        | settings |
        || auto_delete | client_editable |
        || {case}      | true            |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("no", "false")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    xml__xpath_match=[
                        xps.submission_where("not(@orx:auto-delete)"),
                    ],
                )

    def test_bool_setting_unrecognised_value__warning(self):
        """Should show a warning if a bool setting value was not recognised."""
        md = """
        | settings |
        || auto_delete |
        || {case}      |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        cases = ("yeah", "nah", "Y", "N", "X")
        for case in cases:
            with self.subTest(case):
                self.assertPyxformXform(
                    md=md.format(case=case),
                    warnings__contains=[
                        ErrorCode.SETTING_001.value.format(
                            name=co.AUTO_DELETE,
                            value=case,
                            default="no",
                        )
                    ],
                )

    def test_bool_setting_unrecognised_value__no_warning_for_empty(self):
        """Should not show a warning if a bool setting has a column with no value."""
        md = """
        | settings |
        || auto_delete |
        ||             |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            warnings_count=0,
            warnings__not_contains=[
                ErrorCode.SETTING_001.value.format(
                    name=co.AUTO_DELETE,
                    value="",
                    default="no",
                )
            ],
        )

    def test_settings_without_submission_url_does_not_generate_method_attribute(self):
        """Should not generate method attribute on submission config when submission_url is omitted."""
        pk = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwOHPJWD9zc8JPBZj/UtCdHiY7I4HWt61UG1XRaGvvwUkC/y8P5Kk6dRnf3yMTBHQoisT2vU2ODWVaU5elndkhiKiWdhufp1d86FWGYz/i+VOmdoV+0zoyPzk+vTEG8bpiY7/UcDYY0CsrRmaMei115xZwQpSMpayqMjemvwGDyhy2B3Yize4yaxyLFG53wMrHEczzsYz8FuRfuKUleE/6jFc3uXZET4LJ7S76n1XU+bE+mhhoZ+tVERgaVH38l0SZljBITwHeqQ9WQckkmDfbRHBG7TQm+Afnx0s5E2bGIT5jB5cj9YaX6BqZSeodpafQjpXEJg6uufxF1Ni3Btv4wIDAQAB"
        md = f"""
        | settings |
        || public_key | auto_send |
        || {pk}       | false     |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xps.submission_where(f"@base64RsaPublicKey='{pk}' and not(@method)"),
            ],
        )

    def test_settings_with_submission_url_generates_method_attribute(self):
        """Should generate action and method attributes on submission config when submission_url is provided."""
        url = "https://odk.ona.io/random_person/submission"
        md = f"""
        | settings |
        || submission_url | auto_send |
        || {url}          | false     |

        | survey |
        || type | name | label |
        || text | q1   | Q1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xps.submission_where(f"@action='{url}' and @method='post'"),
            ],
        )
