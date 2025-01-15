"""
PyxformTestCase base class using markdown to define the XLSForm.
"""

import logging
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from unittest import TestCase

from lxml import etree

# noinspection PyProtectedMember
from lxml.etree import _Element
from pyxform.constants import NSMAP
from pyxform.errors import PyXFormError
from pyxform.utils import coalesce
from pyxform.validators.odk_validate import ODKValidateError, check_xform
from pyxform.xls2json_backends import SupportedFileTypes
from pyxform.xls2xform import ConvertResult, convert

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


if TYPE_CHECKING:
    from pyxform.survey import Survey

    NSMAPSubs: "list[tuple[str, str]]"


class PyxformTestError(Exception):
    pass


@dataclass(slots=True)
class MatcherContext:
    debug: bool
    nsmap_xpath: "dict[str, str]"
    nsmap_subs: "NSMAPSubs"
    content_str: str


def _run_odk_validate(xml):
    # On Windows, NamedTemporaryFile must be opened exclusively.
    # So it must be explicitly created, opened, closed, and removed
    tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    tmp.close()
    try:
        with open(tmp.name, mode="w", encoding="utf-8") as fp:
            fp.write(xml)
            fp.close()
        check_xform(tmp.name)
    finally:
        # Clean up the temporary file
        tmp_path = Path(tmp.name)
        tmp_path.unlink(missing_ok=True)
        if tmp_path.is_file():
            raise PyXFormError(f"Temporary file still exists: {tmp.name}")


