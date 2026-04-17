//! `#[tauri::command]` IPC surface. Today only a liveness probe; CRUD,
//! provider, and theme commands land in M3–M7.

#[tauri::command]
pub fn ping() -> &'static str {
    "pong"
}
