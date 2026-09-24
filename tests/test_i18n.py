"""
Unit tests for internationalization module.
"""
from __future__ import annotations

import unittest
from src.votetracker.i18n import (
    tr,
    set_language,
    get_language,
    TRANSLATIONS,
)


class TestI18n(unittest.TestCase):
    """Test suite for i18n module."""

    def setUp(self):
        self.original_lang = get_language()

    def tearDown(self):
        set_language(self.original_lang)

    def test_default_english_translations(self):
        set_language("en")
        self.assertEqual(tr("Dashboard"), "Dashboard")
        self.assertEqual(tr("Votes List"), "Votes List")
        self.assertEqual(tr("Report Card"), "Report Card")

    def test_italian_translations(self):
        set_language("it")
        self.assertEqual(tr("Dashboard"), "Dashboard")
        self.assertEqual(tr("Votes List"), "Lista Voti")
        self.assertEqual(tr("Report Card"), "Pagella")

    def test_missing_key_fallback(self):
        set_language("en")
        self.assertEqual(tr("NonExistentKey123"), "NonExistentKey123")

    def test_translation_dictionaries_have_navigation_keys(self):
        nav_keys = ["Dashboard", "Votes", "Subjects", "Simulator", "Calendar", "Report", "Statistics", "Settings"]
        for key in nav_keys:
            self.assertIn(key, TRANSLATIONS["en"])
            self.assertIn(key, TRANSLATIONS["it"])


if __name__ == '__main__':
    unittest.main()
