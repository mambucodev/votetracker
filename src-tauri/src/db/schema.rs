//! Schema DDL, migrations, seeds, and indices.
//!
//! Straight port of `legacy-python/src/votetracker/db_schema.py` — identical
//! table/column names, so a `votes.db` created by the Python app opens
//! here without conversion.

use chrono::{Datelike, Local};
use rusqlite::{params, Transaction};

pub fn create_schema(tx: &Transaction) -> rusqlite::Result<()> {
    tx.execute_batch(
        r#"
        CREATE TABLE IF NOT EXISTS school_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            start_year INTEGER NOT NULL,
            is_active INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

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
        );
        "#,
    )
}

/// Create the `votes` table, or add the multi-year/multi-term columns
/// to a pre-existing old-schema `votes` table.
pub fn migrate_votes_table(tx: &Transaction) -> rusqlite::Result<()> {
    let exists: bool = tx
        .query_row(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='votes'",
            [],
            |_| Ok(true),
        )
        .unwrap_or(false);

    if exists {
        let mut stmt = tx.prepare("PRAGMA table_info(votes)")?;
        let columns: Vec<String> = stmt
            .query_map([], |row| row.get::<_, String>(1))?
            .filter_map(Result::ok)
            .collect();
        drop(stmt);

        if !columns.iter().any(|c| c == "school_year_id") {
            tx.execute("ALTER TABLE votes ADD COLUMN school_year_id INTEGER", [])?;
            tx.execute("ALTER TABLE votes ADD COLUMN term INTEGER DEFAULT 1", [])?;
        }
    } else {
        tx.execute_batch(
            r#"
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
            );
            "#,
        )?;
    }
    Ok(())
}

/// Ensure a blank database has at least one school year + default term setting,
/// and backfill orphan votes with NULL school_year_id.
pub fn seed_defaults(tx: &Transaction) -> rusqlite::Result<()> {
    let year_count: i64 =
        tx.query_row("SELECT COUNT(*) FROM school_years", [], |r| r.get(0))?;
    if year_count == 0 {
        // Italian school year starts in September.
        let now = Local::now();
        let start_year = if now.month() >= 9 {
            now.year()
        } else {
            now.year() - 1
        };
        let name = format!("{}/{}", start_year, start_year + 1);
        tx.execute(
            "INSERT INTO school_years (name, start_year, is_active) VALUES (?, ?, 1)",
            params![name, start_year],
        )?;
    }

    // Backfill orphan votes to the active year.
    if let Ok(active_id) = tx.query_row(
        "SELECT id FROM school_years WHERE is_active = 1",
        [],
        |r| r.get::<_, i64>(0),
    ) {
        tx.execute(
            "UPDATE votes SET school_year_id = ? WHERE school_year_id IS NULL",
            params![active_id],
        )?;
    }

    // Default current_term setting.
    let has_term: bool = tx
        .query_row(
            "SELECT 1 FROM settings WHERE key = 'current_term'",
            [],
            |_| Ok(true),
        )
        .unwrap_or(false);
    if !has_term {
        tx.execute(
            "INSERT INTO settings (key, value) VALUES ('current_term', '1')",
            [],
        )?;
    }
    Ok(())
}

pub fn create_indices(tx: &Transaction) -> rusqlite::Result<()> {
    tx.execute_batch(
        r#"
        CREATE INDEX IF NOT EXISTS idx_votes_subject   ON votes(subject_id);
        CREATE INDEX IF NOT EXISTS idx_votes_year      ON votes(school_year_id);
        CREATE INDEX IF NOT EXISTS idx_votes_term      ON votes(term);
        CREATE INDEX IF NOT EXISTS idx_votes_date      ON votes(date);
        CREATE INDEX IF NOT EXISTS idx_votes_composite ON votes(subject_id, school_year_id, term);
        CREATE INDEX IF NOT EXISTS idx_settings_key    ON settings(key);
        "#,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    fn open_memory() -> Connection {
        let c = Connection::open_in_memory().unwrap();
        c.execute_batch("PRAGMA foreign_keys = ON;").unwrap();
        c
    }

    #[test]
    fn fresh_schema_creates_all_tables_and_seeds() {
        let mut conn = open_memory();
        let tx = conn.transaction().unwrap();
        create_schema(&tx).unwrap();
        migrate_votes_table(&tx).unwrap();
        seed_defaults(&tx).unwrap();
        create_indices(&tx).unwrap();
        tx.commit().unwrap();

        for t in ["school_years", "subjects", "settings", "grade_goals", "votes"] {
            let exists: bool = conn
                .query_row(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    [t],
                    |_| Ok(true),
                )
                .unwrap_or(false);
            assert!(exists, "{t} table missing");
        }

        // Seeded one active year + default current_term.
        let year_count: i64 = conn
            .query_row("SELECT COUNT(*) FROM school_years", [], |r| r.get(0))
            .unwrap();
        assert_eq!(year_count, 1);

        let term: String = conn
            .query_row("SELECT value FROM settings WHERE key='current_term'", [], |r| r.get(0))
            .unwrap();
        assert_eq!(term, "1");
    }

    #[test]
    fn seed_is_idempotent() {
        let mut conn = open_memory();
        for _ in 0..3 {
            let tx = conn.transaction().unwrap();
            create_schema(&tx).unwrap();
            migrate_votes_table(&tx).unwrap();
            seed_defaults(&tx).unwrap();
            tx.commit().unwrap();
        }
        let year_count: i64 = conn
            .query_row("SELECT COUNT(*) FROM school_years", [], |r| r.get(0))
            .unwrap();
        assert_eq!(year_count, 1, "seed_defaults must be idempotent");
    }

    #[test]
    fn migrates_pre_multiyear_votes_table() {
        let mut conn = open_memory();
        conn.execute_batch(
            r#"
            CREATE TABLE subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL);
            CREATE TABLE votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                grade REAL NOT NULL,
                type TEXT DEFAULT 'Written',
                date TEXT,
                description TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            );
            "#,
        )
        .unwrap();

        let tx = conn.transaction().unwrap();
        create_schema(&tx).unwrap();
        migrate_votes_table(&tx).unwrap();
        tx.commit().unwrap();

        let mut stmt = conn.prepare("PRAGMA table_info(votes)").unwrap();
        let cols: Vec<String> = stmt
            .query_map([], |r| r.get::<_, String>(1))
            .unwrap()
            .filter_map(Result::ok)
            .collect();
        assert!(cols.contains(&"school_year_id".into()));
        assert!(cols.contains(&"term".into()));
    }
}
