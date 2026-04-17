//! `#[tauri::command]` IPC surface — votes, subjects, school years,
//! settings. Providers and PDF export land in M4–M5.
//!
//! Every command returns `Result<T, String>` because Tauri's magic
//! `CommandResult` needs a `Serialize` error type. We map the various
//! internal errors to `String` at the boundary.

use crate::db::{school_years, settings, subjects, votes, Database};
use crate::domain::simulator;
use crate::domain::subject_match::{self, AutoSuggestion};
use crate::domain::types::{GradeType, SchoolYear, Vote};
use crate::events;
use crate::sync::{self, import::ImportSummary, RawGrade};
use crate::undo::{UndoKind, UndoManager, UndoState};
use serde::Deserialize;
use std::collections::HashMap;
use std::sync::Mutex;
use tauri::{Emitter, State};

/// Shared app-wide state. One `Database` (pooled), one `UndoManager`,
/// plus cached provider-id list for the UI.
pub struct AppState {
    pub db: Database,
    pub undo: Mutex<UndoManager>,
}

impl AppState {
    pub fn new(db: Database) -> Self {
        Self {
            db,
            undo: Mutex::new(UndoManager::new()),
        }
    }
}

fn err<E: std::fmt::Display>(e: E) -> String {
    e.to_string()
}

fn emit_data_changed<R: tauri::Runtime>(app: &tauri::AppHandle<R>) {
    let _ = app.emit(events::DATA_CHANGED, ());
}

fn emit_undo_state<R: tauri::Runtime>(app: &tauri::AppHandle<R>, state: UndoState) {
    let _ = app.emit(events::UNDO_STATE, state);
}

// ---------- Liveness ----------

#[tauri::command]
pub fn ping() -> &'static str {
    "pong"
}

// ---------- Votes ----------

#[tauri::command]
pub fn list_votes(
    state: State<'_, AppState>,
    subject: Option<String>,
    school_year_id: Option<i64>,
    term: Option<i32>,
) -> Result<Vec<Vote>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    votes::list(
        &conn,
        votes::VoteFilter {
            subject: subject.as_deref(),
            school_year_id,
            term,
        },
    )
    .map_err(err)
}

#[tauri::command]
pub fn get_vote(state: State<'_, AppState>, id: i64) -> Result<Option<Vote>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    votes::get(&conn, id).map_err(err)
}

#[tauri::command]
pub fn add_vote<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    vote: Vote,
) -> Result<i64, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let id = votes::add(&conn, &vote).map_err(err)?;

    let mut mgr = state.undo.lock().unwrap();
    let mut stored = vote.clone();
    stored.id = Some(id);
    mgr.record_add(id, stored);
    emit_undo_state(&app, mgr.state());
    drop(mgr);

    emit_data_changed(&app);
    Ok(id)
}

#[tauri::command]
pub fn update_vote<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    id: i64,
    vote: Vote,
) -> Result<bool, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let previous = votes::get(&conn, id).map_err(err)?;
    let ok = votes::update(&conn, id, &vote).map_err(err)?;

    if ok {
        if let Some(prev) = previous {
            let mut mgr = state.undo.lock().unwrap();
            let mut new_data = vote;
            new_data.id = Some(id);
            mgr.record_edit(id, prev, new_data);
            emit_undo_state(&app, mgr.state());
        }
        emit_data_changed(&app);
    }
    Ok(ok)
}

#[tauri::command]
pub fn delete_vote<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    id: i64,
) -> Result<bool, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let previous = votes::get(&conn, id).map_err(err)?;
    let ok = votes::delete(&conn, id).map_err(err)?;

    if ok {
        if let Some(prev) = previous {
            let mut mgr = state.undo.lock().unwrap();
            mgr.record_delete(id, prev);
            emit_undo_state(&app, mgr.state());
        }
        emit_data_changed(&app);
    }
    Ok(ok)
}

// ---------- Subjects ----------

#[tauri::command]
pub fn list_subjects(state: State<'_, AppState>) -> Result<Vec<String>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    subjects::list(&conn).map_err(err)
}

#[tauri::command]
pub fn add_subject<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    name: String,
) -> Result<i64, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let id = subjects::add(&conn, &name).map_err(err)?;
    emit_data_changed(&app);
    Ok(id)
}

#[tauri::command]
pub fn rename_subject<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    old_name: String,
    new_name: String,
) -> Result<bool, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let ok = subjects::rename(&conn, &old_name, &new_name).map_err(err)?;
    if ok {
        emit_data_changed(&app);
    }
    Ok(ok)
}

