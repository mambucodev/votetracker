"""
Unit tests for database schema, migrations, and seed logic.
"""
from __future__ import annotations

import unittest
import sqlite3
from src.votetracker.db_schema import (
    create_schema,
    migrate_votes_table,
    seed_defaults,
    create_indices,
)


class TestDbSchema(unittest.TestCase):
    """Test suite for db_schema functions."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_schema_creation_and_seeding(self):
        create_schema(self.cursor)
        migrate_votes_table(self.cursor)
        seed_defaults(self.cursor)
        create_indices(self.cursor)
        self.conn.commit()

        # Verify tables exist
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in self.cursor.fetchall()}
        self.assertIn("school_years", tables)
        self.assertIn("subjects", tables)
        self.assertIn("votes", tables)
        self.assertIn("grade_goals", tables)
        self.assertIn("settings", tables)

        # Verify default school year seeded
        self.cursor.execute("SELECT COUNT(*) FROM school_years WHERE is_active = 1")
        self.assertEqual(self.cursor.fetchone()[0], 1)

        # Verify default current term seeded
        self.cursor.execute("SELECT value FROM settings WHERE key = 'current_term'")
        self.assertEqual(self.cursor.fetchone()[0], "1")

    def test_votes_migration_from_legacy_schema(self):
        """Test migrating an older votes table without school_year_id or term."""
        self.cursor.execute("""
            CREATE TABLE votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                grade REAL NOT NULL,
                type TEXT,
                date TEXT,
                description TEXT,
                weight REAL
            )
        """)
        self.conn.commit()

        # Run migration
        migrate_votes_table(self.cursor)
        self.conn.commit()

        # Verify new columns exist
        self.cursor.execute("PRAGMA table_info(votes)")
        columns = {row[1] for row in self.cursor.fetchall()}
        self.assertIn("school_year_id", columns)
        self.assertIn("term", columns)


if __name__ == '__main__':
    unittest.main()
