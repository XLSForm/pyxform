# -*- coding: utf-8 -*-
"""
PyxformTestCase base class using markdown to define the XLSForm.
"""
from __future__ import print_function, unicode_literals

import codecs
from contextlib import contextmanager
import logging
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ETree
import xml.etree.ElementPath as EPath
from unittest import TestCase
from typing import TYPE_CHECKING

from pyxform.builder import create_survey_element_from_dict
from pyxform.errors import PyXFormError
from pyxform.tests_v1.test_utils.md_table import md_table_to_ss_structure
from pyxform.utils import NSMAP, unicode
from pyxform.validators.odk_validate import ODKValidateError, check_xform
from pyxform.xls2json import workbook_to_json

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


if TYPE_CHECKING:
    from typing import Dict
    from xml.etree.ElementTree import Element


class PyxformTestError(Exception):
    pass


class PyxformMarkdown(object):
    """Transform markdown formatted xlsform to a pyxform survey object"""

    def md_to_pyxform_survey(self, md_raw, kwargs=None, autoname=True, warnings=None):
        if kwargs is None:
            kwargs = {}
        if autoname:
            kwargs = self._autoname_inputs(kwargs)
        _md = []
        for line in md_raw.split("\n"):
            if re.match(r"^\s+#", line):
                # ignore lines which start with pound sign
                continue
            elif re.match(r"^(.*)(#[^|]+)$", line):
                # keep everything before the # outside of the last occurrence
                # of |
                _md.append(re.match(r"^(.*)(#[^|]+)$", line).groups()[0].strip())
            else:
                _md.append(line.strip())
        md = "\n".join(_md)

        if kwargs.get("debug"):
            logger.debug(md)

        def list_to_dicts(arr):
            headers = arr[0]

            def _row_to_dict(row):
                out_dict = {}
                for i in range(0, len(row)):
                    col = row[i]
                    if col not in [None, ""]:
                        out_dict[headers[i]] = col
                return out_dict

            return [_row_to_dict(r) for r in arr[1:]]

        sheets = {}
        for sheet, contents in md_table_to_ss_structure(md):
            sheets[sheet] = list_to_dicts(contents)

        return self._ss_structure_to_pyxform_survey(sheets, kwargs, warnings=warnings)

    @staticmethod
    def _ss_structure_to_pyxform_survey(ss_structure, kwargs, warnings=None):
        # using existing methods from the builder
        imported_survey_json = workbook_to_json(ss_structure, warnings=warnings)
        # ideally, when all these tests are working, this would be
        # refactored as well
        survey = create_survey_element_from_dict(imported_survey_json)
        survey.name = kwargs.get("name", "data")
        survey.title = kwargs.get("title")
        survey.id_string = kwargs.get("id_string")

        return survey

    @staticmethod
    def _run_odk_validate(xml):
        # On Windows, NamedTemporaryFile must be opened exclusively.
        # So it must be explicitly created, opened, closed, and removed
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        try:
            with codecs.open(tmp.name, mode="w", encoding="utf-8") as fp:
                fp.write(xml)
                fp.close()
            check_xform(tmp.name)
        finally:
            # Clean up the temporary file
            os.remove(tmp.name)
            assert not os.path.isfile(tmp.name)

    @staticmethod
    def _autoname_inputs(kwargs):
        """
        title and name are necessary for surveys, but not always convenient to
        include in test cases, so this will pull a default value
        from the stack trace.
        """
        test_name_root = "pyxform"
        if "name" not in kwargs.keys():
            kwargs["name"] = test_name_root + "_autotestname"
        if "title" not in kwargs.keys():
            kwargs["title"] = test_name_root + "_autotesttitle"
        if "id_string" not in kwargs.keys():
            kwargs["id_string"] = test_name_root + "_autotest_id_string"

        return kwargs


