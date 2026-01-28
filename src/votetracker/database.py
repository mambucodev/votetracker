"""
Database module for VoteTracker.
Handles SQLite database operations for subjects, votes, school years, and settings.
"""

import os
import sys
import sqlite3
import base64
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


def get_data_dir() -> str:
    """Get the application data directory following XDG specification."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get(
            "XDG_DATA_HOME", 
            os.path.join(os.path.expanduser("~"), ".local", "share")
        )
    
    data_dir = os.path.join(base, "votetracker")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path() -> str:
    """Get the database file path."""
    return os.path.join(get_data_dir(), "votes.db")


class Database:
    """SQLite database manager for votes, subjects, school years, and settings."""
    
    def __init__(self):
        self.db_path = get_db_path()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self):
        """Initialize the database schema and run migrations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # School years table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS school_years (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    start_year INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 0
                )
            """)
            
            # Subjects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Check if votes table exists and needs migration
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='votes'")
            votes_exists = cursor.fetchone() is not None
            
            if votes_exists:
                # Check if migration is needed
                cursor.execute("PRAGMA table_info(votes)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if "school_year_id" not in columns:
                    # Migration: add new columns
                    cursor.execute("ALTER TABLE votes ADD COLUMN school_year_id INTEGER")
                    cursor.execute("ALTER TABLE votes ADD COLUMN term INTEGER DEFAULT 1")
            else:
                # Create votes table with all columns
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
            
            # Ensure at least one school year exists
            cursor.execute("SELECT COUNT(*) FROM school_years")
            if cursor.fetchone()[0] == 0:
                current_year = datetime.now().year
                month = datetime.now().month
                # School year starts in September
                if month >= 9:
                    start_year = current_year
                else:
                    start_year = current_year - 1
                
                year_name = f"{start_year}/{start_year + 1}"
                cursor.execute(
                    "INSERT INTO school_years (name, start_year, is_active) VALUES (?, ?, 1)",
                    (year_name, start_year)
                )
            
            # Migrate existing votes to current school year if needed
            cursor.execute("SELECT id FROM school_years WHERE is_active = 1")
            active_year = cursor.fetchone()
            if active_year:
                cursor.execute(
                    "UPDATE votes SET school_year_id = ? WHERE school_year_id IS NULL",
                    (active_year[0],)
                )
            
            # Set default term if not set
            cursor.execute("SELECT value FROM settings WHERE key = 'current_term'")
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO settings (key, value) VALUES ('current_term', '1')"
                )

            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_subject ON votes(subject_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_year ON votes(school_year_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_term ON votes(term)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_date ON votes(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_composite ON votes(subject_id, school_year_id, term)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)")

            conn.commit()
    
    # ========================================================================
    # SCHOOL YEARS
    # ========================================================================
    
    def get_school_years(self) -> List[Dict[str, Any]]:
        """Get all school years ordered by start year descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, start_year, is_active 
                FROM school_years 
                ORDER BY start_year DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_school_year(self) -> Optional[Dict[str, Any]]:
        """Get the currently active school year."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, start_year, is_active 
                FROM school_years 
                WHERE is_active = 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def set_active_school_year(self, year_id: int):
        """Set a school year as active (deactivates others)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE school_years SET is_active = 0")
            cursor.execute("UPDATE school_years SET is_active = 1 WHERE id = ?", (year_id,))
            conn.commit()
    
    def add_school_year(self, start_year: int) -> bool:
        """Add a new school year."""
        year_name = f"{start_year}/{start_year + 1}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO school_years (name, start_year, is_active) VALUES (?, ?, 0)",
                    (year_name, start_year)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def delete_school_year(self, year_id: int) -> bool:
        """Delete a school year and all associated votes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if it's the only year
            cursor.execute("SELECT COUNT(*) FROM school_years")
            if cursor.fetchone()[0] <= 1:
                return False
            
            # Check if it's active
            cursor.execute("SELECT is_active FROM school_years WHERE id = ?", (year_id,))
            row = cursor.fetchone()
            if row and row[0] == 1:
                # Activate another year first
                cursor.execute(
                    "UPDATE school_years SET is_active = 1 WHERE id != ? LIMIT 1",
                    (year_id,)
                )
            
            cursor.execute("DELETE FROM votes WHERE school_year_id = ?", (year_id,))
            cursor.execute("DELETE FROM school_years WHERE id = ?", (year_id,))
            conn.commit()
            return True
    
    # ========================================================================
    # SETTINGS
    # ========================================================================
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
    
    def get_current_term(self) -> int:
        """Get the current term (1 or 2)."""
        return int(self.get_setting("current_term", "1"))
    
    def set_current_term(self, term: int):
        """Set the current term (1 or 2)."""
        self.set_setting("current_term", str(term))

    # ========================================================================
    # CLASSEVIVA CREDENTIALS
    # ========================================================================

    def save_classeviva_credentials(self, username: str, password: str):
        """Store ClasseViva credentials with base64 encoding (NOT secure encryption)."""
        # Encode credentials to base64 for basic obfuscation
        encoded_user = base64.b64encode(username.encode()).decode()
        encoded_pass = base64.b64encode(password.encode()).decode()

        self.set_setting("classeviva_username", encoded_user)
        self.set_setting("classeviva_password", encoded_pass)

    def get_classeviva_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve stored ClasseViva credentials."""
        encoded_user = self.get_setting("classeviva_username")
        encoded_pass = self.get_setting("classeviva_password")

        if not encoded_user or not encoded_pass:
            return None, None

        try:
            username = base64.b64decode(encoded_user.encode()).decode()
            password = base64.b64decode(encoded_pass.encode()).decode()
            return username, password
        except Exception:
            return None, None

    def clear_classeviva_credentials(self):
        """Remove stored ClasseViva credentials."""
        self.set_setting("classeviva_username", "")
        self.set_setting("classeviva_password", "")

    def has_classeviva_credentials(self) -> bool:
        """Check if credentials are stored."""
        user, pwd = self.get_classeviva_credentials()
        return user is not None and pwd is not None

    # ClasseViva sync settings
    def get_last_sync_time(self) -> Optional[str]:
        """Get the last ClasseViva sync timestamp."""
        return self.get_setting("classeviva_last_sync")

    def set_last_sync_time(self, timestamp: str):
        """Set the last ClasseViva sync timestamp."""
        self.set_setting("classeviva_last_sync", timestamp)

    def get_auto_sync_enabled(self) -> bool:
        """Check if auto-sync is enabled."""
        return self.get_setting("classeviva_auto_sync") == "1"

    def set_auto_sync_enabled(self, enabled: bool):
        """Enable or disable auto-sync."""
        self.set_setting("classeviva_auto_sync", "1" if enabled else "0")

    def get_sync_interval(self) -> int:
        """Get the auto-sync interval in minutes."""
        return int(self.get_setting("classeviva_sync_interval", "60"))

    def set_sync_interval(self, minutes: int):
        """Set the auto-sync interval in minutes."""
        self.set_setting("classeviva_sync_interval", str(minutes))

    # ========================================================================
    # CLASSEVIVA SUBJECT MAPPINGS
    # ========================================================================

    def save_subject_mapping(self, cv_subject: str, vt_subject: str):
        """Save a ClasseViva to VoteTracker subject mapping."""
        self.set_setting(f"cv_mapping_{cv_subject}", vt_subject)

    def get_subject_mapping(self, cv_subject: str) -> Optional[str]:
        """Get the VoteTracker subject for a ClasseViva subject."""
        return self.get_setting(f"cv_mapping_{cv_subject}")

    def get_all_subject_mappings(self) -> Dict[str, str]:
        """Get all ClasseViva subject mappings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings WHERE key LIKE 'cv_mapping_%'")
            mappings = {}
            for row in cursor.fetchall():
                cv_subject = row[0].replace("cv_mapping_", "")
                mappings[cv_subject] = row[1]
            return mappings

    def clear_subject_mapping(self, cv_subject: str):
        """Remove a subject mapping."""
        self.set_setting(f"cv_mapping_{cv_subject}", "")

    def clear_all_subject_mappings(self):
        """Remove all subject mappings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key LIKE 'cv_mapping_%'")
            conn.commit()

    # ========================================================================
    # SUBJECTS
    # ========================================================================
    
    def get_subjects(self) -> List[str]:
        """Get all subject names ordered alphabetically."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM subjects ORDER BY name")
            return [row["name"] for row in cursor.fetchall()]
    
    def get_subject_id(self, name: str) -> Optional[int]:
        """Get subject ID by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            row = cursor.fetchone()
            return row["id"] if row else None
    
    def add_subject(self, name: str) -> bool:
        """Add a new subject."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def rename_subject(self, old_name: str, new_name: str) -> bool:
        """Rename a subject."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE subjects SET name = ? WHERE name = ?",
                    (new_name, old_name)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
    
    def delete_subject(self, name: str):
        """Delete a subject and all associated votes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                subject_id = row["id"]
                cursor.execute("DELETE FROM votes WHERE subject_id = ?", (subject_id,))
                cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
                conn.commit()
    
    # ========================================================================
    # VOTES
    # ========================================================================
    
    def get_votes(
        self, 
        subject: str = None, 
        school_year_id: int = None,
        term: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get votes with optional filters.
        If school_year_id is None, uses the active school year.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Use active school year if not specified
            if school_year_id is None:
                active = self.get_active_school_year()
                school_year_id = active["id"] if active else None
            
            query = """
                SELECT v.id, s.name as subject, v.grade, v.type, v.term,
                       v.date, v.description, v.weight, v.school_year_id
                FROM votes v
                JOIN subjects s ON v.subject_id = s.id
                WHERE v.school_year_id = ?
            """
            params = [school_year_id]
            
            if subject:
                query += " AND s.name = ?"
                params.append(subject)
            
            if term is not None:
                query += " AND v.term = ?"
                params.append(term)
            
            query += " ORDER BY v.date DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def add_vote(
        self,
        subject: str,
        grade: float,
        vote_type: str,
        date: str,
        description: str,
        term: int = None,
        weight: float = 1.0,
        school_year_id: int = None
    ) -> int:
        """Add a new vote. Returns the new vote ID."""
        # Ensure subject exists
        subject_id = self.get_subject_id(subject)
        if not subject_id:
            self.add_subject(subject)
            subject_id = self.get_subject_id(subject)

        # Use active school year if not specified
        if school_year_id is None:
            active = self.get_active_school_year()
            school_year_id = active["id"] if active else None

        # Use current term if not specified
        if term is None:
            term = self.get_current_term()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO votes (subject_id, school_year_id, grade, type, term, date, description, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (subject_id, school_year_id, grade, vote_type, term, date, description, weight))
            conn.commit()
            return cursor.lastrowid
    
    def update_vote(
        self,
        vote_id: int,
        subject: str,
        grade: float,
        vote_type: str,
        date: str,
        description: str,
        term: int,
        weight: float = 1.0
    ):
        """Update an existing vote."""
        subject_id = self.get_subject_id(subject)
        if not subject_id:
            self.add_subject(subject)
            subject_id = self.get_subject_id(subject)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE votes
                SET subject_id = ?, grade = ?, type = ?, term = ?, date = ?, description = ?, weight = ?
                WHERE id = ?
            """, (subject_id, grade, vote_type, term, date, description, weight, vote_id))
            conn.commit()
    
    def get_vote(self, vote_id: int) -> Optional[Dict[str, Any]]:
        """Get a single vote by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.id, s.name as subject, v.grade, v.type, v.term,
                       v.date, v.description, v.weight, v.school_year_id
                FROM votes v
                JOIN subjects s ON v.subject_id = s.id
                WHERE v.id = ?
            """, (vote_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_vote(self, vote_id: int):
        """Delete a vote by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM votes WHERE id = ?", (vote_id,))
            conn.commit()

    def vote_exists(
        self,
        subject: str,
        grade: float,
        date: str,
        vote_type: str,
        school_year_id: int = None
    ) -> bool:
        """
        Check if a vote with the same characteristics already exists.
        Used for duplicate prevention when importing from ClasseViva.

        Args:
            subject: Subject name
            grade: Grade value
            date: Date string
            vote_type: Vote type (Oral/Written/Practical)
            school_year_id: Optional school year ID (defaults to active year)

        Returns:
            True if vote exists, False otherwise
        """
        subject_id = self.get_subject_id(subject)
        if not subject_id:
            return False  # Subject doesn't exist, so vote can't exist

        # Use active school year if not specified
        if school_year_id is None:
            active = self.get_active_school_year()
            school_year_id = active["id"] if active else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM votes
                WHERE subject_id = ?
                AND school_year_id = ?
                AND grade = ?
                AND date = ?
                AND type = ?
            """, (subject_id, school_year_id, grade, date, vote_type))

            count = cursor.fetchone()[0]
            return count > 0

    def get_subjects_with_votes(
        self, 
        school_year_id: int = None,
        term: int = None
    ) -> List[str]:
        """Get subjects that have votes in the specified school year/term."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if school_year_id is None:
                active = self.get_active_school_year()
                school_year_id = active["id"] if active else None
            
            query = """
                SELECT DISTINCT s.name
                FROM subjects s
                JOIN votes v ON s.id = v.subject_id
                WHERE v.school_year_id = ?
            """
            params = [school_year_id]
            
            if term is not None:
                query += " AND v.term = ?"
                params.append(term)
            
            query += " ORDER BY s.name"
            
            cursor.execute(query, params)
            return [row["name"] for row in cursor.fetchall()]
    
    # ========================================================================
    # IMPORT / EXPORT
    # ========================================================================
    
    def import_votes(self, votes: List[Dict[str, Any]], school_year_id: int = None):
        """Import votes from a list of dictionaries."""
        for vote in votes:
            # Support both English and Italian field names
            subject = vote.get("subject") or vote.get("materia", "Unknown")
            grade = vote.get("grade") or vote.get("voto", 0)
            vote_type = vote.get("type") or vote.get("tipo", "Written")
            date = vote.get("date") or vote.get("data", "")
            description = vote.get("description") or vote.get("desc", "")
            weight = vote.get("weight") or vote.get("peso", 1.0)
            term = vote.get("term") or vote.get("quadrimestre", 1)
            
            # Map Italian type names
            type_map = {"Scritto": "Written", "Orale": "Oral", "Pratico": "Practical"}
            vote_type = type_map.get(vote_type, vote_type)
            
            self.add_vote(
                subject, grade, vote_type, date, description,
                term=term, weight=weight, school_year_id=school_year_id
            )
    
    def export_votes(self, school_year_id: int = None, term: int = None) -> List[Dict[str, Any]]:
        """Export votes to a list of dictionaries."""
        return self.get_votes(school_year_id=school_year_id, term=term)
    
    def clear_votes(self, school_year_id: int = None, term: int = None):
        """Clear votes with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if school_year_id is None:
                active = self.get_active_school_year()
                school_year_id = active["id"] if active else None
            
            if term is not None:
                cursor.execute(
                    "DELETE FROM votes WHERE school_year_id = ? AND term = ?",
                    (school_year_id, term)
                )
            else:
                cursor.execute(
                    "DELETE FROM votes WHERE school_year_id = ?",
                    (school_year_id,)
                )
            conn.commit()
