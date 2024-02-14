"""
Test tutorial XLSForm.
"""
from unittest import TestCase

from pyxform.builder import create_survey_from_path

from tests import utils


class TutorialTests(TestCase):
    @staticmethod
    def test_create_from_path():
        path = utils.path_to_text_fixture("tutorial.xls")
        create_survey_from_path(path)
