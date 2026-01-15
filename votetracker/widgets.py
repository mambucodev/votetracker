"""
Custom Qt widgets for VoteTracker.
Contains reusable UI components.
"""

from PySide6.QtWidgets import (
    QLabel, QGroupBox, QVBoxLayout, QHBoxLayout, QFrame, QToolButton
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon

from .utils import (
    get_status_color, get_status_icon_name, get_grade_style,
    get_symbolic_icon, has_icon, get_icon_fallback, calc_average, StatusColors
)


class StatusIndicator(QLabel):
    """
    Status indicator widget using theme icons.
    Shows green/yellow/red based on grade average.
    """
    
    def __init__(self, average: float, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.update_status(average)
    
    def update_status(self, average: float):
        """Update the indicator based on new average."""
        icon_name = get_status_icon_name(average)
        icon = get_symbolic_icon(icon_name)
        
        if icon.isNull():
            # Fallback: colored circle
            color = get_status_color(average)
            self.setStyleSheet(f"""
                background-color: {color.name()};
                border-radius: 10px;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            """)
            self.setText("")
        else:
            self.setPixmap(icon.pixmap(20, 20))
            self.setStyleSheet("")


class NavButton(QToolButton):
    """
    Navigation button with icon above text.
    Used in the sidebar for page navigation.
    """
    
    def __init__(self, icon_name: str, text: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setFixedSize(80, 64)
        
        if has_icon(icon_name):
            icon = get_symbolic_icon(icon_name)
            self.setIcon(icon)
            self.setIconSize(QSize(24, 24))
        else:
            # Fallback: show emoji/text above label
            fallback = get_icon_fallback(icon_name)
            self.setToolButtonStyle(Qt.ToolButtonTextOnly)
            self.setText(f"{fallback}\n{text}")
            return
        
        self.setText(text)


class DashboardSubjectCard(QGroupBox):
    """
    Subject card for dashboard display.
    Shows subject stats without edit functionality.
    """
    
    def __init__(
        self, 
        subject: str, 
        average: float, 
        written_avg: float, 
        oral_avg: float,
        vote_count: int, 
        parent=None
    ):
        super().__init__(parent)
        self._setup_ui(subject, average, written_avg, oral_avg, vote_count)
    
    def _setup_ui(
        self, 
        subject: str, 
        average: float, 
        written_avg: float, 
        oral_avg: float,
        vote_count: int
    ):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header with status and name
        header = QHBoxLayout()
        header.setSpacing(8)
        
        status = StatusIndicator(average)
        header.addWidget(status)
        
        name = QLabel(f"<b>{subject}</b>")
        name.setStyleSheet("font-size: 14px;")
        header.addWidget(name)
        header.addStretch()
        
        # Average
        avg_label = QLabel(f"<b>{average:.2f}</b>")
        avg_label.setStyleSheet(get_grade_style(average) + "font-size: 18px;")
        header.addWidget(avg_label)
        
        layout.addLayout(header)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Details row
        details = QHBoxLayout()
        details.setSpacing(16)
        
        # Written average
        written_box = QVBoxLayout()
        written_box.setSpacing(2)
        w_label = QLabel("Written")
        w_label.setStyleSheet(f"color: {StatusColors.WRITTEN.name()}; font-size: 11px;")
        written_str = f"<b>{written_avg:.1f}</b>" if written_avg > 0 else "-"
        w_value = QLabel(written_str)
        w_value.setStyleSheet(f"color: {StatusColors.WRITTEN.name()};")
        written_box.addWidget(w_label)
        written_box.addWidget(w_value)
        details.addLayout(written_box)
        
        # Oral average
        oral_box = QVBoxLayout()
        oral_box.setSpacing(2)
        o_label = QLabel("Oral")
        o_label.setStyleSheet(f"color: {StatusColors.ORAL.name()}; font-size: 11px;")
        oral_str = f"<b>{oral_avg:.1f}</b>" if oral_avg > 0 else "-"
        o_value = QLabel(oral_str)
        o_value.setStyleSheet(f"color: {StatusColors.ORAL.name()};")
        oral_box.addWidget(o_label)
        oral_box.addWidget(o_value)
        details.addLayout(oral_box)
        
        details.addStretch()
        
        # Vote count
        count_label = QLabel(f"{vote_count} votes")
        count_label.setStyleSheet("color: gray; font-size: 11px;")
        details.addWidget(count_label)
        
        layout.addLayout(details)


class SubjectCard(QGroupBox):
    """
    Subject card with edit functionality.
    Used in the Subjects page for management.
    """
    
    edit_requested = Signal(str)
    
    def __init__(
        self,
        subject: str,
        average: float,
        written_avg: float,
        oral_avg: float,
        vote_count: int,
        report_grade: int,
        parent=None
    ):
        super().__init__(parent)
        self._subject_name = subject
        self._setup_ui(subject, average, written_avg, oral_avg, vote_count, report_grade)
    
    def _setup_ui(
        self,
        subject: str,
        average: float,
        written_avg: float,
        oral_avg: float,
        vote_count: int,
        report_grade: int
    ):
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        if vote_count > 0:
            status = StatusIndicator(average)
            header.addWidget(status)
        
        name = QLabel(f"<b>{subject}</b>")
        name.setStyleSheet("font-size: 16px;")
        header.addWidget(name)
        header.addStretch()
        
        # Edit button
        edit_btn = QToolButton()
        edit_btn.setIcon(get_symbolic_icon("document-edit"))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setToolTip("Edit or delete")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._subject_name))
        header.addWidget(edit_btn)
        
        layout.addLayout(header)
        
        if vote_count > 0:
            # Stats grid
            from PySide6.QtWidgets import QGridLayout
            stats = QGridLayout()
            stats.setSpacing(8)
            
            stats.addWidget(QLabel("Average:"), 0, 0)
            avg_val = QLabel(f"<b>{average:.2f}</b>")
            avg_val.setStyleSheet(get_grade_style(average))
            stats.addWidget(avg_val, 0, 1)
            
            stats.addWidget(QLabel("Written:"), 0, 2)
            w_str = f"<b>{written_avg:.1f}</b>" if written_avg > 0 else "-"
            w_val = QLabel(w_str)
            w_val.setStyleSheet(f"color: {StatusColors.WRITTEN.name()};")
            stats.addWidget(w_val, 0, 3)
            
            stats.addWidget(QLabel("Oral:"), 1, 2)
            o_str = f"<b>{oral_avg:.1f}</b>" if oral_avg > 0 else "-"
            o_val = QLabel(o_str)
            o_val.setStyleSheet(f"color: {StatusColors.ORAL.name()};")
            stats.addWidget(o_val, 1, 3)
            
            stats.addWidget(QLabel("Votes:"), 1, 0)
            stats.addWidget(QLabel(str(vote_count)), 1, 1)
            
            layout.addLayout(stats)
            
            # Separator
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            layout.addWidget(line)
            
            # Report card
            report = QHBoxLayout()
            report.addWidget(QLabel("Report Card:"))
            report.addStretch()
            rp_val = QLabel(f"<b>{report_grade}</b>")
            rp_val.setStyleSheet(get_grade_style(average) + "font-size: 18px;")
            report.addWidget(rp_val)
            layout.addLayout(report)
        else:
            no_votes = QLabel("No votes yet")
            no_votes.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_votes)


