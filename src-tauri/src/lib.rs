//! VoteTracker — Tauri backend library.
//!
//! Public modules are thin vertical slices that together make up the app:
//!   • `db`      — SQLite schema, migrations, seeds, CRUD.
//!   • `domain`  — pure business logic (averages, rounding, simulator, matching).
//!   • `undo`    — vote-scoped undo/redo stack (50-entry cap).
//!   • `sync`    — SyncProvider trait + ClasseViva / Axios implementations + import engine.
//!   • `pdf`     — report-card PDF export.
//!   • `commands`— `#[tauri::command]` bindings exposed to the React frontend.
//!   • `menu`    — native menubar (Ctrl+1-8, Undo/Redo, Sync Now, theme toggle).
//!   • `events`  — typed event payloads emitted to the frontend.
//!   • `i18n`    — en/it translation tables.

pub mod commands;
pub mod db;
pub mod domain;
pub mod events;
pub mod i18n;
pub mod menu;
pub mod pdf;
pub mod sync;
pub mod undo;

use commands::AppState;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,votetracker_lib=debug".into()),
        )
        .init();

    let db = db::Database::open_default().expect("failed to open database");
    let app_state = AppState::new(db);

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_shell::init())
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            commands::ping,
            // votes
            commands::list_votes,
            commands::get_vote,
            commands::add_vote,
            commands::update_vote,
            commands::delete_vote,
            // subjects
            commands::list_subjects,
            commands::add_subject,
            commands::rename_subject,
            commands::delete_subject,
            // school years
            commands::list_years,
            commands::active_year,
            commands::add_year,
            commands::set_active_year,
            commands::delete_year,
            // settings
            commands::get_setting,
            commands::set_setting,
            commands::get_current_term,
            commands::set_current_term,
            // domain
            commands::calculate_needed_grade,
            commands::subject_mapping_suggestion,
            // undo / redo
            commands::undo_state,
            commands::undo,
            commands::redo,
        ])
        .setup(|app| {
            tracing::info!("VoteTracker starting up");
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
