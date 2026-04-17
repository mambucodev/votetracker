//! Vote-scoped undo/redo.
//!
//! Port of `legacy-python/src/votetracker/undo.py`. The manager is a pure
//! in-memory struct — the actual DB mutations happen in the command layer,
//! which wraps each mutation with `record_add / record_edit / record_delete`.
//! The frontend receives an `undo-state` event on every change so it can
//! toggle menu items + button enabled state.

use crate::domain::types::Vote;

pub const MAX_HISTORY: usize = 50;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UndoKind {
    Add,
    Edit,
    Delete,
}

#[derive(Debug, Clone)]
pub struct UndoAction {
    pub kind: UndoKind,
    /// Current vote id (may change after a DELETE-undo which re-adds the row
    /// and gets a new primary key).
    pub vote_id: Option<i64>,
    pub vote_data: Vote,
    /// Only populated for EDIT — the pre-change state to restore on undo.
    pub previous_data: Option<Vote>,
}

#[derive(Debug, Default)]
pub struct UndoManager {
    undo: Vec<UndoAction>,
    redo: Vec<UndoAction>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct UndoState {
    pub can_undo: bool,
    pub can_redo: bool,
    pub undo_text: Option<String>,
    pub redo_text: Option<String>,
}

impl UndoManager {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn state(&self) -> UndoState {
        UndoState {
            can_undo: !self.undo.is_empty(),
            can_redo: !self.redo.is_empty(),
            undo_text: self.undo.last().map(|a| text(a, "Undo")),
            redo_text: self.redo.last().map(|a| text(a, "Redo")),
        }
    }

    pub fn record_add(&mut self, vote_id: i64, vote_data: Vote) {
        self.push(UndoAction {
            kind: UndoKind::Add,
            vote_id: Some(vote_id),
            vote_data,
            previous_data: None,
        });
    }

    pub fn record_edit(&mut self, vote_id: i64, previous: Vote, new: Vote) {
        self.push(UndoAction {
            kind: UndoKind::Edit,
            vote_id: Some(vote_id),
            vote_data: new,
            previous_data: Some(previous),
        });
    }

    pub fn record_delete(&mut self, vote_id: i64, vote_data: Vote) {
        self.push(UndoAction {
            kind: UndoKind::Delete,
            vote_id: Some(vote_id),
            vote_data,
            previous_data: None,
        });
    }

    /// Pop a recorded action for the caller to invert against the DB.
    /// The caller is expected to call `commit_undone` with the inverted
    /// action once it has been applied (so it can be redone).
    pub fn take_undo(&mut self) -> Option<UndoAction> {
        self.undo.pop()
    }

    pub fn commit_undone(&mut self, action: UndoAction) {
        self.redo.push(action);
    }

    pub fn take_redo(&mut self) -> Option<UndoAction> {
        self.redo.pop()
    }

    pub fn commit_redone(&mut self, action: UndoAction) {
        self.undo.push(action);
    }

    pub fn clear(&mut self) {
        self.undo.clear();
        self.redo.clear();
    }

    // ---------- private ----------

    fn push(&mut self, action: UndoAction) {
        self.undo.push(action);
        if self.undo.len() > MAX_HISTORY {
            self.undo.remove(0); // FIFO drop the oldest
        }
        self.redo.clear();
    }
}

fn text(action: &UndoAction, prefix: &str) -> String {
    let verb = match action.kind {
        UndoKind::Add => "add",
        UndoKind::Edit => "edit",
        UndoKind::Delete => "delete",
    };
    format!("{prefix} {verb} {}", action.vote_data.subject)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::types::GradeType;

    fn v(id: Option<i64>, grade: f64) -> Vote {
        Vote {
            id,
            subject: "Math".into(),
            grade,
            kind: GradeType::Written,
            term: 1,
            date: "2026-01-01".into(),
            description: None,
            weight: 1.0,
            school_year_id: None,
        }
    }

    #[test]
    fn push_is_fifo_capped_at_fifty() {
        let mut m = UndoManager::new();
        for i in 0..60 {
            m.record_add(i, v(Some(i), 6.0));
        }
        assert_eq!(m.undo.len(), MAX_HISTORY);
        // Oldest (id=0..9) evicted; latest on top.
        assert_eq!(m.undo.first().unwrap().vote_id, Some(10));
        assert_eq!(m.undo.last().unwrap().vote_id, Some(59));
    }

    #[test]
    fn new_action_clears_redo() {
        let mut m = UndoManager::new();
        m.record_add(1, v(Some(1), 6.0));
        let a = m.take_undo().unwrap();
        m.commit_undone(a);
        assert!(m.state().can_redo);

        m.record_add(2, v(Some(2), 7.0));
        assert!(!m.state().can_redo);
    }

    #[test]
    fn text_lines_match_python_app() {
        let mut m = UndoManager::new();
        m.record_add(1, v(Some(1), 6.0));
        let state = m.state();
        assert_eq!(state.undo_text.as_deref(), Some("Undo add Math"));
    }

    #[test]
    fn edit_records_previous_and_new() {
        let mut m = UndoManager::new();
        m.record_edit(42, v(Some(42), 5.0), v(Some(42), 8.0));
        let action = m.undo.last().unwrap();
        assert_eq!(action.kind, UndoKind::Edit);
        assert_eq!(action.previous_data.as_ref().unwrap().grade, 5.0);
        assert_eq!(action.vote_data.grade, 8.0);
    }
}
