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
from PySide6.QtGui import QColor

from ..database import Database
from ..utils import get_symbolic_icon, has_icon, get_icon_fallback, get_status_color, StatusColors
from ..widgets import TermToggle
from ..dialogs import AddVoteDialog


class VotesPage(QWidget):
    """Votes list page with CRUD operations."""
    
    vote_changed = Signal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Votes List")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        # Term toggle
        self._term_toggle = TermToggle(self._db.get_current_term())
        self._term_toggle.term_changed.connect(self._on_term_changed)
        header.addWidget(self._term_toggle)
        
        header.addSpacing(16)
        
        self._add_btn = QPushButton("Add Vote")
        self._add_btn.setIcon(get_symbolic_icon("list-add"))
        self._add_btn.clicked.connect(self._add_vote)
        header.addWidget(self._add_btn)
        
        layout.addLayout(header)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        filter_layout.addWidget(QLabel("Filter:"))
        self._filter_combo = QComboBox()
        self._filter_combo.setMinimumWidth(150)
        self._filter_combo.addItem("All")
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
            "Date", "Subject", "Description", "Term", "Type", "Grade", "ID"
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
        self._placeholder = QLabel("No votes recorded yet")
        self._placeholder.setStyleSheet("color: gray; font-weight: bold;")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.hide()
        table_layout.addWidget(self._placeholder)
        
        layout.addWidget(self._table_container, 1)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(get_symbolic_icon("document-edit"))
        edit_btn.clicked.connect(self._edit_vote)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(get_symbolic_icon("edit-delete"))
        delete_btn.clicked.connect(self._delete_vote)
        
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
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
            type_item = QTableWidgetItem(vote_type)
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
            self._db.add_vote(
                data["subject"], data["grade"], data["type"],
                data["date"], data["description"],
                term=data["term"], weight=data["weight"]
            )
            self.vote_changed.emit()
    
    def _edit_vote(self):
        """Edit selected vote."""
        row = self._table.currentRow()
        if row < 0:
            return
        
        vote_id = int(self._table.item(row, 6).text())
        votes = self._db.get_votes()
        vote = next((v for v in votes if v.get("id") == vote_id), None)
        
        if vote:
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
                self.vote_changed.emit()
    
    def _delete_vote(self):
        """Delete selected vote."""
        row = self._table.currentRow()
        if row < 0:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this vote?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            vote_id = int(self._table.item(row, 6).text())
            self._db.delete_vote(vote_id)
            self.vote_changed.emit()
