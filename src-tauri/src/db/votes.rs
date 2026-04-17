//! Vote CRUD + statistics queries.
//!
//! Filter semantics match `legacy-python/src/votetracker/database.py::get_votes`:
//! if `subject` / `school_year_id` / `term` are None the filter is skipped;
//! otherwise a WHERE clause is added.

use crate::db::{schema, subjects};
use crate::domain::types::{GradeType, Vote};
use rusqlite::{params_from_iter, types::Value, Connection, OptionalExtension};

#[derive(Default, Debug, Clone, Copy)]
pub struct VoteFilter<'a> {
    pub subject: Option<&'a str>,
    pub school_year_id: Option<i64>,
    pub term: Option<i32>,
}

pub fn list(conn: &Connection, filter: VoteFilter<'_>) -> rusqlite::Result<Vec<Vote>> {
    let mut sql = String::from(
        "SELECT v.id, s.name, v.grade, v.type, v.term, v.date, v.description, v.weight, v.school_year_id
         FROM votes v JOIN subjects s ON v.subject_id = s.id WHERE 1=1",
    );
    let mut args: Vec<Value> = Vec::new();

    if let Some(name) = filter.subject {
        sql.push_str(" AND s.name = ?");
        args.push(Value::Text(name.to_string()));
    }
    if let Some(year_id) = filter.school_year_id {
        sql.push_str(" AND v.school_year_id = ?");
        args.push(Value::Integer(year_id));
    }
    if let Some(term) = filter.term {
        sql.push_str(" AND v.term = ?");
        args.push(Value::Integer(term as i64));
    }
    sql.push_str(" ORDER BY v.date DESC, v.id DESC");

    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(params_from_iter(args.iter()), row_to_vote)?;
    rows.collect()
}

pub fn get(conn: &Connection, id: i64) -> rusqlite::Result<Option<Vote>> {
    conn.query_row(
        "SELECT v.id, s.name, v.grade, v.type, v.term, v.date, v.description, v.weight, v.school_year_id
         FROM votes v JOIN subjects s ON v.subject_id = s.id
         WHERE v.id = ?1",
        [id],
        row_to_vote,
    )
    .optional()
}

/// Returns `true` if an identical vote (same subject, grade, date, type, year) already exists.
pub fn exists_exact(
    conn: &Connection,
    subject: &str,
    grade: f64,
    date: &str,
    kind: GradeType,
    school_year_id: Option<i64>,
) -> rusqlite::Result<bool> {
    let subject_id = match subjects::get_id(conn, subject)? {
        Some(id) => id,
        None => return Ok(false),
    };
    let year_id = school_year_id.or_else(|| active_year_id(conn).ok().flatten());
    let Some(year_id) = year_id else {
        return Ok(false);
    };
    let n: i64 = conn.query_row(
        "SELECT COUNT(*) FROM votes
         WHERE subject_id = ?1 AND school_year_id = ?2 AND date = ?3 AND type = ?4 AND grade = ?5",
        rusqlite::params![subject_id, year_id, date, kind.as_str(), grade],
        |r| r.get(0),
    )?;
    Ok(n > 0)
}

/// Find an existing vote by **metadata only** (ignoring grade / weight /
/// description). This is how sync dedup detects teacher-amended grades.
pub fn find_by_metadata(
    conn: &Connection,
    subject: &str,
    date: &str,
    kind: GradeType,
    school_year_id: Option<i64>,
) -> rusqlite::Result<Option<Vote>> {
    let subject_id = match subjects::get_id(conn, subject)? {
        Some(id) => id,
        None => return Ok(None),
    };
    let year_id = school_year_id.or_else(|| active_year_id(conn).ok().flatten());
    let Some(year_id) = year_id else {
        return Ok(None);
    };
    conn.query_row(
        "SELECT v.id, s.name, v.grade, v.type, v.term, v.date, v.description, v.weight, v.school_year_id
         FROM votes v JOIN subjects s ON v.subject_id = s.id
         WHERE v.subject_id = ?1 AND v.school_year_id = ?2 AND v.date = ?3 AND v.type = ?4",
        rusqlite::params![subject_id, year_id, date, kind.as_str()],
        row_to_vote,
    )
    .optional()
}

