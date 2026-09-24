"""
Unit tests for UndoManager.
"""
from __future__ import annotations

import unittest
import tempfile
import os
from src.votetracker.database import Database

try:
    from src.votetracker.undo import UndoManager
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 not available")
class TestUndoManager(unittest.TestCase):
    """Test suite for UndoManager."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = Database(db_path=self.temp_db.name)
        self.undo = UndoManager(self.db, max_history=5)
        self.active_year = self.db.get_active_school_year()
        assert self.active_year is not None
        self.year_id = self.active_year["id"]
        self.db.add_subject("History")

    def tearDown(self):
        self.db.close()
        os.unlink(self.temp_db.name)

    def test_undo_add(self):
        """Test undoing and redoing an added vote."""
        data = {
            "subject": "History",
            "grade": 8.0,
            "type": "Written",
            "date": "2024-02-01",
            "description": "Essay",
            "term": 1,
            "weight": 1.0,
            "school_year_id": self.year_id,
        }
        vote_id = self.db.add_vote(
            data["subject"], data["grade"], data["type"],
            data["date"], data["description"],
            term=data["term"], weight=data["weight"],
            school_year_id=data["school_year_id"]
        )
        assert vote_id is not None
        self.undo.record_add(vote_id, data)

        self.assertTrue(self.undo.can_undo())
        self.assertFalse(self.undo.can_redo())

        # Undo add -> vote should be deleted
        success = self.undo.undo()
        self.assertTrue(success)
        self.assertIsNone(self.db.get_vote(vote_id))
        self.assertTrue(self.undo.can_redo())

        # Redo add -> vote should exist again
        success = self.undo.redo()
        self.assertTrue(success)
        votes = self.db.get_votes("History", self.year_id, 1)
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["grade"], 8.0)

    def test_undo_edit(self):
        """Test undoing and redoing an edited vote."""
        vote_id = self.db.add_vote(
            "History", 7.0, "Oral", "2024-02-01", "Old desc",
            term=1, weight=1.0, school_year_id=self.year_id
        )
        assert vote_id is not None
        prev_data = self.db.get_vote(vote_id)
        assert prev_data is not None

        new_data = {
            "subject": "History",
            "grade": 9.0,
            "type": "Oral",
            "date": "2024-02-01",
            "description": "New desc",
            "term": 1,
            "weight": 1.0,
        }
        self.db.update_vote(
            vote_id, new_data["subject"], new_data["grade"], new_data["type"],
            new_data["date"], new_data["description"],
            new_data["term"], new_data["weight"]
        )
        self.undo.record_edit(vote_id, prev_data, new_data)

        # Undo edit -> should revert to 7.0
        self.undo.undo()
        updated = self.db.get_vote(vote_id)
        assert updated is not None
        self.assertEqual(updated["grade"], 7.0)
        self.assertEqual(updated["description"], "Old desc")

        # Redo edit -> should reapply 9.0
        self.undo.redo()
        updated = self.db.get_vote(vote_id)
        assert updated is not None
        self.assertEqual(updated["grade"], 9.0)
        self.assertEqual(updated["description"], "New desc")

    def test_undo_delete_preserves_school_year(self):
        """Test undoing a deletion preserves the original school_year_id."""
        vote_id = self.db.add_vote(
            "History", 6.5, "Written", "2024-02-01", "Pop quiz",
            term=1, weight=1.0, school_year_id=self.year_id
        )
        assert vote_id is not None
        vote_data = self.db.get_vote(vote_id)
        assert vote_data is not None
        self.assertEqual(vote_data["school_year_id"], self.year_id)

        self.db.delete_vote(vote_id)
        self.undo.record_delete(vote_id, vote_data)

        # Undo delete
        self.undo.undo()
        votes = self.db.get_votes("History", school_year_id=self.year_id, term=1)
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["grade"], 6.5)
        self.assertEqual(votes[0]["school_year_id"], self.year_id)

    def test_history_cap(self):
        """Test that history doesn't grow past max_history."""
        for i in range(10):
            self.undo.record_add(i, {"subject": "History", "grade": float(i)})

        self.assertEqual(len(self.undo._undo_stack), 5)


if __name__ == '__main__':
    unittest.main()
