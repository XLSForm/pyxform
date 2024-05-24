"""
Test unicode rtl in XLSForms.
"""

from tests.pyxform_test_case import PyxformTestCase


class UnicodeStrings(PyxformTestCase):
    def test_unicode_snowman(self):
        self.assertPyxformXform(
            md="""
            | survey |      |         |       |
            |        | type | name    | label |
            |        | text | snowman | ☃     |
            """,
            xml__contains=["<label>☃</label>"],
        )

    def test_smart_quotes(self):
        self.assertPyxformXform(
            ss_structure={
                "survey": [
                    {
                        "type": "select_one xyz",
                        "name": "smart_single_quoted",
                        "label": """
                     ‘single-quoted’
                     """.strip(),
                    },
                    {
                        "type": "text",
                        "name": "smart_double_quoted",
                        "relevant": "selected(${smart_single_quoted}, ‘xxx’)",
                        "label": """
                     “double-quoted”
                     """.strip(),
                    },
                    {
                        "type": "integer",
                        "name": "my_default_is_123",
                        "label": "my default is 123",
                        "default": 123,
                    },
                ],
                "choices": [
                    {"list_name": "xyz", "name": "xxx", "label": "‘Xxx’"},
                    {"list_name": "xyz", "name": "yyy", "label": "“Yyy”"},
                ],
                "settings": [{"version": "q(‘-’)p"}],
            },
            name="quoth",
            xml__contains=[
                "'single-quoted",
                '"double-quoted"',
                "selected( /quoth/smart_single_quoted , 'xxx')",
                "<my_default_is_123>123</my_default_is_123>",
                "<label>'Xxx'</label>",
                '<label>"Yyy"</label>',
                """
                version="q('-')p"
                """.strip(),
            ],
        )
