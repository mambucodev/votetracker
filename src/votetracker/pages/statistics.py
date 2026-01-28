"""
Statistics page for VoteTracker.
Shows detailed analytics and grade distributions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from ..database import Database
from ..utils import calc_average, get_status_color
from ..widgets import TermToggle
from ..i18n import tr
from ..enhanced_charts import InteractiveBarChart, InteractiveDistributionChart, GradeTrendChart


class BarChart(QFrame):
    """Simple horizontal bar chart widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (label, value, max_value, color)
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

    def set_data(self, data: list):
        """Set chart data. Each item: (label, value, color)"""
        self._data = data
        self._update_chart()

    def _update_chart(self):
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._data:
            empty = QLabel("No data")
            empty.setStyleSheet("color: gray;")
            self._layout.addWidget(empty)
            return

        max_val = max(d[1] for d in self._data) if self._data else 1
        if max_val == 0:
            max_val = 1

        for label, value, color in self._data:
            row = QHBoxLayout()
            row.setSpacing(8)

            # Label
            lbl = QLabel(label)
            lbl.setFixedWidth(120)
            lbl.setStyleSheet("font-size: 11px;")
            row.addWidget(lbl)

            # Bar container
            bar_container = QFrame()
            bar_container.setFixedHeight(20)
            bar_container.setStyleSheet("background: #f0f0f0; border-radius: 4px;")
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            bar_layout.setSpacing(0)

            # Bar fill
            width_percent = (value / max_val) * 100 if max_val > 0 else 0
            bar = QFrame()
            bar.setStyleSheet(f"background: {color}; border-radius: 4px;")
            bar_layout.addWidget(bar, int(width_percent))
            bar_layout.addStretch(int(100 - width_percent))

            row.addWidget(bar_container, 1)

            # Value
            val_lbl = QLabel(f"{value:.1f}" if isinstance(value, float) else str(value))
            val_lbl.setFixedWidth(50)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_lbl.setStyleSheet("font-weight: bold;")
            row.addWidget(val_lbl)

            container = QWidget()
            container.setLayout(row)
            self._layout.addWidget(container)


