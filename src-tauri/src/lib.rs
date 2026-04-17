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
//!
//! Each module has unit tests that pin behavior to `docs/REWRITE_SPEC.md`.

pub mod db;
pub mod domain;
pub mod events;
pub mod i18n;
pub mod undo;

// Scaffolds — implementations land in later milestones (M4–M7).
pub mod commands;
pub mod menu;
pub mod pdf;
pub mod sync;

use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,votetracker_lib=debug".into()),
        )
        .init();

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![commands::ping])
        .setup(|app| {
            tracing::info!("VoteTracker starting up");

            // Eagerly open the DB to trigger migrations at launch.
            if let Err(e) = db::Database::open_default() {
                tracing::error!("failed to open database: {e:?}");
            }

            // Surface window once the frontend is ready.
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
