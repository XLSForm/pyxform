"""
Testing simple cases for pyxform
"""
from unittest import TestCase
from pyxform.survey import Survey

from pyxform.builder import create_survey_element_from_dict


# TODO:
#  * test_two_questions_with_same_id_fails
#     (get this working in json2xform)

class BasicJson2XFormTests(TestCase):
    def test_survey_can_have_to_xml_called_twice(self):
        """
        Test: Survey can have "to_xml" called multiple times
        
        (This was not being allowed before.)
        
        It would be good to know (with confidence) that a survey object
        can be exported to_xml twice, and the same thing will be returned
        both times.
        """
        survey = Survey(name=u"SampleSurvey")
        q = create_survey_element_from_dict(
            {u'type': u'text', u'name': u'name', u'label': u'label'})
        survey.add_child(q)

        str1 = survey.to_xml()
        str2 = survey.to_xml()

        self.assertEqual(str1, str2)
