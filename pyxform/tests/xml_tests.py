from pyxform import create_survey_from_xls
import re
import utils


class XMLTests(utils.XFormTestCase):

    def setUp(self):
        self.survey = create_survey_from_xls(
            utils.path_to_text_fixture("yes_or_no_question.xls"))

    def test_to_xml(self):
        xml_str = u'''<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>yes_or_no_question</h:title>
    <model>
      <itext>
        <translation lang="english">
          <text id="/yes_or_no_question/good_day:label">
            <value>have you had a good day today?</value>
          </text>
          <text id="/yes_or_no_question/good_day/no:label">
            <value>no</value>
          </text>
          <text id="/yes_or_no_question/good_day/yes:label">
            <value>yes</value>
          </text>
        </translation>
      </itext>
      <instance>
        <yes_or_no_question id="yes_or_no_question_2011_04_22">
          <good_day/>
          <meta>
            <instanceID/>
          </meta>
        </yes_or_no_question>
      </instance>
      <bind nodeset="/yes_or_no_question/good_day" type="select1"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/yes_or_no_question/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <select1 ref="/yes_or_no_question/good_day">
      <label ref="jr:itext('/yes_or_no_question/good_day:label')"/>
      <item>
        <label ref="jr:itext('/yes_or_no_question/good_day/yes:label')"/>
        <value>yes</value>
      </item>
      <item>
        <label ref="jr:itext('/yes_or_no_question/good_day/no:label')"/>
        <value>no</value>
      </item>
    </select1>
  </h:body>
</h:html>
'''
        xml_str = re.sub(r"yes_or_no_question_2011_04_22",
                         self.survey.id_string, xml_str)
        self.maxDiff = None
        self.assertXFormEqual(xml_str, self.survey.to_xml())
