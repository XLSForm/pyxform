from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


class TestHiddenOutput(PyxformTestCase):
    def test_hidden(self):
        """Should find that the bind is string, with no control."""
        md = """
        | survey |
        | | type   | name |
        | | hidden | q1   |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "string"),
                xpq.body_empty(),
            ],
            warnings_count=0,
        )
