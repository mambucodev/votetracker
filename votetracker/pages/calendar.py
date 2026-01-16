"""
Calendar page for VoteTracker.
Shows grades plotted on a calendar view.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCalendarWidget,
    QFrame, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QKeyEvent, QColor, QPainter, QBrush, QPen

from ..database import Database
from ..utils import calc_average, get_status_color, get_grade_style, StatusColors
from ..widgets import TermToggle


class GradeCalendar(QCalendarWidget):
    """Custom calendar widget that highlights dates with grades."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dates_with_grades = {}  # {date_str: avg_grade}
        self._grades_by_date = {}
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

    def set_grade_dates(self, grades_by_date: dict):
        """Set which dates have grades and their averages."""
        self._grades_by_date = grades_by_date
        self._dates_with_grades = {}
        for date_str, votes in grades_by_date.items():
            if votes:
                avg = calc_average(votes)
                self._dates_with_grades[date_str] = avg

        # Apply text formatting for dates with grades
        self._update_date_formats()
        self.updateCells()

    def _update_date_formats(self):
        """Apply text formatting to highlight dates with grades."""
        from PySide6.QtGui import QTextCharFormat

        # Reset all dates first
        default_format = QTextCharFormat()

        for date_str, avg in self._dates_with_grades.items():
            qdate = QDate.fromString(date_str, "yyyy-MM-dd")
            if qdate.isValid():
                fmt = QTextCharFormat()
                color = get_status_color(avg)
                fmt.setForeground(color)
                fmt.setFontWeight(700)  # Bold
                self.setDateTextFormat(qdate, fmt)

    def paintCell(self, painter: QPainter, rect, date: QDate):
        """Paint cell with indicator if date has grades."""
        super().paintCell(painter, rect, date)

        date_str = date.toString("yyyy-MM-dd")
        if date_str in self._dates_with_grades:
            avg = self._dates_with_grades[date_str]
            color = get_status_color(avg)

            # Draw a colored circle/dot indicator at bottom of cell
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)

            dot_size = 8
            x = rect.center().x() - dot_size // 2
            y = rect.bottom() - dot_size - 3
            painter.drawEllipse(x, y, dot_size, dot_size)
            painter.restore()


