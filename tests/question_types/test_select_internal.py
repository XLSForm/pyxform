from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase


class TestSelectInternalParsing(PyxformTestCase):
    def test_select_list_name__match__ok(self):
        """Should not raise an error if the select list is found in the choices sheet."""
        md = """
        | survey |
        | | type          | name | label |
        | | select_one c1 | q1   | Q1    |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(md=md, warnings_count=0)

    def test_select_list_name__missing__error(self):
        """Should raise an error if the select list is not found in the choices sheet."""
        md = """
        | survey |
        | | type          | name | label |
        | | select_one c2 | q1   | Q1    |

        | choices |
        | | list_name | name | label |
        | | c1        | n1   | N1    |
        """
        self.assertPyxformXform(
            md=md, errored=True, error__contains=[ErrorCode.NAMES_016.value.format(row=2)]
        )
