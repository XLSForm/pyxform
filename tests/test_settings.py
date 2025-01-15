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


class TestNamespaces(PyxformTestCase):
    """
    Test namespaces, for the XForm and in relation to settings that can be namespaced.
    """

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