#[tauri::command]
pub fn delete_subject<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    name: String,
) -> Result<bool, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let ok = subjects::delete(&conn, &name).map_err(err)?;
    if ok {
        emit_data_changed(&app);
    }
    Ok(ok)
}

// ---------- School years ----------

#[tauri::command]
pub fn list_years(state: State<'_, AppState>) -> Result<Vec<SchoolYear>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    school_years::list(&conn).map_err(err)
}

#[tauri::command]
pub fn active_year(state: State<'_, AppState>) -> Result<Option<SchoolYear>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    school_years::active(&conn).map_err(err)
}

#[tauri::command]
pub fn add_year<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    start_year: i32,
) -> Result<i64, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let id = school_years::add(&conn, start_year).map_err(err)?;
    let _ = app.emit(events::SCHOOL_YEAR_CHANGED, serde_json::json!({ "added": id }));
    Ok(id)
}

#[tauri::command]
pub fn set_active_year<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    year_id: i64,
) -> Result<(), String> {
    let mut conn = state.db.pool().get().map_err(err)?;
    school_years::set_active(&mut conn, year_id).map_err(err)?;
    let _ = app.emit(
        events::SCHOOL_YEAR_CHANGED,
        serde_json::json!({ "school_year_id": year_id }),
    );
    emit_data_changed(&app);
    Ok(())
}

#[tauri::command]
pub fn delete_year(state: State<'_, AppState>, year_id: i64) -> Result<bool, String> {
    let conn = state.db.pool().get().map_err(err)?;
    school_years::delete(&conn, year_id).map_err(err)
}

// ---------- Settings ----------

#[tauri::command]
pub fn get_setting(
    state: State<'_, AppState>,
    key: String,
) -> Result<Option<String>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    settings::get_setting(&conn, &key).map_err(err)
}

#[tauri::command]
pub fn set_setting(
    state: State<'_, AppState>,
    key: String,
    value: String,
) -> Result<(), String> {
    let conn = state.db.pool().get().map_err(err)?;
    settings::set_setting(&conn, &key, &value).map_err(err)
}

#[tauri::command]
pub fn get_current_term(state: State<'_, AppState>) -> Result<i32, String> {
    let conn = state.db.pool().get().map_err(err)?;
    Ok(settings::get_setting(&conn, "current_term")
        .map_err(err)?
        .and_then(|s| s.parse().ok())
        .unwrap_or(1))
}

#[tauri::command]
pub fn set_current_term<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    term: i32,
) -> Result<(), String> {
    let conn = state.db.pool().get().map_err(err)?;
    settings::set_setting(&conn, "current_term", &term.to_string()).map_err(err)?;
    emit_data_changed(&app);
    Ok(())
}

// ---------- Domain helpers ----------

#[tauri::command]
pub fn calculate_needed_grade(
    state: State<'_, AppState>,
    subject: Option<String>,
    target_avg: f64,
    new_weight: f64,
    school_year_id: Option<i64>,
    term: Option<i32>,
) -> Result<Option<f64>, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let all = votes::list(
        &conn,
        votes::VoteFilter {
            subject: subject.as_deref(),
            school_year_id,
            term,
        },
    )
    .map_err(err)?;
    let pairs: Vec<(f64, f64)> = all.iter().map(|v| (v.grade, v.weight)).collect();
    Ok(simulator::calculate_needed_grade(
        &pairs,
        target_avg,
        new_weight,
    ))
}

#[tauri::command]
pub fn subject_mapping_suggestion(
    state: State<'_, AppState>,
    source_subject: String,
) -> Result<AutoSuggestion, String> {
    let conn = state.db.pool().get().map_err(err)?;
    let vt = subjects::list(&conn).map_err(err)?;
    Ok(subject_match::auto_suggestion(&source_subject, &vt))
}

// ---------- Undo / redo ----------

#[tauri::command]
pub fn undo_state(state: State<'_, AppState>) -> UndoState {
    state.undo.lock().unwrap().state()
}

