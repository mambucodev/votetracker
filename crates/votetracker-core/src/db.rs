use rusqlite::{params, Connection, OptionalExtension, Result};
use std::path::Path;

use crate::models::{GradeGoal, GradeStatistics, NewVote, SchoolYear, Subject, Vote};

#[derive(Debug, thiserror::Error)]
pub enum DbError {
    #[error("SQLite error: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("Entity not found: {0}")]
    NotFound(String),
}

pub struct Database {
    conn: Connection,
    subject_cache: Option<Vec<Subject>>,
    year_cache: Option<Vec<SchoolYear>>,
}

impl Database {
    /// Connects to a database at `path`. If `path` is None, uses in-memory SQLite.
    pub fn new<P: AsRef<Path>>(path: Option<P>) -> Result<Self, DbError> {
        let conn = match path {
            Some(p) => Connection::open(p)?,
            None => Connection::open_in_memory()?,
        };

        let mut db = Self {
            conn,
            subject_cache: None,
            year_cache: None,
        };

        db.init_schema()?;
        Ok(db)
    }

    /// Initializes tables, indices, and default seed data.
    fn init_schema(&mut self) -> Result<(), DbError> {
        self.conn.execute_batch(
            r#"
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS school_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#3B82F6',
                target_grade REAL DEFAULT 6.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                grade REAL NOT NULL,
                weight REAL DEFAULT 1.0,
                vote_date DATE NOT NULL,
                term INTEGER DEFAULT 1,
                notes TEXT,
                vote_type TEXT DEFAULT 'Scritto',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                school_year_id INTEGER REFERENCES school_years(id) ON DELETE SET NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS grade_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                target_grade REAL NOT NULL,
                school_year_id INTEGER REFERENCES school_years(id) ON DELETE CASCADE,
                term INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
                UNIQUE(subject_id, school_year_id, term)
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_votes_subject ON votes(subject_id);
            CREATE INDEX IF NOT EXISTS idx_votes_date ON votes(vote_date);
            CREATE INDEX IF NOT EXISTS idx_votes_term ON votes(term);
            CREATE INDEX IF NOT EXISTS idx_votes_school_year ON votes(school_year_id);
            CREATE INDEX IF NOT EXISTS idx_goals_lookup ON grade_goals(subject_id, school_year_id, term);
            "#,
        )?;

        self.seed_defaults()?;
        Ok(())
    }