class CalendarPage(QWidget):
    """Calendar view page showing grades by date."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._current_term = None
        self._grades_by_date = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Calendar")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        # Term toggle
        self._term_toggle = TermToggle(self._db.get_current_term())
        self._term_toggle.term_changed.connect(self._on_term_changed)
        header.addWidget(self._term_toggle)

        layout.addLayout(header)

        # Main content: calendar + details panel
        content = QHBoxLayout()
        content.setSpacing(20)

        # Calendar widget
        calendar_container = QVBoxLayout()
        self._calendar = GradeCalendar()
        self._calendar.selectionChanged.connect(self._on_date_selected)
        self._calendar.setMinimumSize(350, 300)
        calendar_container.addWidget(self._calendar)
        calendar_container.addStretch()
        content.addLayout(calendar_container)

        # Details panel
        details_container = QVBoxLayout()

        self._date_label = QLabel("Select a date")
        self._date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        details_container.addWidget(self._date_label)

        # Grades list in scroll area
        self._grades_group = QGroupBox("Grades")
        grades_layout = QVBoxLayout(self._grades_group)
        grades_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        self._grades_layout = QVBoxLayout(scroll_widget)
        self._grades_layout.setContentsMargins(0, 0, 0, 0)
        self._grades_layout.setSpacing(8)
        self._grades_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        grades_layout.addWidget(scroll)

        details_container.addWidget(self._grades_group, 1)

        # Average for selected date
        self._avg_label = QLabel("")
        self._avg_label.setStyleSheet("font-size: 12px; color: gray;")
        details_container.addWidget(self._avg_label)

        content.addLayout(details_container, 1)

        layout.addLayout(content, 1)

        # Legend
        legend = QHBoxLayout()
        legend.addWidget(QLabel("Legend:"))
        legend.addSpacing(10)

        for label, color in [("Passing (6+)", "#27ae60"), ("Warning (5.5-6)", "#f39c12"), ("Failing (<5.5)", "#e74c3c")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            legend.addWidget(dot)
            legend.addWidget(QLabel(label))
            legend.addSpacing(15)

        legend.addStretch()
        layout.addLayout(legend)

    def _on_term_changed(self, term: int):
        """Handle term toggle change."""
        self._current_term = term
        self._db.set_current_term(term)
        self.refresh()

    def _on_date_selected(self):
        """Handle date selection in calendar."""
        selected = self._calendar.selectedDate()
        self._update_details_panel(selected)

    def _update_details_panel(self, date: QDate):
        """Update the details panel for selected date."""
        date_str = date.toString("yyyy-MM-dd")
        display_date = date.toString("MMMM d, yyyy")

        # Clear existing grades
        while self._grades_layout.count():
            item = self._grades_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        votes = self._grades_by_date.get(date_str, [])

        if not votes:
            self._date_label.setText(display_date)
            placeholder = QLabel("No grades on this date")
            placeholder.setStyleSheet("color: gray;")
            self._grades_layout.addWidget(placeholder)
            self._avg_label.setText("")
            return

        self._date_label.setText(f"{display_date} ({len(votes)} grade{'s' if len(votes) != 1 else ''})")

        for vote in votes:
            grade_widget = self._create_grade_item(vote)
            self._grades_layout.addWidget(grade_widget)

        # Show average
        avg = calc_average(votes)
        self._avg_label.setText(f"Average: {avg:.2f}")
        self._avg_label.setStyleSheet(get_grade_style(avg))

    def _create_grade_item(self, vote: dict) -> QFrame:
        """Create a widget for displaying a single grade."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        # Subject
        subject = QLabel(vote.get("subject", "Unknown"))
        subject.setStyleSheet("font-weight: bold;")
        layout.addWidget(subject)

        # Type
        vote_type = vote.get("type", "Written")
        type_label = QLabel(vote_type)
        if vote_type == "Written":
            type_label.setStyleSheet(f"color: {StatusColors.WRITTEN.name()}; font-size: 11px;")
        elif vote_type == "Oral":
            type_label.setStyleSheet(f"color: {StatusColors.ORAL.name()}; font-size: 11px;")
        else:
            type_label.setStyleSheet(f"color: {StatusColors.PRACTICAL.name()}; font-size: 11px;")
        layout.addWidget(type_label)

        layout.addStretch()

        # Description (if any)
        desc = vote.get("description", "")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: gray; font-size: 11px;")
            desc_label.setMaximumWidth(150)
            layout.addWidget(desc_label)
            layout.addSpacing(10)

        # Grade
        grade = vote.get("grade", 0)
        grade_label = QLabel(f"{grade:.2f}")
        grade_label.setStyleSheet(get_grade_style(grade) + "font-size: 16px;")
        layout.addWidget(grade_label)

        return frame

    def refresh(self):
        """Refresh calendar data."""
        # Update term toggle
        self._term_toggle.set_term(self._db.get_current_term())
        self._current_term = self._term_toggle.get_term()

        # Build date index
        votes = self._db.get_votes(term=self._current_term)
        self._grades_by_date = {}
        for vote in votes:
            date = vote.get("date", "")
            if date:
                self._grades_by_date.setdefault(date, []).append(vote)

        # Update calendar highlighting
        self._calendar.set_grade_dates(self._grades_by_date)

        # Navigate to most recent date with grades if available
        if self._grades_by_date:
            most_recent = max(self._grades_by_date.keys())
            qdate = QDate.fromString(most_recent, "yyyy-MM-dd")
            if qdate.isValid():
                self._calendar.setSelectedDate(qdate)

        # Update details panel for current selection
        self._update_details_panel(self._calendar.selectedDate())

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
