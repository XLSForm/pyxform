from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
from pyxform.tests.utils import prep_class_config


class AreaTest(PyxformTestCase):

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls, test_dir="tests_v1")

    def test_area(self):
        md = self.config.get(self.cls_name, "test_area_md")
        xml_contains = self.config.get(self.cls_name, "test_area_contains")
        self.assertPyxformXform(
            name="area",
            md=md,
            xml__contains=[xml_contains],
            debug=True
        )