pub fn add(conn: &Connection, v: &Vote) -> rusqlite::Result<i64> {
    let subject_id = subjects::add(conn, &v.subject)?;
    let year_id = v.school_year_id.or_else(|| active_year_id(conn).ok().flatten());
    let term = if v.term > 0 { v.term } else { current_term(conn).unwrap_or(1) };

    conn.execute(
        "INSERT INTO votes (subject_id, school_year_id, grade, type, term, date, description, weight)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        rusqlite::params![
            subject_id,
            year_id,
            v.grade,
            v.kind.as_str(),
            term,
            v.date,
            v.description,
            if v.weight > 0.0 { v.weight } else { 1.0 }
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

pub fn update(conn: &Connection, id: i64, v: &Vote) -> rusqlite::Result<bool> {
    let subject_id = subjects::add(conn, &v.subject)?;
    let n = conn.execute(
        "UPDATE votes SET subject_id = ?1, grade = ?2, type = ?3, term = ?4,
                          date = ?5, description = ?6, weight = ?7
         WHERE id = ?8",
        rusqlite::params![
            subject_id,
            v.grade,
            v.kind.as_str(),
            v.term,
            v.date,
            v.description,
            if v.weight > 0.0 { v.weight } else { 1.0 },
            id
        ],
    )?;
    Ok(n > 0)
}

pub fn delete(conn: &Connection, id: i64) -> rusqlite::Result<bool> {
    let n = conn.execute("DELETE FROM votes WHERE id = ?1", rusqlite::params![id])?;
    Ok(n > 0)
}

// ---------- internal helpers ----------

fn row_to_vote(row: &rusqlite::Row<'_>) -> rusqlite::Result<Vote> {
    let kind_str: String = row.get(3)?;
    let kind = GradeType::from_str_loose(&kind_str).unwrap_or(GradeType::Written);
    Ok(Vote {
        id: Some(row.get(0)?),
        subject: row.get(1)?,
        grade: row.get(2)?,
        kind,
        term: row.get(4)?,
        date: row.get::<_, Option<String>>(5)?.unwrap_or_default(),
        description: row.get(6)?,
        weight: row.get(7)?,
        school_year_id: row.get(8)?,
    })
}

fn active_year_id(conn: &Connection) -> rusqlite::Result<Option<i64>> {
    conn.query_row(
        "SELECT id FROM school_years WHERE is_active = 1",
        [],
        |r| r.get::<_, i64>(0),
    )
    .optional()
}

fn current_term(conn: &Connection) -> rusqlite::Result<i32> {
    // The default row seeded by schema::seed_defaults guarantees key exists.
    let _ = schema::seed_defaults;
    let s = crate::db::settings::get_setting(conn, "current_term")?;
    Ok(s.and_then(|v| v.parse().ok()).unwrap_or(1))
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

    fn sample(subject: &str, grade: f64, date: &str) -> Vote {
        Vote {
            id: None,
            subject: subject.into(),
            grade,
            kind: GradeType::Written,
            term: 1,
            date: date.into(),
            description: None,
            weight: 1.0,
            school_year_id: None,
        }
    }

    #[test]
    fn add_list_update_delete() {
        let c = fresh();
        let id = add(&c, &sample("Math", 7.5, "2026-01-10")).unwrap();
        let got = get(&c, id).unwrap().unwrap();
        assert_eq!(got.subject, "Math");
        assert!((got.grade - 7.5).abs() < 1e-9);

        let mut changed = got.clone();
        changed.grade = 8.0;
        assert!(update(&c, id, &changed).unwrap());
        assert_eq!(get(&c, id).unwrap().unwrap().grade, 8.0);

        assert!(delete(&c, id).unwrap());
        assert!(get(&c, id).unwrap().is_none());
    }

    #[test]
    fn list_filtered() {
        let c = fresh();
        add(&c, &sample("Math", 7.0, "2026-02-01")).unwrap();
        add(&c, &sample("Italian", 6.0, "2026-02-05")).unwrap();

        let all = list(&c, VoteFilter::default()).unwrap();
        assert_eq!(all.len(), 2);

        let math = list(
            &c,
            VoteFilter {
                subject: Some("Math"),
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(math.len(), 1);
        assert_eq!(math[0].subject, "Math");
    }

    #[test]
    fn find_by_metadata_ignores_grade() {
        let c = fresh();
        add(&c, &sample("Math", 7.0, "2026-03-05")).unwrap();
        // Same (subject, date, type), different grade — should still match.
        let found = find_by_metadata(&c, "Math", "2026-03-05", GradeType::Written, None)
            .unwrap()
            .unwrap();
        assert!((found.grade - 7.0).abs() < 1e-9);

        // Exact-grade lookup for a different grade → false.
        assert!(!exists_exact(&c, "Math", 9.0, "2026-03-05", GradeType::Written, None).unwrap());
        // Exact-grade lookup for the SAME grade → true.
        assert!(exists_exact(&c, "Math", 7.0, "2026-03-05", GradeType::Written, None).unwrap());
    }
}
