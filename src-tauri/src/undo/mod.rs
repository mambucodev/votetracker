//! Vote-scoped undo/redo. Full behavior ports in M3; today this module
//! exposes the 50-entry cap + `UndoKind` enum so the rest of the crate
//! can depend on the eventual surface area.

pub const MAX_HISTORY: usize = 50;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UndoKind {
    Add,
    Edit,
    Delete,
}
