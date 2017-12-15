from unittest2 import TestCase

from pyxform.tests.utils import prep_class_config
from pyxform.validators.enketo_validate import check_xform


class ODKValidateTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls)

    def test_todo(self):
        # TODO: checks around enketo-validate behaviour
        self.assertListEqual(["Enketo Validate Warnings:\nHello world\n"], check_xform(""))
