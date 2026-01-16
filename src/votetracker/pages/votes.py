"""
Votes page for VoteTracker.
Shows vote list with filtering and CRUD operations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QAbstractItemView, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from ..database import Database
from ..undo import UndoManager
from ..utils import get_symbolic_icon, get_status_color, StatusColors
from ..widgets import TermToggle
from ..dialogs import AddVoteDialog
from ..i18n import tr


class VotesPage(QWidget):
    """Votes list page with CRUD operations."""

    vote_changed = Signal()

    def __init__(self, db: Database, undo_manager: UndoManager = None, parent=None):
        super().__init__(parent)
        self._db = db
        self._undo_manager = undo_manager
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        self._title = QLabel(tr("Votes List"))
        self._title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(self._title)
        header.addStretch()

        # Term toggle
        self._term_toggle = TermToggle(self._db.get_current_term())
        self._term_toggle.term_changed.connect(self._on_term_changed)
        header.addWidget(self._term_toggle)

        header.addSpacing(16)

        self._add_btn = QPushButton(tr("Add Vote"))
        self._add_btn.setIcon(get_symbolic_icon("list-add"))
        self._add_btn.clicked.connect(self._add_vote)
        header.addWidget(self._add_btn)

        layout.addLayout(header)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        self._filter_label = QLabel(tr("Filter:"))
        filter_layout.addWidget(self._filter_label)
        self._filter_combo = QComboBox()
        self._filter_combo.setMinimumWidth(150)
        self._filter_combo.addItem(tr("All"))
        self._filter_combo.currentTextChanged.connect(self.refresh)
        filter_layout.addWidget(self._filter_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table container
        self._table_container = QWidget()
        table_layout = QVBoxLayout(self._table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            tr("Date"), tr("Subject"), tr("Description"), tr("Term"), tr("Type"), tr("Grade"), "ID"
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setColumnHidden(6, True)  # Hide ID column
        self._table.doubleClicked.connect(self._edit_vote)
        table_layout.addWidget(self._table)
        
        # Placeholder
        self._placeholder = QLabel(tr("No votes recorded yet"))
        self._placeholder.setStyleSheet("color: gray; font-weight: bold;")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.hide()
        table_layout.addWidget(self._placeholder)

        layout.addWidget(self._table_container, 1)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self._edit_btn = QPushButton(tr("Edit"))
        self._edit_btn.setIcon(get_symbolic_icon("document-edit"))
        self._edit_btn.clicked.connect(self._edit_vote)

        self._delete_btn = QPushButton(tr("Delete"))
        self._delete_btn.setIcon(get_symbolic_icon("edit-delete"))
        self._delete_btn.clicked.connect(self._delete_vote)

        action_layout.addWidget(self._edit_btn)
        action_layout.addWidget(self._delete_btn)
        action_layout.addStretch()

        layout.addLayout(action_layout)
    
    def _on_term_changed(self, term: int):
        """Handle term toggle change."""
        self._db.set_current_term(term)
        self.refresh()
    
    def get_current_term(self) -> int:
        """Get currently selected term."""
        return self._term_toggle.get_term()
    
    def refresh(self):
        """Refresh the votes list."""
        # Update labels for language changes
        self._title.setText(tr("Votes List"))
        self._add_btn.setText(tr("Add Vote"))
        self._filter_label.setText(tr("Filter:"))
        self._edit_btn.setText(tr("Edit"))
        self._delete_btn.setText(tr("Delete"))
        self._placeholder.setText(tr("No votes recorded yet"))
        self._table.setHorizontalHeaderLabels([
            tr("Date"), tr("Subject"), tr("Description"), tr("Term"), tr("Type"), tr("Grade"), "ID"
        ])

        # Update add button state
        subjects = self._db.get_subjects()
        self._add_btn.setEnabled(len(subjects) > 0)
        self._add_btn.setToolTip("Create a subject first" if not subjects else "")
        
        # Update term toggle
        self._term_toggle.set_term(self._db.get_current_term())
        
        # Update filter combo
        current_filter = self._filter_combo.currentText()
        self._filter_combo.blockSignals(True)
        self._filter_combo.clear()
        self._filter_combo.addItem("All")
        for subject in subjects:
            self._filter_combo.addItem(subject)
        idx = self._filter_combo.findText(current_filter)
        if idx >= 0:
            self._filter_combo.setCurrentIndex(idx)
        self._filter_combo.blockSignals(False)
        
        # Get votes
        filter_subject = self._filter_combo.currentText()
        current_term = self._term_toggle.get_term()
        
        if filter_subject == "All":
            votes = self._db.get_votes(term=current_term)
        else:
            votes = self._db.get_votes(subject=filter_subject, term=current_term)
        
        # Show/hide placeholder
        if not votes:
            self._table.hide()
            self._placeholder.show()
            return
        else:
            self._table.show()
            self._placeholder.hide()
        
        self._table.setRowCount(len(votes))
        
        for row, vote in enumerate(votes):
            # Date
            self._table.setItem(row, 0, QTableWidgetItem(vote.get("date", "")))
            
            # Subject
            self._table.setItem(row, 1, QTableWidgetItem(vote.get("subject", "")))
            
            # Description
            self._table.setItem(row, 2, QTableWidgetItem(vote.get("description", "")))
            
            # Term
            term = vote.get("term", 1)
            term_item = QTableWidgetItem(f"{term}°")
            term_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, term_item)
            
            # Type with color
            vote_type = vote.get("type", "Written")
            type_item = QTableWidgetItem(tr(vote_type))
            if vote_type == "Written":
                type_item.setForeground(StatusColors.WRITTEN)
            elif vote_type == "Oral":
                type_item.setForeground(StatusColors.ORAL)
            else:
                type_item.setForeground(StatusColors.PRACTICAL)
            self._table.setItem(row, 4, type_item)
            
            # Grade with color
            grade = vote.get("grade", 0)
            grade_item = QTableWidgetItem(f"{grade:.2f}")
            grade_item.setForeground(get_status_color(grade))
            grade_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 5, grade_item)
            
            # ID (hidden)
            self._table.setItem(row, 6, QTableWidgetItem(str(vote.get("id", 0))))
    
    def _add_vote(self):
        """Add a new vote."""
        current_term = self._term_toggle.get_term()
        dialog = AddVoteDialog(self._db, current_term=current_term, parent=self)

        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_vote_data()
            vote_id = self._db.add_vote(
                data["subject"], data["grade"], data["type"],
                data["date"], data["description"],
                term=data["term"], weight=data["weight"]
            )
            if self._undo_manager and vote_id:
                self._undo_manager.record_add(vote_id, data)
            self.vote_changed.emit()
    
    def _edit_vote(self):
        """Edit selected vote."""
        row = self._table.currentRow()
        if row < 0:
            return

        vote_id = int(self._table.item(row, 6).text())
        vote = self._db.get_vote(vote_id)

        if vote:
            previous_data = vote.copy()
            current_term = self._term_toggle.get_term()
            dialog = AddVoteDialog(
                self._db, vote, current_term=current_term, parent=self
            )

            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_vote_data()
                self._db.update_vote(
                    vote_id, data["subject"], data["grade"], data["type"],
                    data["date"], data["description"],
                    term=data["term"], weight=data["weight"]
                )
                if self._undo_manager:
                    self._undo_manager.record_edit(vote_id, previous_data, data)
                self.vote_changed.emit()
    
    def _delete_vote(self):
        """Delete selected vote."""
        row = self._table.currentRow()
        if row < 0:
            return

        reply = QMessageBox.question(
            self, tr("Confirm Deletion"),
            tr("Are you sure you want to delete this vote?"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            vote_id = int(self._table.item(row, 6).text())
            vote_data = self._db.get_vote(vote_id)
            self._db.delete_vote(vote_id)
            if self._undo_manager and vote_data:
                self._undo_manager.record_delete(vote_id, vote_data)
            self.vote_changed.emit()

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle keyboard shortcuts for this page. Returns True if handled."""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+N: Add new vote
        if modifiers == Qt.ControlModifier and key == Qt.Key_N:
            if self._add_btn.isEnabled():
                self._add_vote()
            return True

        # Delete: Delete selected vote
        if key == Qt.Key_Delete:
            if self._table.currentRow() >= 0:
                self._delete_vote()
            return True

        # Enter/Return: Edit selected vote
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self._table.currentRow() >= 0:
                self._edit_vote()
            return True

        # 1/2: Switch term
        if key == Qt.Key_1:
            self._term_toggle.set_term(1)
            self._on_term_changed(1)
            return True
        if key == Qt.Key_2:
            self._term_toggle.set_term(2)
            self._on_term_changed(2)
            return True

        return False
