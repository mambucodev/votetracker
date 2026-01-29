"""
Dialog classes for VoteTracker.
Contains all popup dialogs for adding/editing data.
"""

from typing import Dict, Optional, List, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QGroupBox, QMessageBox, QSpinBox, QWidget, QScrollArea,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from .database import Database
from .utils import get_symbolic_icon
from .i18n import tr, PRESET_SUBJECTS, get_translated_subjects
from .subject_matcher import get_auto_suggestions


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


class SubjectMappingDialog(QDialog):
    """Dialog for mapping provider subjects to VoteTracker subjects."""

    def __init__(self, source_subjects: List[str], provider_id: str, provider_name: str,
                 db: Database, parent=None):
        """
        Args:
            source_subjects: List of subject names from the provider
            provider_id: Provider identifier (e.g., "classeviva", "axios")
            provider_name: Human-readable provider name (e.g., "ClasseViva", "Axios")
            db: Database instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._source_subjects = source_subjects
        self._provider_id = provider_id
        self._provider_name = provider_name
        self._db = db
        self._mappings = {}  # source_subject -> vt_subject

        self.setWindowTitle(tr("Map {provider} Subjects").format(provider=provider_name))
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel(
            tr("Map {provider} subjects to VoteTracker subjects").format(provider=self._provider_name) + "\n" +
            tr("We've auto-suggested matches based on subject names.")
        )
        header.setWordWrap(True)
        header.setStyleSheet("font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(header)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            self._provider_name + " " + tr("Subject"),
            tr("→"),
            tr("VoteTracker Subject"),
            ""
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(1, 40)
        self._table.setColumnWidth(3, 80)
        self._table.verticalHeader().setVisible(False)

        # Get existing VoteTracker subjects
        vt_subjects = self._db.get_subjects()

        # Populate table with suggestions
        self._table.setRowCount(len(self._source_subjects))
        for i, source_subject in enumerate(self._source_subjects):
            # Provider subject (read-only)
            source_item = QTableWidgetItem(source_subject)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(i, 0, source_item)

            # Arrow
            arrow_item = QTableWidgetItem("→")
            arrow_item.setFlags(arrow_item.flags() & ~Qt.ItemIsEditable)
            arrow_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 1, arrow_item)

            # VoteTracker subject (dropdown)
            combo = QComboBox()
            combo.setEditable(True)

            # Get auto-suggestion
            suggestion = get_auto_suggestions(source_subject, vt_subjects)

            # Add options to combo
            combo.addItem(tr("-- Create New Subject --"), None)
            for vt_subj in vt_subjects:
                combo.addItem(vt_subj, vt_subj)

            # Set default selection based on suggestion
            if suggestion["action"] == "map" and suggestion["suggested_match"]:
                # High confidence match - select it
                index = combo.findData(suggestion["suggested_match"])
                if index >= 0:
                    combo.setCurrentIndex(index)
                    # Highlight as auto-matched
                    source_item.setBackground(QColor(39, 174, 96, 30))  # Light green
            elif suggestion["action"] == "create" and suggestion["suggested_new"]:
                # Suggest creating new canonical name
                combo.setEditText(suggestion["suggested_new"])
                source_item.setBackground(QColor(52, 152, 219, 30))  # Light blue
            elif suggestion["suggested_match"]:
                # Low confidence - show suggestion but require manual confirmation
                index = combo.findData(suggestion["suggested_match"])
                if index >= 0:
                    combo.setCurrentIndex(index)
                source_item.setBackground(QColor(243, 156, 18, 30))  # Light orange
            else:
                # No suggestion - manual mapping required
                if suggestion["suggested_new"]:
                    combo.setEditText(suggestion["suggested_new"])
                source_item.setBackground(QColor(231, 76, 60, 30))  # Light red

            self._table.setCellWidget(i, 2, combo)

            # Store reference for later retrieval
            combo.setProperty("source_subject", source_subject)

            # Confidence indicator
            if suggestion["confidence"] > 0:
                conf_text = f"{int(suggestion['confidence'] * 100)}%"
                conf_item = QTableWidgetItem(conf_text)
                conf_item.setFlags(conf_item.flags() & ~Qt.ItemIsEditable)
                conf_item.setTextAlignment(Qt.AlignCenter)

                # Color code confidence
                if suggestion["confidence"] > 0.8:
                    conf_item.setForeground(QColor(39, 174, 96))  # Green
                elif suggestion["confidence"] > 0.6:
                    conf_item.setForeground(QColor(243, 156, 18))  # Orange
                else:
                    conf_item.setForeground(QColor(149, 165, 166))  # Gray

                self._table.setItem(i, 3, conf_item)

        layout.addWidget(self._table, 1)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        def add_legend(color, text):
            box = QLabel("  ")
            box.setStyleSheet(f"background-color: rgba{color}; border: 1px solid #ccc;")
            box.setFixedSize(20, 20)
            legend_layout.addWidget(box)
            legend_layout.addWidget(QLabel(text))

        add_legend((39, 174, 96, 30), tr("High confidence"))
        add_legend((243, 156, 18, 30), tr("Low confidence"))
        add_legend((52, 152, 219, 30), tr("Create new"))
        add_legend((231, 76, 60, 30), tr("Manual"))
        legend_layout.addStretch()

        layout.addLayout(legend_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setIcon(get_symbolic_icon("dialog-cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        save_btn = QPushButton(tr("Save Mappings"))
        save_btn.setIcon(get_symbolic_icon("document-save"))
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_mappings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save_mappings(self):
        """Save the mappings and close dialog."""
        for i in range(self._table.rowCount()):
            source_subject = self._table.item(i, 0).text()
            combo = self._table.cellWidget(i, 2)

            # Get selected or entered value
            vt_subject = None
            if combo.currentData() is not None:
                # Existing subject selected
                vt_subject = combo.currentData()
            else:
                # New subject entered
                vt_subject = combo.currentText().strip()

            if vt_subject:
                self._mappings[source_subject] = vt_subject
                # Save mapping to database (provider-aware)
                self._db.save_provider_subject_mapping(self._provider_id, source_subject, vt_subject)
                # Ensure the VoteTracker subject exists
                if vt_subject not in self._db.get_subjects():
                    self._db.add_subject(vt_subject)

        self.accept()

    def get_mappings(self) -> Dict[str, str]:
        """Get the subject mappings."""
        return self._mappings


class ManageSubjectMappingsDialog(QDialog):
    """Dialog for viewing and editing existing provider subject mappings."""

    def __init__(self, provider_id: str, provider_name: str, db: Database, parent=None):
        """
        Args:
            provider_id: Provider identifier (e.g., "classeviva", "axios")
            provider_name: Human-readable provider name (e.g., "ClasseViva", "Axios")
            db: Database instance
            parent: Parent widget
        """
        super().__init__(parent)
        self._provider_id = provider_id
        self._provider_name = provider_name
        self._db = db
        self._changed = False

        self.setWindowTitle(tr("Manage {provider} Subject Mappings").format(provider=provider_name))
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self._setup_ui()
        self._load_mappings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel(
            tr("View and edit how {provider} subjects are mapped to VoteTracker subjects.").format(provider=self._provider_name)
        )
        header.setWordWrap(True)
        header.setStyleSheet("font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(header)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels([
            self._provider_name + " " + tr("Subject"),
            tr("VoteTracker Subject"),
            ""
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self._table.setColumnWidth(2, 80)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table, 1)

        # Info label
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(self._info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        clear_all_btn = QPushButton(tr("Clear All Mappings"))
        clear_all_btn.setIcon(get_symbolic_icon("edit-delete"))
        clear_all_btn.clicked.connect(self._clear_all_mappings)
        btn_layout.addWidget(clear_all_btn)

        btn_layout.addStretch()

        close_btn = QPushButton(tr("Close"))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_mappings(self):
        """Load all existing mappings into the table."""
        mappings = self._db.get_all_provider_subject_mappings(self._provider_id)
        vt_subjects = self._db.get_subjects()

        self._table.setRowCount(len(mappings))

        for i, (source_subject, vt_subject) in enumerate(sorted(mappings.items())):
            # Provider subject (read-only)
            source_item = QTableWidgetItem(source_subject)
            source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(i, 0, source_item)

            # VoteTracker subject (dropdown)
            combo = QComboBox()
            combo.setEditable(True)

            # Add current and other subjects
            for vt_subj in vt_subjects:
                combo.addItem(vt_subj, vt_subj)

            # Set current mapping
            index = combo.findText(vt_subject)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                # Subject might not exist anymore, just set the text
                combo.setEditText(vt_subject)

            # Connect change signal
            combo.currentTextChanged.connect(
                lambda text, src=source_subject: self._on_mapping_changed(src, text)
            )

            self._table.setCellWidget(i, 1, combo)

            # Delete button
            delete_btn = QPushButton(tr("Delete"))
            delete_btn.setIcon(get_symbolic_icon("edit-delete"))
            delete_btn.clicked.connect(
                lambda checked, src=source_subject: self._delete_mapping(src)
            )
            self._table.setCellWidget(i, 2, delete_btn)

        # Update info label
        if len(mappings) == 0:
            self._info_label.setText(tr("No mappings yet. Import grades from {provider} to create mappings.").format(provider=self._provider_name))
        else:
            self._info_label.setText(tr("{count} mapping(s)").format(count=len(mappings)))

    def _on_mapping_changed(self, source_subject: str, new_vt_subject: str):
        """Handle when a mapping is changed."""
        new_vt_subject = new_vt_subject.strip()
        if not new_vt_subject:
            return

        current_mapping = self._db.get_provider_subject_mapping(self._provider_id, source_subject)
        if current_mapping != new_vt_subject:
            # Ensure the subject exists
            if new_vt_subject not in self._db.get_subjects():
                reply = QMessageBox.question(
                    self,
                    tr("Create New Subject"),
                    tr("Subject '{name}' doesn't exist. Create it?").format(name=new_vt_subject),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self._db.add_subject(new_vt_subject)
                else:
                    # Revert change
                    self._reload_row(source_subject)
                    return

            # Save new mapping (provider-aware)
            self._db.save_provider_subject_mapping(self._provider_id, source_subject, new_vt_subject)
            self._changed = True

    def _delete_mapping(self, source_subject: str):
        """Delete a subject mapping."""
        reply = QMessageBox.question(
            self,
            tr("Confirm Deletion"),
            tr("Delete mapping for '{subject}'?").format(subject=source_subject) + "\n" +
            tr("This won't delete any grades, but future imports will ask for mapping again."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._db.clear_provider_subject_mapping(self._provider_id, source_subject)
            self._changed = True
            self._load_mappings()

    def _clear_all_mappings(self):
        """Clear all subject mappings."""
        mappings = self._db.get_all_provider_subject_mappings(self._provider_id)
        if len(mappings) == 0:
            return

        reply = QMessageBox.warning(
            self,
            tr("Confirm Clear All"),
            tr("Delete ALL {count} subject mappings?").format(count=len(mappings)) + "\n" +
            tr("This won't delete any grades, but future imports will ask for mapping again."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._db.clear_all_provider_subject_mappings(self._provider_id)
            self._changed = True
            self._load_mappings()

    def _reload_row(self, source_subject: str):
        """Reload a specific row after reverting changes."""
        for i in range(self._table.rowCount()):
            item = self._table.item(i, 0)
            if item and item.text() == source_subject:
                current_mapping = self._db.get_provider_subject_mapping(self._provider_id, source_subject)
                combo = self._table.cellWidget(i, 1)
                if combo and current_mapping:
                    combo.setCurrentText(current_mapping)
                break

    def was_changed(self) -> bool:
        """Check if any changes were made."""
        return self._changed

class SelectStudentDialog(QDialog):
    """Dialog for selecting a student when multiple are available."""

    def __init__(self, students: List[Tuple[str, str]], parent=None):
        """
        Initialize dialog.

        Args:
            students: List of (student_id, student_name) tuples
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(tr("Select Student"))
        self.setMinimumWidth(350)
        self._students = students
        self._selected_student_id = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Info label
        info_label = QLabel(
            tr("Multiple students found for this account.") + "\n" +
            tr("Please select which student to use:")
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Student selector
        layout.addWidget(QLabel(tr("Student:")))
        self._student_combo = QComboBox()
        for student_id, student_name in self._students:
            self._student_combo.addItem(student_name, student_id)
        layout.addWidget(self._student_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setIcon(get_symbolic_icon("dialog-cancel"))
        cancel_btn.clicked.connect(self.reject)

        select_btn = QPushButton(tr("Select"))
        select_btn.setIcon(get_symbolic_icon("dialog-ok"))
        select_btn.setDefault(True)
        select_btn.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)

    def get_selected_student_id(self) -> Optional[str]:
        """Get the selected student ID."""
        return self._student_combo.currentData()
