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

        # Top section: Statistics (left) and Recent Grades (right)
        top_section = QHBoxLayout()
        top_section.setSpacing(12)

        # Stats group (left side, narrower)
        self._stats_group = QGroupBox(tr("Statistics"))
        stats_layout = QVBoxLayout(self._stats_group)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        stats_layout.setSpacing(12)

        # Store stat box tuples: (layout, label_widget, value_widget, key)
        self._stat_boxes = {}
        for key in ["Overall Average", "Total Votes", "Subjects", "Failing"]:
            box_layout, label_w, value_w = self._create_stat_box(tr(key), "-" if key == "Overall Average" else "0")
            self._stat_boxes[key] = (label_w, value_w)
            stats_layout.addLayout(box_layout)

        stats_layout.addStretch()
        top_section.addWidget(self._stats_group, 1)  # Smaller proportion

        # Recent grades widget (right side, wider)
        self._recent_group = QGroupBox(tr("Recent Grades"))
        recent_layout = QVBoxLayout(self._recent_group)
        recent_layout.setContentsMargins(12, 12, 12, 12)
        recent_layout.setSpacing(6)

        # Container for recent grades list
        self._recent_container = QVBoxLayout()
        self._recent_container.setSpacing(4)
        recent_layout.addLayout(self._recent_container)

        top_section.addWidget(self._recent_group, 2)  # Larger proportion (2x stats)

        layout.addLayout(top_section)

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

    def _update_recent_grades(self, votes: list):
        """Update the recent grades widget with latest grades."""
        # Clear existing items
        while self._recent_container.count():
            item = self._recent_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not votes:
            empty = QLabel(tr("No votes recorded yet"))
            empty.setStyleSheet("color: gray; padding: 20px;")
            empty.setAlignment(Qt.AlignCenter)
            self._recent_container.addWidget(empty)
            return

        # Sort votes by date (most recent first)
        sorted_votes = sorted(votes, key=lambda v: v.get('date', ''), reverse=True)

        # Show last 5 grades (to save space)
        recent_votes = sorted_votes[:5]

        for vote in recent_votes:
            item = self._create_recent_grade_item(vote)
            self._recent_container.addWidget(item)

        # Add stretch at the end
        self._recent_container.addStretch()

    def _create_recent_grade_item(self, vote: dict) -> QWidget:
        """Create a widget for a single recent grade item."""
        item = QFrame()
        item.setFrameShape(QFrame.StyledPanel)
        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(8, 6, 8, 6)
        item_layout.setSpacing(12)

        # Subject name
        subject_label = QLabel(vote.get('subject', ''))
        subject_label.setStyleSheet("font-weight: bold;")
        subject_label.setMinimumWidth(120)
        item_layout.addWidget(subject_label)

        # Grade value
        grade = vote.get('grade', 0)
        grade_label = QLabel(f"{grade:.2f}" if grade > 0 else "+/-")
        grade_label.setStyleSheet(get_grade_style(grade) + "font-weight: bold; font-size: 16px;")
        grade_label.setFixedWidth(50)
        grade_label.setAlignment(Qt.AlignCenter)
        item_layout.addWidget(grade_label)

        # Vote type
        vote_type = vote.get('type', '')
        type_label = QLabel(tr(vote_type) if vote_type else "-")
        type_label.setStyleSheet("color: gray;")
        type_label.setFixedWidth(80)
        item_layout.addWidget(type_label)

        # Date
        date_str = vote.get('date', '')
        if date_str:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except:
                formatted_date = date_str
        else:
            formatted_date = "-"

        date_label = QLabel(formatted_date)
        date_label.setStyleSheet("color: gray; font-size: 11px;")
        date_label.setFixedWidth(80)
        item_layout.addWidget(date_label)

        # Description (if any)
        description = vote.get('description', '')
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: gray; font-style: italic; font-size: 11px;")
            desc_label.setWordWrap(False)
            item_layout.addWidget(desc_label, 1)
        else:
            item_layout.addStretch(1)

        return item

    def set_term_filter(self, term: int = None):
        """Set term filter (None for all terms)."""
        self._current_term = term
    
    def refresh(self):
        """Refresh all dashboard data."""
        # Update labels for language changes
        self._title.setText(tr("Dashboard"))
        self._stats_group.setTitle(tr("Statistics"))
        self._recent_group.setTitle(tr("Recent Grades"))
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

        # Update recent grades
        self._update_recent_grades(votes)

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
