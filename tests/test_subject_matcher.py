"""
Unit tests for subject matcher utility.
"""
from __future__ import annotations

import unittest
from src.votetracker.subject_matcher import (
    normalize_subject,
    find_best_match,
    suggest_canonical_name,
    get_auto_suggestions,
)


class TestSubjectMatcher(unittest.TestCase):
    """Test suite for Subject Matcher."""

    def test_normalize_subject(self):
        self.assertEqual(normalize_subject("  Matematica  "), "matematica")
        self.assertEqual(normalize_subject("ENGLISH"), "english")

    def test_find_best_match_exact(self):
        match = find_best_match("Matematica", ["Matematica", "Storia"])
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[0], "Matematica")
        self.assertEqual(match[1], 1.0)

    def test_find_best_match_keyword(self):
        # "algebra" is keyword for Math
        match = find_best_match("algebra", ["Math", "History"])
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match[0], "Math")
        self.assertGreaterEqual(match[1], 0.8)

    def test_suggest_canonical_name(self):
        self.assertEqual(suggest_canonical_name("lingua italiana"), "Italian")
        self.assertEqual(suggest_canonical_name("scienze naturali"), "Science")
        self.assertIsNone(suggest_canonical_name("materia_sconosciuta_xyz"))

    def test_get_auto_suggestions_existing(self):
        suggestion = get_auto_suggestions("Inglese", ["English", "Math"])
        self.assertEqual(suggestion["suggested_match"], "English")
        self.assertIn(suggestion["action"], ["map", "create"])

    def test_get_auto_suggestions_new_canonical(self):
        suggestion = get_auto_suggestions("filosofia", ["Math", "Physics"])
        self.assertEqual(suggestion["suggested_new"], "Philosophy")
        self.assertEqual(suggestion["action"], "create")


if __name__ == '__main__':
    unittest.main()