class PyxformTestCase(TestCase):
    maxDiff = None

    def assertPyxformXform(
        self,
        # Survey input
        md: str | None = None,
        ss_structure: dict | None = None,
        survey: Optional["Survey"] = None,
        # XForm assertions
        xml__xpath_match: Iterable[str] | None = None,
        xml__xpath_exact: Iterable[tuple[str, set[str]]] | None = None,
        xml__xpath_count: Iterable[tuple[str, int]] | None = None,
        # XForm assertions - deprecated
        xml__contains: Iterable[str] | None = None,
        xml__excludes: Iterable[str] | None = None,
        model__contains: Iterable[str] | None = None,
        model__excludes: Iterable[str] | None = None,
        itext__contains: Iterable[str] | None = None,
        itext__excludes: Iterable[str] | None = None,
        instance__contains: Iterable[str] | None = None,
        # Errors assertions
        error__contains: Iterable[str] | None = None,
        error__not_contains: Iterable[str] | None = None,
        odk_validate_error__contains: Iterable[str] | None = None,
        warnings__contains: Iterable[str] | None = None,
        warnings__not_contains: Iterable[str] | None = None,
        warnings_count: int | None = None,
        errored: bool = False,
        # Optional extras
        name: str | None = None,
        warnings: list[str] | None = None,
        run_odk_validate: bool = False,
        debug: bool = False,
    ) -> ConvertResult | None:
        """
        One survey input:
        :param md: a markdown formatted xlsform (easy to read in code). Escape a literal
          pipe value with a single back-slash.
        :param ss_structure: a dictionary with sheets and their contents. Best used in
          cases where testing whitespace and cells' type is important.
        :param survey: easy for reuse within a test
        # Note: XLS is not implemented at this time. You can use builder to create a
        pyxform Survey object

        One or more XForm assertions:
        :param xml__xpath_exact: A list of tuples where the first tuple element is an
          XPath expression and the second tuple element is a set of exact string match
          results that are expected. E.g. `[(".//some_xpath", {"match1", "match2"}), ...]`
        :param xml__xpath_count: A list of tuples where the first tuple element is an
          XPath expression and the second tuple element is the integer number of match
          results that are expected. E.g. `[(".//some_xpath", 1), (".//an_xpath", 2)]`
        :param xml__xpath_match: A list of XPath expression strings for which exactly one
          match result each is expected. Effectively a shortcut for xml__xpath_count with
          a count of 1. E.g. `[".//some_xpath", ".//an_xpath"]`

        For each of the xpath_* assertions above, if the XPath expression looks for an
        element in the 'default' namespace (xforms) then use an 'x' namespace prefix for
        the element. For example to find input nodes in the body: ".//h:body/x:input".
        This 'x' prefix is not required for attributes. When writing a xpath_* test, the
        option debug=True can be used to show the XPath match results.

        XForm assertions that should not be used in new tests:
        :param xml__contains: Strings that should which exist in the XForm.
        :param xml__excludes: Strings that should not exist in the XForm.
        :param model__contains: Strings that should exist in the XForm model.
        :param model__excludes: Strings that should not exist in the XForm model.
        :param itext__contains: Strings that should exist in the XForm itext.
        :param itext__excludes: Strings that should not exist in the XForm itext.
        :param instance__contains: Strings that should exist in the XForm main instance.

        One or more Pyxform errors assertions:
        :param error__contains: Strings which should exist in the PyxformError.
        :param error__not_contains: Strings which should not exist in the PyxformError.
        :param odk_validate_error__contains: Strings which should exist in the ODK
          Validate error. The parameter `run_odk_validate` must be set for this to work.
        :param warnings__contains: Strings which should exist in the warnings.
        :param warnings__not_contains: Strings which should not exist in the warnings.
        :param warnings_count: the number of expected warning messages.
        :param errored: If True, it is expected that a PyxformError will be raised.

        Optional extra parameters:
        :param name: a valid xml tag, for the root element in the XForm main instance.
        :param warnings: a list to use for storing warnings for inspection.
        :param run_odk_validate: If True, run ODK Validate on the XForm output.
        :param debug: If True, log details of the test to stdout. Details include the
          input survey markdown, the XML document, XPath match strings.
        """
        errors = []
        warnings = coalesce(warnings, [])
        xml_nodes = {}

        odk_validate_error__contains = coalesce(odk_validate_error__contains, [])
        survey_valid = True
        result = None

        try:
            if survey is None:
                result = convert(
                    xlsform=coalesce(md, ss_structure),
                    pretty_print=True,
                    form_name=coalesce(name, "test_name"),
                    warnings=warnings,
                    file_type=SupportedFileTypes.md.value,
                )
                survey = result._survey
                xml = result.xform
            else:
                xml = survey._to_pretty_xml()
            root = etree.fromstring(xml.encode("utf-8"))

            # Ensure all namespaces are present, even if unused
            survey_nsmap = survey.get_nsmap()
            final_nsmap = NSMAP.copy()
            final_nsmap.update(survey_nsmap)
            root.nsmap.update(final_nsmap)
            final_nsmap_xpath = {
                "x": final_nsmap["xmlns"],
                **{k.split(":")[1]: v for k, v in final_nsmap.items() if k != "xmlns"},
            }
            final_nsmap_subs = [(f' {k}="{v}"', "") for k, v in final_nsmap.items()]
            # guarantee that strings contain alphanumerically sorted attributes across
            # Python versions
            reorder_attributes(root)

            xml_nodes["xml"] = root

            def _pull_xml_node_from_root(element_selector):
                _r = root.findall(
                    f".//n:{element_selector}",
                    namespaces={"n": "http://www.w3.org/2002/xforms"},
                )
                if _r:
                    return _r[0]

                return None

            for _n in ["model", "instance", "itext"]:
                xml_nodes[_n] = _pull_xml_node_from_root(_n)
            if debug:
                logger.debug(xml)
            if run_odk_validate:
                _run_odk_validate(xml=xml)
                if odk_validate_error__contains:
                    raise PyxformTestError("ODKValidateError was not raised")

        except PyXFormError as e:
            survey_valid = False
            errors = [str(e)]
            if debug:
                logger.debug("<xml unavailable />")
                logger.debug("ERROR: '%s'", errors[0])
            if not errored:
                raise PyxformTestError(
                    "Expected valid survey but compilation failed. Try correcting the "
                    "error with 'debug=True', setting 'errored=True', and or optionally "
                    "'error__contains=[...]'\nError(s): " + "\n".join(errors)
                ) from e
        except ODKValidateError as e:
            if not odk_validate_error__contains:
                raise PyxformTestError(
                    "ODK Validate error was thrown but 'odk_validate_error__contains' "
                    "was empty: " + str(e)
                ) from e
            for v_err in odk_validate_error__contains:
                self.assertContains(
                    e.args[0], v_err, msg_prefix="odk_validate_error__contains"
                )

        if survey_valid:
            if errored:
                raise PyxformTestError("Expected survey to be invalid.")

            xml_nodes_str = {}

            def get_xml_nodes_str(node_key: str) -> str:
                if node_key not in xml_nodes_str:
                    xml_nodes_str[node_key] = etree.tostring(
                        xml_nodes[node_key], encoding=str, pretty_print=True
                    )
                return xml_nodes_str[node_key]

            string_test_specs = (
                (xml__contains, "xml", self.assertContains),
                (xml__excludes, "xml", self.assertNotContains),
                (instance__contains, "instance", self.assertContains),
                (model__contains, "model", self.assertContains),
                (model__excludes, "model", self.assertNotContains),
                (itext__contains, "itext", self.assertContains),
                (itext__excludes, "itext", self.assertNotContains),
            )

            for test_spec, key, test_func in string_test_specs:
                if test_spec is not None:
                    for i in test_spec:
                        test_func(content=get_xml_nodes_str(key), text=i, msg_prefix=key)

            def get_xpath_matcher_context():
                return MatcherContext(
                    debug=debug,
                    nsmap_xpath=final_nsmap_xpath,
                    nsmap_subs=final_nsmap_subs,
                    content_str=get_xml_nodes_str("xml"),
                )

            if xml__xpath_exact is not None:
                xpath_matcher = get_xpath_matcher_context()
                for idx, i in enumerate(xml__xpath_exact, start=1):
                    self.assert_xpath_exact(
                        matcher_context=xpath_matcher,
                        content=xml_nodes["xml"],
                        xpath=i[0],
                        expected=i[1],
                        case_num=idx,
                    )

            if xml__xpath_count is not None:
                xpath_matcher = get_xpath_matcher_context()
                for idx, i in enumerate(xml__xpath_count, start=1):
                    self.assert_xpath_count(
                        matcher_context=xpath_matcher,
                        content=xml_nodes["xml"],
                        xpath=i[0],
                        expected=i[1],
                        case_num=idx,
                    )

            if xml__xpath_match is not None:
                xpath_matcher = get_xpath_matcher_context()
                for idx, i in enumerate(xml__xpath_match, start=1):
                    self.assert_xpath_count(
                        matcher_context=xpath_matcher,
                        content=xml_nodes["xml"],
                        xpath=i,
                        expected=1,
                        case_num=idx,
                    )

        problem_test_specs = (
            (error__contains, "errors", errors, self.assertContains),
            (error__not_contains, "errors", errors, self.assertNotContains),
            (warnings__contains, "warnings", warnings, self.assertContains),
            (warnings__not_contains, "warnings", warnings, self.assertNotContains),
        )
        for test_spec, prefix, test_obj, test_func in problem_test_specs:
            if test_spec is not None:
                test_str = "\n".join(test_obj)
                for i in test_spec:
                    test_func(content=test_str, text=i, msg_prefix=prefix)

        if warnings_count is not None:
            if not isinstance(warnings_count, int):
                raise PyxformTestError("warnings_count must be an integer.")
            self.assertEqual(warnings_count, len(warnings))

        return result

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
                f"{msg_prefix}Couldn't find {text_repr} in content:\n{content}",
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
            real_count, 0, f"{msg_prefix}Response should not contain {text_repr}"
        )

    def assert_xpath_exact(
        self,
        matcher_context: "MatcherContext",
        content: "_Element",
        xpath: str,
        expected: "set[str]",
        case_num: int,
    ) -> None:
        """
        Process an assertion for xml__xpath_exact.

        Compares result strings since expected strings may contain xml namespace prefixes.
        To allow parsing required to compare as ETrees would require injecting namespace
        declarations into the expected match strings.

        :param matcher_context: A MatcherContext dataclass.
        :param content: XML to be examined.
        :param xpath: XPath to execute.
        :param expected: Expected XPath matches, as XML fragments.
        :param case_num: The list position of the test case in the input.
        """
        if not (isinstance(xpath, str) and isinstance(expected, set)):
            msg = "Each xpath_exact requires: tuple(xpath: str, expected: Set[str])."
            raise TypeError(msg)
        observed = xpath_evaluate(
            matcher_context=matcher_context,
            content=content,
            xpath=xpath,
            for_exact=True,
        )
        msg = (
            f"XPath found no matches (test case {case_num}):\n{xpath}"
            f"\n\nXForm content:\n{matcher_context.content_str}"
        )
        self.assertSetEqual(set(expected), observed, msg=msg)

    def assert_xpath_count(
        self,
        matcher_context: "MatcherContext",
        content: "_Element",
        xpath: str,
        expected: int,
        case_num: int,
    ):
        """
        Process an assertion for xml__xpath_count.

        :param matcher_context: A MatcherContext dataclass.
        :param content: XML to be examined.
        :param xpath: XPath to execute.
        :param expected: Expected count of XPath matches.
        :param case_num: The list position of the test case in the input.
        """
        if not (isinstance(xpath, str) and isinstance(expected, int)):
            msg = "Each xpath_count requires: tuple(xpath: str, count: int)"
            raise TypeError(msg)
        observed = xpath_evaluate(
            matcher_context=matcher_context,
            content=content,
            xpath=xpath,
        )
        msg = (
            f"XPath did not find the expected number of matches ({expected}, test case {case_num}):\n{xpath}"
            f"\n\nXForm content:\n{matcher_context.content_str}"
        )
        self.assertEqual(expected, len(observed), msg=msg)


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


