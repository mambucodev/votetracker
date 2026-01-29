"""
Statistics page for VoteTracker.
Shows detailed analytics and grade distributions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPainter, QColor, QPen
from datetime import datetime

from ..database import Database
from ..utils import calc_average, get_status_color
from ..widgets import TermToggle
from ..i18n import tr


class BarChart(QFrame):
    """Simple horizontal bar chart widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (label, value, color)
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

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
            empty = QLabel(tr("No data"))
            empty.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(empty)
            return

        max_val = max(d[1] for d in self._data) if self._data else 1
        if max_val == 0:
            max_val = 1

        for label, value, color in self._data:
            # Create row widget
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(12)

            # Subject name label - make sure it's visible
            lbl = QLabel(label)
            lbl.setMinimumWidth(150)
            lbl.setMaximumWidth(200)
            lbl.setWordWrap(False)
            lbl.setToolTip(label)
            row.addWidget(lbl)

            # Bar container
            bar_container = QFrame()
            bar_container.setFixedHeight(28)
            bar_container.setFrameShape(QFrame.StyledPanel)
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(2, 2, 2, 2)
            bar_layout.setSpacing(0)

            # Bar fill
            width_percent = (value / max_val) * 100 if max_val > 0 else 0
            bar = QFrame()
            bar.setStyleSheet(f"background: {color}; border-radius: 2px;")
            bar_layout.addWidget(bar, int(width_percent))
            bar_layout.addStretch(int(100 - width_percent))

            row.addWidget(bar_container, 1)

            # Value label
            val_lbl = QLabel(f"{value:.2f}")
            val_lbl.setFixedWidth(55)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_lbl.setStyleSheet(f"font-weight: bold; color: {color};")
            row.addWidget(val_lbl)

            self._layout.addWidget(row_widget)


