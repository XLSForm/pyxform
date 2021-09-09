import unittest
from pyxform.utils import levenshtein_distance


""" /* To test in Postgres */
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
SELECT levenshtein(a, b)
FROM (
  VALUES
    ('sitting', 'kitten'),
    ('Sunday', 'Saturday'),
    ('settings', 'settings'),
    ('setting', 'settings'),
    ('abcdefghijklm', 'nopqrstuvwxyz'),
    ('abc  klm', '** _rs /wxyz'),
    ('ABCD', 'abcd')
) as t(a, b);
"""


class TestLevenshteinDistance(unittest.TestCase):
    def test_levenshtein_distance(self):
        """Should return the expected distance value."""
        # Verified against Postgres v10 extension "fuzzystrmatch" levenshtein().
        test_data = (
            (3, "sitting", "kitten"),
            (3, "Sunday", "Saturday"),
            (0, "settings", "settings"),
            (1, "setting", "settings"),
            (13, "abcdefghijklm", "nopqrstuvwxyz"),
            (11, "abc  klm", "** _rs /wxyz"),
            (4, "ABCD", "abcd"),
        )
        for i in test_data:
            self.assertEqual(i[0], levenshtein_distance(i[1], i[2]), str(i))