def xpath_clean_result_strings(
    nsmap_subs: "NSMAPSubs", results: "set[_Element]"
) -> "set[str]":
    """
    Clean XPath results: stringify, remove namespace declarations, clean up whitespace.

    :param nsmap_subs: namespace replacements e.g. [('x="http://www.w3.org/2002/xforms", "")]
    :param results: XPath results to clean.
    """
    xmlex = [(" >", ">"), (" />", "/>")]
    subs = nsmap_subs + xmlex
    cleaned = set()
    for x in results:
        if isinstance(x, _Element):
            reorder_attributes(x)
            x = etree.tostring(x, encoding=str, pretty_print=True)
            x = x.strip()
            for s in subs:
                x = x.replace(*s)
        cleaned.add(x)
    return cleaned


def xpath_evaluate(
    matcher_context: "MatcherContext", content: "_Element", xpath: str, for_exact=False
) -> "set[_Element] | set[str]":
    """
    Evaluate an XPath and return the results.

    :param matcher_context: A MatcherContext dataclass.
    :param content: XML to be examined.
    :param xpath: XPath to execute.
    :param for_exact: If True, convert the results to strings and perform clean-up. If
      False, return the set of Element (or attribute string) matches as-is.
    :return:
    """
    try:
        results = content.xpath(xpath, namespaces=matcher_context.nsmap_xpath)
    except etree.XPathEvalError as e:
        msg = f"Error processing XPath: {xpath}\n" + "\n".join(e.args)
        raise PyxformTestError(msg) from e
    if matcher_context.debug:
        if 0 == len(results):
            logger.debug(f"Results for XPath: {xpath}\n" + "(No matches)" + "\n")
        else:
            cleaned = xpath_clean_result_strings(
                nsmap_subs=matcher_context.nsmap_subs, results=results
            )
            logger.debug(f"Results for XPath: {xpath}\n" + "\n".join(cleaned) + "\n")
    if for_exact:
        return xpath_clean_result_strings(
            nsmap_subs=matcher_context.nsmap_subs, results=results
        )
    else:
        return set(results)
