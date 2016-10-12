from pyxform.tests_v1.pyxform_test_case import PyxformTestCase
from pyxform.tests.utils import prep_class_config


class CustomXMLNamespacesTest(PyxformTestCase):

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls, test_dir="tests_v1")

    def test_custom_xml_name_spaces(self):
        # re: https://github.com/XLSForm/pyxform/issues/65
        md = self.config.get(self.cls_name, "test_custom_xml_name_spaces_md")
        self.assertPyxformXform(
            name="custom_namespaces",
            md=md,
            xml__contains=[
                'xmlns="http://www.w3.org/2002/xforms"',
                'xmlns:h="http://www.w3.org/1999/xhtml"',
                'xmlns:jr="http://openrosa.org/javarosa"',
                'xmlns:orx="http://openrosa.org/xforms"',
                'xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
                'xmlns:esri="http://esri.com/xforms"',
                'xmlns:enk="http://enketo.org/xforms"',
                'xmlns:naf="http://nafundi.com/xforms"',
            ],
        )
