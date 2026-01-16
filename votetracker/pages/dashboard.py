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
from ..i18n import tr


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
        self._title = QLabel(tr("Dashboard"))
        self._title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self._title)

        # Stats group
        self._stats_group = QGroupBox(tr("Statistics"))
        stats_layout = QHBoxLayout(self._stats_group)
        stats_layout.setContentsMargins(16, 16, 16, 16)
        stats_layout.setSpacing(24)

        # Store stat box tuples: (layout, label_widget, value_widget, key)
        self._stat_boxes = {}
        for key in ["Overall Average", "Total Votes", "Subjects", "Failing"]:
            box_layout, label_w, value_w = self._create_stat_box(tr(key), "-" if key == "Overall Average" else "0")
            self._stat_boxes[key] = (label_w, value_w)
            stats_layout.addLayout(box_layout)

        stats_layout.addStretch()
        layout.addWidget(self._stats_group)

        # Subjects overview
        self._overview_group = QGroupBox(tr("Subjects Overview"))
        overview_layout = QVBoxLayout(self._overview_group)
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

        layout.addWidget(self._overview_group, 1)
    
    def _create_stat_box(self, label: str, value: str):
        """Create a statistics display box. Returns (layout, label_widget, value_widget)."""
        box = QVBoxLayout()
        box.setSpacing(4)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: gray; font-size: 12px;")

        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 24px; font-weight: bold;")

        box.addWidget(label_widget)
        box.addWidget(value_widget)

        return box, label_widget, value_widget
    
    def set_term_filter(self, term: int = None):
        """Set term filter (None for all terms)."""
        self._current_term = term
    
    def refresh(self):
        """Refresh all dashboard data."""
        # Update labels for language changes
        self._title.setText(tr("Dashboard"))
        self._stats_group.setTitle(tr("Statistics"))
        self._overview_group.setTitle(tr("Subjects Overview"))
        for key, (label_w, _) in self._stat_boxes.items():
            label_w.setText(tr(key))

        votes = self._db.get_votes(term=self._current_term)
        subjects_with_votes = self._db.get_subjects_with_votes(term=self._current_term)

        avg = calc_average(votes)
        failing = sum(
            1 for s in subjects_with_votes
            if calc_average(self._db.get_votes(s, term=self._current_term)) < 6
        )

        # Update stats values
        _, avg_val = self._stat_boxes["Overall Average"]
        avg_val.setText(f"<b>{avg:.2f}</b>" if votes else "-")
        if votes:
            avg_val.setStyleSheet(get_grade_style(avg) + "font-size: 24px;")

        _, votes_val = self._stat_boxes["Total Votes"]
        votes_val.setText(str(len(votes)))

        _, subjects_val = self._stat_boxes["Subjects"]
        subjects_val.setText(str(len(subjects_with_votes)))

        _, failing_val = self._stat_boxes["Failing"]
        failing_val.setText(f"<b>{failing}</b>")
        color = "#e74c3c" if failing > 0 else "#27ae60"
        failing_val.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        
        # Clear subjects grid
        while self._subjects_grid.count():
            item = self._subjects_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not subjects_with_votes:
            empty = QLabel(tr("No votes recorded yet"))
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