#[tauri::command]
pub fn undo<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
) -> Result<bool, String> {
    let mut mgr = state.undo.lock().unwrap();
    let Some(action) = mgr.take_undo() else {
        return Ok(false);
    };

    let conn = state.db.pool().get().map_err(err)?;

    match action.kind {
        UndoKind::Add => {
            // Undo-add = delete.
            if let Some(id) = action.vote_id {
                votes::delete(&conn, id).map_err(err)?;
            }
        }
        UndoKind::Edit => {
            // Undo-edit = restore previous state.
            if let (Some(id), Some(prev)) = (action.vote_id, action.previous_data.as_ref()) {
                votes::update(&conn, id, prev).map_err(err)?;
            }
        }
        UndoKind::Delete => {
            // Undo-delete = re-add. Vote gets a new id; patch action for redo.
            let new_id = votes::add(&conn, &action.vote_data).map_err(err)?;
            let mut patched = action.clone();
            patched.vote_id = Some(new_id);
            mgr.commit_undone(patched);
            emit_undo_state(&app, mgr.state());
            drop(mgr);
            emit_data_changed(&app);
            return Ok(true);
        }
    }

    mgr.commit_undone(action);
    emit_undo_state(&app, mgr.state());
    drop(mgr);
    emit_data_changed(&app);
    Ok(true)
}

#[tauri::command]
pub fn redo<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
) -> Result<bool, String> {
    let mut mgr = state.undo.lock().unwrap();
    let Some(action) = mgr.take_redo() else {
        return Ok(false);
    };

    let conn = state.db.pool().get().map_err(err)?;

    match action.kind {
        UndoKind::Add => {
            // Redo-add = add again. New id; patch for future undo.
            let new_id = votes::add(&conn, &action.vote_data).map_err(err)?;
            let mut patched = action.clone();
            patched.vote_id = Some(new_id);
            mgr.commit_redone(patched);
            emit_undo_state(&app, mgr.state());
            drop(mgr);
            emit_data_changed(&app);
            return Ok(true);
        }
        UndoKind::Edit => {
            if let Some(id) = action.vote_id {
                votes::update(&conn, id, &action.vote_data).map_err(err)?;
            }
        }
        UndoKind::Delete => {
            if let Some(id) = action.vote_id {
                votes::delete(&conn, id).map_err(err)?;
            }
        }
    }

    mgr.commit_redone(action);
    emit_undo_state(&app, mgr.state());
    drop(mgr);
    emit_data_changed(&app);
    Ok(true)
}

// ---------- Providers / sync / import ----------

#[derive(Debug, Clone, Deserialize)]
pub struct JsonVote {
    #[serde(alias = "materia")]
    pub subject: String,
    #[serde(alias = "voto")]
    pub grade: f64,
    #[serde(default, alias = "tipo")]
    pub r#type: Option<String>,
    #[serde(default, alias = "quadrimestre")]
    pub term: Option<i32>,
    #[serde(default, alias = "data")]
    pub date: Option<String>,
    #[serde(default, alias = "desc")]
    pub description: Option<String>,
    #[serde(default, alias = "peso")]
    pub weight: Option<f64>,
}

#[tauri::command]
pub fn import_votes_json<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    records: Vec<JsonVote>,
) -> Result<ImportSummary, String> {
    let year_id = {
        let conn = state.db.pool().get().map_err(err)?;
        school_years::active(&conn).map_err(err)?.map(|y| y.id)
    };

    let raw: Vec<RawGrade> = records
        .into_iter()
        .map(|r| {
            let kind = r
                .r#type
                .as_deref()
                .and_then(GradeType::from_str_loose)
                .unwrap_or(GradeType::Written);
            RawGrade {
                subject: r.subject,
                grade: r.grade,
                kind,
                date: r.date.unwrap_or_default(),
                description: r.description,
                weight: r.weight.unwrap_or(1.0),
                term: r.term.unwrap_or(1),
            }
        })
        .collect();

    let summary = sync::import::import_all(&state.db, "json", &raw, year_id)
        .map_err(|e| e.to_string())?;

    let _ = app.emit(
        events::DATA_IMPORTED,
        serde_json::json!({
            "new": summary.new_count,
            "updated": summary.updated_count,
            "skipped": summary.skipped_count,
        }),
    );
    emit_data_changed(&app);
    Ok(summary)
}

