"""
Settings page for VoteTracker.
Import/export data and manage school years.
"""

import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTabWidget, QPlainTextEdit, QFileDialog, QMessageBox,
    QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from ..database import Database, get_db_path
from ..utils import get_symbolic_icon, has_icon, get_icon_fallback
from ..dialogs import ManageSchoolYearsDialog


class SettingsPage(QWidget):
    """Settings page with import/export and school year management."""
    
    data_imported = Signal()
    school_year_changed = Signal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # Data location
        data_group = QGroupBox("Data Location")
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(12, 12, 12, 12)
        path_label = QLabel(get_db_path())
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        data_layout.addWidget(path_label)
        layout.addWidget(data_group)
        
        # School years management
        years_group = QGroupBox("School Years")
        years_layout = QHBoxLayout(years_group)
        years_layout.setContentsMargins(12, 12, 12, 12)
        
        self._years_label = QLabel("...")
        years_layout.addWidget(self._years_label)
        years_layout.addStretch()
        
        manage_btn = QPushButton("Manage Years")
        manage_btn.setIcon(get_symbolic_icon("configure"))
        manage_btn.clicked.connect(self._manage_years)
        years_layout.addWidget(manage_btn)
        
        layout.addWidget(years_group)
        
        # Tabs
        tabs = QTabWidget()
        
        # Import tab
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        import_layout.setContentsMargins(12, 12, 12, 12)
        import_layout.setSpacing(8)
        
        import_layout.addWidget(QLabel("Paste JSON array to import votes:"))
        
        self._json_input = QPlainTextEdit()
        self._json_input.setPlaceholderText(
            '[\n'
            '  {"subject": "Math", "grade": 7.5, "type": "Written", '
            '"term": 1, "date": "2024-01-15", "description": "Test"}\n'
            ']'
        )
        import_layout.addWidget(self._json_input, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        import_btn = QPushButton("Import")
        import_btn.setIcon(get_symbolic_icon("document-import"))
        import_btn.clicked.connect(self._import_json)
        
        import_file_btn = QPushButton("Import from File")
        import_file_btn.setIcon(get_symbolic_icon("document-open"))
        import_file_btn.clicked.connect(self._import_from_file)
        
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(import_file_btn)
        btn_layout.addStretch()
        import_layout.addLayout(btn_layout)
        
        self._import_status = QLabel("")
        import_layout.addWidget(self._import_status)
        
        tabs.addTab(import_tab, "Import")
        
        # Export tab
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.setContentsMargins(12, 12, 12, 12)
        export_layout.setSpacing(8)
        
        export_layout.addWidget(QLabel("Export your votes as JSON for backup."))
        
        export_btn = QPushButton("Export to File")
        export_btn.setIcon(get_symbolic_icon("document-export"))
        export_btn.clicked.connect(self._export_to_file)
        export_layout.addWidget(export_btn)
        
        self._export_preview = QPlainTextEdit()
        self._export_preview.setReadOnly(True)
        export_layout.addWidget(self._export_preview, 1)
        
        tabs.addTab(export_tab, "Export")
        
        # Danger zone
        danger_tab = QWidget()
        danger_layout = QVBoxLayout(danger_tab)
        danger_layout.setContentsMargins(12, 12, 12, 12)
        danger_layout.setSpacing(8)
        
        danger_layout.addWidget(QLabel("Danger Zone"))
        
        clear_term_btn = QPushButton("Delete Current Term Votes")
        clear_term_btn.setIcon(get_symbolic_icon("edit-delete"))
        clear_term_btn.clicked.connect(self._clear_term_votes)
        danger_layout.addWidget(clear_term_btn)
        
        clear_year_btn = QPushButton("Delete Current Year Votes")
        clear_year_btn.setIcon(get_symbolic_icon("edit-delete"))
        clear_year_btn.clicked.connect(self._clear_year_votes)
        danger_layout.addWidget(clear_year_btn)
        
        danger_layout.addStretch()
        
        tabs.addTab(danger_tab, "Other")
        
        layout.addWidget(tabs, 1)
    
    def refresh(self):
        """Refresh settings display."""
        # Update years label
        years = self._db.get_school_years()
        active = self._db.get_active_school_year()
        self._years_label.setText(
            f"{len(years)} year(s), active: {active['name'] if active else '-'}"
        )
        
        # Update export preview
        votes = self._db.export_votes()
        self._export_preview.setPlainText(
            json.dumps(votes, ensure_ascii=False, indent=2)
        )
    
    def _manage_years(self):
        """Open school years management dialog."""
        dialog = ManageSchoolYearsDialog(self._db, self)
        dialog.exec()
        
        if dialog.was_changed():
            self.school_year_changed.emit()
            self.refresh()
    
    def _import_json(self):
        """Import votes from JSON text."""
        text = self._json_input.toPlainText().strip()
        if not text:
            self._import_status.setText("Enter JSON data")
            self._import_status.setStyleSheet("color: #f39c12;")
            return
        
        try:
            votes = json.loads(text)
            if not isinstance(votes, list):
                raise ValueError("JSON must be an array")
            
            self._db.import_votes(votes)
            self._import_status.setText(f"Imported {len(votes)} votes successfully!")
            self._import_status.setStyleSheet("color: #27ae60;")
            self._json_input.clear()
            self.data_imported.emit()
            
        except json.JSONDecodeError as e:
            self._import_status.setText(f"JSON Error: {e}")
            self._import_status.setStyleSheet("color: #e74c3c;")
        except ValueError as e:
            self._import_status.setText(f"Error: {e}")
            self._import_status.setStyleSheet("color: #e74c3c;")
    
    def _import_from_file(self):
        """Import votes from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select JSON File", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Support different formats
                if isinstance(data, dict) and 'votes' in data:
                    votes = data['votes']
                elif isinstance(data, dict) and 'voti' in data:
                    votes = data['voti']
                else:
                    votes = data
                
                if not isinstance(votes, list):
                    raise ValueError("File must contain an array of votes")
                
                self._db.import_votes(votes)
                self._import_status.setText(f"Imported {len(votes)} votes from file!")
                self._import_status.setStyleSheet("color: #27ae60;")
                self.data_imported.emit()
                
            except Exception as e:
                self._import_status.setText(f"Error: {e}")
                self._import_status.setStyleSheet("color: #e74c3c;")
    
    def _export_to_file(self):
        """Export votes to JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save JSON File", "votes_export.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(
                        self._db.export_votes(), f, 
                        ensure_ascii=False, indent=2
                    )
                QMessageBox.information(
                    self, "Export Complete", 
                    f"Votes exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export error:\n{e}")
    
    def _clear_term_votes(self):
        """Clear votes for current term."""
        term = self._db.get_current_term()
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete all votes in Term {term}?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._db.clear_votes(term=term)
            self.data_imported.emit()
            QMessageBox.information(
                self, "Complete", 
                f"All votes in Term {term} have been deleted."
            )
    
    def _clear_year_votes(self):
        """Clear all votes for current year."""
        active = self._db.get_active_school_year()
        year_name = active["name"] if active else "current year"

        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete ALL votes in {year_name}?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._db.clear_votes()
            self.data_imported.emit()
            QMessageBox.information(
                self, "Complete",
                f"All votes in {year_name} have been deleted."
            )

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle keyboard shortcuts for this page. Returns True if handled."""
        key = event.key()
        modifiers = event.modifiers()

        if modifiers == Qt.ControlModifier:
            # Ctrl+I: Import from file
            if key == Qt.Key_I:
                self._import_from_file()
                return True
            # Ctrl+E: Export to file
            if key == Qt.Key_E:
                self._export_to_file()
                return True

        return False
