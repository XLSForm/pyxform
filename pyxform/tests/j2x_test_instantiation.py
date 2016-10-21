"""
Testing the instance object for pyxform.
"""
from unittest import TestCase
from pyxform import *
from pyxform.builder import create_survey_element_from_dict
from pyxform.tests.utils import prep_class_config


class Json2XformExportingPrepTests(TestCase):

    @classmethod
    def setUpClass(cls):
        prep_class_config(cls=cls)

    def test_simple_survey_instantiation(self):
        surv = Survey(name=u"Simple")
        q = create_survey_element_from_dict(
            {u"type": u"text",
             u"name": u"survey_question",
             u"label": u"Question"})
        surv.add_child(q)
        
        i = surv.instantiate()
        
        self.assertEquals(i.keys(), [u"survey_question"])
        self.assertEquals(set(i.xpaths()),
                          {u"/Simple", u"/Simple/survey_question"})
    
    def test_simple_survey_answering(self):
        surv = Survey(name=u"Water")
        q = create_survey_element_from_dict({
            u"type": u"text",
            u"name": u"color",
            u"label": u"Color"})
        q2 = create_survey_element_from_dict({
            u"type": u"text",
            u"name": u"feeling",
            u"label": u"Feeling"})
        
        surv.add_child(q)
        surv.add_child(q2)
        i = SurveyInstance(surv)
        
        i.answer(name=u"color", value=u"blue")
        self.assertEquals(i.answers()[u'color'], u"blue")
        
        i.answer(name=u"feeling", value=u"liquidy")
        self.assertEquals(i.answers()[u'feeling'], u"liquidy")
        
    def test_answers_can_be_imported_from_xml(self):
        surv = Survey(name=u"data")
        
        surv.add_child(create_survey_element_from_dict({
            u'type': u'text', u'name': u'name', u"label": u"Name"}))
        surv.add_child(create_survey_element_from_dict({
            u'type': u'integer', u'name': u'users_per_month',
            u"label": u"Users per month"}))
        surv.add_child(create_survey_element_from_dict({
            u'type': u'gps', u'name': u'geopoint', u'label': u'gps'}))
        surv.add_child(create_survey_element_from_dict({
            u'type': u'imei', u'name': u'device_id'}))
        
        instance = surv.instantiate()
        import_xml = self.config.get(
            self.cls_name, "test_answers_can_be_imported_from_xml")
        instance.import_from_xml(import_xml)
        
    def test_simple_registration_xml(self):
        reg_xform = Survey(name=u"Registration")
        name_question = create_survey_element_from_dict({
            u'type': u'text', u'name': u'name', u"label": u"Name"})
        reg_xform.add_child(name_question)
        
        reg_instance = reg_xform.instantiate()
        
        reg_instance.answer(name=u"name", value=u"bob")
        
        rx = reg_instance.to_xml()
        expected_xml = self.config.get(
            self.cls_name, "test_simple_registration_xml"
        ).format(reg_xform.id_string)
        self.assertEqual(rx, expected_xml)