class TermToggle(QFrame):
    """
    Toggle widget for switching between terms (quadrimestri).
    """
    
    term_changed = Signal(int)
    
    def __init__(self, current_term: int = 1, parent=None):
        super().__init__(parent)
        self._current_term = current_term
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._btn1 = QToolButton()
        self._btn1.setText("1° Term")
        self._btn1.setCheckable(True)
        self._btn1.setChecked(self._current_term == 1)
        self._btn1.clicked.connect(lambda: self._set_term(1))
        self._btn1.setMinimumWidth(70)
        
        self._btn2 = QToolButton()
        self._btn2.setText("2° Term")
        self._btn2.setCheckable(True)
        self._btn2.setChecked(self._current_term == 2)
        self._btn2.clicked.connect(lambda: self._set_term(2))
        self._btn2.setMinimumWidth(70)
        
        layout.addWidget(self._btn1)
        layout.addWidget(self._btn2)
    
    def _set_term(self, term: int):
        if term != self._current_term:
            self._current_term = term
            self._btn1.setChecked(term == 1)
            self._btn2.setChecked(term == 2)
            self.term_changed.emit(term)
    
    def get_term(self) -> int:
        return self._current_term
    
    def set_term(self, term: int):
        """Set term without emitting signal."""
        self._current_term = term
        self._btn1.setChecked(term == 1)
        self._btn2.setChecked(term == 2)


class YearSelector(QFrame):
    """
    Widget for navigating between school years.
    Shows current year with prev/next buttons.
    """
    
    year_changed = Signal(int)  # Emits school_year_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._years = []
        self._current_index = 0
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Year label on top
        self._year_label = QLabel("-")
        self._year_label.setAlignment(Qt.AlignCenter)
        self._year_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        layout.addWidget(self._year_label)
        
        # Buttons row below
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        
        self._prev_btn = QToolButton()
        if has_icon("go-previous"):
            self._prev_btn.setIcon(get_symbolic_icon("go-previous"))
            self._prev_btn.setIconSize(QSize(16, 16))
        else:
            self._prev_btn.setText(get_icon_fallback("go-previous"))
        self._prev_btn.clicked.connect(self._go_prev)
        self._prev_btn.setFixedSize(28, 24)
        
        self._next_btn = QToolButton()
        if has_icon("go-next"):
            self._next_btn.setIcon(get_symbolic_icon("go-next"))
            self._next_btn.setIconSize(QSize(16, 16))
        else:
            self._next_btn.setText(get_icon_fallback("go-next"))
        self._next_btn.clicked.connect(self._go_next)
        self._next_btn.setFixedSize(28, 24)
        
        btn_layout.addWidget(self._prev_btn)
        btn_layout.addWidget(self._next_btn)
        layout.addLayout(btn_layout)
    
    def set_years(self, years: list, active_id: int = None):
        """Set available years and optionally select one."""
        self._years = years
        if not years:
            self._year_label.setText("-")
            self._current_index = 0
            return
        
        # Find active year index
        if active_id is not None:
            for i, year in enumerate(years):
                if year["id"] == active_id:
                    self._current_index = i
                    break
        else:
            self._current_index = 0
        
        self._update_display()
    
    def _update_display(self):
        if not self._years:
            return
        
        year = self._years[self._current_index]
        # Show short format like "25/26"
        start = year["start_year"]
        self._year_label.setText(f"{start % 100}/{(start + 1) % 100}")
        
        # Update button states
        self._prev_btn.setEnabled(self._current_index > 0)
        self._next_btn.setEnabled(self._current_index < len(self._years) - 1)
    
    def _go_prev(self):
        if self._current_index > 0:
            self._current_index -= 1
            self._update_display()
            self.year_changed.emit(self._years[self._current_index]["id"])
    
    def _go_next(self):
        if self._current_index < len(self._years) - 1:
            self._current_index += 1
            self._update_display()
            self.year_changed.emit(self._years[self._current_index]["id"])
    
    def get_current_year_id(self) -> int:
        if self._years and 0 <= self._current_index < len(self._years):
            return self._years[self._current_index]["id"]
        return None