    fn seed_defaults(&mut self) -> Result<(), DbError> {
        // Seed initial school year if empty
        let year_count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM school_years", [], |r| r.get(0))?;

        if year_count == 0 {
            self.conn.execute(
                "INSERT INTO school_years (name, is_active) VALUES ('2025/2026', 1)",
                [],
            )?;
        }

        // Seed default subjects if empty
        let subject_count: i64 = self
            .conn
            .query_row("SELECT COUNT(*) FROM subjects", [], |r| r.get(0))?;

        if subject_count == 0 {
            let defaults = [
                ("Italiano", "#EF4444"),
                ("Storia", "#F59E0B"),
                ("Matematica", "#3B82F6"),
                ("Inglese", "#10B981"),
                ("Scienze", "#8B5CF6"),
                ("Filosofia", "#EC4899"),
                ("Arte", "#14B8A6"),
                ("Ed. Fisica", "#F97316"),
            ];

            let mut stmt = self
                .conn
                .prepare("INSERT INTO subjects (name, color, target_grade) VALUES (?1, ?2, 6.0)")?;
            for (name, color) in defaults {
                stmt.execute(params![name, color])?;
            }
        }

        // Seed settings
        self.conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'it')",
            [],
        )?;
        self.conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'system')",
            [],
        )?;

        Ok(())
    }

    // -------------------------------------------------------------------------
    // School Years
    // -------------------------------------------------------------------------

    pub fn get_school_years(&mut self) -> Result<Vec<SchoolYear>, DbError> {
        if let Some(ref cached) = self.year_cache {
            return Ok(cached.clone());
        }

        let mut stmt = self.conn.prepare(
            "SELECT id, name, is_active, created_at FROM school_years ORDER BY name DESC",
        )?;
        let rows = stmt.query_map([], |r| {
            Ok(SchoolYear {
                id: r.get(0)?,
                name: r.get(1)?,
                is_active: r.get(2)?,
                created_at: r.get(3)?,
            })
        })?;

        let mut years = Vec::new();
        for y in rows {
            years.push(y?);
        }

        self.year_cache = Some(years.clone());
        Ok(years)
    }

    pub fn get_active_school_year(&mut self) -> Result<Option<SchoolYear>, DbError> {
        let years = self.get_school_years()?;
        Ok(years.into_iter().find(|y| y.is_active))
    }

    pub fn add_school_year(&mut self, name: &str, set_active: bool) -> Result<i64, DbError> {
        if set_active {
            self.conn
                .execute("UPDATE school_years SET is_active = 0", [])?;
        }

        self.conn.execute(
            "INSERT INTO school_years (name, is_active) VALUES (?1, ?2)",
            params![name, set_active],
        )?;

        self.year_cache = None;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn set_active_school_year(&mut self, id: i64) -> Result<(), DbError> {
        self.conn
            .execute("UPDATE school_years SET is_active = 0", [])?;
        self.conn.execute(
            "UPDATE school_years SET is_active = 1 WHERE id = ?1",
            params![id],
        )?;
        self.year_cache = None;
        Ok(())
    }

    // -------------------------------------------------------------------------
    // Subjects
    // -------------------------------------------------------------------------

    pub fn get_subjects(&mut self) -> Result<Vec<Subject>, DbError> {
        if let Some(ref cached) = self.subject_cache {
            return Ok(cached.clone());
        }

        let mut stmt = self
            .conn
            .prepare("SELECT id, name, color, target_grade, created_at FROM subjects ORDER BY name")?;
        let rows = stmt.query_map([], |r| {
            Ok(Subject {
                id: r.get(0)?,
                name: r.get(1)?,
                color: r.get(2)?,
                target_grade: r.get(3)?,
                created_at: r.get(4)?,
            })
        })?;

        let mut subjects = Vec::new();
        for s in rows {
            subjects.push(s?);
        }

        self.subject_cache = Some(subjects.clone());
        Ok(subjects)
    }

    pub fn add_subject(&mut self, name: &str, color: &str, target_grade: f64) -> Result<i64, DbError> {
        self.conn.execute(
            "INSERT INTO subjects (name, color, target_grade) VALUES (?1, ?2, ?3)",
            params![name, color, target_grade],
        )?;
        self.subject_cache = None;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn update_subject(&mut self, id: i64, name: &str, color: &str, target_grade: f64) -> Result<(), DbError> {
        self.conn.execute(
            "UPDATE subjects SET name = ?1, color = ?2, target_grade = ?3 WHERE id = ?4",
            params![name, color, target_grade, id],
        )?;
        self.subject_cache = None;
        Ok(())
    }

    pub fn delete_subject(&mut self, id: i64) -> Result<(), DbError> {
        self.conn.execute("DELETE FROM subjects WHERE id = ?1", params![id])?;
        self.subject_cache = None;
        Ok(())
    }

    // -------------------------------------------------------------------------
    // Votes
    // -------------------------------------------------------------------------

    pub fn add_vote(&mut self, vote: &NewVote) -> Result<i64, DbError> {
        self.conn.execute(
            r#"
            INSERT INTO votes (subject_id, grade, weight, vote_date, term, notes, vote_type, school_year_id)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
            "#,
            params![
                vote.subject_id,
                vote.grade,
                vote.weight,
                vote.vote_date,
                vote.term,
                vote.notes,
                vote.vote_type,
                vote.school_year_id
            ],
        )?;
        Ok(self.conn.last_insert_rowid())
    }

    pub fn restore_vote(&mut self, vote: &Vote) -> Result<(), DbError> {
        self.conn.execute(
            r#"
            INSERT INTO votes (id, subject_id, grade, weight, vote_date, term, notes, vote_type, created_at, school_year_id)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)
            "#,
            params![
                vote.id,
                vote.subject_id,
                vote.grade,
                vote.weight,
                vote.vote_date,
                vote.term,
                vote.notes,
                vote.vote_type,
                vote.created_at,
                vote.school_year_id
            ],
        )?;
        Ok(())
    }

    pub fn update_vote(&mut self, vote: &Vote) -> Result<(), DbError> {
        self.conn.execute(
            r#"
            UPDATE votes SET
                subject_id = ?1,
                grade = ?2,
                weight = ?3,
                vote_date = ?4,
                term = ?5,
                notes = ?6,
                vote_type = ?7,
                school_year_id = ?8
            WHERE id = ?9
            "#,
            params![
                vote.subject_id,
                vote.grade,
                vote.weight,
                vote.vote_date,
                vote.term,
                vote.notes,
                vote.vote_type,
                vote.school_year_id,
                vote.id
            ],
        )?;
        Ok(())
    }

    pub fn delete_vote(&mut self, id: i64) -> Result<(), DbError> {
        self.conn.execute("DELETE FROM votes WHERE id = ?1", params![id])?;
        Ok(())
    }

    pub fn get_vote_by_id(&self, id: i64) -> Result<Option<Vote>, DbError> {
        let mut stmt = self.conn.prepare(
            r#"
            SELECT id, subject_id, grade, weight, vote_date, term, notes, vote_type, created_at, school_year_id
            FROM votes WHERE id = ?1
            "#,
        )?;
        let vote = stmt
            .query_row(params![id], |r| {
                Ok(Vote {
                    id: r.get(0)?,
                    subject_id: r.get(1)?,
                    grade: r.get(2)?,
                    weight: r.get(3)?,
                    vote_date: r.get(4)?,
                    term: r.get(5)?,
                    notes: r.get(6)?,
                    vote_type: r.get(7)?,
                    created_at: r.get(8)?,
                    school_year_id: r.get(9)?,
                })
            })
            .optional()?;

        Ok(vote)
    }

    pub fn get_votes(
        &self,
        subject_id: Option<i64>,
        term: Option<i32>,
        school_year_id: Option<i64>,
    ) -> Result<Vec<Vote>, DbError> {
        let mut query = String::from(
            r#"
            SELECT id, subject_id, grade, weight, vote_date, term, notes, vote_type, created_at, school_year_id
            FROM votes WHERE 1=1
            "#,
        );

        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

        if let Some(sid) = subject_id {
            query.push_str(" AND subject_id = ?");
            params_vec.push(Box::new(sid));
        }

        if let Some(t) = term {
            query.push_str(" AND term = ?");
            params_vec.push(Box::new(t));
        }

        if let Some(yid) = school_year_id {
            query.push_str(" AND school_year_id = ?");
            params_vec.push(Box::new(yid));
        }

        query.push_str(" ORDER BY vote_date DESC, id DESC");

        let mut stmt = self.conn.prepare(&query)?;
        let rusqlite_params: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();

        let rows = stmt.query_map(&rusqlite_params[..], |r| {
            Ok(Vote {
                id: r.get(0)?,
                subject_id: r.get(1)?,
                grade: r.get(2)?,
                weight: r.get(3)?,
                vote_date: r.get(4)?,
                term: r.get(5)?,
                notes: r.get(6)?,
                vote_type: r.get(7)?,
                created_at: r.get(8)?,
                school_year_id: r.get(9)?,
            })
        })?;

        let mut votes = Vec::new();
        for v in rows {
            votes.push(v?);
        }

        Ok(votes)
    }

    /// Finds a vote matching (subject_id, vote_date, vote_type, school_year_id)
    /// Used for electronic register import duplicate checking.
    pub fn find_vote_by_metadata(
        &self,
        subject_id: i64,
        date: &str,
        vote_type: &str,
        school_year_id: i64,
    ) -> Result<Option<Vote>, DbError> {
        let mut stmt = self.conn.prepare(
            r#"
            SELECT id, subject_id, grade, weight, vote_date, term, notes, vote_type, created_at, school_year_id
            FROM votes
            WHERE subject_id = ?1 AND vote_date = ?2 AND vote_type = ?3 AND school_year_id = ?4
            LIMIT 1
            "#,
        )?;

        let vote = stmt
            .query_row(params![subject_id, date, vote_type, school_year_id], |r| {
                Ok(Vote {
                    id: r.get(0)?,
                    subject_id: r.get(1)?,
                    grade: r.get(2)?,
                    weight: r.get(3)?,
                    vote_date: r.get(4)?,
                    term: r.get(5)?,
                    notes: r.get(6)?,
                    vote_type: r.get(7)?,
                    created_at: r.get(8)?,
                    school_year_id: r.get(9)?,
                })
            })
            .optional()?;

        Ok(vote)
    }

    // -------------------------------------------------------------------------
    // Settings
    // -------------------------------------------------------------------------

    pub fn get_setting(&self, key: &str) -> Result<Option<String>, DbError> {
        let mut stmt = self.conn.prepare("SELECT value FROM settings WHERE key = ?1")?;
        let val = stmt.query_row(params![key], |r| r.get(0)).optional()?;
        Ok(val)
    }

    pub fn set_setting(&mut self, key: &str, value: &str) -> Result<(), DbError> {
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?1, ?2)",
            params![key, value],
        )?;
        Ok(())
    }

    // -------------------------------------------------------------------------
    // Statistics & Goals
    // -------------------------------------------------------------------------

    pub fn get_grade_statistics(
        &self,
        subject_id: Option<i64>,
        term: Option<i32>,
        school_year_id: Option<i64>,
    ) -> Result<GradeStatistics, DbError> {
        let votes = self.get_votes(subject_id, term, school_year_id)?;
        Ok(crate::calculator::calculate_statistics(&votes))
    }

    pub fn get_grade_goals(
        &self,
        school_year_id: i64,
        term: i32,
    ) -> Result<Vec<GradeGoal>, DbError> {
        let mut stmt = self.conn.prepare(
            r#"
            SELECT id, subject_id, target_grade, school_year_id, term, notes
            FROM grade_goals
            WHERE school_year_id = ?1 AND term = ?2
            "#,
        )?;

        let rows = stmt.query_map(params![school_year_id, term], |r| {
            Ok(GradeGoal {
                id: r.get(0)?,
                subject_id: r.get(1)?,
                target_grade: r.get(2)?,
                school_year_id: r.get(3)?,
                term: r.get(4)?,
                notes: r.get(5)?,
            })
        })?;

        let mut goals = Vec::new();
        for g in rows {
            goals.push(g?);
        }
        Ok(goals)
    }

    pub fn set_grade_goal(
        &mut self,
        subject_id: i64,
        target_grade: f64,
        school_year_id: i64,
        term: i32,
        notes: &str,
    ) -> Result<(), DbError> {
        self.conn.execute(
            r#"
            INSERT INTO grade_goals (subject_id, target_grade, school_year_id, term, notes)
            VALUES (?1, ?2, ?3, ?4, ?5)
            ON CONFLICT(subject_id, school_year_id, term) DO UPDATE SET
                target_grade = excluded.target_grade,
                notes = excluded.notes
            "#,
            params![subject_id, target_grade, school_year_id, term, notes],
        )?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_db_init_and_seed() {
        let mut db = Database::new::<&str>(None).expect("In-memory db should initialize");
        let subjects = db.get_subjects().expect("Should load seeded subjects");
        assert_eq!(subjects.len(), 8);

        let years = db.get_school_years().expect("Should load seeded school year");
        assert_eq!(years.len(), 1);
        assert!(years[0].is_active);
    }

    #[test]
    fn test_vote_crud_and_metadata_lookup() {
        let mut db = Database::new::<&str>(None).unwrap();
        let subjects = db.get_subjects().unwrap();
        let sub_id = subjects[0].id;
        let year_id = db.get_active_school_year().unwrap().unwrap().id;

        let new_vote = NewVote {
            subject_id: sub_id,
            grade: 8.5,
            weight: 1.0,
            vote_date: "2026-02-10".to_string(),
            term: 2,
            notes: "Test note".to_string(),
            vote_type: "Scritto".to_string(),
            school_year_id: year_id,
        };

        let vote_id = db.add_vote(&new_vote).expect("Should add vote");
        assert!(vote_id > 0);

        let found = db
            .find_vote_by_metadata(sub_id, "2026-02-10", "Scritto", year_id)
            .unwrap();
        assert!(found.is_some());
        assert_eq!(found.unwrap().grade, 8.5);

        db.delete_vote(vote_id).unwrap();
        let after_del = db.get_vote_by_id(vote_id).unwrap();
        assert!(after_del.is_none());
    }
}
