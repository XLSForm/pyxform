"""
Ensuring that the pyxform_test_case.PyxformTestCase class does some
internal conversions correctly.
"""

from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase, PyxformTestError
from tests.xpath_helpers.settings import xps


class PyxformTestCaseNonMarkdownSurveyAlternatives(PyxformTestCase):
    def test_tainted_vanilla_survey_failure(self):
        """
        The _invalid_ss_structure structure should fail to compile
        because the note has no label.

        if "errored" parameter is not set to False, it should
        raise an exception
        """
        _invalid_ss_structure = {"survey": [{"type": "note", "name": "q1"}]}

        def _no_valid_flag():
            """
            When the 'errored' flag is set to false (default) and the survey
            fails to compile, the test should raise an exception.
            """
            self.assertPyxformXform(
                ss_structure=_invalid_ss_structure,
                errored=False,  # errored=False by default
            )

        self.assertRaises(PyxformTestError, _no_valid_flag)

        # however when errored=True is present,
        self.assertPyxformXform(
            ss_structure=_invalid_ss_structure,
            errored=True,
            error__contains=[ErrorCode.LABEL_003.value.format(row=2)],
        )

    def test_vanilla_survey(self):
        """
        Testing that a survey can be passed as a _spreadsheet structure_ named
        'ss_structure'.

        this will be helpful when testing whitespace constraints and
        cell data types since markdown'd surveys strip spaces and
        cast empty strings to None values
        """
        self.assertPyxformXform(
            ss_structure={"survey": [{"type": "note", "name": "n1", "label": "Note 1"}]},
        )


class XlsFormPyxformSurveyTest(PyxformTestCase):
    def test_formid_is_not_none(self):
        """
        When the form id is not set, it should never use python's
        None. Fixing because this messes up other tests.
        """
        self.assertPyxformXform(
            md="""
            | survey |      |      |       |
            |        | type | name | label |
            |        | note | q    | Q     |
            """,
            xml__xpath_match=[
                xps.form_id("data"),
            ],
        )
