"""
Dashboard page for VoteTracker.
Shows overview statistics and subject cards.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Qt

from ..database import Database
from ..utils import calc_average, get_grade_style
from ..widgets import DashboardSubjectCard


class DashboardPage(QWidget):
    """Dashboard page with statistics overview."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._current_term = None  # None = all terms
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # Stats group
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setContentsMargins(16, 16, 16, 16)
        stats_layout.setSpacing(24)
        
        self._avg_box = self._create_stat_box("Overall Average", "-")
        self._votes_box = self._create_stat_box("Total Votes", "0")
        self._subjects_box = self._create_stat_box("Subjects", "0")
        self._failing_box = self._create_stat_box("Failing", "0")
        
        stats_layout.addLayout(self._avg_box)
        stats_layout.addLayout(self._votes_box)
        stats_layout.addLayout(self._subjects_box)
        stats_layout.addLayout(self._failing_box)
        stats_layout.addStretch()
        
        layout.addWidget(stats_group)
        
        # Subjects overview
        overview_group = QGroupBox("Subjects Overview")
        overview_layout = QVBoxLayout(overview_group)
        overview_layout.setContentsMargins(12, 12, 12, 12)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        self._subjects_grid = QGridLayout(scroll_widget)
        self._subjects_grid.setContentsMargins(4, 4, 4, 4)
        self._subjects_grid.setSpacing(12)
        self._subjects_grid.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        overview_layout.addWidget(scroll)
        
        layout.addWidget(overview_group, 1)
    
    def _create_stat_box(self, label: str, value: str) -> QVBoxLayout:
        """Create a statistics display box."""
        box = QVBoxLayout()
        box.setSpacing(4)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: gray; font-size: 12px;")
        
        value_widget = QLabel(value)
        value_widget.setObjectName(f"stat_{label.replace(' ', '_').lower()}")
        value_widget.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        box.addWidget(label_widget)
        box.addWidget(value_widget)
        
        return box
    
    def set_term_filter(self, term: int = None):
        """Set term filter (None for all terms)."""
        self._current_term = term
    
    def refresh(self):
        """Refresh all dashboard data."""
        votes = self._db.get_votes(term=self._current_term)
        subjects_with_votes = self._db.get_subjects_with_votes(term=self._current_term)
        
        avg = calc_average(votes)
        failing = sum(
            1 for s in subjects_with_votes 
            if calc_average(self._db.get_votes(s, term=self._current_term)) < 6
        )
        
        # Update stats
        avg_label = self.findChild(QLabel, "stat_overall_average")
        if avg_label:
            avg_label.setText(f"<b>{avg:.2f}</b>" if votes else "-")
            if votes:
                avg_label.setStyleSheet(get_grade_style(avg) + "font-size: 24px;")
        
        votes_label = self.findChild(QLabel, "stat_total_votes")
        if votes_label:
            votes_label.setText(str(len(votes)))
        
        subjects_label = self.findChild(QLabel, "stat_subjects")
        if subjects_label:
            subjects_label.setText(str(len(subjects_with_votes)))
        
        failing_label = self.findChild(QLabel, "stat_failing")
        if failing_label:
            failing_label.setText(f"<b>{failing}</b>")
            color = "#e74c3c" if failing > 0 else "#27ae60"
            failing_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        
        # Clear subjects grid
        while self._subjects_grid.count():
            item = self._subjects_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not subjects_with_votes:
            empty = QLabel("No votes recorded yet")
            empty.setStyleSheet("color: gray; font-weight: bold; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self._subjects_grid.addWidget(empty, 0, 0, 1, 3)
            return
        
        col = 0
        row = 0
        for subject in sorted(subjects_with_votes):
            subject_votes = self._db.get_votes(subject, term=self._current_term)
            avg_s = calc_average(subject_votes)
            written_votes = [v for v in subject_votes if v.get("type") == "Written"]
            oral_votes = [v for v in subject_votes if v.get("type") == "Oral"]
            written_avg = calc_average(written_votes)
            oral_avg = calc_average(oral_votes)
            
            card = DashboardSubjectCard(
                subject, avg_s, written_avg, oral_avg, len(subject_votes)
            )
            self._subjects_grid.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
