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
        expectedStr += """/html/body/select1[@ref=${test1}]/item/value
    With element <value>"""
        self.assertEqual(_cleanup_errors(testStr), expectedStr.strip())

    def test_do_not_over_trim_javarosa_errors(self):
        testStr = """
org.javarosa.xpath.XPathUnhandledException: XPath evaluation: cannot handle function 'testfunc'
org.javarosa.xpath.XPathUnhandledException: XPath evaluation: cannot handle function 'testfunc'
\tat org.javarosa.xpath.expr.XPathFuncExpr.eval(XPathFuncExpr.java:270)
\tat org.javarosa.xpath.XPathConditional.evalRaw(XPathConditional.java:68)
\tat org.javarosa.core.model.condition.Recalculate.eval(Recalculate.java:53)
\tat org.javarosa.core.model.condition.Triggerable.apply(Triggerable.java:69)
\tat org.javarosa.core.model.FormDef.evaluateTriggerable(FormDef.java:706)
\tat org.javarosa.core.model.FormDef.evaluateTriggerables(FormDef.java:696)
\tat org.javarosa.core.model.FormDef.initializeTriggerables(FormDef.java:651)
\tat org.javarosa.core.model.FormDef.initializeTriggerables(FormDef.java:629)
\tat org.javarosa.core.model.FormDef.initialize(FormDef.java:1123)
\tat org.odk.validate.FormValidator.validate(FormValidator.java:336)
\tat org.odk.validate.FormValidator.<init>(FormValidator.java:95)
\tat org.odk.validate.FormValidator.main(FormValidator.java:82)
\tat sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
\tat sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:39)
\tat sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:25)
\tat java.lang.reflect.Method.invoke(Method.java:597)
\tat org.eclipse.jdt.internal.jarinjarloader.JarRsrcLoader.main(JarRsrcLoader.java:58)
>> Something broke the parser. See above for a hint.
Result: Invalid"""
        expectedStr = """
XPath evaluation: cannot handle function 'testfunc'
>> Something broke the parser. See above for a hint.
Result: Invalid"""
        self.assertEqual(_cleanup_errors(testStr), expectedStr.strip())