class PyxformTestCase(PyxformMarkdown, TestCase):
    maxDiff = None

    def assertPyxformXform(self, **kwargs):
        """
        PyxformTestCase.assertPyxformXform() named arguments:
        -----------------------------------------------------

        one of these possible survey input types
          * md: (str) a markdown formatted xlsform (easy to read in code)
                [consider a plugin to help with formatting md tables,
                 e.g. https://github.com/vkocubinsky/SublimeTableEditor]
          * ss_structure: (dict) a python dictionary with sheets and their
                contents. best used in cases where testing whitespace and
                cells' type is important
          * survey: (pyxform.survey.Survey) easy for reuse within a test
          # Note: XLS is not implemented at this time. You can use builder to
          create a pyxform Survey object

        one or many of these string "matchers":
          * xml__contains: an array of strings which exist in the
                resulting xml. [xml|model|instance|itext]_excludes are also supported.
          * error__contains: a list of strings which should exist in the error
          * error__not_contains: a list of strings which should not exist in the error
          * odk_validate_error__contains: list of strings; run_odk_validate must be set
          * warning__contains: a list of strings which should exist in the warnings
          * warning__not_contains: a list of strings which should not exist in the warnings
          * warnings_count: the number of expected warning messages
          * xml__excludes: an array of strings which should not exist in the resulting
               xml. [xml|model|instance|itext]_excludes are also supported.
          * [xml|model|instance|itext]__xpath_exact: A list of tuples where the
               first tuple element is an XPath expression and the second tuple
               element is a list of exact string match results that are expected.
          * [xml|model|instance|itext]__xpath_count: A list of tuples where the
               first tuple element is an XPath expression and the second tuple
               element is the integer number of match results that are expected.

        optional other parameters passed to pyxform:
          * errored: (bool) if the xlsform is not supposed to compile,
                this must be True
          * name: (str) a valid xml tag to be used as the form name
          * id_string: (str)
          * title: (str)
          * run_odk_validate: (bool) when True, runs ODK Validate process
                Default value = False because it slows down tests
          * warnings: (list) a list to use for storing warnings for inspection.
        """
        debug = kwargs.get("debug", False)
        expecting_invalid_survey = kwargs.get("errored", False)
        errors = []
        warnings = kwargs.get("warnings", [])
        xml_nodes = {}

        run_odk_validate = kwargs.get("run_odk_validate", False)
        odk_validate_error__contains = kwargs.get("odk_validate_error__contains", [])
        survey_valid = True

        try:
            if "md" in kwargs.keys():
                kwargs = self._autoname_inputs(kwargs)
                survey = self.md_to_pyxform_survey(
                    kwargs.get("md"), kwargs, warnings=warnings
                )
            elif "ss_structure" in kwargs.keys():
                kwargs = self._autoname_inputs(kwargs)
                survey = self._ss_structure_to_pyxform_survey(
                    kwargs.get("ss_structure"), kwargs, warnings=warnings,
                )
            else:
                survey = kwargs.get("survey")

            xml = survey._to_pretty_xml()
            root = ETree.fromstring(xml.encode("utf-8"))

            # Ensure all namespaces are present, even if unused
            survey_nsmap = survey.get_nsmap()
            survey_nsmap_xpath = {
                k.replace("xmlns", "").replace(":", ""): v
                for k, v in survey_nsmap.items()
            }
            final_nsmap = NSMAP.copy()
            final_nsmap.update(survey_nsmap)
            root.attrib.update(final_nsmap)

            xml_nodes["xml"] = root

            def _pull_xml_node_from_root(element_selector):
                _r = root.findall(
                    ".//n:%s" % element_selector,
                    namespaces={"n": "http://www.w3.org/2002/xforms"},
                )
                if _r:
                    return _r[0]

                return False

            for _n in ["model", "instance", "itext"]:
                xml_nodes[_n] = _pull_xml_node_from_root(_n)
            if debug:
                logger.debug(xml)
            if run_odk_validate:
                self._run_odk_validate(xml=xml)
                if odk_validate_error__contains:
                    raise PyxformTestError("ODKValidateError was not raised")

        except PyXFormError as e:
            survey_valid = False
            errors = [unicode(e)]
            if debug:
                logger.debug("<xml unavailable />")
                logger.debug("ERROR: '%s'", errors[0])
        except ODKValidateError as e:
            if not odk_validate_error__contains:
                raise PyxformTestError(
                    "ODK Validate error was thrown but "
                    + "'odk_validate_error__contains'"
                    + " was empty:"
                    + unicode(e)
                )
            for v_err in odk_validate_error__contains:
                self.assertContains(
                    e.args[0], v_err, msg_prefix="odk_validate_error__contains"
                )

        if survey_valid:

            def _check(keyword, verb):
                verb_str = "%s__%s" % (keyword, verb)

                bad_kwarg = "%s_%s" % (code, verb)
                if bad_kwarg in kwargs:
                    good_kwarg = "%s__%s" % (code, verb)
                    raise SyntaxError(
                        (
                            "'%s' is not a valid parameter. "
                            "Use double underscores: '%s'"
                        )
                        % (bad_kwarg, good_kwarg)
                    )

                def process_xpath(content: "Element", xpath: str):
                    with xpath_tokenizer_swap():
                        return [
                            stringify_xml(x, survey_nsmap_xpath)
                            for x in EPath.iterfind(
                                elem=content,
                                path=xpath,
                                namespaces=survey_nsmap_xpath,
                            )
                        ]

                def check_content(content):
                    if not content:
                        self.fail(msg="No '{}' found in document.".format(keyword))
                    cstr = ETree.tostring(content, encoding="unicode")
                    text_arr = kwargs[verb_str]
                    for i in text_arr:
                        if verb == "contains":
                            self.assertContains(cstr, i, msg_prefix=keyword)
                        elif verb == "excludes":
                            self.assertNotContains(cstr, i, msg_prefix=keyword)
                        elif verb == "xpath_exact":
                            observed = process_xpath(content=content, xpath=i[0])
                            self.assertListEqual(i[1], observed)
                        elif verb == "xpath_count":
                            observed = process_xpath(content=content, xpath=i[0])
                            self.assertEqual(i[1], len(observed))

                return verb_str, check_content

            if "body_contains" in kwargs or "body__contains" in kwargs:
                raise SyntaxError(
                    "Invalid parameter: 'body__contains'." "Use 'xml__contains' instead"
                )

            # guarantee that strings contain alphanumerically sorted attributes across Python versions
            reorder_attributes(root)

            for code in ["xml", "instance", "model", "itext"]:
                for verb in ["contains", "excludes", "xpath_exact", "xpath_count"]:
                    (code__str, checker) = _check(code, verb)
                    if kwargs.get(code__str):
                        checker(xml_nodes[code])

        if not survey_valid and not expecting_invalid_survey:
            raise PyxformTestError(
                "Expected valid survey but compilation failed. "
                "Try correcting the error with 'debug=True', "
                "setting 'errored=True', "
                "and or optionally 'error__contains=[...]'"
                "\nError(s): " + "\n".join(errors)
            )
        elif survey_valid and expecting_invalid_survey:
            raise PyxformTestError("Expected survey to be invalid.")

        search_test_kwargs = (
            "error__contains",
            "error__not_contains",
            "warnings__contains",
            "warnings__not_contains",
        )
        for k in search_test_kwargs:
            if k not in kwargs:
                continue
            if k.endswith("__contains"):
                assertion = self.assertContains
            elif k.endswith("__not_contains"):
                assertion = self.assertNotContains
            else:
                raise PyxformTestError("Unexpected search test kwarg: {}".format(k))
            if k.startswith("error"):
                joined = "\n".join(errors)
            elif k.startswith("warnings"):
                joined = "\n".join(warnings)
            else:
                raise PyxformTestError("Unexpected search test kwarg: {}".format(k))
            for text in kwargs[k]:
                assertion(joined, text, msg_prefix=k)
        if "warnings_count" in kwargs:
            c = kwargs.get("warnings_count")
            if not isinstance(c, int):
                PyxformTestError("warnings_count must be an integer.")
            self.assertEqual(c, len(warnings))

    @staticmethod
    def _assert_contains(content, text, msg_prefix):
        if msg_prefix:
            msg_prefix += ": "

        # Account for space in self-closing tags
        text_repr = repr(text)
        content = content.replace(" />", "/>")
        real_count = content.count(text)

        return text_repr, real_count, msg_prefix

    def assertContains(self, content, text, count=None, msg_prefix=""):
        """
        FROM: django source- testcases.py

        Asserts that ``text`` occurs ``count`` times in the content string.
        If ``count`` is None, the count doesn't matter - the assertion is
        true if the text occurs at least once in the content.
        """
        text_repr, real_count, msg_prefix = self._assert_contains(
            content, text, msg_prefix
        )

        if count is not None:
            self.assertEqual(
                real_count,
                count,
                msg_prefix + "Found %d instances of %s in content"
                " (expected %d)" % (real_count, text_repr, count),
            )
        else:
            self.assertTrue(
                real_count != 0,
                msg_prefix + "Couldn't find %s in content:\n" % text_repr + content,
            )

    def assertNotContains(self, content, text, msg_prefix=""):
        """
        Asserts that a content indicates that some content was retrieved
        successfully, (i.e., the HTTP status code was as expected), and that
        ``text`` doesn't occurs in the content of the content.
        """
        text_repr, real_count, msg_prefix = self._assert_contains(
            content, text, msg_prefix
        )

        self.assertEqual(
            real_count, 0, msg_prefix + "Response should not contain %s" % text_repr
        )


