"""
Settings page for VoteTracker.
Import/export data and manage school years.
"""

import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTabWidget, QPlainTextEdit, QFileDialog, QMessageBox,
    QComboBox, QLineEdit, QCheckBox, QProgressBar, QScrollArea, QDialog,
    QRadioButton, QButtonGroup, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeyEvent

from ..database import Database, get_db_path
from ..utils import get_symbolic_icon
from ..dialogs import ManageSchoolYearsDialog, ShortcutsHelpDialog, SubjectMappingDialog, ManageSubjectMappingsDialog
from ..i18n import tr, get_language, set_language
from ..classeviva import ClasseVivaClient, convert_classeviva_to_votetracker
from ..sync_provider import SyncProviderRegistry
from ..providers import register_all_providers
from datetime import datetime


class SettingsPage(QWidget):
    """Settings page with import/export and school year management."""

    data_imported = Signal()
    school_year_changed = Signal()
    language_changed = Signal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._cv_client = ClasseVivaClient()  # Keep for backward compatibility

        # Initialize provider system
        register_all_providers()
        self._provider_instances = {}  # provider_id -> provider instance
        self._active_provider_id = None

        self._setup_ui()
    
    def _setup_ui(self):
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar (not scrolled)
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 20, 20, 12)
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_layout.addWidget(title)
        main_layout.addWidget(title_widget)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 8, 20, 20)
        layout.setSpacing(16)

        # =====================================================================
        # GENERAL SETTINGS
        # =====================================================================
        general_group = QGroupBox(tr("General"))
        general_layout = QVBoxLayout(general_group)
        general_layout.setContentsMargins(12, 12, 12, 12)
        general_layout.setSpacing(12)

        # Language
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(tr("Language") + ":"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("English", "en")
        self._lang_combo.addItem("Italiano", "it")
        current = get_language()
        idx = self._lang_combo.findData(current)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        general_layout.addLayout(lang_row)

        # School Years
        years_row = QHBoxLayout()
        self._years_label = QLabel("...")
        years_row.addWidget(self._years_label)
        years_row.addStretch()
        manage_years_btn = QPushButton(tr("Manage Years"))
        manage_years_btn.setIcon(get_symbolic_icon("configure"))
        manage_years_btn.clicked.connect(self._manage_years)
        years_row.addWidget(manage_years_btn)
        general_layout.addLayout(years_row)

        # Current Term indicator
        term_row = QHBoxLayout()
        self._term_label = QLabel("...")
        term_row.addWidget(self._term_label)
        term_row.addStretch()
        general_layout.addLayout(term_row)

        layout.addWidget(general_group)

        # =====================================================================
        # DATA MANAGEMENT
        # =====================================================================
        data_group = QGroupBox(tr("Data Management"))
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(12, 12, 12, 12)
        data_layout.setSpacing(12)

        # Database location
        db_label = QLabel(tr("Database:") + " " + get_db_path())
        db_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        db_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        db_label.setWordWrap(True)
        data_layout.addWidget(db_label)

        # Import section
        import_label = QLabel(tr("Import Votes (JSON)"))
        import_label.setStyleSheet("font-weight: bold;")
        data_layout.addWidget(import_label)

        self._json_input = QPlainTextEdit()
        self._json_input.setPlaceholderText(
            '[\n'
            '  {"subject": "Math", "grade": 7.5, "type": "Written", '
            '"term": 1, "date": "2024-01-15", "description": "Test"}\n'
            ']'
        )
        self._json_input.setMaximumHeight(100)
        data_layout.addWidget(self._json_input)

        import_btn_layout = QHBoxLayout()
        import_btn_layout.setSpacing(8)

        import_btn = QPushButton(tr("Import"))
        import_btn.setIcon(get_symbolic_icon("document-import"))
        import_btn.clicked.connect(self._import_json)
        import_btn_layout.addWidget(import_btn)

        import_file_btn = QPushButton(tr("Import from File"))
        import_file_btn.setIcon(get_symbolic_icon("document-open"))
        import_file_btn.clicked.connect(self._import_from_file)
        import_btn_layout.addWidget(import_file_btn)

        import_btn_layout.addStretch()
        data_layout.addLayout(import_btn_layout)

        self._import_status = QLabel("")
        data_layout.addWidget(self._import_status)

        # Export section
        export_label = QLabel(tr("Export Votes"))
        export_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        data_layout.addWidget(export_label)

        export_btn = QPushButton(tr("Export to File"))
        export_btn.setIcon(get_symbolic_icon("document-export"))
        export_btn.clicked.connect(self._export_to_file)
        data_layout.addWidget(export_btn)

        # Clear data section
        clear_label = QLabel(tr("Clear Data"))
        clear_label.setStyleSheet("font-weight: bold; margin-top: 8px; color: #e74c3c;")
        data_layout.addWidget(clear_label)

        clear_btn_layout = QHBoxLayout()
        clear_btn_layout.setSpacing(8)

        clear_term_btn = QPushButton(tr("Delete Current Term"))
        clear_term_btn.setIcon(get_symbolic_icon("edit-delete"))
        clear_term_btn.clicked.connect(self._clear_term_votes)
        clear_btn_layout.addWidget(clear_term_btn)

        clear_year_btn = QPushButton(tr("Delete Current Year"))
        clear_year_btn.setIcon(get_symbolic_icon("edit-delete"))
        clear_year_btn.clicked.connect(self._clear_year_votes)
        clear_btn_layout.addWidget(clear_year_btn)

        clear_btn_layout.addStretch()
        data_layout.addLayout(clear_btn_layout)

        layout.addWidget(data_group)

        # =====================================================================
        # SYNC INTEGRATION (Provider-based)
        # =====================================================================
        sync_group = QGroupBox(tr("Sync Integration"))
        sync_layout = QVBoxLayout(sync_group)
        sync_layout.setContentsMargins(12, 12, 12, 12)
        sync_layout.setSpacing(12)

        # Provider selection section
        provider_select_group = QGroupBox(tr("Sync Provider"))
        provider_select_layout = QVBoxLayout(provider_select_group)
        provider_select_layout.setContentsMargins(12, 12, 12, 12)
        provider_select_layout.setSpacing(8)

        select_hint = QLabel(tr("Select a sync provider to automatically import grades:"))
        select_hint.setWordWrap(True)
        select_hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        provider_select_layout.addWidget(select_hint)

        # Radio buttons for provider selection
        self._provider_button_group = QButtonGroup(self)
        self._provider_radios = {}  # provider_id -> QRadioButton

        # None option
        none_radio = QRadioButton(tr("No sync provider (manual data entry only)"))
        self._provider_button_group.addButton(none_radio, 0)
        self._provider_radios["none"] = none_radio
        provider_select_layout.addWidget(none_radio)

        # Add radio button for each registered provider
        available_providers = SyncProviderRegistry.get_available_providers()
        for idx, (provider_id, provider_name) in enumerate(available_providers, start=1):
            radio = QRadioButton(provider_name)
            self._provider_button_group.addButton(radio, idx)
            self._provider_radios[provider_id] = radio
            provider_select_layout.addWidget(radio)

        # Connect signal
        self._provider_button_group.buttonClicked.connect(self._on_provider_changed)

        sync_layout.addWidget(provider_select_group)

        # Stacked widget for provider-specific settings
        self._provider_stack = QStackedWidget()

        # Create a page for each provider
        self._provider_pages = {}  # provider_id -> widget index
        self._provider_widgets = {}  # provider_id -> dict of UI elements

        # Page 0: None (empty placeholder)
        none_page = QWidget()
        none_layout = QVBoxLayout(none_page)
        none_label = QLabel(tr("No sync provider selected. Use manual data entry."))
        none_label.setStyleSheet("color: #95a5a6; font-style: italic; padding: 20px;")
        none_label.setAlignment(Qt.AlignCenter)
        none_layout.addWidget(none_label)
        self._provider_stack.addWidget(none_page)
        self._provider_pages["none"] = 0

        # Create a page for each registered provider
        for idx, (provider_id, provider_name) in enumerate(available_providers, start=1):
            provider = SyncProviderRegistry.get_provider(provider_id, self._db)
            page_widget = self._create_provider_page(provider_id, provider)
            self._provider_stack.addWidget(page_widget)
            self._provider_pages[provider_id] = idx
            self._provider_instances[provider_id] = provider

        sync_layout.addWidget(self._provider_stack)

        layout.addWidget(sync_group)

        # Keep old ClasseViva section commented out for reference during transition
        # =====================================================================
        # OLD CLASSEVIVA INTEGRATION (replaced by provider system above)
        # =====================================================================
        """
        cv_group = QGroupBox(tr("ClasseViva Integration"))
        cv_layout = QVBoxLayout(cv_group)
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

        # Auto-login checkbox
        self._cv_auto_login = QCheckBox(tr("Auto-login on app startup"))
        self._cv_auto_login.stateChanged.connect(self._on_auto_login_changed)
        account_layout.addWidget(self._cv_auto_login)

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

        # Subject Mappings section
        mappings_group = QGroupBox(tr("Subject Mappings"))
        mappings_layout = QVBoxLayout(mappings_group)
        mappings_layout.setContentsMargins(12, 12, 12, 12)
        mappings_layout.setSpacing(8)

        mappings_hint = QLabel(tr("View and edit how ClasseViva subjects are mapped to your VoteTracker subjects."))
        mappings_hint.setWordWrap(True)
        mappings_hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        mappings_layout.addWidget(mappings_hint)

        manage_mappings_btn = QPushButton(tr("Manage Subject Mappings"))
        manage_mappings_btn.setIcon(get_symbolic_icon("configure"))
        manage_mappings_btn.clicked.connect(self._manage_subject_mappings)
        mappings_layout.addWidget(manage_mappings_btn)

        cv_layout.addWidget(mappings_group)

        layout.addWidget(cv_group)
        """
        # End of old ClasseViva section

        # =====================================================================
        # HELP & INFO
        # =====================================================================
        help_group = QGroupBox(tr("Help & Information"))
        help_layout = QVBoxLayout(help_group)
        help_layout.setContentsMargins(12, 12, 12, 12)
        help_layout.setSpacing(12)

        # Keyboard shortcuts
        shortcuts_btn = QPushButton(tr("Keyboard Shortcuts"))
        shortcuts_btn.setIcon(get_symbolic_icon("input-keyboard"))
        shortcuts_btn.clicked.connect(self._show_shortcuts)
        help_layout.addWidget(shortcuts_btn)

        # Version info
        from .. import __version__
        version_label = QLabel(f"VoteTracker v{__version__}")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        help_layout.addWidget(version_label)

        layout.addWidget(help_group)

        # Add stretch at the end
        layout.addStretch()

        # Set scroll widget
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _create_provider_page(self, provider_id: str, provider):
        """
        Dynamically create a settings page for a provider.

        Args:
            provider_id: Provider identifier (e.g., "classeviva", "axios")
            provider: Provider instance

        Returns:
            QWidget with provider-specific settings
        """
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)

        # Store UI elements for this provider
        widgets = {}
        self._provider_widgets[provider_id] = widgets

        # =====================
        # Account Section
        # =====================
        account_group = QGroupBox(tr("Account"))
        account_layout = QVBoxLayout(account_group)
        account_layout.setContentsMargins(12, 12, 12, 12)
        account_layout.setSpacing(8)

        # Create input fields dynamically from provider definition
        widgets['credential_fields'] = {}
        for field_def in provider.get_credential_fields():
            field_name = field_def['name']
            field_label = field_def['label']
            field_type = field_def['type']
            field_placeholder = field_def.get('placeholder', '')

            field_layout = QHBoxLayout()
            field_layout.addWidget(QLabel(tr(field_label) + ":"))

            line_edit = QLineEdit()
            line_edit.setPlaceholderText(field_placeholder)
            if field_type == 'password':
                line_edit.setEchoMode(QLineEdit.Password)

            widgets['credential_fields'][field_name] = line_edit
            field_layout.addWidget(line_edit, 1)
            account_layout.addLayout(field_layout)

        # Save credentials checkbox
        save_creds_check = QCheckBox(tr("Save credentials"))
        widgets['save_creds'] = save_creds_check
        account_layout.addWidget(save_creds_check)

        # Auto-login checkbox
        auto_login_check = QCheckBox(tr("Auto-login on app startup"))
        widgets['auto_login'] = auto_login_check
        account_layout.addWidget(auto_login_check)

        # Warning label
        warning_label = QLabel(tr("Credentials stored with basic encoding. Not fully secure."))
        warning_label.setStyleSheet("color: #e67e22; font-size: 11px;")
        warning_label.setWordWrap(True)
        warning_label.setVisible(False)
        widgets['creds_warning'] = warning_label
        account_layout.addWidget(warning_label)

        # Test connection and clear buttons
        btn_layout = QHBoxLayout()
        test_btn = QPushButton(tr("Test Connection"))
        test_btn.setIcon(get_symbolic_icon("network-transmit-receive"))
        test_btn.clicked.connect(lambda: self._test_provider_connection(provider_id))
        widgets['test_btn'] = test_btn
        btn_layout.addWidget(test_btn)

        clear_btn = QPushButton(tr("Clear saved credentials"))
        clear_btn.setIcon(get_symbolic_icon("edit-delete"))
        clear_btn.clicked.connect(lambda: self._clear_provider_credentials(provider_id))
        clear_btn.setEnabled(False)
        widgets['clear_btn'] = clear_btn
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        account_layout.addLayout(btn_layout)

        # Status label
        status_label = QLabel(tr("Not connected"))
        status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        widgets['status_label'] = status_label
        account_layout.addWidget(status_label)

        page_layout.addWidget(account_group)

        # =====================
        # Manual Import Section
        # =====================
        import_group = QGroupBox(tr("Manual Import"))
        import_layout = QVBoxLayout(import_group)
        import_layout.setContentsMargins(12, 12, 12, 12)
        import_layout.setSpacing(8)

        import_btn = QPushButton(tr("Import Grades Now"))
        import_btn.setIcon(get_symbolic_icon("document-import"))
        import_btn.clicked.connect(lambda: self._import_from_provider(provider_id))
        import_btn.setEnabled(False)
        widgets['import_btn'] = import_btn
        import_layout.addWidget(import_btn)

        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        progress_bar.setMaximum(0)  # Indeterminate
        widgets['progress'] = progress_bar
        import_layout.addWidget(progress_bar)

        last_import_label = QLabel(f"{tr('Last import')}: {tr('Never')}")
        last_import_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        widgets['last_import_label'] = last_import_label
        import_layout.addWidget(last_import_label)

        import_status_label = QLabel("")
        widgets['import_status'] = import_status_label
        import_layout.addWidget(import_status_label)

        page_layout.addWidget(import_group)

        # =====================
        # Auto-Sync Section
        # =====================
        auto_sync_group = QGroupBox(tr("Automatic Sync"))
        auto_sync_layout = QVBoxLayout(auto_sync_group)
        auto_sync_layout.setContentsMargins(12, 12, 12, 12)
        auto_sync_layout.setSpacing(8)

        auto_sync_check = QCheckBox(tr("Enable automatic sync"))
        auto_sync_check.stateChanged.connect(lambda state: self._on_provider_auto_sync_toggled(provider_id, state))
        widgets['auto_sync_enabled'] = auto_sync_check
        auto_sync_layout.addWidget(auto_sync_check)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel(tr("Sync interval") + ":"))
        interval_combo = QComboBox()
        interval_combo.addItem(tr("30 minutes"), 30)
        interval_combo.addItem(tr("1 hour"), 60)
        interval_combo.addItem(tr("2 hours"), 120)
        interval_combo.addItem(tr("6 hours"), 360)
        interval_combo.addItem(tr("12 hours"), 720)
        interval_combo.addItem(tr("Daily"), 1440)
        interval_combo.setCurrentIndex(1)  # Default: 1 hour
        interval_combo.currentIndexChanged.connect(lambda idx: self._on_provider_sync_interval_changed(provider_id, idx))
        widgets['sync_interval'] = interval_combo
        interval_layout.addWidget(interval_combo)
        interval_layout.addStretch()
        auto_sync_layout.addLayout(interval_layout)

        notifications_check = QCheckBox(tr("Show notification when new grades are imported"))
        widgets['show_notifications'] = notifications_check
        auto_sync_layout.addWidget(notifications_check)

        auto_sync_status = QLabel(tr("Auto-sync: Disabled"))
        auto_sync_status.setStyleSheet("color: #95a5a6;")
        widgets['auto_sync_status'] = auto_sync_status
        auto_sync_layout.addWidget(auto_sync_status)

        page_layout.addWidget(auto_sync_group)

        # =====================
        # Options Section
        # =====================
        options_group = QGroupBox(tr("Options"))
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_layout.setSpacing(8)

        skip_duplicates_check = QCheckBox(tr("Skip grades already in database"))
        skip_duplicates_check.setChecked(True)
        widgets['skip_duplicates'] = skip_duplicates_check
        options_layout.addWidget(skip_duplicates_check)

        current_year_check = QCheckBox(tr("Only import current school year"))
        current_year_check.setChecked(True)
        widgets['current_year_only'] = current_year_check
        options_layout.addWidget(current_year_check)

        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel(tr("Import from term") + ":"))
        term_combo = QComboBox()
        term_combo.addItem(tr("Both"), 0)
        term_combo.addItem(tr("Term 1"), 1)
        term_combo.addItem(tr("Term 2"), 2)
        widgets['term_filter'] = term_combo
        term_layout.addWidget(term_combo)
        term_layout.addStretch()
        options_layout.addLayout(term_layout)

        page_layout.addWidget(options_group)

        # =====================
        # Subject Mappings Section
        # =====================
        mappings_group = QGroupBox(tr("Subject Mappings"))
        mappings_layout = QVBoxLayout(mappings_group)
        mappings_layout.setContentsMargins(12, 12, 12, 12)
        mappings_layout.setSpacing(8)

        provider_name = provider.get_provider_name()
        mappings_hint = QLabel(tr("View and edit how {provider} subjects are mapped to your VoteTracker subjects.").format(provider=provider_name))
        mappings_hint.setWordWrap(True)
        mappings_hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        mappings_layout.addWidget(mappings_hint)

        manage_mappings_btn = QPushButton(tr("Manage Subject Mappings"))
        manage_mappings_btn.setIcon(get_symbolic_icon("configure"))
        manage_mappings_btn.clicked.connect(lambda: self._manage_provider_subject_mappings(provider_id))
        mappings_layout.addWidget(manage_mappings_btn)

        page_layout.addWidget(mappings_group)

        page_layout.addStretch()
        return page

    def refresh(self):
        """Refresh settings display."""
        # Update years label
        years = self._db.get_school_years()
        active = self._db.get_active_school_year()
        self._years_label.setText(
            f"{tr('School years')}: {len(years)}, {tr('Active')}: {active['name'] if active else '-'}"
        )

        # Update term label
        current_term = self._db.get_current_term()
        self._term_label.setText(f"{tr('Current term')}: {current_term}")

        # Load active provider and set radio button
        active_provider_id = self._db.get_active_provider()
        if not active_provider_id:
            active_provider_id = "none"

        # Set the correct radio button
        if active_provider_id in self._provider_radios:
            self._provider_radios[active_provider_id].setChecked(True)
            page_index = self._provider_pages.get(active_provider_id, 0)
            self._provider_stack.setCurrentIndex(page_index)
            self._active_provider_id = active_provider_id

            # Load provider settings
            if active_provider_id != "none":
                self._load_provider_settings(active_provider_id)
    
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

    def _flash_import_button(self, success: bool):
        """Flash the import button with green (success) or red (failure).

        Args:
            success: True for green flash, False for red flash
        """
        color = "#27ae60" if success else "#e74c3c"  # Green or red

        # Save original style
        original_style = self._cv_import_btn.styleSheet()

        # Apply flash style with border and text color
        flash_style = f"""
            QPushButton {{
                border: 2px solid {color};
                color: {color};
                font-weight: bold;
            }}
        """
        self._cv_import_btn.setStyleSheet(flash_style)

        # Reset to original style after 800ms
        QTimer.singleShot(800, lambda: self._cv_import_btn.setStyleSheet(original_style))

    def _load_cv_credentials(self):
        """Load saved ClasseViva credentials if they exist."""
        username, password = self._db.get_classeviva_credentials()

        # Block signals to prevent triggering handlers during load
        self._cv_save_creds.blockSignals(True)
        self._cv_auto_login.blockSignals(True)

        if username and password:
            self._cv_username.setText(username)
            self._cv_password.setText(password)
            self._cv_save_creds.setChecked(True)
            self._cv_clear_creds_btn.setEnabled(True)
            # Enable auto-login checkbox since credentials are saved
            self._cv_auto_login.setEnabled(True)
            # Load and set auto-login state while signals are blocked
            auto_login = self._db.get_setting("classeviva_auto_login") == "1"
            self._cv_auto_login.setChecked(auto_login)
        else:
            # Disable and uncheck auto-login if no credentials
            self._cv_auto_login.setEnabled(False)
            self._cv_auto_login.setChecked(False)

        self._cv_save_creds.blockSignals(False)
        self._cv_auto_login.blockSignals(False)

    def _on_save_creds_changed(self, state):
        """Handle save credentials checkbox change."""
        # stateChanged signal sends int, need to compare with int value
        is_checked = state == Qt.CheckState.Checked.value
        self._cv_creds_warning.setVisible(is_checked)
        # Auto-login requires saved credentials
        self._cv_auto_login.setEnabled(is_checked)
        if not is_checked:
            # Block signals to avoid overwriting the saved auto-login preference
            self._cv_auto_login.blockSignals(True)
            self._cv_auto_login.setChecked(False)
            self._cv_auto_login.blockSignals(False)

    def _on_auto_login_changed(self, state):
        """Handle auto-login checkbox change."""
        # stateChanged signal sends int, need to compare with int value
        enabled = state == Qt.CheckState.Checked.value
        self._db.set_setting("classeviva_auto_login", "1" if enabled else "0")

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

    def _manage_subject_mappings(self):
        """Open the subject mappings management dialog."""
        dialog = ManageSubjectMappingsDialog(self._db, self)
        dialog.exec()

    def _import_from_classeviva(self):
        """Import grades from ClasseViva."""
        if not self._cv_client.is_authenticated():
            # Try to authenticate first
            username = self._cv_username.text().strip()
            password = self._cv_password.text().strip()

            if not username or not password:
                self._cv_import_status.setText(tr("Invalid credentials"))
                self._cv_import_status.setStyleSheet("color: #e74c3c;")
                self._flash_import_button(False)
                return

            success, message = self._cv_client.login(username, password)
            if not success:
                self._cv_import_status.setText(message)
                self._cv_import_status.setStyleSheet("color: #e74c3c;")
                self._flash_import_button(False)
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
            self._flash_import_button(False)
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

            # Flash button green for success
            self._flash_import_button(True)
        else:
            if skipped_count > 0:
                self._cv_import_status.setText(tr("Skipped {count} duplicates").format(count=skipped_count) + " - " + tr("No votes yet"))
            else:
                self._cv_import_status.setText(tr("No votes yet"))
            self._cv_import_status.setStyleSheet("color: #f39c12;")

    def _on_auto_sync_toggled(self, state):
        """Handle auto-sync checkbox toggle."""
        # stateChanged signal sends int, need to compare with int value
        enabled = state == Qt.CheckState.Checked.value
        self._db.set_auto_sync_enabled(enabled)

        # Get main window to start/stop auto-sync
        main_window = self.window()
        if enabled:
            main_window.start_auto_sync()
            self._cv_auto_sync_status.setText(tr("Auto-sync: Active"))
            self._cv_auto_sync_status.setStyleSheet("color: #27ae60;")
            self._cv_next_sync_label.setVisible(True)
            self._update_next_sync_label()
        else:
            main_window.stop_auto_sync()
            self._cv_auto_sync_status.setText(tr("Auto-sync: Disabled"))
            self._cv_auto_sync_status.setStyleSheet("color: #95a5a6;")
            self._cv_next_sync_label.setVisible(False)

    def _on_sync_interval_changed(self, index):
        """Handle sync interval selection change."""
        minutes = self._cv_sync_interval.currentData()
        self._db.set_sync_interval(minutes)

        # Restart timer if auto-sync is enabled
        main_window = self.window()
        if self._cv_auto_sync_enabled.isChecked():
            main_window.start_auto_sync()
            self._update_next_sync_label()

    def _update_next_sync_label(self):
        """Update the 'next sync in' label."""
        interval = self._db.get_sync_interval()
        self._cv_next_sync_label.setText(f"{tr('Next sync in')}: {interval} {tr('30 minutes').split()[1]}")  # Get 'minutes' word

    # ========================================================================
    # PUBLIC INTERFACE (for MainWindow)
    # ========================================================================

    def enable_classeviva_import(self):
        """Enable the ClasseViva import button (called after successful login)."""
        self._cv_import_btn.setEnabled(True)

    def trigger_classeviva_sync(self):
        """
        Trigger a ClasseViva import operation.
        This is the public interface for auto-sync functionality.
        """
        self._import_from_classeviva()

    # ========================================================================
    # KEYBOARD SHORTCUTS
    # ========================================================================

    # ========================================================================
    # SYNC PROVIDER METHODS (Generic)
    # ========================================================================

    def _on_provider_changed(self, button):
        """Handle provider selection change."""
        # Determine which provider was selected
        selected_provider_id = None
        for provider_id, radio in self._provider_radios.items():
            if radio == button:
                selected_provider_id = provider_id
                break

        if not selected_provider_id:
            return

        # Save active provider to database
        self._db.set_active_provider(selected_provider_id if selected_provider_id != "none" else None)
        self._active_provider_id = selected_provider_id

        # Switch to corresponding page
        page_index = self._provider_pages.get(selected_provider_id, 0)
        self._provider_stack.setCurrentIndex(page_index)

        # Load provider settings if not "none"
        if selected_provider_id != "none" and selected_provider_id in self._provider_widgets:
            self._load_provider_settings(selected_provider_id)

    def _load_provider_settings(self, provider_id: str):
        """Load settings for a provider."""
        widgets = self._provider_widgets.get(provider_id)
        if not widgets:
            return

        provider = self._provider_instances.get(provider_id)
        if not provider:
            return

        # Load credentials
        field_names = [f['name'] for f in provider.get_credential_fields()]
        credentials = self._db.get_provider_credentials(provider_id, field_names)

        for field_name, value in credentials.items():
            if field_name in widgets['credential_fields']:
                widgets['credential_fields'][field_name].setText(value or "")

        # Load save credentials checkbox
        has_creds = self._db.has_provider_credentials(provider_id, field_names)
        widgets['save_creds'].setChecked(has_creds)
        widgets['creds_warning'].setVisible(has_creds)
        widgets['clear_btn'].setEnabled(has_creds)

        # Load auto-login
        auto_login = self._db.get_provider_auto_login(provider_id)
        widgets['auto_login'].setChecked(auto_login)

        # Load last import time
        last_sync = self._db.get_provider_last_sync(provider_id)
        if last_sync:
            widgets['last_import_label'].setText(f"{tr('Last import')}: {last_sync}")
        else:
            widgets['last_import_label'].setText(f"{tr('Last import')}: {tr('Never')}")

        # Load auto-sync settings
        auto_sync_enabled = self._db.get_provider_auto_sync_enabled(provider_id)
        widgets['auto_sync_enabled'].setChecked(auto_sync_enabled)

        interval = self._db.get_provider_sync_interval(provider_id)
        interval_combo = widgets['sync_interval']
        index = interval_combo.findData(interval)
        if index >= 0:
            interval_combo.setCurrentIndex(index)

        # Update status label
        if auto_sync_enabled:
            widgets['auto_sync_status'].setText(tr("Auto-sync: Active"))
            widgets['auto_sync_status'].setStyleSheet("color: #27ae60;")
        else:
            widgets['auto_sync_status'].setText(tr("Auto-sync: Disabled"))
            widgets['auto_sync_status'].setStyleSheet("color: #95a5a6;")

    def _test_provider_connection(self, provider_id: str):
        """Test connection for a provider."""
        widgets = self._provider_widgets.get(provider_id)
        if not widgets:
            return

        provider = self._provider_instances.get(provider_id)
        if not provider:
            return

        # Get credentials from UI
        credentials = {}
        for field_name, line_edit in widgets['credential_fields'].items():
            credentials[field_name] = line_edit.text().strip()

        # Update status
        widgets['status_label'].setText(tr("Connecting..."))
        widgets['status_label'].setStyleSheet("color: #3498db; font-style: italic;")
        widgets['test_btn'].setEnabled(False)

        # Attempt login
        success, message = provider.login(credentials)

        # Update UI
        widgets['test_btn'].setEnabled(True)

        if success:
            widgets['status_label'].setText(f"{tr('Connected as')} {provider.get_user_display_name()}")
            widgets['status_label'].setStyleSheet("color: #27ae60; font-weight: bold;")
            widgets['import_btn'].setEnabled(True)

            # Save credentials if checkbox is checked
            if widgets['save_creds'].isChecked():
                self._db.save_provider_credentials(provider_id, credentials)
                widgets['creds_warning'].setVisible(True)
                widgets['clear_btn'].setEnabled(True)

            # Save auto-login setting
            self._db.set_provider_auto_login(provider_id, widgets['auto_login'].isChecked())
        else:
            # Check if multiple students found
            if message.startswith("MULTIPLE_STUDENTS:"):
                import json
                from ..dialogs import SelectStudentDialog

                # Parse student list
                students_json = message.replace("MULTIPLE_STUDENTS:", "")
                try:
                    students_data = json.loads(students_json)
                    students = [(s["id"], s["name"]) for s in students_data]

                    # Show selection dialog
                    dialog = SelectStudentDialog(students, self)
                    if dialog.exec():
                        selected_student_id = dialog.get_selected_student_id()
                        if selected_student_id:
                            # Retry login with selected student
                            credentials['student_id'] = selected_student_id
                            success, message = provider.login(credentials)

                            if success:
                                widgets['status_label'].setText(f"{tr('Connected as')} {provider.get_user_display_name()}")
                                widgets['status_label'].setStyleSheet("color: #27ae60; font-weight: bold;")
                                widgets['import_btn'].setEnabled(True)

                                # Save credentials if checkbox is checked
                                if widgets['save_creds'].isChecked():
                                    self._db.save_provider_credentials(provider_id, credentials)
                                    widgets['creds_warning'].setVisible(True)
                                    widgets['clear_btn'].setEnabled(True)

                                # Save auto-login setting
                                self._db.set_provider_auto_login(provider_id, widgets['auto_login'].isChecked())
                            else:
                                widgets['status_label'].setText(f"{tr('Authentication failed')}: {message}")
                                widgets['status_label'].setStyleSheet("color: #e74c3c;")
                                widgets['import_btn'].setEnabled(False)
                        else:
                            widgets['status_label'].setText(tr("No student selected"))
                            widgets['status_label'].setStyleSheet("color: #e74c3c;")
                            widgets['import_btn'].setEnabled(False)
                    else:
                        widgets['status_label'].setText(tr("Student selection cancelled"))
                        widgets['status_label'].setStyleSheet("color: #e74c3c;")
                        widgets['import_btn'].setEnabled(False)
                except Exception as e:
                    widgets['status_label'].setText(f"{tr('Error')}: {str(e)}")
                    widgets['status_label'].setStyleSheet("color: #e74c3c;")
                    widgets['import_btn'].setEnabled(False)
            else:
                widgets['status_label'].setText(f"{tr('Authentication failed')}: {message}")
                widgets['status_label'].setStyleSheet("color: #e74c3c;")
                widgets['import_btn'].setEnabled(False)

    def _clear_provider_credentials(self, provider_id: str):
        """Clear saved credentials for a provider."""
        widgets = self._provider_widgets.get(provider_id)
        if not widgets:
            return

        provider = self._provider_instances.get(provider_id)
        if not provider:
            return

        field_names = [f['name'] for f in provider.get_credential_fields()]
        self._db.clear_provider_credentials(provider_id, field_names)

        widgets['creds_warning'].setVisible(False)
        widgets['clear_btn'].setEnabled(False)
        widgets['save_creds'].setChecked(False)

        QMessageBox.information(self, tr("Credentials Cleared"),
                              tr("Saved credentials have been removed."))

    def _import_from_provider(self, provider_id: str):
        """Import grades from a provider."""
        widgets = self._provider_widgets.get(provider_id)
        if not widgets:
            return

        provider = self._provider_instances.get(provider_id)
        if not provider:
            return

        # Check authentication
        if not provider.is_authenticated():
            # Try to authenticate first
            credentials = {}
            for field_name, line_edit in widgets['credential_fields'].items():
                credentials[field_name] = line_edit.text().strip()

            if not all(credentials.values()):
                widgets['import_status'].setText(tr("Invalid credentials"))
                widgets['import_status'].setStyleSheet("color: #e74c3c;")
                return

            success, message = provider.login(credentials)
            if not success:
                widgets['import_status'].setText(message)
                widgets['import_status'].setStyleSheet("color: #e74c3c;")
                return

        # Show progress
        widgets['progress'].setVisible(True)
        widgets['import_btn'].setEnabled(False)
        widgets['import_status'].setText(tr("Fetching grades..."))
        widgets['import_status'].setStyleSheet("color: #3498db;")

        # Fetch grades
        success, grades, message = provider.get_grades()

        if not success:
            widgets['progress'].setVisible(False)
            widgets['import_btn'].setEnabled(True)
            widgets['import_status'].setText(message)
            widgets['import_status'].setStyleSheet("color: #e74c3c;")
            return

        # Apply term filter
        term_filter = widgets['term_filter'].currentData()
        if term_filter > 0:
            grades = [g for g in grades if g.get('term') == term_filter]

        # Apply year filter
        if widgets['current_year_only'].isChecked():
            active_year = self._db.get_active_school_year()
            if active_year:
                # Filter grades by date range (simplified)
                pass  # For now, keep all grades

        widgets['import_status'].setText(f"{tr('Found {count} new grades').format(count=len(grades))}")

        # Get active school year
        active_year = self._db.get_active_school_year()
        if not active_year:
            widgets['progress'].setVisible(False)
            widgets['import_btn'].setEnabled(True)
            widgets['import_status'].setText(tr("No active school year found"))
            widgets['import_status'].setStyleSheet("color: #e74c3c;")
            return

        school_year_id = active_year['id']

        # Get subject mappings
        subject_mappings = self._db.get_all_provider_subject_mappings(provider_id)

        # Check for unmapped subjects
        unmapped_subjects = []
        for grade in grades:
            provider_subject = grade['subject']
            if provider_subject not in subject_mappings:
                if provider_subject not in unmapped_subjects:
                    unmapped_subjects.append(provider_subject)

        # Show mapping dialog if needed
        if unmapped_subjects:
            from ..dialogs import SubjectMappingDialog

            provider_name = provider.get_provider_name()
            dialog = SubjectMappingDialog(unmapped_subjects, provider_id, provider_name, self._db, self)
            if dialog.exec() != QDialog.Accepted:
                widgets['progress'].setVisible(False)
                widgets['import_btn'].setEnabled(True)
                widgets['import_status'].setText(tr("Import cancelled - subjects not mapped"))
                widgets['import_status'].setStyleSheet("color: #95a5a6;")
                return

            # Get updated mappings
            subject_mappings = self._db.get_all_provider_subject_mappings(provider_id)

        # Import grades
        imported_count = 0
        skipped_count = 0
        skip_duplicates = widgets['skip_duplicates'].isChecked()

        for grade in grades:
            try:
                # Map subject
                provider_subject = grade['subject']
                vt_subject = subject_mappings.get(provider_subject, provider_subject)

                # Get or create subject
                subject_id = self._db.get_subject_id(vt_subject)
                if not subject_id:
                    self._db.add_subject(vt_subject)
                    subject_id = self._db.get_subject_id(vt_subject)

                # Get current term if not specified in grade
                term = grade.get('term', self._db.get_current_term())

                # Check for duplicate
                if skip_duplicates:
                    if self._db.vote_exists(vt_subject, grade['grade'], grade['date'], grade['type'], school_year_id):
                        skipped_count += 1
                        continue

                # Add vote
                self._db.add_vote(
                    subject=vt_subject,
                    grade=grade['grade'],
                    vote_type=grade['type'],
                    date=grade['date'],
                    description=grade.get('description', ''),
                    term=term,
                    weight=grade.get('weight', 1.0),
                    school_year_id=school_year_id
                )
                imported_count += 1

            except Exception as e:
                print(f"Error importing grade: {e}")
                continue

        # Hide progress
        widgets['progress'].setVisible(False)
        widgets['import_btn'].setEnabled(True)

        # Show result
        if imported_count > 0:
            status_msg = tr("Imported {imported} grades").format(imported=imported_count)
            if skipped_count > 0:
                status_msg += tr(" ({skipped} skipped)").format(skipped=skipped_count)
            widgets['import_status'].setText(status_msg)
            widgets['import_status'].setStyleSheet("color: #27ae60;")
        else:
            widgets['import_status'].setText(tr("No new grades to import"))
            widgets['import_status'].setStyleSheet("color: #95a5a6;")

        # Update last sync time
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._db.set_provider_last_sync(provider_id, now)
        widgets['last_import_label'].setText(f"{tr('Last import')}: {now}")

        # Emit signal
        self.data_imported.emit()

    def _manage_provider_subject_mappings(self, provider_id: str):
        """Open subject mappings dialog for a provider."""
        provider = self._provider_instances.get(provider_id)
        if not provider:
            return

        provider_name = provider.get_provider_name()
        dialog = ManageSubjectMappingsDialog(self._db, self)
        # TODO: Update ManageSubjectMappingsDialog to accept provider_id
        dialog.exec()

    def _on_provider_auto_sync_toggled(self, provider_id: str, state):
        """Handle auto-sync toggle for a provider."""
        enabled = state == Qt.Checked
        self._db.set_provider_auto_sync_enabled(provider_id, enabled)

        widgets = self._provider_widgets.get(provider_id)
        if widgets:
            if enabled:
                widgets['auto_sync_status'].setText(tr("Auto-sync: Active"))
                widgets['auto_sync_status'].setStyleSheet("color: #27ae60;")
            else:
                widgets['auto_sync_status'].setText(tr("Auto-sync: Disabled"))
                widgets['auto_sync_status'].setStyleSheet("color: #95a5a6;")

    def _on_provider_sync_interval_changed(self, provider_id: str, index):
        """Handle sync interval change for a provider."""
        widgets = self._provider_widgets.get(provider_id)
        if not widgets:
            return

        interval = widgets['sync_interval'].itemData(index)
        self._db.set_provider_sync_interval(provider_id, interval)

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