#[tauri::command]
pub async fn trigger_sync_now<R: tauri::Runtime>(
    app: tauri::AppHandle<R>,
    state: State<'_, AppState>,
    provider_id: String,
) -> Result<ImportSummary, String> {
    let _ = app.emit(
        events::SYNC_STATUS,
        crate::events::SyncStatusPayload::Started {
            provider_id: provider_id.clone(),
        },
    );

    let result = do_sync(&state.db, &provider_id).await;
    match &result {
        Ok(summary) => {
            if let Ok(conn) = state.db.pool().get() {
                let _ = settings::set_last_sync(
                    &conn,
                    &provider_id,
                    &chrono::Local::now().to_rfc3339(),
                );
            }
            let _ = app.emit(
                events::SYNC_STATUS,
                crate::events::SyncStatusPayload::Done {
                    provider_id: provider_id.clone(),
                    new_count: summary.new_count,
                    updated_count: summary.updated_count,
                    skipped_count: summary.skipped_count,
                },
            );
            let _ = app.emit(
                events::DATA_IMPORTED,
                serde_json::json!({
                    "new": summary.new_count,
                    "updated": summary.updated_count,
                    "skipped": summary.skipped_count,
                }),
            );
            emit_data_changed(&app);
        }
        Err(e) => {
            let _ = app.emit(
                events::SYNC_STATUS,
                crate::events::SyncStatusPayload::Failed {
                    provider_id: provider_id.clone(),
                    message: e.clone(),
                },
            );
        }
    }
    result
}

async fn do_sync(db: &Database, provider_id: &str) -> Result<ImportSummary, String> {
    let mut provider = sync::provider_by_id(provider_id)
        .ok_or_else(|| format!("unknown provider {provider_id}"))?;

    let creds = {
        let conn = db.pool().get().map_err(err)?;
        let mut out: HashMap<String, String> = HashMap::new();
        for f in provider.credential_fields() {
            if let Some(v) = settings::get_credential(&conn, provider_id, &f.name).map_err(err)? {
                out.insert(f.name.clone(), v);
            }
        }
        out
    };

    provider
        .login(&creds)
        .await
        .map_err(|e| format!("login: {e}"))?;

    let grades = provider
        .fetch_grades()
        .await
        .map_err(|e| format!("fetch: {e}"))?;

    let year_id = {
        let conn = db.pool().get().map_err(err)?;
        school_years::active(&conn).map_err(err)?.map(|y| y.id)
    };

    sync::import::import_all(db, provider_id, &grades, year_id)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_providers() -> Vec<serde_json::Value> {
    sync::all_provider_ids()
        .iter()
        .filter_map(|id| sync::provider_by_id(id))
        .map(|p| {
            serde_json::json!({
                "id": p.id(),
                "name": p.display_name(),
                "mapping_prefix": p.mapping_prefix(),
                "fields": p.credential_fields(),
            })
        })
        .collect()
}

// ---------- PDF export ----------

#[tauri::command]
pub fn export_report_card_pdf(
    state: State<'_, AppState>,
    path: String,
    term: i32,
    school_year_id: Option<i64>,
    split: bool,
) -> Result<(), String> {
    crate::pdf::report_card::export(
        &state.db,
        term,
        school_year_id,
        split,
        std::path::Path::new(&path),
    )
    .map_err(|e| e.to_string())
}

// ---------- Misc ----------

#[tauri::command]
pub fn open_data_dir<R: tauri::Runtime>(_app: tauri::AppHandle<R>) -> Result<(), String> {
    let path = data_dir()?;
    // Use platform-specific opener — Tauri v2 shell.open is deprecated but
    // we avoid the plugin-opener dependency to keep the bundle small.
    #[cfg(target_os = "linux")]
    let program = "xdg-open";
    #[cfg(target_os = "macos")]
    let program = "open";
    #[cfg(target_os = "windows")]
    let program = "explorer";

    std::process::Command::new(program)
        .arg(path)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}

fn data_dir() -> Result<std::path::PathBuf, String> {
    // Same resolver as db::default_db_path, minus the final filename.
    #[cfg(all(unix, not(target_os = "macos")))]
    let base = std::env::var_os("XDG_DATA_HOME")
        .map(std::path::PathBuf::from)
        .or_else(|| {
            std::env::var_os("HOME").map(|h| std::path::PathBuf::from(h).join(".local/share"))
        })
        .ok_or_else(|| "no data dir".to_string())?;
    #[cfg(target_os = "macos")]
    let base = std::env::var_os("HOME")
        .map(|h| std::path::PathBuf::from(h).join("Library/Application Support"))
        .ok_or_else(|| "no data dir".to_string())?;
    #[cfg(target_os = "windows")]
    let base = std::env::var_os("APPDATA")
        .map(std::path::PathBuf::from)
        .ok_or_else(|| "no data dir".to_string())?;
    Ok(base.join("votetracker"))
}
