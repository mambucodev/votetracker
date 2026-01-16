"""
Undo/Redo manager for VoteTracker.
Tracks vote operations and allows undoing/redoing them.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

from PySide6.QtCore import QObject, Signal


class ActionType(Enum):
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"


@dataclass
class UndoAction:
    """Represents an undoable action."""
    action_type: ActionType
    vote_id: Optional[int]  # None for ADD before execution
    vote_data: Dict[str, Any]  # The vote data
    previous_data: Optional[Dict[str, Any]] = None  # For EDIT: previous state


class UndoManager(QObject):
    """Manages undo/redo stacks for vote operations."""

    state_changed = Signal()  # Emitted when undo/redo availability changes

    def __init__(self, db, max_history: int = 50):
        super().__init__()
        self._db = db
        self._undo_stack: List[UndoAction] = []
        self._redo_stack: List[UndoAction] = []
        self._max_history = max_history

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def get_undo_text(self) -> str:
        if not self._undo_stack:
            return "Undo"
        action = self._undo_stack[-1]
        return f"Undo {action.action_type.value} {action.vote_data.get('subject', '')}"

    def get_redo_text(self) -> str:
        if not self._redo_stack:
            return "Redo"
        action = self._redo_stack[-1]
        return f"Redo {action.action_type.value} {action.vote_data.get('subject', '')}"

    def record_add(self, vote_id: int, vote_data: Dict[str, Any]):
        """Record an add operation."""
        action = UndoAction(
            action_type=ActionType.ADD,
            vote_id=vote_id,
            vote_data=vote_data.copy()
        )
        self._push_undo(action)

    def record_edit(self, vote_id: int, previous_data: Dict[str, Any], new_data: Dict[str, Any]):
        """Record an edit operation."""
        action = UndoAction(
            action_type=ActionType.EDIT,
            vote_id=vote_id,
            vote_data=new_data.copy(),
            previous_data=previous_data.copy()
        )
        self._push_undo(action)

    def record_delete(self, vote_id: int, vote_data: Dict[str, Any]):
        """Record a delete operation."""
        action = UndoAction(
            action_type=ActionType.DELETE,
            vote_id=vote_id,
            vote_data=vote_data.copy()
        )
        self._push_undo(action)

    def _push_undo(self, action: UndoAction):
        """Push action to undo stack and clear redo stack."""
        self._undo_stack.append(action)
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self.state_changed.emit()

    def undo(self) -> bool:
        """Undo the last action. Returns True if successful."""
        if not self._undo_stack:
            return False

        action = self._undo_stack.pop()

        if action.action_type == ActionType.ADD:
            # Undo add = delete
            self._db.delete_vote(action.vote_id)

        elif action.action_type == ActionType.EDIT:
            # Undo edit = restore previous data
            prev = action.previous_data
            self._db.update_vote(
                action.vote_id,
                prev["subject"], prev["grade"], prev["type"],
                prev["date"], prev["description"],
                prev["term"], prev.get("weight", 1.0)
            )

        elif action.action_type == ActionType.DELETE:
            # Undo delete = re-add
            data = action.vote_data
            self._db.add_vote(
                data["subject"], data["grade"], data["type"],
                data["date"], data["description"],
                term=data["term"], weight=data.get("weight", 1.0)
            )
            # Note: vote gets a new ID, update action for redo
            votes = self._db.get_votes(subject=data["subject"])
            if votes:
                # Find the vote we just added (most recent with matching data)
                for v in votes:
                    if (v["grade"] == data["grade"] and
                        v["date"] == data["date"] and
                        v["type"] == data["type"]):
                        action.vote_id = v["id"]
                        break

        self._redo_stack.append(action)
        self.state_changed.emit()
        return True

    def redo(self) -> bool:
        """Redo the last undone action. Returns True if successful."""
        if not self._redo_stack:
            return False

        action = self._redo_stack.pop()

        if action.action_type == ActionType.ADD:
            # Redo add = add again
            data = action.vote_data
            self._db.add_vote(
                data["subject"], data["grade"], data["type"],
                data["date"], data["description"],
                term=data["term"], weight=data.get("weight", 1.0)
            )
            # Update action with new ID
            votes = self._db.get_votes(subject=data["subject"])
            if votes:
                for v in votes:
                    if (v["grade"] == data["grade"] and
                        v["date"] == data["date"] and
                        v["type"] == data["type"]):
                        action.vote_id = v["id"]
                        break

        elif action.action_type == ActionType.EDIT:
            # Redo edit = apply new data
            data = action.vote_data
            self._db.update_vote(
                action.vote_id,
                data["subject"], data["grade"], data["type"],
                data["date"], data["description"],
                data["term"], data.get("weight", 1.0)
            )

        elif action.action_type == ActionType.DELETE:
            # Redo delete = delete again
            self._db.delete_vote(action.vote_id)

        self._undo_stack.append(action)
        self.state_changed.emit()
        return True

    def clear(self):
        """Clear all undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.state_changed.emit()