def reorder_attributes(root):
    """
    Forces alphabetical ordering of all XML attributes to match pre Python 3.8 behavior.
    In general, we should not rely on ordering, but changing all the tests is not
    realistic at this moment.

    See bottom of https://docs.python.org/3/library/xml.etree.elementtree.html#element-objects and
    https://github.com/python/cpython/commit/a3697db0102b9b6747fe36009e42f9b08f0c1ea8 for more information.

    NOTE: there's a similar ordering change made in utils.node. This one is also needed because in
    assertPyxformXform, the survey is converted to XML and then read back in using ETree.fromstring. This
    means that attribute ordering here is based on the attribute representation of xml.etree.ElementTree objects.
    In utils.node, it is based on xml.dom.minidom.Element objects. See https://github.com/XLSForm/pyxform/issues/414.
    """
    for el in root.iter():
        attrib = el.attrib
        if len(attrib) > 1:
            # Sort attributes. Attributes are represented as {namespace}name so attributes with explicit
            # namespaces will always sort after those without explicit namespaces.
            attribs = sorted(attrib.items())
            attrib.clear()
            attrib.update(attribs)


def stringify_xml(node: "Element", namespaces: "Dict[str, str]"):
    """
    Convert an element node to string, retaining namespace prefixes on names.

    ElementTree puts namespace declarations in the output nodes. In order to
    make an exact node fragment string comparison, the declarations need to be
    removed but the prefixes need to remain.

    For example a document has an element "x:localname" which ETree reads as
    "{uri}localname". The output would have a namespace declaration like
    'xmlns:x="http://etc"'. This keeps "x:localname" without the declaration.

    :param node: The ETree XML Element to process.
    :param namespaces: Namespaces known to be used by the XML document.
    """

    def swap_ns(name):
        for ns, uri in namespaces.items():
            if ns != "":
                ns += ":"
            if uri in name:
                name = name.replace("{" + uri + "}", ns)
        return name

    def strip_ns(n):
        if hasattr(n, "tag"):
            n.tag = swap_ns(name=n.tag)
        if hasattr(n, "attrib"):
            keys = ((k, swap_ns(name=k)) for k in n.attrib.keys())
            n.attrib = {new: n.attrib[old] for old, new in keys}

    def strip_ns_recurse(_node):
        strip_ns(_node)
        for child in _node:
            strip_ns_recurse(child)

    strip_ns_recurse(node)
    reorder_attributes(node)  # Required to match attribute order.
    enc = ETree.tostring(node, encoding="unicode")
    return enc.strip().replace(" />", "/>")


