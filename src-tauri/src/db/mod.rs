//! SQLite-backed persistence layer.
//!
//! The schema is a straight port of `legacy-python/src/votetracker/db_schema.py`
//! so the existing `~/.local/share/votetracker/votes.db` file from the Python
//! release opens without any on-disk migration.

pub mod schema;
pub mod school_years;
pub mod settings;
pub mod subjects;
pub mod votes;

use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use std::path::PathBuf;

pub type ConnPool = Pool<SqliteConnectionManager>;

#[derive(Debug, thiserror::Error)]
pub enum DbError {
    #[error("sqlite: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("pool: {0}")]
    Pool(#[from] r2d2::Error),
    #[error("io: {0}")]
    Io(#[from] std::io::Error),
    #[error("no data dir")]
    NoDataDir,
}

pub struct Database {
    pool: ConnPool,
}

impl Database {
    /// Open the canonical app database (~/.local/share/votetracker/votes.db on Linux,
    /// XDG-equivalent on Windows/macOS). Runs schema + migrations on first connection.
    pub fn open_default() -> Result<Self, DbError> {
        let path = default_db_path()?;
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        Self::open_at(path)
    }

    pub fn open_at(path: PathBuf) -> Result<Self, DbError> {
        let manager = SqliteConnectionManager::file(&path).with_init(|c| {
            c.execute_batch("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;")
        });
        let pool = Pool::builder().max_size(8).build(manager)?;
        let db = Self { pool };
        db.init()?;
        tracing::info!(path = %path.display(), "database ready");
        Ok(db)
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    fn init(&self) -> Result<(), DbError> {
        let mut conn = self.pool.get()?;
        let tx = conn.transaction()?;
        schema::create_schema(&tx)?;
        schema::migrate_votes_table(&tx)?;
        schema::seed_defaults(&tx)?;
        schema::create_indices(&tx)?;
        tx.commit()?;
        Ok(())
    }
}

fn default_db_path() -> Result<PathBuf, DbError> {
    // Mirrors the Python resolver in legacy-python/src/votetracker/database.py.
    #[cfg(target_os = "windows")]
    let base = std::env::var_os("APPDATA")
        .map(PathBuf::from)
        .or_else(|| dirs_home())
        .ok_or(DbError::NoDataDir)?;

    #[cfg(target_os = "macos")]
    let base = dirs_home()
        .map(|h| h.join("Library").join("Application Support"))
        .ok_or(DbError::NoDataDir)?;

    #[cfg(all(unix, not(target_os = "macos")))]
    let base = std::env::var_os("XDG_DATA_HOME")
        .map(PathBuf::from)
        .or_else(|| dirs_home().map(|h| h.join(".local").join("share")))
        .ok_or(DbError::NoDataDir)?;

    Ok(base.join("votetracker").join("votes.db"))
}

#[allow(dead_code)]
fn dirs_home() -> Option<PathBuf> {
    std::env::var_os("HOME").map(PathBuf::from)
}
