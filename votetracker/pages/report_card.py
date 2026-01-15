"""
Report Card page for VoteTracker.
Shows simulated report card with grades.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QScrollArea, QFrame, QCheckBox
)
from PySide6.QtCore import Qt

from ..database import Database
from ..utils import (
    calc_average, round_report_card, get_grade_style, 
    get_symbolic_icon, has_icon, get_icon_fallback, StatusColors
)
from ..widgets import StatusIndicator, TermToggle


class ReportCardPage(QWidget):
    """Simulated report card page."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._split_by_type = False
        self._current_term = None  # None = all terms
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header with title and toggles
        header = QHBoxLayout()
        title = QLabel("Simulated Report Card")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        # Term selector
        self._term_toggle = TermToggle(self._db.get_current_term())
        self._term_toggle.term_changed.connect(self._on_term_changed)
        header.addWidget(self._term_toggle)
        
        header.addSpacing(16)
        
        # Split toggle
        self._split_toggle = QCheckBox("Split Written/Oral")
        self._split_toggle.setChecked(False)
        self._split_toggle.toggled.connect(self._on_split_changed)
        header.addWidget(self._split_toggle)
        
        layout.addLayout(header)
        
        # Report card
        active_year = self._db.get_active_school_year()
        year_name = active_year["name"] if active_year else "-"
        self._report_group = QGroupBox(f"Report Card - {year_name}")
        report_layout = QVBoxLayout(self._report_group)
        report_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        self._grades_layout = QVBoxLayout(scroll_widget)
        self._grades_layout.setContentsMargins(0, 0, 0, 0)
        self._grades_layout.setSpacing(4)
        self._grades_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        report_layout.addWidget(scroll)
        
        layout.addWidget(self._report_group, 1)
        
        # Legend
        legend_group = QGroupBox("Rounding Rules")
        legend_layout = QVBoxLayout(legend_group)
        legend_layout.setContentsMargins(12, 12, 12, 12)
        legend_layout.addWidget(QLabel("• Average ≥ 0.5 decimal rounds up (e.g., 5.5 → 6)"))
        legend_layout.addWidget(QLabel("• Average < 0.5 decimal rounds down (e.g., 5.4 → 5)"))
        layout.addWidget(legend_group)
    
    def _on_term_changed(self, term: int):
        """Handle term change."""
        self._current_term = term
        self._db.set_current_term(term)
        self.refresh()
    
    def _on_split_changed(self, checked: bool):
        """Handle split toggle change."""
        self._split_by_type = checked
        self.refresh()
    
    def refresh(self):
        """Refresh report card display."""
        # Update year in title
        active_year = self._db.get_active_school_year()
        year_name = active_year["name"] if active_year else "-"
        term_str = f" - {self._current_term}° Term" if self._current_term else ""
        self._report_group.setTitle(f"Report Card - {year_name}{term_str}")
        
        # Update term toggle
        self._term_toggle.set_term(self._db.get_current_term())
        self._current_term = self._term_toggle.get_term()
        
        # Clear layout
        while self._grades_layout.count():
            item = self._grades_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        subjects = self._db.get_subjects_with_votes(term=self._current_term)
        
        if not subjects:
            empty = QLabel("No votes recorded yet")
            empty.setStyleSheet("color: gray; font-weight: bold; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self._grades_layout.addWidget(empty)
            return
        
        total_avg = 0
        count = 0
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.addWidget(QLabel("<b>Subject</b>"))
        header_layout.addStretch()
        header_layout.addWidget(QLabel("<b>Votes</b>"))
        header_layout.addSpacing(16)
        header_layout.addWidget(QLabel("<b>Avg</b>"))
        header_layout.addSpacing(20)
        header_layout.addWidget(QLabel("<b>Grade</b>"))
        self._grades_layout.addWidget(header)
        
        # Header separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self._grades_layout.addWidget(line)
        
        for subject in sorted(subjects):
            votes = self._db.get_votes(subject, term=self._current_term)
            
            if self._split_by_type:
                # Split mode
                written_votes = [v for v in votes if v.get("type") == "Written"]
                oral_votes = [v for v in votes if v.get("type") == "Oral"]
                
                if written_votes:
                    self._add_grade_row(
                        subject, written_votes, "Written", 
                        StatusColors.WRITTEN.name()
                    )
                    total_avg += calc_average(written_votes)
                    count += 1
                
                if oral_votes:
                    self._add_grade_row(
                        subject, oral_votes, "Oral",
                        StatusColors.ORAL.name()
                    )
                    total_avg += calc_average(oral_votes)
                    count += 1
            else:
                # Combined mode
                self._add_grade_row(subject, votes)
                total_avg += calc_average(votes)
                count += 1
        
        # Footer separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        self._grades_layout.addWidget(line2)
        
        # Overall average
        if count > 0:
            overall = total_avg / count
            footer = QFrame()
            footer_layout = QHBoxLayout(footer)
            footer_layout.setContentsMargins(8, 8, 8, 8)
            footer_layout.addWidget(QLabel("<b>Overall Average</b>"))
            footer_layout.addStretch()
            footer_val = QLabel(f"<b>{overall:.2f}</b>")
            footer_val.setStyleSheet(get_grade_style(overall) + "font-size: 18px;")
            footer_layout.addWidget(footer_val)
            self._grades_layout.addWidget(footer)
    
    def _add_grade_row(
        self, 
        subject: str, 
        votes: list, 
        type_label: str = None,
        type_color: str = None
    ):
        """Add a grade row to the report card."""
        avg = calc_average(votes)
        final_grade = round_report_card(avg)
        
        row = QFrame()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 4, 8, 4)
        
        # Status indicator
        status = StatusIndicator(avg)
        row_layout.addWidget(status)
        row_layout.addSpacing(8)
        
        # Subject name
        name_label = QLabel(subject)
        row_layout.addWidget(name_label)
        
        # Type label (if split mode)
        if type_label:
            tl = QLabel(type_label)
            tl.setStyleSheet(f"color: {type_color}; font-size: 11px;")
            row_layout.addWidget(tl)
        
        row_layout.addStretch()
        
        # Vote count
        count_label = QLabel(f"{len(votes)}")
        count_label.setStyleSheet("color: gray; font-size: 11px;")
        count_label.setMinimumWidth(30)
        row_layout.addWidget(count_label)
        row_layout.addSpacing(16)
        
        # Average
        avg_label = QLabel(f"{avg:.2f}")
        avg_label.setStyleSheet("color: gray;")
        row_layout.addWidget(avg_label)
        
        # Arrow icon
        arrow = QLabel()
        if has_icon("go-next"):
            arrow.setPixmap(get_symbolic_icon("go-next").pixmap(16, 16))
        else:
            arrow.setText(get_icon_fallback("go-next"))
        row_layout.addWidget(arrow)
        
        # Final grade
        grade_label = QLabel(f"<b>{final_grade}</b>")
        grade_label.setStyleSheet(get_grade_style(avg) + "font-size: 18px;")
        grade_label.setMinimumWidth(30)
        grade_label.setAlignment(Qt.AlignCenter)
        row_layout.addWidget(grade_label)
        
        self._grades_layout.addWidget(row)
