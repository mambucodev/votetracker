"""
Dialog classes for VoteTracker.
Contains all popup dialogs for adding/editing data.
"""

from typing import Dict, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QGroupBox, QMessageBox, QSpinBox, QWidget
)
from PySide6.QtCore import Qt, QDate

from .database import Database
from .utils import get_symbolic_icon
from .i18n import tr, PRESET_SUBJECTS, get_translated_subjects


class AddVoteDialog(QDialog):
    """Dialog for adding or editing a vote."""
    
    def __init__(
        self, 
        db: Database, 
        vote: Dict = None, 
        current_term: int = 1,
        parent=None
    ):
        super().__init__(parent)
        self._db = db
        self._vote = vote
        self._current_term = current_term
        
        self.setWindowTitle("Edit Vote" if vote else "Add Vote")
        self.setMinimumWidth(350)
        self._setup_ui()
        
        if vote:
            self._populate_fields()
    
    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Subject
        self._subject_combo = QComboBox()
        self._subject_combo.addItems(self._db.get_subjects())
        self._subject_combo.setEditable(True)
        layout.addRow("Subject:", self._subject_combo)
        
        # Grade
        self._grade_spin = QDoubleSpinBox()
        self._grade_spin.setRange(1.0, 10.0)
        self._grade_spin.setSingleStep(0.25)
        self._grade_spin.setValue(6.0)
        self._grade_spin.setDecimals(2)
        layout.addRow("Grade:", self._grade_spin)
        
        # Type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["Written", "Oral", "Practical"])
        layout.addRow("Type:", self._type_combo)
        
        # Term
        self._term_combo = QComboBox()
        self._term_combo.addItems(["1° Term", "2° Term"])
        self._term_combo.setCurrentIndex(self._current_term - 1)
        layout.addRow("Term:", self._term_combo)
        
        # Date
        self._date_edit = QDateEdit()
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        layout.addRow("Date:", self._date_edit)
        
        # Description
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("e.g., Chapter 5 test")
        layout.addRow("Description:", self._desc_edit)
        
        # Weight
        self._weight_spin = QDoubleSpinBox()
        self._weight_spin.setRange(0.5, 3.0)
        self._weight_spin.setSingleStep(0.5)
        self._weight_spin.setValue(1.0)
        layout.addRow("Weight:", self._weight_spin)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setIcon(get_symbolic_icon("dialog-cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.setIcon(get_symbolic_icon("document-save"))
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addRow(btn_layout)
    
    def _populate_fields(self):
        if not self._vote:
            return
        
        # Subject
        idx = self._subject_combo.findText(self._vote.get("subject", ""))
        if idx >= 0:
            self._subject_combo.setCurrentIndex(idx)
        else:
            self._subject_combo.setCurrentText(self._vote.get("subject", ""))
        
        # Grade
        self._grade_spin.setValue(self._vote.get("grade", 6.0))
        
        # Type
        idx = self._type_combo.findText(self._vote.get("type", "Written"))
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        
        # Term
        term = self._vote.get("term", 1)
        self._term_combo.setCurrentIndex(term - 1)
        
        # Date
        if self._vote.get("date"):
            date = QDate.fromString(self._vote["date"], "yyyy-MM-dd")
            if date.isValid():
                self._date_edit.setDate(date)
        
        # Description
        self._desc_edit.setText(self._vote.get("description", ""))
        
        # Weight
        self._weight_spin.setValue(self._vote.get("weight", 1.0))
    
    def get_vote_data(self) -> Dict:
        """Get the entered vote data."""
        return {
            "subject": self._subject_combo.currentText(),
            "grade": self._grade_spin.value(),
            "type": self._type_combo.currentText(),
            "term": self._term_combo.currentIndex() + 1,
            "date": self._date_edit.date().toString("yyyy-MM-dd"),
            "description": self._desc_edit.text(),
            "weight": self._weight_spin.value()
        }


class AddSubjectDialog(QDialog):
    """Dialog for adding a new subject."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Subject")
        self.setMinimumWidth(250)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        layout.addWidget(QLabel("Subject name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Geography")
        layout.addWidget(self._name_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setIcon(get_symbolic_icon("dialog-cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        add_btn = QPushButton("Add")
        add_btn.setIcon(get_symbolic_icon("list-add"))
        add_btn.setDefault(True)
        add_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)
    
    def get_name(self) -> str:
        """Get the entered subject name."""
        return self._name_edit.text().strip()


class EditSubjectDialog(QDialog):
    """Dialog for editing or deleting a subject."""
    
    def __init__(self, subject_name: str, vote_count: int, parent=None):
        super().__init__(parent)
        self._subject_name = subject_name
        self._vote_count = vote_count
        self.action: Optional[str] = None  # "rename" or "delete"
        self.new_name: Optional[str] = None
        
        self.setWindowTitle(f"Edit Subject: {subject_name}")
        self.setMinimumWidth(300)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Rename section
        rename_group = QGroupBox("Rename")
        rename_layout = QHBoxLayout(rename_group)
        self._name_edit = QLineEdit(self._subject_name)
        rename_btn = QPushButton("Rename")
        rename_btn.setIcon(get_symbolic_icon("edit-rename"))
        rename_btn.clicked.connect(self._on_rename)
        rename_layout.addWidget(self._name_edit)
        rename_layout.addWidget(rename_btn)
        layout.addWidget(rename_group)
        
        # Delete section
        delete_group = QGroupBox("Delete")
        delete_layout = QVBoxLayout(delete_group)
        
        if self._vote_count > 0:
            warning = f"This will delete the subject and all {self._vote_count} associated votes."
        else:
            warning = "This subject has no votes."
        
        warning_label = QLabel(warning)
        warning_label.setStyleSheet("color: gray;")
        warning_label.setWordWrap(True)
        delete_layout.addWidget(warning_label)
        
        delete_btn = QPushButton("Delete Subject")
        delete_btn.setIcon(get_symbolic_icon("edit-delete"))
        delete_btn.clicked.connect(self._on_delete)
        delete_layout.addWidget(delete_btn)
        
        layout.addWidget(delete_group)
        
        # Cancel button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def _on_rename(self):
        new_name = self._name_edit.text().strip()
        if new_name and new_name != self._subject_name:
            self.action = "rename"
            self.new_name = new_name
            self.accept()
    
    def _on_delete(self):
        if self._vote_count > 0:
            reply = QMessageBox.warning(
                self, "Confirm Deletion",
                f"Are you sure you want to delete '{self._subject_name}' "
                f"and all {self._vote_count} associated votes?\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.action = "delete"
        self.accept()


class AddSchoolYearDialog(QDialog):
    """Dialog for adding a new school year."""
    
    def __init__(self, existing_years: list, parent=None):
        super().__init__(parent)
        self._existing_years = set(y["start_year"] for y in existing_years)
        
        self.setWindowTitle("Add School Year")
        self.setMinimumWidth(280)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        layout.addWidget(QLabel("Select start year:"))
        
        # Year selector
        from datetime import datetime
        current_year = datetime.now().year
        
        year_layout = QHBoxLayout()
        self._year_spin = QSpinBox()
        self._year_spin.setRange(current_year - 10, current_year + 5)
        self._year_spin.setValue(current_year)
        self._year_spin.valueChanged.connect(self._update_preview)
        year_layout.addWidget(self._year_spin)
        
        self._preview_label = QLabel()
        self._preview_label.setStyleSheet("color: gray;")
        year_layout.addWidget(self._preview_label)
        year_layout.addStretch()
        
        layout.addLayout(year_layout)
        
        self._warning_label = QLabel()
        self._warning_label.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self._warning_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self._add_btn = QPushButton("Add")
        self._add_btn.setIcon(get_symbolic_icon("list-add"))
        self._add_btn.setDefault(True)
        self._add_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self._add_btn)
        layout.addLayout(btn_layout)
        
        self._update_preview()
    
    def _update_preview(self):
        year = self._year_spin.value()
        self._preview_label.setText(f"→ {year}/{year + 1}")
        
        if year in self._existing_years:
            self._warning_label.setText("This year already exists!")
            self._add_btn.setEnabled(False)
        else:
            self._warning_label.setText("")
            self._add_btn.setEnabled(True)
    
    def get_start_year(self) -> int:
        """Get the selected start year."""
        return self._year_spin.value()


class ManageSchoolYearsDialog(QDialog):
    """Dialog for managing school years."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._changed = False
        
        self.setWindowTitle("Manage School Years")
        self.setMinimumWidth(350)
        self.setMinimumHeight(300)
        self._setup_ui()
        self._refresh_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # List
        from PySide6.QtWidgets import QListWidget
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self._list)
        
        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        add_btn = QPushButton("Add Year")
        add_btn.setIcon(get_symbolic_icon("list-add"))
        add_btn.clicked.connect(self._add_year)
        
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setIcon(get_symbolic_icon("edit-delete"))
        self._delete_btn.clicked.connect(self._delete_year)
        
        self._activate_btn = QPushButton("Set Active")
        self._activate_btn.clicked.connect(self._set_active)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(self._delete_btn)
        btn_layout.addWidget(self._activate_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)
    
    def _refresh_list(self):
        self._list.clear()
        years = self._db.get_school_years()
        
        for year in years:
            text = year["name"]
            if year["is_active"]:
                text += " (active)"
            
            from PySide6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, year["id"])
            self._list.addItem(item)
        
        # Update button states
        has_selection = self._list.currentRow() >= 0
        self._delete_btn.setEnabled(has_selection and len(years) > 1)
        self._activate_btn.setEnabled(has_selection)
    
    def _add_year(self):
        years = self._db.get_school_years()
        dialog = AddSchoolYearDialog(years, self)
        
        if dialog.exec() == QDialog.Accepted:
            start_year = dialog.get_start_year()
            if self._db.add_school_year(start_year):
                self._changed = True
                self._refresh_list()
    
    def _delete_year(self):
        item = self._list.currentItem()
        if not item:
            return
        
        year_id = item.data(Qt.UserRole)
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            "Are you sure you want to delete this school year?\n"
            "All votes in this year will be deleted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self._db.delete_school_year(year_id):
                self._changed = True
                self._refresh_list()
    
    def _set_active(self):
        item = self._list.currentItem()
        if not item:
            return
        
        year_id = item.data(Qt.UserRole)
        self._db.set_active_school_year(year_id)
        self._changed = True
        self._refresh_list()
    
    def was_changed(self) -> bool:
        """Check if any changes were made."""
        return self._changed


