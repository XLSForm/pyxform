import os
import xml.etree.ElementTree as ETree
from unittest import TestCase

from formencode.doctest_xml_compare import xml_compare

from tests import example_xls, test_output


# Do not use this class for new tests. Use PyxformTestCase instead.
class XFormTestCase(TestCase):
    """
    XFormTestCase provides an assertion for comparing two XForms for
    equivalence.  It relies on the xml_compare function provided by FormEncode,
    but with some extra logic to handle the essentially random order of tags in
    the <model> section.  The iteration order of dict keys in Python 3 is
    unpredictable, and many of the elements in <model> tag are generated from
    dicts.  A simple workaround is to just reorder those tags here.  An ideal
    solution might be to rewrite the code that generates an XForm to use
    OrderedDicts where appropriate.
    """

    def get_file_path(self, filename):
        self.path_to_excel_file = os.path.join(example_xls.PATH, filename)

        # Get the xform output path:
        self.root_filename, self.ext = os.path.splitext(filename)
        self.output_path = os.path.join(test_output.PATH, self.root_filename + ".xml")

    def assertXFormEqual(self, xform1, xform2):
        xform1 = ETree.fromstring(xform1.encode("utf-8"))
        xform2 = ETree.fromstring(xform2.encode("utf-8"))

        # Sort tags under <model> section in each form
        self.sort_model(xform1)
        self.sort_model(xform2)

        # Report any errors returned from xform_compare
        errs = []
        self.assertTrue(
            xml_compare(xform1, xform2, errs.append), "\n\n" + "\n".join(reversed(errs))
        )

    @staticmethod
    def sort_elems(elems, attr=None):
        if attr:

            def elem_get_attr(elem):
                return elem.get(attr, "")

            key = elem_get_attr
        else:

            def elem_get_tag(elem):
                return elem.tag

            key = elem_get_tag
        elems[:] = sorted(elems, key=key)

    def sort_model(self, xform):
        ns = "{http://www.w3.org/2002/xforms}"
        model = xform.find(".//" + ns + "model")

        # Sort multiple <instance> tags, if any
        self.sort_elems(model, "id")

        # Sort any <item> tags in each <instance>
        for instance in model.findall(ns + "instance"):
            if instance.get("id", None):
                root = instance.find(ns + "root")
                if root is not None:
                    for item in root:
                        self.sort_elems(item)

        # Sort <translation> tags as well as inner <text> and <value> tags.
        itext = model.find(ns + "itext")
        if itext is None:
            return

        self.sort_elems(itext, "lang")
        for translation in itext:
            self.sort_elems(translation, "id")
            for text in translation:
                self.sort_elems(text, "form")
