"""
Main window for VoteTracker application.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from .database import Database
from .utils import calc_average, get_grade_style
from .widgets import NavButton, YearSelector
from .pages import (
    DashboardPage, VotesPage, SubjectsPage,
    SimulatorPage, ReportCardPage, SettingsPage
)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self._db = Database()
        
        self.setWindowTitle("VoteTracker")
        self.setMinimumSize(1000, 700)
        
        self._setup_ui()
        self._connect_signals()
        self._refresh_all()
    
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
        nav_items = [
            ("go-home", "Dashboard", 0),
            ("view-list-details", "Votes", 1),
            ("folder", "Subjects", 2),
            ("office-chart-line", "Simulator", 3),
            ("x-office-document", "Report", 4),
            ("configure", "Settings", 5),
        ]
        
        for icon_name, label, idx in nav_items:
            btn = NavButton(icon_name, label)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)
        
        sidebar_layout.addStretch()
        
        # Quick stats
        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(4, 8, 4, 4)
        stats_layout.setSpacing(4)
        
        stats_title = QLabel("Quick Stats")
        stats_title.setStyleSheet("font-size: 10px; color: gray;")
        stats_title.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(stats_title)
        
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
        
        year_title = QLabel("School Year")
        year_title.setStyleSheet("font-size: 10px; color: gray;")
        year_title.setAlignment(Qt.AlignCenter)
        year_layout.addWidget(year_title)
        
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
        self._votes_page = VotesPage(self._db)
        self._subjects_page = SubjectsPage(self._db)
        self._simulator_page = SimulatorPage(self._db)
        self._report_card_page = ReportCardPage(self._db)
        self._settings_page = SettingsPage(self._db)
        
        self._stack.addWidget(self._dashboard_page)
        self._stack.addWidget(self._votes_page)
        self._stack.addWidget(self._subjects_page)
        self._stack.addWidget(self._simulator_page)
        self._stack.addWidget(self._report_card_page)
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
            self._report_card_page,
            self._settings_page
        ]
        
        if hasattr(pages[idx], 'refresh'):
            pages[idx].refresh()
    
    def _refresh_all(self):
        """Refresh all data displays."""
        votes = self._db.get_votes()
        avg = calc_average(votes)
        subjects = self._db.get_subjects_with_votes()
        
        failing = sum(
            1 for s in subjects 
            if calc_average(self._db.get_votes(s)) < 6
        )
        
        # Update quick stats
        if votes:
            self._quick_avg.setText(f"Avg: <b>{avg:.1f}</b>")
            self._quick_avg.setStyleSheet(get_grade_style(avg))
        else:
            self._quick_avg.setText("Avg: -")
            self._quick_avg.setStyleSheet("")
        
        self._quick_failing.setText(f"Fail: <b>{failing}</b>")
        color = "#e74c3c" if failing > 0 else "#27ae60"
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

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        # Page navigation with PgUp/PgDown
        if key == Qt.Key_PageDown:
            self._next_page()
            return
        elif key == Qt.Key_PageUp:
            self._prev_page()
            return

        # Direct page access with Ctrl+1-6
        if modifiers == Qt.ControlModifier:
            page_keys = {
                Qt.Key_1: 0,  # Dashboard
                Qt.Key_2: 1,  # Votes
                Qt.Key_3: 2,  # Subjects
                Qt.Key_4: 3,  # Simulator
                Qt.Key_5: 4,  # Report Card
                Qt.Key_6: 5,  # Settings
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