class ShortcutsHelpDialog(QDialog):
    """Dialog showing keyboard shortcuts help."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Shortcuts sections
        sections = [
            ("Global", [
                ("Ctrl+1-8", "Jump to page"),
                ("PgUp / PgDown", "Navigate pages"),
                ("Ctrl+Z", "Undo"),
                ("Ctrl+Shift+Z", "Redo"),
                ("?", "Show this help"),
            ]),
            ("Votes Page", [
                ("Ctrl+N", "Add new grade"),
                ("Enter", "Edit selected"),
                ("Delete", "Delete selected"),
                ("1 / 2", "Switch term"),
            ]),
            ("Subjects Page", [
                ("Ctrl+N", "Add new subject"),
            ]),
            ("Settings Page", [
                ("Ctrl+I", "Import data"),
                ("Ctrl+E", "Export data"),
            ]),
            ("Calendar / Report / Statistics", [
                ("1 / 2", "Switch term"),
            ]),
        ]

        for section_name, shortcuts in sections:
            section = QGroupBox(section_name)
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(12, 8, 12, 8)
            section_layout.setSpacing(4)

            for key, desc in shortcuts:
                row = QHBoxLayout()
                row.setSpacing(12)

                # Style keys as keyboard buttons
                key_label = QLabel(key)
                key_label.setStyleSheet("""
                    background: #e0e0e0;
                    border: 1px solid #bbb;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: monospace;
                    font-weight: bold;
                    color: #333;
                """)

                desc_label = QLabel(desc)
                desc_label.setStyleSheet("color: #666;")

                row.addWidget(key_label)
                row.addWidget(desc_label)
                row.addStretch()

                row_widget = QWidget()
                row_widget.setLayout(row)
                section_layout.addWidget(row_widget)

            layout.addWidget(section)

        # Close hint
        hint = QLabel("Press ? or Esc to close")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def keyPressEvent(self, event):
        """Close on ? or Esc."""
        if event.key() in (Qt.Key_Question, Qt.Key_Escape):
            self.accept()
        else:
            super().keyPressEvent(event)


class OnboardingWizard(QDialog):
    """First-run wizard to set up school year and subjects."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._selected_subjects = set()
        # Get translated subject names (displayed) and map to English keys (stored)
        self._translated_subjects = get_translated_subjects()
        # Map translated name -> English key
        self._subject_map = {tr(s): s for s in PRESET_SUBJECTS}

        self.setWindowTitle(tr("Welcome to VoteTracker!"))
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Welcome header
        title = QLabel(tr("Welcome to VoteTracker!"))
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(tr("Let's set up your grade tracker in a few simple steps."))
        subtitle.setStyleSheet("font-size: 14px; color: gray;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # School year info
        year_group = QGroupBox(tr("School Year"))
        year_layout = QVBoxLayout(year_group)
        year_layout.setContentsMargins(16, 16, 16, 16)

        active_year = self._db.get_active_school_year()
        year_name = active_year["name"] if active_year else "-"
        year_label = QLabel(f"{tr('Current school year:')} <b>{year_name}</b>")
        year_layout.addWidget(year_label)

        year_hint = QLabel(tr("You can manage school years later in Settings."))
        year_hint.setStyleSheet("color: gray; font-size: 11px;")
        year_layout.addWidget(year_hint)

        layout.addWidget(year_group)

        # Subject selection
        subjects_group = QGroupBox(tr("Add Subjects"))
        subjects_layout = QVBoxLayout(subjects_group)
        subjects_layout.setContentsMargins(16, 16, 16, 16)
        subjects_layout.setSpacing(8)

        subjects_hint = QLabel(tr("Select the subjects you want to track:"))
        subjects_layout.addWidget(subjects_hint)

        # Grid of checkboxes
        from PySide6.QtWidgets import QCheckBox, QGridLayout, QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setMaximumHeight(150)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)

        self._checkboxes = {}
        existing_subjects = set(self._db.get_subjects())

        for i, translated_name in enumerate(self._translated_subjects):
            cb = QCheckBox(translated_name)
            # Check if this subject (by English key) already exists
            english_key = self._subject_map.get(translated_name, translated_name)
            if english_key in existing_subjects or translated_name in existing_subjects:
                cb.setChecked(True)
                cb.setEnabled(False)
                cb.setStyleSheet("color: gray;")
            cb.toggled.connect(lambda checked, s=translated_name: self._on_subject_toggled(s, checked))
            self._checkboxes[translated_name] = cb
            grid.addWidget(cb, i // 3, i % 3)

        scroll.setWidget(grid_widget)
        subjects_layout.addWidget(scroll)

        # Custom subject input
        custom_layout = QHBoxLayout()
        self._custom_input = QLineEdit()
        self._custom_input.setPlaceholderText(tr("Add custom subject..."))
        self._custom_input.returnPressed.connect(self._add_custom_subject)

        add_btn = QPushButton(tr("Add"))
        add_btn.clicked.connect(self._add_custom_subject)

        custom_layout.addWidget(self._custom_input)
        custom_layout.addWidget(add_btn)
        subjects_layout.addLayout(custom_layout)

        self._custom_list = QLabel("")
        self._custom_list.setStyleSheet("color: #27ae60; font-size: 11px;")
        subjects_layout.addWidget(self._custom_list)

        layout.addWidget(subjects_group, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        start_btn = QPushButton(tr("Get Started"))
        start_btn.setStyleSheet("font-size: 14px; padding: 8px 24px;")
        start_btn.setDefault(True)
        start_btn.clicked.connect(self._finish)

        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)

    def _on_subject_toggled(self, subject: str, checked: bool):
        if checked:
            self._selected_subjects.add(subject)
        else:
            self._selected_subjects.discard(subject)

    def _add_custom_subject(self):
        name = self._custom_input.text().strip()
        if name and name not in self._selected_subjects:
            self._selected_subjects.add(name)
            self._custom_input.clear()
            self._update_custom_list()

    def _update_custom_list(self):
        custom = [s for s in self._selected_subjects if s not in self._translated_subjects]
        if custom:
            self._custom_list.setText(tr("Custom:") + " " + ", ".join(sorted(custom)))
        else:
            self._custom_list.setText("")

    def _finish(self):
        # Add selected subjects (store with translated names)
        existing = set(self._db.get_subjects())
        for subject in self._selected_subjects:
            if subject not in existing:
                self._db.add_subject(subject)

        # Mark onboarding complete
        self._db.set_setting("onboarding_complete", "1")
        self.accept()
