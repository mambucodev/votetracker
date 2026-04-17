//! VoteTracker — Tauri backend library.

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
            // providers / sync / import
            commands::list_providers,
            commands::import_votes_json,
            commands::trigger_sync_now,
            // pdf
            commands::export_report_card_pdf,
            // misc
            commands::open_data_dir,
        ])
        .setup(|app| {
            tracing::info!("VoteTracker starting up");

            // Native menu.
            match menu::build(app.handle()) {
                Ok(m) => {
                    if let Err(e) = app.set_menu(m) {
                        tracing::warn!("failed to set menu: {e}");
                    }
                    menu::bind(app.handle());
                }
                Err(e) => tracing::warn!("failed to build menu: {e}"),
            }

            // Startup auto-sync — one Tokio task per enabled provider.
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = startup_auto_sync(&app_handle).await {
                    tracing::warn!("startup auto-sync failed: {e}");
                }
            });

            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

async fn startup_auto_sync<R: tauri::Runtime>(app: &tauri::AppHandle<R>) -> anyhow::Result<()> {
    use tauri::Manager;
    let state = app.state::<AppState>();

    // Small delay so the window renders before we start network work.
    tokio::time::sleep(std::time::Duration::from_millis(1500)).await;

    for &provider_id in sync::all_provider_ids() {
        let auto = {
            let conn = state.db.pool().get()?;
            db::settings::auto_sync_enabled(&conn, provider_id)?
        };
        if !auto {
            continue;
        }

        let app_h = app.clone();
        let pid = provider_id.to_string();
        tauri::async_runtime::spawn(async move {
            tracing::info!(provider = %pid, "startup auto-sync");
            let state = app_h.state::<AppState>();
            match run_one_sync(&app_h, &state.db, &pid).await {
                Ok(()) => tracing::info!(provider = %pid, "auto-sync ok"),
                Err(e) => tracing::warn!(provider = %pid, "auto-sync failed: {e}"),
            }
        });

        // Kick off a periodic sync task for this provider too.
        let app_h = app.clone();
        let pid = provider_id.to_string();
        tauri::async_runtime::spawn(async move {
            loop {
                let interval = {
                    let state = app_h.state::<AppState>();
                    let conn = match state.db.pool().get() {
                        Ok(c) => c,
                        Err(_) => break,
                    };
                    db::settings::sync_interval_minutes(&conn, &pid)
                        .unwrap_or(60)
                        .max(5)
                };
                tokio::time::sleep(std::time::Duration::from_secs(interval as u64 * 60)).await;

                // Bail out if auto-sync was disabled mid-flight.
                let still_on = {
                    let state = app_h.state::<AppState>();
                    let conn = match state.db.pool().get() {
                        Ok(c) => c,
                        Err(_) => continue,
                    };
                    db::settings::auto_sync_enabled(&conn, &pid).unwrap_or(false)
                };
                if !still_on {
                    break;
                }

                let state = app_h.state::<AppState>();
                if let Err(e) = run_one_sync(&app_h, &state.db, &pid).await {
                    tracing::warn!(provider = %pid, "interval sync failed: {e}");
                }
            }
        });
    }

    Ok(())
}

async fn run_one_sync<R: tauri::Runtime>(
    app: &tauri::AppHandle<R>,
    db: &db::Database,
    provider_id: &str,
) -> anyhow::Result<()> {
    use tauri::Emitter;

    let _ = app.emit(
        events::SYNC_STATUS,
        events::SyncStatusPayload::Started {
            provider_id: provider_id.to_string(),
        },
    );

    let mut provider = sync::provider_by_id(provider_id)
        .ok_or_else(|| anyhow::anyhow!("unknown provider {provider_id}"))?;

    let creds = {
        let conn = db.pool().get()?;
        let mut map = std::collections::HashMap::new();
        for f in provider.credential_fields() {
            if let Some(v) = db::settings::get_credential(&conn, provider_id, &f.name)? {
                map.insert(f.name, v);
            }
        }
        map
    };

    provider
        .login(&creds)
        .await
        .map_err(|e| anyhow::anyhow!("login: {e}"))?;
    let grades = provider
        .fetch_grades()
        .await
        .map_err(|e| anyhow::anyhow!("fetch: {e}"))?;
    let year_id = {
        let conn = db.pool().get()?;
        db::school_years::active(&conn)?.map(|y| y.id)
    };
    let summary = sync::import::import_all(db, provider_id, &grades, year_id)?;

    {
        let conn = db.pool().get()?;
        db::settings::set_last_sync(&conn, provider_id, &chrono::Local::now().to_rfc3339())?;
    }

    let _ = app.emit(
        events::SYNC_STATUS,
        events::SyncStatusPayload::Done {
            provider_id: provider_id.to_string(),
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
    let _ = app.emit(events::DATA_CHANGED, ());
    Ok(())
}
