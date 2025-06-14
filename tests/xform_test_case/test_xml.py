"""
Test XForm XML syntax.
"""

from sys import version_info
from unittest import TestCase
from xml.dom.minidom import getDOMImplementation

from pyxform import create_survey_from_xls
from pyxform.utils import node

from tests.utils import path_to_text_fixture
from tests.xform_test_case.base import XFormTestCase


class XMLTests(XFormTestCase):
    maxDiff = None

    def setUp(self):
        self.survey = create_survey_from_xls(
            path_to_text_fixture("yes_or_no_question.xls"), "yes_or_no_question"
        )

    def test_to_xml(self):
        xml_str = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms"
    xmlns:ev="http://www.w3.org/2001/xml-events"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns:jr="http://openrosa.org/javarosa"
    xmlns:orx="http://openrosa.org/xforms"
    xmlns:odk="http://www.opendatakit.org/xforms"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>yes_or_no_question</h:title>
    <model odk:xforms-version="1.0.0">
      <itext>
        <translation lang="english">
          <text id="/yes_or_no_question/good_day:label">
            <value>have you had a good day today?</value>
          </text>
          <text id="yes_or_no-0">
            <value>yes</value>
          </text>
          <text id="yes_or_no-1">
            <value>no</value>
          </text>
        </translation>
      </itext>
      <instance>
        <yes_or_no_question id="yes_or_no_question">
          <good_day/>
          <meta>
            <instanceID/>
          </meta>
        </yes_or_no_question>
      </instance>
      <instance id="yes_or_no">
        <root>
          <item>
            <itextId>yes_or_no-0</itextId>
            <name>yes</name>
          </item>
          <item>
            <itextId>yes_or_no-1</itextId>
            <name>no</name>
          </item>
        </root>
      </instance>
      <bind nodeset="/yes_or_no_question/good_day" type="string"/>
      <bind jr:preload="uid"
        nodeset="/yes_or_no_question/meta/instanceID"
        readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <select1 ref="/yes_or_no_question/good_day">
      <label ref="jr:itext('/yes_or_no_question/good_day:label')"/>
      <itemset nodeset="instance('yes_or_no')/root/item">
        <value ref="name"/>
        <label ref="jr:itext(itextId)"/>
      </itemset>
    </select1>
  </h:body>
</h:html>
"""
        self.assertXFormEqual(xml_str, self.survey.to_xml())


class MinidomTextWriterMonkeyPatchTest(TestCase):
    maxDiff = None

    def test_patch_lets_node_func_escape_only_necessary(self):
        """Should find that pyxform escapes ["&<>] in attrs and [&<>] in text."""
        replaceable_chars = "' \" & < > \r \n \t"
        expected = """<root attr="' &quot; &amp; &lt; &gt; \r \n \t">' " &amp; &lt; &gt; \r \n \t</root>"""
        observed = node("root", replaceable_chars, attr=replaceable_chars).toprettyxml(
            indent="", newl=""
        )
        self.assertEqual(expected, observed)

    def test_original_escape_escapes_more_than_necessary(self):
        """Should fail if the original is updated (the patch can be removed)."""
        replaceable_chars = "' \" & < > \r \n \t"
        document = getDOMImplementation().createDocument(None, "root", None)
        root = document.documentElement
        root.appendChild(document.createTextNode(replaceable_chars))
        root.setAttribute("attr", replaceable_chars)
        observed = root.toprettyxml(indent="", newl="")
        if version_info.major == 3 and version_info.minor >= 13:
            # In 3.13, minidom was updated to only escape " in attrs, and also escape \r\n\t.
            expected = """<root attr="' &quot; &amp; &lt; &gt; &#13; &#10; &#9;">' " &amp; &lt; &gt; \r \n \t</root>"""
            self.assertEqual(expected, observed)
        else:
            # Prior to 3.13 " was escaped in text unnecessarily, and \r\n\t not escaped in attrs.
            expected = """<root attr="' &quot; &amp; &lt; &gt; \r \n \t">' &quot; &amp; &lt; &gt; \r \n \t</root>"""
            self.assertEqual(expected, observed)
