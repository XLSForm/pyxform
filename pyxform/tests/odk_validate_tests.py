from pyxform.odk_validate import _cleanup_errors

from unittest2 import TestCase


class ODKValidateTests(TestCase):
    def test_cleanup_error_message(self):
        testStr = """
Invalid XPath expression [ /Frm13/Section4/pictures_repeat  <> 'Inacc']!
Invalid XPath expression [ /Frm13/Section4/pictures_repeat/Demo  <> 'Inacc']!
Invalid XPath expression [ /Frm13/Section4/pictures/repeat/aDemo  <> 'Inacc']!

WARNING: choice value [Internationalcalltariffsareattractive] is too long"""
        testStr += """; max. suggested length 32 chars
Problem found at nodeset: """
        testStr += """/html/body/select1[@ref=/some/test1]/item/value
    With element <value>
"""
        expectedStr = """
Invalid XPath expression [ ${pictures_repeat}  <> 'Inacc']!
Invalid XPath expression [ ${Demo}  <> 'Inacc']!
Invalid XPath expression [ ${aDemo}  <> 'Inacc']!

WARNING: choice value [Internationalcalltariffsareattractive] is too long"""
        expectedStr += """; max. suggested length 32 chars
Problem found at nodeset: """
        expectedStr += """/html/body/select1[@ref=/some/test1]/item/value
    With element <value>"""
        self.assertEqual(_cleanup_errors(testStr), expectedStr)
