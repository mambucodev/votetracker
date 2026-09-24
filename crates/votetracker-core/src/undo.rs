use crate::db::{Database, DbError};
use crate::models::Vote;

#[derive(Debug, Clone, PartialEq)]
pub enum UndoAction {
    Add {
        vote_id: i64,
        data: Vote,
    },
    Edit {
        vote_id: i64,
        previous_data: Vote,
        new_data: Vote,
    },
    Delete {
        vote_id: i64,
        data: Vote,
    },
}

#[derive(Default)]
pub struct UndoManager {
    undo_stack: Vec<UndoAction>,
    redo_stack: Vec<UndoAction>,
}

impl UndoManager {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn can_undo(&self) -> bool {
        !self.undo_stack.is_empty()
    }

    pub fn can_redo(&self) -> bool {
        !self.redo_stack.is_empty()
    }

    pub fn record_add(&mut self, vote: Vote) {
        self.undo_stack.push(UndoAction::Add {
            vote_id: vote.id,
            data: vote,
        });
        self.redo_stack.clear();
    }

    pub fn record_edit(&mut self, previous_data: Vote, new_data: Vote) {
        self.undo_stack.push(UndoAction::Edit {
            vote_id: previous_data.id,
            previous_data,
            new_data,
        });
        self.redo_stack.clear();
    }

    pub fn record_delete(&mut self, vote: Vote) {
        self.undo_stack.push(UndoAction::Delete {
            vote_id: vote.id,
            data: vote,
        });
        self.redo_stack.clear();
    }

    pub fn undo(&mut self, db: &mut Database) -> Result<Option<UndoAction>, DbError> {
        let action = match self.undo_stack.pop() {
            Some(a) => a,
            None => return Ok(None),
        };

        match &action {
            UndoAction::Add { vote_id, .. } => {
                db.delete_vote(*vote_id)?;
            }
            UndoAction::Edit { previous_data, .. } => {
                db.update_vote(previous_data)?;
            }
            UndoAction::Delete { data, .. } => {
                db.restore_vote(data)?;
            }
        }

        self.redo_stack.push(action.clone());
        Ok(Some(action))
    }

    pub fn redo(&mut self, db: &mut Database) -> Result<Option<UndoAction>, DbError> {
        let action = match self.redo_stack.pop() {
            Some(a) => a,
            None => return Ok(None),
        };

        match &action {
            UndoAction::Add { data, .. } => {
                db.restore_vote(data)?;
            }
            UndoAction::Edit { new_data, .. } => {
                db.update_vote(new_data)?;
            }
            UndoAction::Delete { vote_id, .. } => {
                db.delete_vote(*vote_id)?;
            }
        }

        self.undo_stack.push(action.clone());
        Ok(Some(action))
    }

    pub fn clear(&mut self) {
        self.undo_stack.clear();
        self.redo_stack.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::NewVote;

    fn sample_vote(id: i64, grade: f64) -> Vote {
        Vote {
            id,
            subject_id: 1,
            grade,
            weight: 1.0,
            vote_date: "2026-03-01".to_string(),
            term: 2,
            notes: "Test".to_string(),
            vote_type: "Scritto".to_string(),
            created_at: None,
            school_year_id: 1,
        }
    }

    #[test]
    fn test_undo_redo_add() {
        let mut db = Database::new::<&str>(None).unwrap();
        let mut undo_mgr = UndoManager::new();

        let new_vote = NewVote {
            subject_id: 1,
            grade: 9.0,
            weight: 1.0,
            vote_date: "2026-03-01".to_string(),
            term: 2,
            notes: "".to_string(),
            vote_type: "Scritto".to_string(),
            school_year_id: 1,
        };

        let id = db.add_vote(&new_vote).unwrap();
        let vote = db.get_vote_by_id(id).unwrap().unwrap();
        undo_mgr.record_add(vote.clone());

        assert!(undo_mgr.can_undo());
        assert!(!undo_mgr.can_redo());

        // Undo: should delete
        undo_mgr.undo(&mut db).unwrap();
        assert!(db.get_vote_by_id(id).unwrap().is_none());
        assert!(undo_mgr.can_redo());

        // Redo: should re-insert
        undo_mgr.redo(&mut db).unwrap();
        assert!(db.get_vote_by_id(id).unwrap().is_some());
    }

    #[test]
    fn test_undo_redo_delete() {
        let mut db = Database::new::<&str>(None).unwrap();
        let mut undo_mgr = UndoManager::new();

        let new_vote = NewVote {
            subject_id: 1,
            grade: 8.0,
            weight: 1.0,
            vote_date: "2026-03-01".to_string(),
            term: 2,
            notes: "".to_string(),
            vote_type: "Orale".to_string(),
            school_year_id: 1,
        };

        let id = db.add_vote(&new_vote).unwrap();
        let vote = db.get_vote_by_id(id).unwrap().unwrap();

        db.delete_vote(id).unwrap();
        undo_mgr.record_delete(vote.clone());

        // Undo delete: restores vote
        undo_mgr.undo(&mut db).unwrap();
        let restored = db.get_vote_by_id(id).unwrap();
        assert!(restored.is_some());
        assert_eq!(restored.unwrap().grade, 8.0);

        // Redo delete: re-deletes vote
        undo_mgr.redo(&mut db).unwrap();
        assert!(db.get_vote_by_id(id).unwrap().is_none());
    }

    #[test]
    fn test_undo_redo_edit() {
        let mut db = Database::new::<&str>(None).unwrap();
        let mut undo_mgr = UndoManager::new();

        let initial_vote = sample_vote(1, 6.0);
        db.restore_vote(&initial_vote).unwrap();

        let mut edited_vote = initial_vote.clone();
        edited_vote.grade = 7.5;
        db.update_vote(&edited_vote).unwrap();

        undo_mgr.record_edit(initial_vote.clone(), edited_vote.clone());

        // Undo edit: reverts to 6.0
        undo_mgr.undo(&mut db).unwrap();
        let current = db.get_vote_by_id(1).unwrap().unwrap();
        assert_eq!(current.grade, 6.0);

        // Redo edit: reapplies 7.5
        undo_mgr.redo(&mut db).unwrap();
        let current_redo = db.get_vote_by_id(1).unwrap().unwrap();
        assert_eq!(current_redo.grade, 7.5);
    }
}
