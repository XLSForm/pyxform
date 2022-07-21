from tests.pyxform_test_case import PyxformTestCase


class TestSettings(PyxformTestCase):
    def test_instance_xmlns__is_set__custom_xmlns(self):
        """Should find the instance_xmlns value in the instance xmlns attribute."""
        md = """
        | settings |
        |          | instance_xmlns |
        |          | 1234           |
        | survey |       |      |       |
        |        | type  | name | label |
        |        | text  | q1   | hello |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                """
                /h:html/h:head/x:model/x:instance/*[
                  local-name()='test_name'
                  and @id='test_id'
                  and namespace-uri()='1234'
                ]
                """
            ],
        )

    def test_instance_xmlns__not_set__default_xmlns(self):
        """Should find the default xmlns for the instance element."""
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
                  local-name()='test_name'
                  and @id='test_id'
                  and namespace-uri()='http://www.w3.org/2002/xforms'
                ]
                """
            ],
        )
