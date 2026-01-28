"""
Main window for VoteTracker application.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent

from .database import Database
from .undo import UndoManager
from .utils import calc_average, get_grade_style, get_symbolic_icon
from .widgets import NavButton, YearSelector
from .pages import (
    DashboardPage, VotesPage, SubjectsPage,
    SimulatorPage, CalendarPage, ReportCardPage, StatisticsPage, SettingsPage
)
from .dialogs import ShortcutsHelpDialog, OnboardingWizard
from .i18n import init_language, tr
from .classeviva import ClasseVivaClient


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._db = Database()
        self._undo_manager = UndoManager(self._db)
        self._undo_manager.state_changed.connect(self._on_undo_state_changed)

        # Initialize ClasseViva client
        self._cv_client = ClasseVivaClient()
        self._auto_sync_timer = None

        # Initialize language from db or system
        init_language(self._db)

        self.setWindowTitle("VoteTracker")
        self.setMinimumSize(1000, 700)

        self._setup_ui()
        self._connect_signals()
        self._check_onboarding()
        self._refresh_all()
        self._auto_login_classeviva()
        self._start_auto_sync_if_enabled()
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(96)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)
        sidebar_layout.setAlignment(Qt.AlignTop)
        
        # Navigation buttons
        self._nav_buttons = []
        self._nav_keys = [
            ("go-home", "Dashboard"),
            ("view-list-details", "Votes"),
            ("bookmarks", "Subjects"),
            ("office-chart-line", "Simulator"),
            ("view-calendar", "Calendar"),
            ("office-report", "Report"),
            ("view-statistics", "Statistics"),
            ("configure", "Settings"),
        ]

        for idx, (icon_name, label_key) in enumerate(self._nav_keys):
            btn = NavButton(icon_name, tr(label_key))
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)
        
        sidebar_layout.addStretch()
        
        # Quick stats
        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(4, 8, 4, 4)
        stats_layout.setSpacing(4)

        self._stats_title = QLabel(tr("Quick Stats"))
        self._stats_title.setStyleSheet("font-size: 10px; color: gray;")
        self._stats_title.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self._stats_title)
        
        self._quick_avg = QLabel("Avg: -")
        self._quick_avg.setAlignment(Qt.AlignCenter)
        self._quick_failing = QLabel("Fail: 0")
        self._quick_failing.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self._quick_avg)
        stats_layout.addWidget(self._quick_failing)
        
        sidebar_layout.addWidget(stats_frame)
        
        # Year selector
        year_frame = QFrame()
        year_layout = QVBoxLayout(year_frame)
        year_layout.setContentsMargins(4, 8, 4, 4)
        year_layout.setSpacing(4)

        self._year_title = QLabel(tr("School Year"))
        self._year_title.setStyleSheet("font-size: 10px; color: gray;")
        self._year_title.setAlignment(Qt.AlignCenter)
        year_layout.addWidget(self._year_title)
        
        self._year_selector = YearSelector()
        self._year_selector.year_changed.connect(self._on_year_changed)
        year_layout.addWidget(self._year_selector)

        sidebar_layout.addWidget(year_frame)

        main_layout.addWidget(sidebar)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(sep)
        
        # Content stack
        self._stack = QStackedWidget()
        
        self._dashboard_page = DashboardPage(self._db)
        self._votes_page = VotesPage(self._db, self._undo_manager)
        self._subjects_page = SubjectsPage(self._db)
        self._simulator_page = SimulatorPage(self._db)
        self._calendar_page = CalendarPage(self._db)
        self._report_card_page = ReportCardPage(self._db)
        self._statistics_page = StatisticsPage(self._db)
        self._settings_page = SettingsPage(self._db)

        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._votes_page)
        self._stack.addWidget(self._subjects_page)
        self._stack.addWidget(self._simulator_page)
        self._stack.addWidget(self._calendar_page)
        self._stack.addWidget(self._report_card_page)
        self._stack.addWidget(self._statistics_page)
        self._stack.addWidget(self._settings_page)
        
        main_layout.addWidget(self._stack, 1)
        
        # Initialize year selector
        self._update_year_selector()
        
        # Start on dashboard
        self._switch_page(0)
    
    def _connect_signals(self):
        """Connect page signals."""
        self._votes_page.vote_changed.connect(self._refresh_all)
        self._subjects_page.subject_changed.connect(self._refresh_all)
        self._settings_page.data_imported.connect(self._refresh_all)
        self._settings_page.school_year_changed.connect(self._on_school_year_changed)
        self._settings_page.language_changed.connect(self._on_language_changed)

    def _check_onboarding(self):
        """Show onboarding wizard if first run."""
        if self._db.get_setting("onboarding_complete") != "1":
            wizard = OnboardingWizard(self._db, self)
            wizard.exec()
            self._refresh_all()

    def _auto_login_classeviva(self):
        """Auto-login to ClasseViva if enabled."""
        # Check if auto-login is enabled
        if self._db.get_setting("classeviva_auto_login") != "1":
            return

        # Get saved credentials
        username, password = self._db.get_classeviva_credentials()
        if not username or not password:
            return

        # Attempt login
        success, message = self._cv_client.login(username, password)
        if success:
            # Enable import button in settings page
            self._settings_page._cv_import_btn.setEnabled(True)

    def _start_auto_sync_if_enabled(self):
        """Start auto-sync timer if enabled in settings."""
        if self._db.get_auto_sync_enabled():
            self.start_auto_sync()

    def start_auto_sync(self):
        """Start the auto-sync timer."""
        if self._auto_sync_timer is None:
            self._auto_sync_timer = QTimer(self)
            self._auto_sync_timer.timeout.connect(self._auto_sync_tick)

        # Stop if already running to avoid duplicate timers
        if self._auto_sync_timer.isActive():
            self._auto_sync_timer.stop()

        interval = self._db.get_sync_interval()
        self._auto_sync_timer.start(interval * 60 * 1000)  # Convert minutes to ms

    def stop_auto_sync(self):
        """Stop the auto-sync timer."""
        if self._auto_sync_timer:
            self._auto_sync_timer.stop()

    def _auto_sync_tick(self):
        """Perform automatic sync."""
        # Call the settings page import method which handles everything
        self._settings_page._import_from_classeviva()
    
    def _switch_page(self, index: int):
        """Switch to a page by index."""
        self._stack.setCurrentIndex(index)

        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

        self._refresh_current_page()
    
    def _refresh_current_page(self):
        """Refresh the currently visible page."""
        idx = self._stack.currentIndex()
        pages = [
            self._dashboard_page,
            self._votes_page,
            self._subjects_page,
            self._simulator_page,
            self._calendar_page,
            self._report_card_page,
            self._statistics_page,
            self._settings_page
        ]

        if hasattr(pages[idx], 'refresh'):
            pages[idx].refresh()
    
    def _refresh_all(self):
        """Refresh all data displays using optimized single-query approach."""
        # Single database query instead of N+2 queries
        stats = self._db.get_grade_statistics()

        # Update quick stats
        if stats['total_votes'] > 0:
            self._quick_avg.setText(f"Avg: <b>{stats['overall_avg']:.1f}</b>")
            self._quick_avg.setStyleSheet(get_grade_style(stats['overall_avg']))
        else:
            self._quick_avg.setText("Avg: -")
            self._quick_avg.setStyleSheet("")

        self._quick_failing.setText(f"Fail: <b>{stats['failing_count']}</b>")
        color = "#e74c3c" if stats['failing_count'] > 0 else "#27ae60"
        self._quick_failing.setStyleSheet(f"color: {color};")
        
        self._refresh_current_page()
    
    def _update_year_selector(self):
        """Update the year selector with available years."""
        years = self._db.get_school_years()
        active = self._db.get_active_school_year()
        active_id = active["id"] if active else None
        self._year_selector.set_years(years, active_id)
    
    def _on_year_changed(self, year_id: int):
        """Handle school year change."""
        self._db.set_active_school_year(year_id)
        self._refresh_all()
    
    def _on_school_year_changed(self):
        """Handle school year list change."""
        self._update_year_selector()
        self._refresh_all()

    def _on_language_changed(self):
        """Handle language change - update all UI text."""
        # Update navigation buttons
        for btn, (_, label_key) in zip(self._nav_buttons, self._nav_keys):
            btn.set_label(tr(label_key))

        # Update sidebar titles
        self._stats_title.setText(tr("Quick Stats"))
        self._year_title.setText(tr("School Year"))

        # Refresh all pages to update their text
        self._refresh_all()

    def _next_page(self):
        """Switch to next page (wraps around)."""
        current = self._stack.currentIndex()
        next_idx = (current + 1) % self._stack.count()
        self._switch_page(next_idx)

    def _prev_page(self):
        """Switch to previous page (wraps around)."""
        current = self._stack.currentIndex()
        prev_idx = (current - 1) % self._stack.count()
        self._switch_page(prev_idx)

    def _on_undo_state_changed(self):
        """Handle undo/redo state changes."""
        # Could update UI elements here if needed
        pass

    def _undo(self):
        """Perform undo operation."""
        if self._undo_manager.undo():
            self._refresh_all()

    def _redo(self):
        """Perform redo operation."""
        if self._undo_manager.redo():
            self._refresh_all()

    def _show_shortcuts_help(self):
        """Show keyboard shortcuts help dialog."""
        dialog = ShortcutsHelpDialog(self)
        dialog.exec()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        # Help: ? (show shortcuts)
        if key == Qt.Key_Question:
            self._show_shortcuts_help()
            return

        # Undo: Ctrl+Z
        if modifiers == Qt.ControlModifier and key == Qt.Key_Z:
            self._undo()
            return

        # Redo: Ctrl+Shift+Z or Ctrl+Y
        if key == Qt.Key_Z and modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            self._redo()
            return
        if modifiers == Qt.ControlModifier and key == Qt.Key_Y:
            self._redo()
            return

        # Page navigation with PgUp/PgDown
        if key == Qt.Key_PageDown:
            self._next_page()
            return
        elif key == Qt.Key_PageUp:
            self._prev_page()
            return

        # Direct page access with Ctrl+1-8
        if modifiers == Qt.ControlModifier:
            page_keys = {
                Qt.Key_1: 0,  # Dashboard
                Qt.Key_2: 1,  # Votes
                Qt.Key_3: 2,  # Subjects
                Qt.Key_4: 3,  # Simulator
                Qt.Key_5: 4,  # Calendar
                Qt.Key_6: 5,  # Report Card
                Qt.Key_7: 6,  # Statistics
                Qt.Key_8: 7,  # Settings
            }
            if key in page_keys:
                self._switch_page(page_keys[key])
                return

        # Delegate to current page if it has key handling
        current_page = self._stack.currentWidget()
        if hasattr(current_page, 'handle_key'):
            if current_page.handle_key(event):
                return

        super().keyPressEvent(event)