def xpath_tokenizer__v3_8(pattern, namespaces=None):
    """
    Copied verbatim from CPython 3.8 source, for 3.7 backwards compatibility.

    https://github.com/python/cpython/blob/5a42a49477cd601d67d81483f9589258dccb14b1/Lib/xml/etree/ElementPath.py#L73-L94
    """
    default_namespace = namespaces.get('') if namespaces else None
    parsing_attribute = False
    for token in EPath.xpath_tokenizer_re.findall(pattern):
        ttype, tag = token
        if tag and tag[0] != "{":
            if ":" in tag:
                prefix, uri = tag.split(":", 1)
                try:
                    if not namespaces:
                        raise KeyError
                    yield ttype, "{%s}%s" % (namespaces[prefix], uri)
                except KeyError:
                    raise SyntaxError("prefix %r not found in prefix map" % prefix) from None
            elif default_namespace and not parsing_attribute:
                yield ttype, "{%s}%s" % (default_namespace, tag)
            else:
                yield token
            parsing_attribute = False
        else:
            yield token
            parsing_attribute = ttype == '@'


@contextmanager
def xpath_tokenizer_swap():
    """
    If on Python < 3.8, swap the ElementPath xpath_tokenizer to the 3.8 one.

    See https://bugs.python.org/issue28238
    The relevant fix for pyxform is insertion of default namespace to tag name.
    """
    xpath_tokenizer__epath = EPath.xpath_tokenizer
    try:
        if sys.version_info < (3, 8, 0):
            EPath.xpath_tokenizer = xpath_tokenizer__v3_8
        yield
    finally:
        if sys.version_info < (3, 8, 0):
            EPath.xpath_tokenizer = xpath_tokenizer__epath
