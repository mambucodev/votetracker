"""
Schema DDL, migrations, seed data, and indices for the VoteTracker database.

Kept separate from :mod:`.database` to isolate schema concerns from the
CRUD / query layer. If this project ever moves to a versioned migration
system, this module is where those migrations would live.

All functions in this module take a live ``sqlite3.Cursor`` — they never
open connections themselves, so the caller controls transactions.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime


def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create all tables (``CREATE TABLE IF NOT EXISTS``).

    The ``votes`` table is handled separately by :func:`migrate_votes_table`
    because existing databases may need an ``ALTER TABLE`` migration.
    """
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            start_year INTEGER NOT NULL,
            is_active INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            school_year_id INTEGER NOT NULL,
            term INTEGER NOT NULL,
            target_grade REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (school_year_id) REFERENCES school_years(id) ON DELETE CASCADE,
            UNIQUE(subject_id, school_year_id, term)
        )
    """)


def migrate_votes_table(cursor: sqlite3.Cursor) -> None:
    """Create the ``votes`` table, or migrate an older schema in place.

    Pre-existing databases may have a ``votes`` table that predates the
    multi-year / multi-term feature. In that case we add the missing
    columns rather than recreating the table.
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='votes'"
    )
    votes_exists = cursor.fetchone() is not None

    if votes_exists:
        cursor.execute("PRAGMA table_info(votes)")
        columns = [col[1] for col in cursor.fetchall()]
        if "school_year_id" not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN school_year_id INTEGER")
            cursor.execute("ALTER TABLE votes ADD COLUMN term INTEGER DEFAULT 1")
    else:
        cursor.execute("""
            CREATE TABLE votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                school_year_id INTEGER,
                grade REAL NOT NULL,
                type TEXT DEFAULT 'Written',
                term INTEGER DEFAULT 1,
                date TEXT,
                description TEXT,
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (school_year_id) REFERENCES school_years(id) ON DELETE CASCADE
            )
        """)


def seed_defaults(cursor: sqlite3.Cursor) -> None:
    """Insert default rows required for a blank database and backfill
    orphan votes. Safe to call on an already-seeded database."""
    # Ensure at least one school year exists.
    cursor.execute("SELECT COUNT(*) FROM school_years")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        # Italian school year starts in September.
        start_year = now.year if now.month >= 9 else now.year - 1
        year_name = f"{start_year}/{start_year + 1}"
        cursor.execute(
            "INSERT INTO school_years (name, start_year, is_active) VALUES (?, ?, 1)",
            (year_name, start_year),
        )

    # Backfill orphan votes (pre-multi-year schema) to the active year.
    cursor.execute("SELECT id FROM school_years WHERE is_active = 1")
    active_year = cursor.fetchone()
    if active_year:
        cursor.execute(
            "UPDATE votes SET school_year_id = ? WHERE school_year_id IS NULL",
            (active_year[0],),
        )

    # Default current term.
    cursor.execute("SELECT value FROM settings WHERE key = 'current_term'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES ('current_term', '1')"
        )


def create_indices(cursor: sqlite3.Cursor) -> None:
    """Create performance indices. Called last, after tables exist."""
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_votes_subject ON votes(subject_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_votes_year ON votes(school_year_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_votes_term ON votes(term)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_votes_date ON votes(date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_votes_composite "
        "ON votes(subject_id, school_year_id, term)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)"
    )
