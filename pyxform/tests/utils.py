import os
from pyxform import file_utils
from pyxform.builder import create_survey, create_survey_from_path
from unittest2 import TestCase
import xml.etree.ElementTree as ETree
from formencode.doctest_xml_compare import xml_compare
try:
    import ConfigParser
    configparser = ConfigParser
except ImportError:
    import configparser


def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


def build_survey(filename):
    path = path_to_text_fixture(filename)
    return create_survey_from_path(path)


def create_survey_from_fixture(fixture_name, filetype="xls",
                               include_directory=False):
    fixture_path = path_to_text_fixture("%s.%s" % (fixture_name, filetype))
    noop, section_dict = file_utils.load_file_to_dict(fixture_path)
    pkg = {u'main_section': section_dict}
    if include_directory:
        directory, noop = os.path.split(fixture_path)
        pkg[u'sections'] = file_utils.collect_compatible_files_in_directory(
            directory)
    return create_survey(**pkg)


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

    def assertXFormEqual(self, xform1, xform2):
        xform1 = ETree.fromstring(xform1.encode('utf-8'))
        xform2 = ETree.fromstring(xform2.encode('utf-8'))

        # Sort tags under <model> section in each form
        self.sort_model(xform1)
        self.sort_model(xform2)

        # Report any errors returned from xform_compare
        errs = []

        def reporter(msg):
            errs.append(msg)

        self.assertTrue(
            xml_compare(xform1, xform2, reporter),
            "\n\n" + "\n".join(reversed(errs))
        )

    def sort_elems(self, elems, attr=None):
        if attr:
            def elem_get_attr(elem): return elem.get(attr, '')
            key = elem_get_attr
        else:
            def elem_get_tag(elem): return elem.tag
            key = elem_get_tag
        elems[:] = sorted(elems, key=key)

    def sort_model(self, xform):
        ns = "{http://www.w3.org/2002/xforms}"
        model = xform.find('.//' + ns + 'model')

        # Sort multiple <instance> tags, if any
        self.sort_elems(model, 'id')

        # Sort any <item> tags in each <instance>
        for instance in model.findall(ns + 'instance'):
            if instance.get('id', None):
                root = instance.find(ns + 'root')
                if root is not None:
                    for item in root:
                        self.sort_elems(item)

        # Sort <translation> tags as well as inner <text> and <value> tags.
        itext = model.find(ns + 'itext')
        if itext is None:
            return

        self.sort_elems(itext, 'lang')
        for translation in itext:
            self.sort_elems(translation, 'id')
            for text in translation:
                self.sort_elems(text, 'form')


def prep_class_config(cls, test_dir="tests"):
    cls.config = configparser.ConfigParser()
    here = os.path.dirname(__file__)
    root = os.path.dirname(here)
    strings = os.path.join(root, test_dir, "fixtures", "strings.ini")
    cls.config.read(strings)
    cls.cls_name = cls.__name__
