# The Django application xls2xform uses the function
# pyxform.create_survey. We have a test here to make sure no one
# breaks that function.

from unittest import TestCase
import pyxform


class XLS2XFormTests(TestCase):
    survey_package = {
        'id_string': u'test_2011_08_29b',
        'name_of_main_section': u'gps',
        'sections': {
            u'gps': {
                u'children': [
                    {
                        u'name': u'location',
                        u'type': u'gps'
                        }
                    ],
                u'name': u'gps',
                u'type': u'survey'
                }
            },
        'title': u'test'
        }
    survey = pyxform.create_survey(**survey_package)