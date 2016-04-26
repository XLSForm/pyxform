# -*- coding: utf-8 -*-
from unittest import TestCase
from pyxform.errors import PyXFormError
from lxml import etree
import re
from pyxform.tests_v1.test_utils.md_table import md_table_to_ss_structure
from pyxform.xls2json import workbook_to_json
from pyxform.builder import create_survey_element_from_dict


class PyxformTestError(Exception):
    pass


class PyxformTestCase(TestCase):
    def assertPyxformXform(self, *args, **kwargs):
        '''
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
                resulting xml
          * error__contains: an array of strings which should exist in
                the error
          * warning__contains: an array of strings which should exist in any
                warnings returned from the conversion
          # Note: Order of occurrence of items in the array is not yet checked)

        optional other parameters passed to pyxform:
          * errored: (bool) if the xlsform is not supposed to compile,
                this must be True
          * name: (str) a valid xml tag to be used as the form name
          * id_string: (str)
          * title: (str)
          # * validate: (bool) when True, runs ODK Validate process
          #       Default value = False because it slows down tests
        '''
        debug = kwargs.get('debug', False)
        expecting_invalid_survey = kwargs.get('errored', False)
        warnings = []
        errors = []
        xml_nodes = {}

        try:
            if 'md' in kwargs.keys():
                kwargs = self._autonameInputs(kwargs)
                survey = self.md_to_pyxform_survey(kwargs.get('md'), kwargs)
            elif 'ss_structure' in kwargs.keys():
                kwargs = self._autonameInputs(kwargs)
                survey = self._ss_structure_to_pyxform_survey(
                    kwargs.get('ss_structure'), kwargs)
            xml = survey.to_xml(warnings=warnings)
            root = etree.fromstring(xml)

            xml_nodes['xml'] = root

            def _pull_xml_node_from_root(element_selector):
                NS = 'http://www.w3.org/2002/xforms'
                _r = etree.XPath('//n:%s' % element_selector,
                                 namespaces={'n': NS})(root)
                if len(_r) == 0:
                    return False
                else:
                    return _r[0]

            for _n in ['model', 'instance', 'itext']:
                xml_nodes[_n] = _pull_xml_node_from_root(_n)
            if debug:
                print xml
        except PyXFormError, e:
            survey = False
            xml = ("<xml unavailable /> ! PyxformTestCaseError: "
                   "Could not compile XForm. See errors")
            errors = [str(e)]
            if debug:
                print "<xml unavailable />"
                print "ERROR: '%s'" % errors[0]

        if survey:
            def _check_contains(keyword):
                contains_str = '%s__contains' % keyword

                def check_content(content):
                    text_arr = kwargs[contains_str]
                    for text in text_arr:
                        self.assertContains(content, text, msg_prefix=keyword)

                return (contains_str, check_content)

            for code in ['xml', 'instance', 'model', 'itext']:
                (code__str, checker) = _check_contains(code)
                if kwargs.get(code__str):
                    checker(etree.tostring(xml_nodes[code]))

        if 'error__contains' in kwargs:
            joined_error = '\n'.join(errors)
            for text in kwargs['error__contains']:
                self.assertContains(joined_error, text,
                                    msg_prefix="error__contains")

        if survey is False and expecting_invalid_survey is False:
            raise PyxformTestError(
                "Expected valid survey but compilation failed. "
                "Try correcting the error with 'debug=True', "
                "setting 'errored=True', "
                "and or optionally 'error__contains=[...]'")

    def md_to_pyxform_survey(self, md_raw, kwargs={}, autoname=True):
        if autoname:
            kwargs = self._autonameInputs(kwargs)
        _md = []
        for line in md_raw.split('\n'):
            if re.match(r'^\s+\#', line):
                # ignore lines which start with pound sign
                continue
            elif re.match(r'^(.*)(\#[^\|]+)$', line):
                # keep everything before the # outside of the last occurrence
                # of |
                _md.append(
                    re.match(r'^(.*)(\#[^\|]+)$', line).groups()[0].strip())
            else:
                _md.append(line.strip())
        md = '\n'.join(_md)

        if kwargs.get('debug'):
            print md

        def list_to_dicts(arr):
            headers = arr[0]

            def _row_to_dict(row):
                out_dict = {}
                for i in range(0, len(row)):
                    col = row[i]
                    if col not in [None, '']:
                        out_dict[headers[i]] = col
                return out_dict

            return [_row_to_dict(r) for r in arr[1:]]

        sheets = {}
        for sheet, contents in md_table_to_ss_structure(md):
            sheets[sheet] = list_to_dicts(contents)

        return self._ss_structure_to_pyxform_survey(sheets, kwargs)

    def _ss_structure_to_pyxform_survey(self, ss_structure, kwargs):
        # using existing methods from the builder
        imported_survey_json = workbook_to_json(ss_structure)
        # ideally, when all these tests are working, this would be
        # refactored as well
        survey = create_survey_element_from_dict(imported_survey_json)
        survey.name = kwargs.get('name')
        survey.title = kwargs.get('title')
        survey.id_string = kwargs.get('id_string')

        return survey

    def _assert_contains(self, content, text, msg_prefix):
        if msg_prefix:
            msg_prefix += ": "

        text_repr = repr(text)
        real_count = content.count(text)

        return (text_repr, real_count, msg_prefix)

    def assertContains(self, content, text, count=None, msg_prefix=''):
        """
        FROM: django source- testcases.py

        Asserts that ``text`` occurs ``count`` times in the content string.
        If ``count`` is None, the count doesn't matter - the assertion is
        true if the text occurs at least once in the content.
        """
        text_repr, real_count, msg_prefix = self._assert_contains(
            content, text, msg_prefix)

        if count is not None:
            self.assertEqual(
                real_count, count,
                msg_prefix + "Found %d instances of %s in content"
                " (expected %d)" % (real_count, text_repr, count))
        else:
            self.assertTrue(
                real_count != 0,
                msg_prefix + "Couldn't find %s in content" % text_repr)

    def assertNotContains(self, content, text, msg_prefix=''):
        """
        Asserts that a content indicates that some content was retrieved
        successfully, (i.e., the HTTP status code was as expected), and that
        ``text`` doesn't occurs in the content of the content.
        """
        text_repr, real_count, msg_prefix = self._assert_contains(
            content, text, msg_prefix)

        self.assertEqual(
            real_count, 0,
            msg_prefix + "Response should not contain %s" % text_repr)

    def _autonameInputs(self, kwargs):
        '''
        title and name are necessary for surveys, but not always convenient to
        include in test cases, so this will pull a default value
        from the stack trace.
        '''
        test_name_root = 'pyxform'
        if 'name' not in kwargs.keys():
            kwargs['name'] = test_name_root + '_autotestname'
        if 'title' not in kwargs.keys():
            kwargs['title'] = test_name_root + "_autotesttitle"
        if 'id_string' not in kwargs.keys():
            kwargs['id_string'] = test_name_root + "_autotest_id_string"

        return kwargs
