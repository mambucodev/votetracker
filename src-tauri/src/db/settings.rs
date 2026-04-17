//! Key/value settings store + base64 credential helpers + provider
//! subject-mapping helpers.
//!
//! Ports `legacy-python/src/votetracker/database.py` settings methods
//! (lines ~300–530). Base64 is obfuscation-only — same semantics as Python.

use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use rusqlite::{params, Connection, OptionalExtension};

/// Store / upsert a setting key.
pub fn set_setting(conn: &Connection, key: &str, value: &str) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?1, ?2)
         ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        params![key, value],
    )?;
    Ok(())
}

pub fn get_setting(conn: &Connection, key: &str) -> rusqlite::Result<Option<String>> {
    conn.query_row(
        "SELECT value FROM settings WHERE key = ?1",
        params![key],
        |row| row.get::<_, Option<String>>(0),
    )
    .optional()
    .map(|opt| opt.flatten())
}

pub fn delete_setting(conn: &Connection, key: &str) -> rusqlite::Result<()> {
    conn.execute("DELETE FROM settings WHERE key = ?1", params![key])?;
    Ok(())
}

/// Base64-encode + store a credential. The Python app uses stdlib base64 on
/// the utf-8 encoding of the string; we match byte-for-byte.
pub fn set_credential(
    conn: &Connection,
    provider_id: &str,
    field: &str,
    value: &str,
) -> rusqlite::Result<()> {
    let encoded = B64.encode(value.as_bytes());
    set_setting(conn, &format!("{provider_id}_{field}"), &encoded)
}

pub fn get_credential(
    conn: &Connection,
    provider_id: &str,
    field: &str,
) -> rusqlite::Result<Option<String>> {
    let raw = get_setting(conn, &format!("{provider_id}_{field}"))?;
    Ok(raw.and_then(|s| {
        B64.decode(s.as_bytes())
            .ok()
            .and_then(|bytes| String::from_utf8(bytes).ok())
    }))
}

pub fn get_credentials(
    conn: &Connection,
    provider_id: &str,
    field_names: &[&str],
) -> rusqlite::Result<std::collections::HashMap<String, Option<String>>> {
    let mut out = std::collections::HashMap::with_capacity(field_names.len());
    for f in field_names {
        out.insert((*f).to_string(), get_credential(conn, provider_id, f)?);
    }
    Ok(out)
}

pub fn has_all_credentials(
    conn: &Connection,
    provider_id: &str,
    field_names: &[&str],
) -> rusqlite::Result<bool> {
    for f in field_names {
        match get_credential(conn, provider_id, f)? {
            Some(v) if !v.is_empty() => {}
            _ => return Ok(false),
        }
    }
    Ok(true)
}

// ---------- Provider subject mappings ----------

pub fn save_mapping(
    conn: &Connection,
    provider_id: &str,
    source_subject: &str,
    target_subject: &str,
) -> rusqlite::Result<()> {
    set_setting(
        conn,
        &format!("{provider_id}_mapping_{source_subject}"),
        target_subject,
    )
}

pub fn get_mapping(
    conn: &Connection,
    provider_id: &str,
    source_subject: &str,
) -> rusqlite::Result<Option<String>> {
    get_setting(conn, &format!("{provider_id}_mapping_{source_subject}"))
}

pub fn all_mappings(
    conn: &Connection,
    provider_id: &str,
) -> rusqlite::Result<std::collections::HashMap<String, String>> {
    let prefix = format!("{provider_id}_mapping_");
    let mut stmt =
        conn.prepare("SELECT key, value FROM settings WHERE key LIKE ?1 || '%'")?;
    let rows = stmt.query_map(params![&prefix], |r| {
        Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?))
    })?;
    let mut out = std::collections::HashMap::new();
    for row in rows {
        let (k, v) = row?;
        if let Some(src) = k.strip_prefix(&prefix) {
            out.insert(src.to_string(), v);
        }
    }
    Ok(out)
}

// ---------- Auto-sync config ----------

pub fn auto_sync_enabled(conn: &Connection, provider_id: &str) -> rusqlite::Result<bool> {
    Ok(get_setting(conn, &format!("{provider_id}_auto_sync"))?
        .map(|v| v == "1")
        .unwrap_or(false))
}

pub fn set_auto_sync_enabled(
    conn: &Connection,
    provider_id: &str,
    enabled: bool,
) -> rusqlite::Result<()> {
    set_setting(
        conn,
        &format!("{provider_id}_auto_sync"),
        if enabled { "1" } else { "0" },
    )
}

pub fn sync_interval_minutes(conn: &Connection, provider_id: &str) -> rusqlite::Result<u32> {
    Ok(get_setting(conn, &format!("{provider_id}_sync_interval"))?
        .and_then(|s| s.parse().ok())
        .unwrap_or(60))
}

pub fn set_sync_interval_minutes(
    conn: &Connection,
    provider_id: &str,
    minutes: u32,
) -> rusqlite::Result<()> {
    set_setting(conn, &format!("{provider_id}_sync_interval"), &minutes.to_string())
}

pub fn get_last_sync(conn: &Connection, provider_id: &str) -> rusqlite::Result<Option<String>> {
    get_setting(conn, &format!("{provider_id}_last_sync"))
}

pub fn set_last_sync(
    conn: &Connection,
    provider_id: &str,
    iso_timestamp: &str,
) -> rusqlite::Result<()> {
    set_setting(conn, &format!("{provider_id}_last_sync"), iso_timestamp)
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
    fn setting_roundtrip_upserts() {
        let c = fresh();
        set_setting(&c, "language", "it").unwrap();
        assert_eq!(get_setting(&c, "language").unwrap().unwrap(), "it");
        set_setting(&c, "language", "en").unwrap();
        assert_eq!(get_setting(&c, "language").unwrap().unwrap(), "en");
    }

    #[test]
    fn credential_roundtrip_is_base64() {
        let c = fresh();
        set_credential(&c, "classeviva", "username", "S1234567").unwrap();
        assert_eq!(
            get_credential(&c, "classeviva", "username").unwrap().unwrap(),
            "S1234567"
        );
        let raw = get_setting(&c, "classeviva_username").unwrap().unwrap();
        assert_ne!(raw, "S1234567"); // actually encoded
    }

    #[test]
    fn mappings_namespaced_per_provider() {
        let c = fresh();
        save_mapping(&c, "cv", "MATEMATICA", "Math").unwrap();
        save_mapping(&c, "axios", "MATEMATICA", "Matematica").unwrap();
        assert_eq!(get_mapping(&c, "cv", "MATEMATICA").unwrap().unwrap(), "Math");
        assert_eq!(
            get_mapping(&c, "axios", "MATEMATICA").unwrap().unwrap(),
            "Matematica"
        );

        let cv = all_mappings(&c, "cv").unwrap();
        assert_eq!(cv.len(), 1);
        assert_eq!(cv["MATEMATICA"], "Math");
    }

    #[test]
    fn auto_sync_defaults() {
        let c = fresh();
        assert_eq!(auto_sync_enabled(&c, "cv").unwrap(), false);
        assert_eq!(sync_interval_minutes(&c, "cv").unwrap(), 60);
        set_auto_sync_enabled(&c, "cv", true).unwrap();
        set_sync_interval_minutes(&c, "cv", 15).unwrap();
        assert!(auto_sync_enabled(&c, "cv").unwrap());
        assert_eq!(sync_interval_minutes(&c, "cv").unwrap(), 15);
    }
}