class DistributionChart(QFrame):
    """Grade distribution histogram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}  # {range_label: (count, color)}
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(6)
        self._layout.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)

    def set_data(self, grades: list):
        """Set distribution data from list of grades."""
        if not grades:
            self._data = {}
            self._update_chart()
            return

        # Define ranges
        ranges = [
            ("2-4", 2, 4, "#c0392b"),
            ("4-5.5", 4, 5.5, "#e74c3c"),
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
            empty = QLabel(tr("No data"))
            empty.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(empty)
            return

        max_count = max(c for c, _ in self._data.values()) if self._data else 1
        if max_count == 0:
            max_count = 1

        for label, (count, color) in self._data.items():
            col = QVBoxLayout()
            col.setSpacing(6)
            col.setContentsMargins(0, 0, 0, 0)

            # Count label at top (fixed position)
            count_lbl = QLabel(str(count) if count > 0 else "")
            count_lbl.setAlignment(Qt.AlignCenter)
            count_lbl.setStyleSheet(f"font-weight: bold; color: {color};")
            count_lbl.setFixedHeight(20)
            col.addWidget(count_lbl)

            # Add spacer to push bar to bottom
            col.addStretch()

            # Bar
            height = int((count / max_count) * 100) if max_count > 0 else 0
            bar = QFrame()
            bar.setFixedWidth(40)
            bar.setFixedHeight(max(height, 3))
            bar.setStyleSheet(f"background: {color}; border-radius: 3px;")
            col.addWidget(bar, 0, Qt.AlignCenter)

            # Range label at bottom
            range_lbl = QLabel(label)
            range_lbl.setAlignment(Qt.AlignCenter)
            range_lbl.setFixedHeight(20)
            col.addWidget(range_lbl)

            container = QWidget()
            container.setLayout(col)
            self._layout.addWidget(container)


class TrendChart(QFrame):
    """Simple line chart showing grade trends over time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_points = []  # List of (date, grade)
        self.setMinimumHeight(200)
        self.setFrameShape(QFrame.StyledPanel)

    def set_data(self, votes: list):
        """Set data from list of votes."""
        if not votes:
            self._data_points = []
            self.update()
            return

        # Sort votes by date
        sorted_votes = sorted(votes, key=lambda v: v.get('date', ''))
        self._data_points = [
            (v.get('date', ''), v.get('grade', 0))
            for v in sorted_votes
        ]
        self.update()

    def paintEvent(self, event):
        """Custom paint to draw the line chart."""
        super().paintEvent(event)

        if not self._data_points:
            painter = QPainter(self)
            painter.drawText(self.rect(), Qt.AlignCenter, tr("No data"))
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate drawing area with margins
        margin = 40
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin

        # Find min/max grades for scaling
        grades = [d[1] for d in self._data_points]
        min_grade = max(0, min(grades) - 0.5)
        max_grade = min(10, max(grades) + 0.5)
        grade_range = max_grade - min_grade
        if grade_range == 0:
            grade_range = 1

        # Draw grid lines with Y-axis labels
        painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DotLine))
        for i in range(5):
            y = margin + (height * i / 4)
            painter.drawLine(margin, int(y), margin + width, int(y))

            # Draw Y-axis grade label
            grade_val = max_grade - (grade_range * i / 4)
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(5, int(y + 5), f"{grade_val:.1f}")
            painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DotLine))

        # Draw passing threshold (6.0)
        if min_grade <= 6 <= max_grade:
            passing_y = margin + height * (1 - (6 - min_grade) / grade_range)
            painter.setPen(QPen(QColor("#27ae60"), 1, Qt.DashLine))
            painter.drawLine(margin, int(passing_y), margin + width, int(passing_y))
            # Label the passing line
            painter.setPen(QColor("#27ae60"))
            painter.drawText(margin + width - 50, int(passing_y - 5), tr("Pass (6.0)"))

        # Calculate points
        points = []
        for i, (date, grade) in enumerate(self._data_points):
            x = margin + (width * i / max(len(self._data_points) - 1, 1))
            y = margin + height * (1 - (grade - min_grade) / grade_range)
            points.append((x, y, grade))

        # Draw line
        if len(points) >= 2:
            painter.setPen(QPen(QColor("#3498db"), 2))
            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]), int(points[i][1]),
                    int(points[i + 1][0]), int(points[i + 1][1])
                )

        # Draw points
        for x, y, grade in points:
            color = get_status_color(grade)
            painter.setPen(QPen(QColor("white"), 1))
            painter.setBrush(color)
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

        # Draw X-axis date labels (first, middle, last)
        painter.setPen(QColor(150, 150, 150))
        if len(self._data_points) > 0:
            # First date
            date_str = self._format_date(self._data_points[0][0])
            painter.drawText(int(points[0][0]) - 20, self.height() - 15, date_str)

            # Last date
            if len(self._data_points) > 1:
                date_str = self._format_date(self._data_points[-1][0])
                painter.drawText(int(points[-1][0]) - 20, self.height() - 15, date_str)

            # Middle date
            if len(self._data_points) > 2:
                mid_idx = len(self._data_points) // 2
                date_str = self._format_date(self._data_points[mid_idx][0])
                painter.drawText(int(points[mid_idx][0]) - 20, self.height() - 15, date_str)

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m")
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str


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
        self._distribution_chart = DistributionChart()
        self._distribution_chart.setMinimumHeight(180)
        dist_layout.addWidget(self._distribution_chart)
        scroll_layout.addWidget(self._dist_group)

        # Grade trend over time
        self._trend_group = QGroupBox(tr("Grade Trend Over Time"))
        trend_layout = QVBoxLayout(self._trend_group)
        trend_layout.setContentsMargins(16, 16, 16, 16)
        self._trend_chart = TrendChart()
        self._trend_chart.setMinimumHeight(200)
        trend_layout.addWidget(self._trend_chart)
        scroll_layout.addWidget(self._trend_group)

        # Subject averages
        self._subjects_group = QGroupBox(tr("Subject Averages"))
        subjects_layout = QVBoxLayout(self._subjects_group)
        subjects_layout.setContentsMargins(16, 16, 16, 16)
        self._subjects_chart = BarChart()
        self._subjects_chart.setMinimumHeight(200)
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
            subject_data.append((subj, avg, color))

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
            layout.addWidget(empty)
            return

        for i, item in enumerate(subjects):
            name, avg, color = item[0], item[1], item[2]

            row = QHBoxLayout()
            rank = QLabel(f"#{i + 1}")
            rank.setFixedWidth(30)
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
