//! School-year CRUD. Sorted DESC by `start_year`.

use crate::domain::types::SchoolYear;
use rusqlite::{params, Connection, OptionalExtension};

pub fn list(conn: &Connection) -> rusqlite::Result<Vec<SchoolYear>> {
    let mut stmt = conn.prepare(
        "SELECT id, name, start_year, is_active
         FROM school_years
         ORDER BY start_year DESC",
    )?;
    let rows = stmt.query_map([], |r| {
        Ok(SchoolYear {
            id: r.get(0)?,
            name: r.get(1)?,
            start_year: r.get(2)?,
            is_active: r.get::<_, i64>(3)? != 0,
        })
    })?;
    rows.collect()
}

pub fn active(conn: &Connection) -> rusqlite::Result<Option<SchoolYear>> {
    conn.query_row(
        "SELECT id, name, start_year, is_active FROM school_years WHERE is_active = 1",
        [],
        |r| {
            Ok(SchoolYear {
                id: r.get(0)?,
                name: r.get(1)?,
                start_year: r.get(2)?,
                is_active: true,
            })
        },
    )
    .optional()
}

pub fn add(conn: &Connection, start_year: i32) -> rusqlite::Result<i64> {
    let name = format!("{}/{}", start_year, start_year + 1);
    conn.execute(
        "INSERT INTO school_years (name, start_year, is_active) VALUES (?1, ?2, 0)",
        params![name, start_year],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Set a single year active; all others become inactive. Emits no events;
/// the command layer is responsible for `school-year-changed`.
pub fn set_active(conn: &mut Connection, year_id: i64) -> rusqlite::Result<()> {
    let tx = conn.transaction()?;
    tx.execute("UPDATE school_years SET is_active = 0", [])?;
    tx.execute(
        "UPDATE school_years SET is_active = 1 WHERE id = ?1",
        params![year_id],
    )?;
    tx.commit()
}

/// Cannot delete the last remaining year.
pub fn delete(conn: &Connection, year_id: i64) -> rusqlite::Result<bool> {
    let count: i64 =
        conn.query_row("SELECT COUNT(*) FROM school_years", [], |r| r.get(0))?;
    if count <= 1 {
        return Ok(false);
    }
    conn.execute("DELETE FROM school_years WHERE id = ?1", params![year_id])?;
    Ok(true)
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
    fn seed_produces_one_active_year() {
        let c = fresh();
        let active = active(&c).unwrap().unwrap();
        assert!(active.is_active);
        let all = list(&c).unwrap();
        assert_eq!(all.len(), 1);
    }

    #[test]
    fn add_and_switch_active() {
        let mut c = fresh();
        let new_id = add(&c, 2024).unwrap();
        set_active(&mut c, new_id).unwrap();
        let active = active(&c).unwrap().unwrap();
        assert_eq!(active.id, new_id);
        assert_eq!(active.start_year, 2024);
    }

    #[test]
    fn cannot_delete_last_year() {
        let c = fresh();
        let current = active(&c).unwrap().unwrap();
        assert_eq!(delete(&c, current.id).unwrap(), false);
        assert_eq!(list(&c).unwrap().len(), 1);
    }

    #[test]
    fn list_sorted_desc() {
        let c = fresh();
        add(&c, 2020).unwrap();
        add(&c, 2022).unwrap();
        let all = list(&c).unwrap();
        assert!(all.windows(2).all(|w| w[0].start_year >= w[1].start_year));
    }
}
