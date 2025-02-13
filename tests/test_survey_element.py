import warnings
from unittest import TestCase

from pyxform.survey_element import SurveyElement


class TestSurveyElementMappingBehaviour(TestCase):
    def tearDown(self):
        # Undo the warnings filter set in the below test.
        warnings.resetwarnings()

    def test_get_call_patterns_equivalent_to_base_dict(self):
        """Should find that, except for deprecated usage, SurveyElement is dict-like."""
        # To demonstrate how dict normally works using same test cases.
        _dict = {"name": "test", "label": None}
        # getattr
        self.assertEqual("default", getattr(_dict, "foo", "default"))
        # defined key, no default
        self.assertEqual("test", _dict.get("name"))
        # defined key, with default
        self.assertEqual("test", _dict.get("name", "default"))
        # defined key, with None value
        self.assertEqual(None, _dict.get("label"))
        # defined key, with None value, with default
        self.assertEqual(None, _dict.get("label", "default"))
        # undefined key, with default
        self.assertEqual("default", _dict.get("foo", "default"))
        # undefined key, with default None
        self.assertEqual(None, _dict.get("foo", None))
        # other access patterns for undefined key
        self.assertEqual(None, _dict.get("foo"))
        with self.assertRaises(AttributeError):
            _ = _dict.foo
        with self.assertRaises(KeyError):
            _ = _dict["foo"]

        elem = SurveyElement(name="test")
        # getattr
        self.assertEqual("default", getattr(elem, "foo", "default"))
        # defined key, no default
        self.assertEqual("test", elem.get("name"))
        # defined key, with default
        self.assertEqual("test", elem.get("name", "default"))
        # defined key, with None value
        self.assertEqual(None, elem.get("label"))
        # defined key, with None value, with default
        self.assertEqual(None, elem.get("label", "default"))
        # undefined key, with default
        with self.assertWarns(DeprecationWarning) as warned:
            self.assertEqual("default", elem.get("foo", "default"))
        # Warning points to caller, rather than survey_element or collections.abc.
        self.assertEqual(__file__, warned.filename)
        # undefined key, with default None
        with self.assertWarns(DeprecationWarning) as warned:
            self.assertEqual(None, elem.get("foo", None))
        # Callers can disable warnings at module-level.
        warnings.simplefilter("ignore", DeprecationWarning)
        with warnings.catch_warnings(record=True) as warned:
            elem.get("foo", "default")
        self.assertEqual(0, len(warned))
        # other access patterns for undefined key
        with self.assertRaises(AttributeError):
            _ = elem.get("foo")
        with self.assertRaises(AttributeError):
            _ = elem.foo
        with self.assertRaises(AttributeError):
            _ = elem["foo"]
