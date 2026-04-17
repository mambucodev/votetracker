//! Typed Tauri event names + payload shapes.
//!
//! These mirror the signal names from the Python app (`data_changed`,
//! `data_imported`, `school_year_changed`) plus rewrite-only additions
//! (`undo-state`, `sync-status`, `theme-changed`).

use serde::Serialize;

pub const DATA_CHANGED: &str = "data-changed";
pub const DATA_IMPORTED: &str = "data-imported";
pub const SCHOOL_YEAR_CHANGED: &str = "school-year-changed";
pub const UNDO_STATE: &str = "undo-state";
pub const SYNC_STATUS: &str = "sync-status";
pub const THEME_CHANGED: &str = "theme-changed";

#[derive(Debug, Clone, Serialize)]
pub struct UndoStatePayload {
    pub can_undo: bool,
    pub can_redo: bool,
    pub undo_text: Option<String>,
    pub redo_text: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum SyncStatusPayload {
    Started {
        provider_id: String,
    },
    Progress {
        provider_id: String,
        message: String,
    },
    Done {
        provider_id: String,
        new_count: u32,
        updated_count: u32,
        skipped_count: u32,
    },
    Failed {
        provider_id: String,
        message: String,
    },
}
