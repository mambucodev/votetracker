"""
Subjects page for VoteTracker.
Shows all subjects with stats and management options.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from ..database import Database
from ..utils import calc_average, round_report_card, get_symbolic_icon, has_icon, get_icon_fallback
from ..widgets import SubjectCard
from ..dialogs import AddSubjectDialog, EditSubjectDialog


class SubjectsPage(QWidget):
    """Subjects management page."""
    
    subject_changed = Signal()
    
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
        title = QLabel("Subjects")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        add_btn = QPushButton("New Subject")
        add_btn.setIcon(get_symbolic_icon("list-add"))
        add_btn.clicked.connect(self._add_subject)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Content
        self._content_widget = QWidget()
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Grid in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        self._grid = QGridLayout(scroll_widget)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(12)
        self._grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        content_layout.addWidget(scroll)
        
        # Placeholder
        self._placeholder = QLabel("No subjects yet")
        self._placeholder.setStyleSheet("color: gray; font-weight: bold;")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.hide()
        content_layout.addWidget(self._placeholder)
        
        layout.addWidget(self._content_widget, 1)
    
    def refresh(self):
        """Refresh subjects list."""
        # Clear grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        subjects = self._db.get_subjects()
        
        if not subjects:
            self._placeholder.show()
            return
        else:
            self._placeholder.hide()
        
        col = 0
        row = 0
        for subject in sorted(subjects):
            card = self._create_subject_card(subject)
            self._grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
    
    def _create_subject_card(self, subject: str) -> SubjectCard:
        """Create a subject card widget."""
        votes = self._db.get_votes(subject)
        avg = calc_average(votes)
        written_votes = [v for v in votes if v.get("type") == "Written"]
        oral_votes = [v for v in votes if v.get("type") == "Oral"]
        written_avg = calc_average(written_votes)
        oral_avg = calc_average(oral_votes)
        report_grade = round_report_card(avg) if votes else 0
        
        card = SubjectCard(
            subject, avg, written_avg, oral_avg, len(votes), report_grade
        )
        card.edit_requested.connect(self._edit_subject)
        return card
    
    def _add_subject(self):
        """Add a new subject."""
        dialog = AddSubjectDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            if name:
                if self._db.add_subject(name):
                    self.subject_changed.emit()
                else:
                    QMessageBox.warning(
                        self, "Error", "Subject already exists."
                    )
    
    def _edit_subject(self, subject_name: str):
        """Edit or delete a subject."""
        votes = self._db.get_votes(subject_name)
        dialog = EditSubjectDialog(subject_name, len(votes), self)

        if dialog.exec() == QDialog.Accepted:
            if dialog.action == "rename":
                if self._db.rename_subject(subject_name, dialog.new_name):
                    self.subject_changed.emit()
                else:
                    QMessageBox.warning(
                        self, "Error",
                        "A subject with that name already exists."
                    )
            elif dialog.action == "delete":
                self._db.delete_subject(subject_name)
                self.subject_changed.emit()

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle keyboard shortcuts for this page. Returns True if handled."""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+N: Add new subject
        if modifiers == Qt.ControlModifier and key == Qt.Key_N:
            self._add_subject()
            return True

        return False
