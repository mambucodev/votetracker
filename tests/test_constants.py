"""
Unit tests for application constants.
"""
from __future__ import annotations

import unittest
from src.votetracker.constants import (
    PASSING_GRADE,
    GRADE_INSUFFICIENT,
    AVAILABLE_LANGUAGES
)

class TestConstants(unittest.TestCase):
    """Test suite for application constants."""

    def test_grade_thresholds(self):
        """Test that grade thresholds make logical sense."""
        self.assertLess(GRADE_INSUFFICIENT, PASSING_GRADE,
                        "Insufficient grade threshold must be strictly less than passing grade.")

    def test_available_languages(self):
        """Test that AVAILABLE_LANGUAGES is properly configured."""
        self.assertIsInstance(AVAILABLE_LANGUAGES, dict)
        self.assertTrue(len(AVAILABLE_LANGUAGES) > 0, "AVAILABLE_LANGUAGES should not be empty")

        for code, name in AVAILABLE_LANGUAGES.items():
            self.assertIsInstance(code, str)
            self.assertIsInstance(name, str)

        self.assertIn("en", AVAILABLE_LANGUAGES)
        self.assertIn("it", AVAILABLE_LANGUAGES)

if __name__ == '__main__':
    unittest.main()
