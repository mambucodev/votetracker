"""
Settings page for VoteTracker.
Import/export data and manage school years.
"""

import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTabWidget, QPlainTextEdit, QFileDialog, QMessageBox,
    QComboBox, QLineEdit, QCheckBox, QProgressBar, QScrollArea, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QKeyEvent

from ..database import Database, get_db_path
from ..utils import get_symbolic_icon
from ..dialogs import ManageSchoolYearsDialog, ShortcutsHelpDialog, SubjectMappingDialog
from ..i18n import tr, get_language, set_language
from ..classeviva import ClasseVivaClient, convert_classeviva_to_votetracker
from datetime import datetime


class SettingsPage(QWidget):
    """Settings page with import/export and school year management."""

    data_imported = Signal()
    school_year_changed = Signal()
    language_changed = Signal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._cv_client = ClasseVivaClient()
        self._auto_sync_timer = None
        self._sync_worker = None
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

        # Help section
        help_group = QGroupBox("Help")
        help_layout = QHBoxLayout(help_group)
        help_layout.setContentsMargins(12, 12, 12, 12)

        shortcuts_btn = QPushButton("Keyboard Shortcuts")
        shortcuts_btn.setIcon(get_symbolic_icon("input-keyboard"))
        shortcuts_btn.clicked.connect(self._show_shortcuts)
        help_layout.addWidget(shortcuts_btn)
        help_layout.addStretch()

        layout.addWidget(help_group)

        # Language
        lang_group = QGroupBox(tr("Language"))
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.setContentsMargins(12, 12, 12, 12)

        self._lang_combo = QComboBox()
        self._lang_combo.addItem("English", "en")
        self._lang_combo.addItem("Italiano", "it")
        # Set current language
        current = get_language()
        idx = self._lang_combo.findData(current)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self._lang_combo)
        lang_layout.addStretch()

        layout.addWidget(lang_group)

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

        # ClasseViva tab
        cv_tab = QWidget()
        cv_tab_layout = QVBoxLayout(cv_tab)
        cv_tab_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for ClasseViva content
        cv_scroll = QScrollArea()
        cv_scroll.setWidgetResizable(True)
        cv_scroll.setFrameShape(QScrollArea.NoFrame)

        cv_content = QWidget()
        cv_layout = QVBoxLayout(cv_content)
        cv_layout.setContentsMargins(12, 12, 12, 12)
        cv_layout.setSpacing(12)

        # Account section
        account_group = QGroupBox(tr("Account"))
        account_layout = QVBoxLayout(account_group)
        account_layout.setContentsMargins(12, 12, 12, 12)
        account_layout.setSpacing(8)

        # Username field
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel(tr("Username") + ":"))
        self._cv_username = QLineEdit()
        self._cv_username.setPlaceholderText("S1234567")
        username_layout.addWidget(self._cv_username, 1)
        account_layout.addLayout(username_layout)

        # Password field
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel(tr("Password") + ":"))
        self._cv_password = QLineEdit()
        self._cv_password.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self._cv_password, 1)
        account_layout.addLayout(password_layout)

        # Save credentials checkbox with warning
        self._cv_save_creds = QCheckBox(tr("Save credentials"))
        self._cv_save_creds.stateChanged.connect(self._on_save_creds_changed)
        account_layout.addWidget(self._cv_save_creds)

        self._cv_creds_warning = QLabel(tr("Credentials stored with basic encoding. Not fully secure."))
        self._cv_creds_warning.setStyleSheet("color: #e67e22; font-size: 11px;")
        self._cv_creds_warning.setWordWrap(True)
        self._cv_creds_warning.setVisible(False)
        account_layout.addWidget(self._cv_creds_warning)

        # Connection buttons and status
        conn_btn_layout = QHBoxLayout()
        self._cv_test_btn = QPushButton(tr("Test Connection"))
        self._cv_test_btn.setIcon(get_symbolic_icon("network-transmit-receive"))
        self._cv_test_btn.clicked.connect(self._test_cv_connection)
        conn_btn_layout.addWidget(self._cv_test_btn)

        self._cv_clear_creds_btn = QPushButton(tr("Clear saved credentials"))
        self._cv_clear_creds_btn.setIcon(get_symbolic_icon("edit-delete"))
        self._cv_clear_creds_btn.clicked.connect(self._clear_cv_credentials)
        self._cv_clear_creds_btn.setEnabled(False)
        conn_btn_layout.addWidget(self._cv_clear_creds_btn)

        conn_btn_layout.addStretch()
        account_layout.addLayout(conn_btn_layout)

        self._cv_status_label = QLabel(tr("Not connected"))
        self._cv_status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        account_layout.addWidget(self._cv_status_label)

        cv_layout.addWidget(account_group)

        # Manual Import section
        manual_group = QGroupBox(tr("Manual Import"))
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(12, 12, 12, 12)
        manual_layout.setSpacing(8)

        self._cv_import_btn = QPushButton(tr("Import Grades Now"))
        self._cv_import_btn.setIcon(get_symbolic_icon("document-import"))
        self._cv_import_btn.clicked.connect(self._import_from_classeviva)
        self._cv_import_btn.setEnabled(False)
        manual_layout.addWidget(self._cv_import_btn)

        self._cv_progress = QProgressBar()
        self._cv_progress.setVisible(False)
        self._cv_progress.setMaximum(0)  # Indeterminate
        manual_layout.addWidget(self._cv_progress)

        self._cv_last_import_label = QLabel(f"{tr('Last import')}: {tr('Never')}")
        self._cv_last_import_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        manual_layout.addWidget(self._cv_last_import_label)

        self._cv_import_status = QLabel("")
        manual_layout.addWidget(self._cv_import_status)

        cv_layout.addWidget(manual_group)

        # Auto-Sync section
        auto_sync_group = QGroupBox(tr("Automatic Sync"))
        auto_sync_layout = QVBoxLayout(auto_sync_group)
        auto_sync_layout.setContentsMargins(12, 12, 12, 12)
        auto_sync_layout.setSpacing(8)

        self._cv_auto_sync_enabled = QCheckBox(tr("Enable automatic sync"))
        self._cv_auto_sync_enabled.stateChanged.connect(self._on_auto_sync_toggled)
        auto_sync_layout.addWidget(self._cv_auto_sync_enabled)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel(tr("Sync interval") + ":"))
        self._cv_sync_interval = QComboBox()
        self._cv_sync_interval.addItem(tr("30 minutes"), 30)
        self._cv_sync_interval.addItem(tr("1 hour"), 60)
        self._cv_sync_interval.addItem(tr("2 hours"), 120)
        self._cv_sync_interval.addItem(tr("6 hours"), 360)
        self._cv_sync_interval.addItem(tr("12 hours"), 720)
        self._cv_sync_interval.addItem(tr("Daily"), 1440)
        self._cv_sync_interval.setCurrentIndex(1)  # Default: 1 hour
        self._cv_sync_interval.currentIndexChanged.connect(self._on_sync_interval_changed)
        interval_layout.addWidget(self._cv_sync_interval)
        interval_layout.addStretch()
        auto_sync_layout.addLayout(interval_layout)

        self._cv_show_notifications = QCheckBox(tr("Show notification when new grades are imported"))
        auto_sync_layout.addWidget(self._cv_show_notifications)

        self._cv_auto_sync_status = QLabel(tr("Auto-sync: Disabled"))
        self._cv_auto_sync_status.setStyleSheet("color: #95a5a6;")
        auto_sync_layout.addWidget(self._cv_auto_sync_status)

        self._cv_next_sync_label = QLabel("")
        self._cv_next_sync_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        self._cv_next_sync_label.setVisible(False)
        auto_sync_layout.addWidget(self._cv_next_sync_label)

        cv_layout.addWidget(auto_sync_group)

        # Options section
        options_group = QGroupBox(tr("Options"))
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setSpacing(8)

        self._cv_skip_duplicates = QCheckBox(tr("Skip grades already in database"))
        self._cv_skip_duplicates.setChecked(True)
        options_layout.addWidget(self._cv_skip_duplicates)

        self._cv_current_year_only = QCheckBox(tr("Only import current school year"))
        self._cv_current_year_only.setChecked(True)
        options_layout.addWidget(self._cv_current_year_only)

        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel(tr("Import from term") + ":"))
        self._cv_term_filter = QComboBox()
        self._cv_term_filter.addItem(tr("Both"), 0)
        self._cv_term_filter.addItem(tr("Term 1"), 1)
        self._cv_term_filter.addItem(tr("Term 2"), 2)
        term_layout.addWidget(self._cv_term_filter)
        term_layout.addStretch()
        options_layout.addLayout(term_layout)

        cv_layout.addWidget(options_group)
        cv_layout.addStretch()

        cv_scroll.setWidget(cv_content)
        cv_tab_layout.addWidget(cv_scroll)

        tabs.addTab(cv_tab, tr("ClasseViva"))

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

        # Load ClasseViva settings
        self._load_cv_credentials()

        # Load last import time
        last_sync = self._db.get_last_sync_time()
        if last_sync:
            self._cv_last_import_label.setText(f"{tr('Last import')}: {last_sync}")
        else:
            self._cv_last_import_label.setText(f"{tr('Last import')}: {tr('Never')}")

        # Load auto-sync settings
        auto_sync_enabled = self._db.get_auto_sync_enabled()
        self._cv_auto_sync_enabled.setChecked(auto_sync_enabled)

        # Load sync interval
        interval = self._db.get_sync_interval()
        index = self._cv_sync_interval.findData(interval)
        if index >= 0:
            self._cv_sync_interval.setCurrentIndex(index)

        # Start auto-sync if enabled
        if auto_sync_enabled:
            self._start_auto_sync()
    
    def _manage_years(self):
        """Open school years management dialog."""
        dialog = ManageSchoolYearsDialog(self._db, self)
        dialog.exec()

        if dialog.was_changed():
            self.school_year_changed.emit()
            self.refresh()

    def _show_shortcuts(self):
        """Show keyboard shortcuts help dialog."""
        dialog = ShortcutsHelpDialog(self)
        dialog.exec()

    def _on_language_changed(self, index: int):
        """Handle language selection change."""
        lang = self._lang_combo.itemData(index)
        if lang and lang != get_language():
            set_language(lang)
            self._db.set_setting("language", lang)
            self.language_changed.emit()

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

    # ========================================================================
    # CLASSEVIVA METHODS
    # ========================================================================

    def _load_cv_credentials(self):
        """Load saved ClasseViva credentials if they exist."""
        username, password = self._db.get_classeviva_credentials()
        if username and password:
            self._cv_username.setText(username)
            self._cv_password.setText(password)
            self._cv_save_creds.setChecked(True)
            self._cv_clear_creds_btn.setEnabled(True)

    def _on_save_creds_changed(self, state):
        """Handle save credentials checkbox change."""
        self._cv_creds_warning.setVisible(state == Qt.Checked)

    def _test_cv_connection(self):
        """Test connection to ClasseViva."""
        username = self._cv_username.text().strip()
        password = self._cv_password.text().strip()

        if not username or not password:
            self._cv_status_label.setText(tr("Invalid credentials"))
            self._cv_status_label.setStyleSheet("color: #e74c3c;")
            return

        self._cv_test_btn.setEnabled(False)
        self._cv_status_label.setText(tr("Connecting..."))
        self._cv_status_label.setStyleSheet("color: #3498db;")

        # Attempt login
        success, message = self._cv_client.login(username, password)

        if success:
            self._cv_status_label.setText(tr("Connected as") + " " + message.replace("Connected as ", ""))
            self._cv_status_label.setStyleSheet("color: #27ae60;")
            self._cv_import_btn.setEnabled(True)

            # Save credentials if checkbox is checked
            if self._cv_save_creds.isChecked():
                self._db.save_classeviva_credentials(username, password)
                self._cv_clear_creds_btn.setEnabled(True)
        else:
            self._cv_status_label.setText(message)
            self._cv_status_label.setStyleSheet("color: #e74c3c;")
            self._cv_import_btn.setEnabled(False)

        self._cv_test_btn.setEnabled(True)

    def _clear_cv_credentials(self):
        """Clear saved ClasseViva credentials."""
        self._db.clear_classeviva_credentials()
        self._cv_username.clear()
        self._cv_password.clear()
        self._cv_save_creds.setChecked(False)
        self._cv_clear_creds_btn.setEnabled(False)
        self._cv_status_label.setText(tr("Not connected"))
        self._cv_status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")

    def _import_from_classeviva(self):
        """Import grades from ClasseViva."""
        if not self._cv_client.is_authenticated():
            # Try to authenticate first
            username = self._cv_username.text().strip()
            password = self._cv_password.text().strip()

            if not username or not password:
                self._cv_import_status.setText(tr("Invalid credentials"))
                self._cv_import_status.setStyleSheet("color: #e74c3c;")
                return

            success, message = self._cv_client.login(username, password)
            if not success:
                self._cv_import_status.setText(message)
                self._cv_import_status.setStyleSheet("color: #e74c3c;")
                return

        # Show progress
        self._cv_progress.setVisible(True)
        self._cv_import_btn.setEnabled(False)
        self._cv_import_status.setText(tr("Fetching grades..."))
        self._cv_import_status.setStyleSheet("color: #3498db;")

        # Fetch grades
        success, grades, message = self._cv_client.get_grades()

        if not success:
            self._cv_import_status.setText(message)
            self._cv_import_status.setStyleSheet("color: #e74c3c;")
            self._cv_progress.setVisible(False)
            self._cv_import_btn.setEnabled(True)
            return

        # Convert to VoteTracker format
        vt_grades = convert_classeviva_to_votetracker(grades)

        # Apply filters
        term_filter = self._cv_term_filter.currentData()
        if term_filter > 0:
            vt_grades = [g for g in vt_grades if g.get("term") == term_filter]

        # Extract unique ClasseViva subjects
        cv_subjects = list(set(g["subject"] for g in vt_grades))

        # Check which subjects need mapping
        unmapped_subjects = []
        for cv_subject in cv_subjects:
            if not self._db.get_subject_mapping(cv_subject):
                unmapped_subjects.append(cv_subject)

        # Show mapping dialog if there are unmapped subjects
        if unmapped_subjects:
            self._cv_progress.setVisible(False)
            dialog = SubjectMappingDialog(unmapped_subjects, self._db, self)
            if dialog.exec() != QDialog.Accepted:
                # User cancelled mapping
                self._cv_import_status.setText(tr("Import cancelled"))
                self._cv_import_status.setStyleSheet("color: #f39c12;")
                self._cv_import_btn.setEnabled(True)
                return
            self._cv_progress.setVisible(True)

        # Apply subject mappings to grades
        for grade in vt_grades:
            cv_subject = grade["subject"]
            mapped_subject = self._db.get_subject_mapping(cv_subject)
            if mapped_subject:
                grade["subject"] = mapped_subject

        # Check for duplicates if option is enabled
        new_grades = []
        skipped_count = 0

        for grade in vt_grades:
            if self._cv_skip_duplicates.isChecked():
                if self._db.vote_exists(
                    grade["subject"],
                    grade["grade"],
                    grade["date"],
                    grade["type"]
                ):
                    skipped_count += 1
                    continue

            new_grades.append(grade)

        # Import new grades
        if new_grades:
            self._db.import_votes(new_grades)

        # Update UI
        imported_count = len(new_grades)
        self._cv_progress.setVisible(False)
        self._cv_import_btn.setEnabled(True)

        # Build status message
        if imported_count > 0:
            status_msg = tr("Import complete: {count} grades imported").format(count=imported_count)
            if skipped_count > 0:
                status_msg += " (" + tr("Skipped {count} duplicates").format(count=skipped_count) + ")"
            self._cv_import_status.setText(status_msg)
            self._cv_import_status.setStyleSheet("color: #27ae60;")
            self.data_imported.emit()

            # Update last import time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._db.set_last_sync_time(timestamp)
            self._cv_last_import_label.setText(f"{tr('Last import')}: {timestamp}")
        else:
            if skipped_count > 0:
                self._cv_import_status.setText(tr("Skipped {count} duplicates").format(count=skipped_count) + " - " + tr("No votes yet"))
            else:
                self._cv_import_status.setText(tr("No votes yet"))
            self._cv_import_status.setStyleSheet("color: #f39c12;")

    def _on_auto_sync_toggled(self, state):
        """Handle auto-sync checkbox toggle."""
        enabled = state == Qt.Checked
        self._db.set_auto_sync_enabled(enabled)

        if enabled:
            self._start_auto_sync()
            self._cv_auto_sync_status.setText(tr("Auto-sync: Active"))
            self._cv_auto_sync_status.setStyleSheet("color: #27ae60;")
            self._cv_next_sync_label.setVisible(True)
        else:
            self._stop_auto_sync()
            self._cv_auto_sync_status.setText(tr("Auto-sync: Disabled"))
            self._cv_auto_sync_status.setStyleSheet("color: #95a5a6;")
            self._cv_next_sync_label.setVisible(False)

    def _on_sync_interval_changed(self, index):
        """Handle sync interval selection change."""
        minutes = self._cv_sync_interval.currentData()
        self._db.set_sync_interval(minutes)

        # Restart timer if auto-sync is enabled
        if self._cv_auto_sync_enabled.isChecked():
            self._start_auto_sync()

    def _start_auto_sync(self):
        """Start the auto-sync timer."""
        if self._auto_sync_timer is None:
            self._auto_sync_timer = QTimer(self)
            self._auto_sync_timer.timeout.connect(self._auto_sync_tick)

        interval = self._db.get_sync_interval()
        self._auto_sync_timer.start(interval * 60 * 1000)  # Convert minutes to ms
        self._update_next_sync_label()

    def _stop_auto_sync(self):
        """Stop the auto-sync timer."""
        if self._auto_sync_timer:
            self._auto_sync_timer.stop()

    def _auto_sync_tick(self):
        """Perform automatic sync."""
        # Only sync if we have valid credentials
        if self._cv_client.is_authenticated() or self._db.has_classeviva_credentials():
            self._import_from_classeviva()
        self._update_next_sync_label()

    def _update_next_sync_label(self):
        """Update the 'next sync in' label."""
        if self._auto_sync_timer and self._auto_sync_timer.isActive():
            interval = self._db.get_sync_interval()
            self._cv_next_sync_label.setText(f"{tr('Next sync in')}: {interval} {tr('30 minutes').split()[1]}")  # Get 'minutes' word

    # ========================================================================
    # KEYBOARD SHORTCUTS
    # ========================================================================

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