class DistributionChart(QFrame):
    """Grade distribution histogram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}  # {range_label: count}
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignBottom)

    def set_data(self, grades: list):
        """Set distribution data from list of grades."""
        # Define ranges (grades below 2 don't exist in Italian schools)
        ranges = [
            ("2-3", 2, 4, "#c0392b"),
            ("4-5", 4, 5.5, "#e74c3c"),
            ("5.5-6", 5.5, 6, "#f39c12"),
            ("6-7", 6, 7, "#27ae60"),
            ("7-8", 7, 8, "#2ecc71"),
            ("8-9", 8, 9, "#3498db"),
            ("9-10", 9, 10.01, "#9b59b6"),
        ]

        self._data = {}
        for label, low, high, color in ranges:
            count = sum(1 for g in grades if low <= g < high)
            self._data[label] = (count, color)

        self._update_chart()

    def _update_chart(self):
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._data:
            return

        max_count = max(c for c, _ in self._data.values()) if self._data else 1
        if max_count == 0:
            max_count = 1

        for label, (count, color) in self._data.items():
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignBottom)

            # Count label
            count_lbl = QLabel(str(count))
            count_lbl.setAlignment(Qt.AlignCenter)
            count_lbl.setStyleSheet("font-size: 10px; font-weight: bold;")
            col.addWidget(count_lbl)

            # Bar
            height = int((count / max_count) * 100) if max_count > 0 else 0
            bar = QFrame()
            bar.setFixedWidth(30)
            bar.setFixedHeight(max(height, 5))
            bar.setStyleSheet(f"background: {color}; border-radius: 4px;")
            col.addWidget(bar, 0, Qt.AlignCenter)

            # Range label
            range_lbl = QLabel(label)
            range_lbl.setAlignment(Qt.AlignCenter)
            range_lbl.setStyleSheet("font-size: 10px;")
            col.addWidget(range_lbl)

            container = QWidget()
            container.setLayout(col)
            self._layout.addWidget(container)


class StatisticsPage(QWidget):
    """Statistics page with analytics and charts."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._current_term = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        self._title = QLabel(tr("Statistics"))
        self._title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(self._title)
        header.addStretch()

        # Term toggle
        self._term_toggle = TermToggle(self._db.get_current_term())
        self._term_toggle.term_changed.connect(self._on_term_changed)
        header.addWidget(self._term_toggle)

        layout.addLayout(header)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # Summary stats
        self._summary_group = QGroupBox(tr("Summary"))
        summary_layout = QGridLayout(self._summary_group)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(16)

        self._stat_labels = {}
        self._stat_label_widgets = {}
        stats = [
            ("total_grades", "Total Grades"),
            ("overall_avg", "Overall Average"),
            ("highest_grade", "Highest Grade"),
            ("lowest_grade", "Lowest Grade"),
            ("passing_count", "Passing (>=6)"),
            ("failing_count", "Failing (<6)"),
            ("written_avg", "Written Avg"),
            ("oral_avg", "Oral Avg"),
        ]

        for i, (key, label_key) in enumerate(stats):
            row, col = divmod(i, 4)
            box, label_widget, value_label = self._create_stat_box(tr(label_key))
            self._stat_labels[key] = value_label
            self._stat_label_widgets[key] = (label_key, label_widget)
            summary_layout.addLayout(box, row, col)

        scroll_layout.addWidget(self._summary_group)

        # Distribution chart
        self._dist_group = QGroupBox(tr("Grade Distribution"))
        dist_layout = QVBoxLayout(self._dist_group)
        dist_layout.setContentsMargins(16, 16, 16, 16)
        self._distribution_chart = InteractiveDistributionChart()
        self._distribution_chart.setMinimumHeight(200)
        dist_layout.addWidget(self._distribution_chart)
        scroll_layout.addWidget(self._dist_group)

        # Grade trend over time
        self._trend_group = QGroupBox(tr("Grade Trend Over Time"))
        trend_layout = QVBoxLayout(self._trend_group)
        trend_layout.setContentsMargins(16, 16, 16, 16)
        self._trend_chart = GradeTrendChart()
        self._trend_chart.setMinimumHeight(250)
        trend_layout.addWidget(self._trend_chart)
        scroll_layout.addWidget(self._trend_group)

        # Subject comparison
        self._subjects_group = QGroupBox(tr("Subject Averages"))
        subjects_layout = QVBoxLayout(self._subjects_group)
        subjects_layout.setContentsMargins(16, 16, 16, 16)
        self._subjects_chart = InteractiveBarChart()
        self._subjects_chart.setMinimumHeight(250)
        subjects_layout.addWidget(self._subjects_chart)
        scroll_layout.addWidget(self._subjects_group)

        # Best/Worst subjects
        extremes_layout = QHBoxLayout()

        self._best_group = QGroupBox(tr("Best Subjects"))
        best_layout = QVBoxLayout(self._best_group)
        best_layout.setContentsMargins(12, 12, 12, 12)
        self._best_list = QVBoxLayout()
        self._best_list.setSpacing(4)
        best_layout.addLayout(self._best_list)
        extremes_layout.addWidget(self._best_group)

        self._worst_group = QGroupBox(tr("Subjects to Improve"))
        worst_layout = QVBoxLayout(self._worst_group)
        worst_layout.setContentsMargins(12, 12, 12, 12)
        self._worst_list = QVBoxLayout()
        self._worst_list.setSpacing(4)
        worst_layout.addLayout(self._worst_list)
        extremes_layout.addWidget(self._worst_group)

        scroll_layout.addLayout(extremes_layout)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

    def _create_stat_box(self, label: str) -> tuple:
        """Create a statistics display box. Returns (layout, label_widget, value_widget)."""
        box = QVBoxLayout()
        box.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: gray; font-size: 11px;")

        value_widget = QLabel("-")
        value_widget.setStyleSheet("font-size: 18px; font-weight: bold;")

        box.addWidget(label_widget)
        box.addWidget(value_widget)

        return box, label_widget, value_widget

    def _on_term_changed(self, term: int):
        """Handle term toggle change."""
        self._current_term = term
        self._db.set_current_term(term)
        self.refresh()

    def refresh(self):
        """Refresh all statistics."""
        # Update labels for language changes
        self._title.setText(tr("Statistics"))
        self._summary_group.setTitle(tr("Summary"))
        self._dist_group.setTitle(tr("Grade Distribution"))
        self._trend_group.setTitle(tr("Grade Trend Over Time"))
        self._subjects_group.setTitle(tr("Subject Averages"))
        self._best_group.setTitle(tr("Best Subjects"))
        self._worst_group.setTitle(tr("Subjects to Improve"))
        for key, (label_key, label_widget) in self._stat_label_widgets.items():
            label_widget.setText(tr(label_key))

        self._term_toggle.set_term(self._db.get_current_term())
        self._current_term = self._term_toggle.get_term()

        votes = self._db.get_votes(term=self._current_term)
        grades = [v.get("grade", 0) for v in votes]

        # Summary stats
        self._stat_labels["total_grades"].setText(str(len(grades)))

        if grades:
            avg = calc_average(votes)
            self._stat_labels["overall_avg"].setText(f"{avg:.2f}")
            self._stat_labels["overall_avg"].setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {get_status_color(avg).name()};"
            )

            self._stat_labels["highest_grade"].setText(f"{max(grades):.2f}")
            self._stat_labels["lowest_grade"].setText(f"{min(grades):.2f}")

            passing = sum(1 for g in grades if g >= 6)
            failing = sum(1 for g in grades if g < 6)
            self._stat_labels["passing_count"].setText(str(passing))
            self._stat_labels["passing_count"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #27ae60;"
            )
            self._stat_labels["failing_count"].setText(str(failing))
            self._stat_labels["failing_count"].setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {'#e74c3c' if failing > 0 else '#27ae60'};"
            )

            written = [v for v in votes if v.get("type") == "Written"]
            oral = [v for v in votes if v.get("type") == "Oral"]
            w_avg = calc_average(written)
            o_avg = calc_average(oral)
            self._stat_labels["written_avg"].setText(f"{w_avg:.2f}" if written else "-")
            self._stat_labels["oral_avg"].setText(f"{o_avg:.2f}" if oral else "-")
        else:
            for key in self._stat_labels:
                self._stat_labels[key].setText("-")
                self._stat_labels[key].setStyleSheet("font-size: 18px; font-weight: bold;")

        # Distribution chart
        self._distribution_chart.set_data(grades)

        # Trend chart
        self._trend_chart.set_data(votes)

        # Subject averages chart
        subjects = self._db.get_subjects_with_votes(term=self._current_term)
        subject_data = []
        for subj in subjects:
            subj_votes = self._db.get_votes(subject=subj, term=self._current_term)
            avg = calc_average(subj_votes)
            color = get_status_color(avg).name()

            # Calculate detailed stats for tooltip
            vote_count = len(subj_votes)
            written_votes = [v for v in subj_votes if v.get("type") == "Written"]
            oral_votes = [v for v in subj_votes if v.get("type") == "Oral"]
            practical_votes = [v for v in subj_votes if v.get("type") == "Practical"]

            w_avg = calc_average(written_votes) if written_votes else 0
            o_avg = calc_average(oral_votes) if oral_votes else 0
            p_avg = calc_average(practical_votes) if practical_votes else 0

            detail_parts = [f"Total grades: {vote_count}"]
            if written_votes:
                detail_parts.append(f"Written: {w_avg:.2f} ({len(written_votes)} grades)")
            if oral_votes:
                detail_parts.append(f"Oral: {o_avg:.2f} ({len(oral_votes)} grades)")
            if practical_votes:
                detail_parts.append(f"Practical: {p_avg:.2f} ({len(practical_votes)} grades)")

            detail = "<br>".join(detail_parts)
            subject_data.append((subj, avg, color, detail))

        # Sort by average descending
        subject_data.sort(key=lambda x: x[1], reverse=True)
        self._subjects_chart.set_data(subject_data)

        # Best/Worst subjects
        self._update_extremes_list(self._best_list, subject_data[:3], is_best=True)
        self._update_extremes_list(self._worst_list, subject_data[-3:][::-1], is_best=False)

    def _update_extremes_list(self, layout: QVBoxLayout, subjects: list, is_best: bool):
        """Update best/worst subjects list."""
        # Clear existing
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not subjects:
            empty = QLabel(tr("No data"))
            empty.setStyleSheet("color: gray;")
            layout.addWidget(empty)
            return

        for i, (name, avg, color) in enumerate(subjects):
            row = QHBoxLayout()
            rank = QLabel(f"#{i + 1}")
            rank.setStyleSheet("font-weight: bold; color: gray;")
            rank.setFixedWidth(25)
            row.addWidget(rank)

            name_lbl = QLabel(name)
            row.addWidget(name_lbl, 1)

            avg_lbl = QLabel(f"{avg:.2f}")
            avg_lbl.setStyleSheet(f"font-weight: bold; color: {color};")
            row.addWidget(avg_lbl)

            container = QWidget()
            container.setLayout(row)
            layout.addWidget(container)

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle keyboard shortcuts for this page. Returns True if handled."""
        key = event.key()

        # 1/2: Switch term
        if key == Qt.Key_1:
            self._term_toggle.set_term(1)
            self._on_term_changed(1)
            return True
        if key == Qt.Key_2:
            self._term_toggle.set_term(2)
            self._on_term_changed(2)
            return True

        return False
