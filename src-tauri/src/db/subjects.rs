//! Subject CRUD. Names are UNIQUE; lookups are case-sensitive.

use rusqlite::{params, Connection, OptionalExtension};

pub fn list(conn: &Connection) -> rusqlite::Result<Vec<String>> {
    let mut stmt = conn.prepare("SELECT name FROM subjects ORDER BY name")?;
    let rows = stmt.query_map([], |r| r.get::<_, String>(0))?;
    rows.collect()
}

pub fn get_id(conn: &Connection, name: &str) -> rusqlite::Result<Option<i64>> {
    conn.query_row(
        "SELECT id FROM subjects WHERE name = ?1",
        params![name],
        |r| r.get::<_, i64>(0),
    )
    .optional()
}

/// Insert, returning new id. If the subject already exists, returns the existing id.
pub fn add(conn: &Connection, name: &str) -> rusqlite::Result<i64> {
    if let Some(id) = get_id(conn, name)? {
        return Ok(id);
    }
    conn.execute("INSERT INTO subjects (name) VALUES (?1)", params![name])?;
    Ok(conn.last_insert_rowid())
}

pub fn rename(conn: &Connection, old_name: &str, new_name: &str) -> rusqlite::Result<bool> {
    if old_name == new_name {
        return Ok(true);
    }
    // Fail if new_name already exists.
    if get_id(conn, new_name)?.is_some() {
        return Ok(false);
    }
    let n = conn.execute(
        "UPDATE subjects SET name = ?1 WHERE name = ?2",
        params![new_name, old_name],
    )?;
    Ok(n > 0)
}

/// Delete cascades to votes (ON DELETE CASCADE in schema).
pub fn delete(conn: &Connection, name: &str) -> rusqlite::Result<bool> {
    let n = conn.execute("DELETE FROM subjects WHERE name = ?1", params![name])?;
    Ok(n > 0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::schema::{create_indices, create_schema, migrate_votes_table, seed_defaults};

    fn fresh() -> Connection {
        let mut c = Connection::open_in_memory().unwrap();
        let tx = c.transaction().unwrap();
        create_schema(&tx).unwrap();
        migrate_votes_table(&tx).unwrap();
        seed_defaults(&tx).unwrap();
        create_indices(&tx).unwrap();
        tx.commit().unwrap();
        c
    }

    #[test]
    fn crud_cycle() {
        let c = fresh();
        let id = add(&c, "Math").unwrap();
        assert_eq!(get_id(&c, "Math").unwrap().unwrap(), id);

        // duplicate add returns same id
        let id2 = add(&c, "Math").unwrap();
        assert_eq!(id, id2);

        assert_eq!(list(&c).unwrap(), vec!["Math".to_string()]);

        assert!(rename(&c, "Math", "Mathematics").unwrap());
        assert!(get_id(&c, "Math").unwrap().is_none());
        assert!(get_id(&c, "Mathematics").unwrap().is_some());

        assert!(delete(&c, "Mathematics").unwrap());
        assert!(list(&c).unwrap().is_empty());
    }

    #[test]
    fn rename_rejects_existing_target() {
        let c = fresh();
        add(&c, "Math").unwrap();
        add(&c, "Italian").unwrap();
        assert_eq!(rename(&c, "Math", "Italian").unwrap(), false);
    }

    #[test]
    fn list_alphabetical() {
        let c = fresh();
        for s in ["Physics", "Math", "Italian"] {
            add(&c, s).unwrap();
        }
        assert_eq!(list(&c).unwrap(), vec!["Italian", "Math", "Physics"]);
    }
}
