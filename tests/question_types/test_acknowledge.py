from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


class TestAcknowledge(PyxformTestCase):
    def test_acknowledge_aliases(self):
        """Each spelling should produce a trigger control with a string binding."""
        for alias in (
            "acknowledge",
            "trigger",
            "q acknowledge",
            "add acknowledge prompt",
        ):
            with self.subTest(alias=alias):
                self.assertPyxformXform(
                    md=f"""
                    | survey |
                    | | type    | name     | label    | required |
                    | | {alias} | optional | Optional |          |
                    | | {alias} | required | Required | yes      |
                    """,
                    xml__xpath_match=[
                        xpq.model_instance_bind("optional", "string"),
                        xpq.model_instance_bind("required", "string"),
                        xpq.model_instance_bind_attr("required", "required", "true()"),
                        xpq.body_label_inline("trigger", "optional", "Optional"),
                        xpq.body_label_inline("trigger", "required", "Required"),
                    ],
                )
