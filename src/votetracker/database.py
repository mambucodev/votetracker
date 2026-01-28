"""
Database module for VoteTracker.
Handles SQLite database operations for subjects, votes, school years, and settings.
"""

import os
import sys
import sqlite3
import base64
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


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
        # Caches for frequently accessed data
        self._subject_cache = None
        self._year_cache = None
        # Persistent database connection
        self._connection = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection (reused).

        Creates and configures a persistent connection on first call,
        then reuses it for all subsequent operations.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrent access
            self._connection.execute("PRAGMA journal_mode=WAL")
        return self._connection

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
    
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

            # Grade goals table
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
    
    def get_school_years(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all school years ordered by start year descending (cached).

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of school year dictionaries
        """
        if force_refresh or self._year_cache is None:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, start_year, is_active
                    FROM school_years
                    ORDER BY start_year DESC
                """)
                self._year_cache = [dict(row) for row in cursor.fetchall()]
        return [dict(y) for y in self._year_cache]  # Return deep copy
    
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
        """
        Add a new school year.

        Returns:
            bool: True if successful, False otherwise
        """
        year_name = f"{start_year}/{start_year + 1}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO school_years (name, start_year, is_active) VALUES (?, ?, 0)",
                    (year_name, start_year)
                )
                conn.commit()
                self._year_cache = None  # Invalidate cache
                return True
        except sqlite3.IntegrityError as e:
            logger.warning(f"School year {year_name} already exists")
            return False
        except sqlite3.Error as e:
            logger.error(f"Database error adding school year {year_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error adding school year {year_name}: {e}")
            return False
    
    def delete_school_year(self, year_id: int) -> bool:
        """
        Delete a school year and all associated votes.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Check if it's the only year
                cursor.execute("SELECT COUNT(*) FROM school_years")
                if cursor.fetchone()[0] <= 1:
                    logger.warning("Cannot delete the only school year")
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
                self._year_cache = None  # Invalidate cache
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error deleting school year {year_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting school year {year_id}: {e}")
            return False
    
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
    # SYNC PROVIDER (GENERIC)
    # ========================================================================
    # Provider-agnostic methods for managing multiple sync providers
    # (ClasseViva, Axios, etc.)

    def get_active_provider(self) -> Optional[str]:
        """
        Get the currently active sync provider.

        Returns:
            Provider ID (e.g., "classeviva", "axios") or None
        """
        # Migrate existing ClasseViva users
        active = self.get_setting("active_sync_provider")
        if not active and self.has_classeviva_credentials():
            # Auto-migrate: existing CV users get CV set as active
            self.set_active_provider("classeviva")
            return "classeviva"
        return active

    def set_active_provider(self, provider_id: Optional[str]):
        """
        Set the active sync provider.

        Args:
            provider_id: Provider ID or None to disable sync
        """
        self.set_setting("active_sync_provider", provider_id or "")

    def save_provider_credentials(self, provider_id: str, credentials: Dict[str, str]):
        """
        Save credentials for a provider.

        Args:
            provider_id: Provider identifier
            credentials: Dict of field_name -> value pairs
        """
        for field_name, value in credentials.items():
            # Encode for basic obfuscation
            encoded_value = base64.b64encode(value.encode()).decode()
            self.set_setting(f"{provider_id}_{field_name}", encoded_value)

    def get_provider_credentials(self, provider_id: str, field_names: List[str]) -> Dict[str, Optional[str]]:
        """
        Get credentials for a provider.

        Args:
            provider_id: Provider identifier
            field_names: List of credential field names

        Returns:
            Dict of field_name -> value (None if not found)
        """
        credentials = {}
        for field_name in field_names:
            encoded_value = self.get_setting(f"{provider_id}_{field_name}")
            if encoded_value:
                try:
                    credentials[field_name] = base64.b64decode(encoded_value.encode()).decode()
                except Exception:
                    credentials[field_name] = None
            else:
                credentials[field_name] = None
        return credentials

    def clear_provider_credentials(self, provider_id: str, field_names: List[str]):
        """
        Clear credentials for a provider.

        Args:
            provider_id: Provider identifier
            field_names: List of credential field names to clear
        """
        for field_name in field_names:
            self.set_setting(f"{provider_id}_{field_name}", "")

    def has_provider_credentials(self, provider_id: str, field_names: List[str]) -> bool:
        """
        Check if all required credentials are stored for a provider.

        Args:
            provider_id: Provider identifier
            field_names: List of required credential field names

        Returns:
            True if all fields have values
        """
        credentials = self.get_provider_credentials(provider_id, field_names)
        return all(credentials.values())

    def save_provider_subject_mapping(self, provider_id: str, source_subject: str, target_subject: str):
        """
        Save a subject mapping for a provider.

        Args:
            provider_id: Provider identifier
            source_subject: Provider's subject name
            target_subject: VoteTracker subject name
        """
        self.set_setting(f"{provider_id}_mapping_{source_subject}", target_subject)

    def get_provider_subject_mapping(self, provider_id: str, source_subject: str) -> Optional[str]:
        """
        Get the VoteTracker subject for a provider's subject.

        Args:
            provider_id: Provider identifier
            source_subject: Provider's subject name

        Returns:
            VoteTracker subject name or None
        """
        return self.get_setting(f"{provider_id}_mapping_{source_subject}")

    def get_all_provider_subject_mappings(self, provider_id: str) -> Dict[str, str]:
        """
        Get all subject mappings for a provider.

        Args:
            provider_id: Provider identifier

        Returns:
            Dict of source_subject -> target_subject
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            prefix = f"{provider_id}_mapping_"
            cursor.execute("SELECT key, value FROM settings WHERE key LIKE ?", (f"{prefix}%",))
            mappings = {}
            for row in cursor.fetchall():
                source_subject = row[0].replace(prefix, "")
                mappings[source_subject] = row[1]
            return mappings

    def clear_provider_subject_mapping(self, provider_id: str, source_subject: str):
        """
        Remove a subject mapping for a provider.

        Args:
            provider_id: Provider identifier
            source_subject: Provider's subject name
        """
        self.set_setting(f"{provider_id}_mapping_{source_subject}", "")

    def clear_all_provider_subject_mappings(self, provider_id: str):
        """
        Remove all subject mappings for a provider.

        Args:
            provider_id: Provider identifier
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key LIKE ?", (f"{provider_id}_mapping_%",))
            conn.commit()

    # Provider sync settings
    def get_provider_last_sync(self, provider_id: str) -> Optional[str]:
        """Get last sync timestamp for provider."""
        return self.get_setting(f"{provider_id}_last_sync")

    def set_provider_last_sync(self, provider_id: str, timestamp: str):
        """Set last sync timestamp for provider."""
        self.set_setting(f"{provider_id}_last_sync", timestamp)

    def get_provider_auto_sync_enabled(self, provider_id: str) -> bool:
        """Check if auto-sync is enabled for provider."""
        return self.get_setting(f"{provider_id}_auto_sync") == "1"

    def set_provider_auto_sync_enabled(self, provider_id: str, enabled: bool):
        """Enable/disable auto-sync for provider."""
        self.set_setting(f"{provider_id}_auto_sync", "1" if enabled else "0")

    def get_provider_sync_interval(self, provider_id: str) -> int:
        """Get auto-sync interval in minutes for provider."""
        return int(self.get_setting(f"{provider_id}_sync_interval", "60"))

    def set_provider_sync_interval(self, provider_id: str, minutes: int):
        """Set auto-sync interval in minutes for provider."""
        self.set_setting(f"{provider_id}_sync_interval", str(minutes))

    def get_provider_auto_login(self, provider_id: str) -> bool:
        """Check if auto-login is enabled for provider."""
        return self.get_setting(f"{provider_id}_auto_login") == "1"

    def set_provider_auto_login(self, provider_id: str, enabled: bool):
        """Enable/disable auto-login for provider."""
        self.set_setting(f"{provider_id}_auto_login", "1" if enabled else "0")

    # ========================================================================
    # SUBJECTS
    # ========================================================================
    
    def get_subjects(self, force_refresh: bool = False) -> List[str]:
        """
        Get all subject names ordered alphabetically (cached).

        Args:
            force_refresh: If True, bypass cache and fetch from database

        Returns:
            List of subject names
        """
        if force_refresh or self._subject_cache is None:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM subjects ORDER BY name")
                self._subject_cache = [row["name"] for row in cursor.fetchall()]
        return self._subject_cache.copy()  # Return copy to prevent external mutation
    
    def get_subject_id(self, name: str) -> Optional[int]:
        """Get subject ID by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
            row = cursor.fetchone()
            return row["id"] if row else None
    
    def add_subject(self, name: str) -> Optional[int]:
        """
        Add a new subject.

        Returns:
            int: Subject ID if successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
                conn.commit()
                result = cursor.lastrowid
                self._subject_cache = None  # Invalidate cache
                return result
        except sqlite3.IntegrityError:
            logger.warning(f"Subject '{name}' already exists")
            return self.get_subject_id(name)
        except sqlite3.Error as e:
            logger.error(f"Database error adding subject '{name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error adding subject '{name}': {e}")
            return None
    
    def rename_subject(self, old_name: str, new_name: str) -> bool:
        """
        Rename a subject.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE subjects SET name = ? WHERE name = ?",
                    (new_name, old_name)
                )
                conn.commit()
                result = cursor.rowcount > 0
                if result:
                    self._subject_cache = None  # Invalidate cache
                return result
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to rename subject (integrity error): {e}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Database error renaming subject '{old_name}' to '{new_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error renaming subject '{old_name}' to '{new_name}': {e}")
            return False
    
    def delete_subject(self, name: str) -> bool:
        """
        Delete a subject and all associated votes.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    subject_id = row["id"]
                    cursor.execute("DELETE FROM votes WHERE subject_id = ?", (subject_id,))
                    cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
                    conn.commit()
                    self._subject_cache = None  # Invalidate cache
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Database error deleting subject '{name}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting subject '{name}': {e}")
            return False
    
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
    ) -> Optional[int]:
        """
        Add a new vote.

        Returns:
            int: Vote ID if successful, None otherwise
        """
        try:
            # Ensure subject exists
            subject_id = self.get_subject_id(subject)
            if not subject_id:
                subject_id = self.add_subject(subject)
                if not subject_id:
                    logger.error(f"Failed to create subject '{subject}'")
                    return None

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
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to add vote (integrity error): {e}")
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error adding vote: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error adding vote: {e}")
            return None
    
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
    ) -> bool:
        """
        Update an existing vote.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            subject_id = self.get_subject_id(subject)
            if not subject_id:
                subject_id = self.add_subject(subject)
                if not subject_id:
                    logger.error(f"Failed to create subject '{subject}'")
                    return False

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE votes
                    SET subject_id = ?, grade = ?, type = ?, term = ?, date = ?, description = ?, weight = ?
                    WHERE id = ?
                """, (subject_id, grade, vote_type, term, date, description, weight, vote_id))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Database error updating vote {vote_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating vote {vote_id}: {e}")
            return False
    
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

    def delete_vote(self, vote_id: int) -> bool:
        """
        Delete a vote by ID.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM votes WHERE id = ?", (vote_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Database error deleting vote {vote_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting vote {vote_id}: {e}")
            return False

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

    def get_grade_statistics(self) -> Dict[str, Any]:
        """
        Get aggregated grade statistics in a single query.

        Returns dict with:
            - overall_avg: Overall weighted average across all subjects
            - failing_count: Number of subjects with average < 6
            - total_votes: Total number of votes
            - subject_avgs: Dict of {subject_name: average}
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get active year and current term
            active_year = self.get_active_school_year()
            if not active_year:
                return {
                    'overall_avg': 0.0,
                    'failing_count': 0,
                    'total_votes': 0,
                    'subject_avgs': {}
                }

            current_term = self.get_current_term()

            # Single query with aggregation - calculates weighted average per subject
            cursor.execute("""
                SELECT
                    s.name,
                    SUM(v.grade * v.weight) / SUM(v.weight) as weighted_avg,
                    COUNT(*) as vote_count
                FROM votes v
                JOIN subjects s ON v.subject_id = s.id
                WHERE v.school_year_id = ? AND v.term = ?
                GROUP BY s.id, s.name
                HAVING COUNT(*) > 0
            """, (active_year['id'], current_term))

            subject_stats = cursor.fetchall()

            if not subject_stats:
                return {
                    'overall_avg': 0.0,
                    'failing_count': 0,
                    'total_votes': 0,
                    'subject_avgs': {}
                }

            # Calculate overall average (mean of subject averages)
            subject_avgs_dict = {row['name']: row['weighted_avg'] for row in subject_stats}
            overall_avg = sum(subject_avgs_dict.values()) / len(subject_avgs_dict)

            # Count failing subjects
            failing_count = sum(1 for avg in subject_avgs_dict.values() if avg < 6.0)

            # Total votes
            total_votes = sum(row['vote_count'] for row in subject_stats)

            return {
                'overall_avg': overall_avg,
                'failing_count': failing_count,
                'total_votes': total_votes,
                'subject_avgs': subject_avgs_dict
            }

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
    
    def import_votes(self, votes: List[Dict[str, Any]], school_year_id: int = None) -> bool:
        """
        Import votes from a list of dictionaries.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
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

                result = self.add_vote(
                    subject, grade, vote_type, date, description,
                    term=term, weight=weight, school_year_id=school_year_id
                )
                if result is None:
                    logger.warning(f"Failed to import vote for {subject}")
            return True
        except Exception as e:
            logger.error(f"Error importing votes: {e}")
            return False
    
    def export_votes(self, school_year_id: int = None, term: int = None) -> List[Dict[str, Any]]:
        """Export votes to a list of dictionaries."""
        return self.get_votes(school_year_id=school_year_id, term=term)
    
    def clear_votes(self, school_year_id: int = None, term: int = None) -> bool:
        """
        Clear votes with optional filters.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error clearing votes: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error clearing votes: {e}")
            return False

    # ========================================================================
    # GRADE GOALS
    # ========================================================================

    def set_grade_goal(self, subject: str, target_grade: float, school_year_id: int = None, term: int = None) -> bool:
        """
        Set or update grade goal for a subject.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            subject_id = self.get_subject_id(subject)
            if not subject_id:
                logger.error(f"Subject '{subject}' does not exist")
                return False

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
                    INSERT OR REPLACE INTO grade_goals
                    (subject_id, school_year_id, term, target_grade, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (subject_id, school_year_id, term, target_grade, datetime.now().isoformat()))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error setting grade goal: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting grade goal: {e}")
            return False

    def get_grade_goal(self, subject: str, school_year_id: int = None, term: int = None) -> Optional[float]:
        """
        Get grade goal for a subject.

        Returns:
            float: Target grade if exists, None otherwise
        """
        try:
            subject_id = self.get_subject_id(subject)
            if not subject_id:
                return None

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
                    SELECT target_grade FROM grade_goals
                    WHERE subject_id = ? AND school_year_id = ? AND term = ?
                """, (subject_id, school_year_id, term))
                result = cursor.fetchone()
                return result['target_grade'] if result else None
        except sqlite3.Error as e:
            logger.error(f"Database error getting grade goal: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting grade goal: {e}")
            return None

    def delete_grade_goal(self, subject: str, school_year_id: int = None, term: int = None) -> bool:
        """
        Delete grade goal for a subject.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            subject_id = self.get_subject_id(subject)
            if not subject_id:
                return False

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
                    DELETE FROM grade_goals
                    WHERE subject_id = ? AND school_year_id = ? AND term = ?
                """, (subject_id, school_year_id, term))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Database error deleting grade goal: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting grade goal: {e}")
            return False

    def get_all_grade_goals(self, school_year_id: int = None, term: int = None) -> Dict[str, float]:
        """
        Get all grade goals for current year/term.

        Returns:
            Dict mapping subject names to target grades
        """
        try:
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
                    SELECT s.name, g.target_grade
                    FROM grade_goals g
                    JOIN subjects s ON g.subject_id = s.id
                    WHERE g.school_year_id = ? AND g.term = ?
                """, (school_year_id, term))
                return {row['name']: row['target_grade'] for row in cursor.fetchall()}
        except sqlite3.Error as e:
            logger.error(f"Database error getting all grade goals: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting all grade goals: {e}")
            return {}

    def calculate_needed_grade(self, subject: str, target_avg: float, school_year_id: int = None, term: int = None, weight: float = 1.0) -> Optional[float]:
        """
        Calculate what grade is needed next to reach target average.

        Returns:
            float: Needed grade, or None if already at/above target or no votes exist
        """
        try:
            votes = self.get_votes(subject, school_year_id, term)
            if not votes:
                return target_avg  # First vote should be target

            # Calculate current weighted sum
            total_weighted = sum(v['grade'] * v['weight'] for v in votes)
            total_weight = sum(v['weight'] for v in votes)

            current_avg = total_weighted / total_weight if total_weight > 0 else 0

            if current_avg >= target_avg:
                return None  # Already at goal

            # Calculate needed grade
            # Formula: (current_sum + needed_grade * weight) / (total_weight + weight) = target
            # Solve for needed_grade
            needed = (target_avg * (total_weight + weight)) - total_weighted
            needed = needed / weight

            return min(needed, 10.0)  # Cap at max grade
        except Exception as e:
            logger.error(f"Error calculating needed grade: {e}")
            return None
