from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class FieldsTests(PyxformTestCase):
    """
    Test XLSForm Fields
    """

    def test_duplicate_fields(self):
        """
        Ensure that duplicate field names are not allowed
        """
        self.assertPyxformXform(
            name="duplicatefields",
            md="""
            | Survey |         |         |               |
            |        | Type    | Name    | Label         |
            |        | integer | age     | the age       |
            |        | integer | age     | the age       |
            """,
            errored=True,
            error__contains=[
                "There are more than one survey elements named 'age'"],
        )

    def test_duplicate_fields_diff_cases(self):
        """
        Ensure that duplicate field names with different cases are not allowed
        """
        self.assertPyxformXform(
            name="duplicatefieldsdiffcases",
            md="""
            | Survey |         |         |               |
            |        | Type    | Name    | Label         |
            |        | integer | age     | the age       |
            |        | integer | Age     | the age       |
            """,
            errored=True,
            error__contains=[
                "There are more than one survey elements named 'age'"],
        )
