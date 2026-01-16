"""
Report Card page for VoteTracker.
Shows simulated report card with grades.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QScrollArea, QFrame, QCheckBox, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from ..database import Database
from ..utils import (
    calc_average, round_report_card, get_grade_style,
    get_symbolic_icon, has_icon, get_icon_fallback, StatusColors
)
from ..widgets import StatusIndicator, TermToggle
from ..i18n import tr


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
        self._title = QLabel(tr("Report Card"))
        self._title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(self._title)
        header.addStretch()

        # Export PDF button
        self._export_btn = QPushButton(tr("Export PDF"))
        self._export_btn.setIcon(get_symbolic_icon("document-export"))
        self._export_btn.clicked.connect(self._export_pdf)
        header.addWidget(self._export_btn)

        header.addSpacing(8)

        # Term selector
        self._term_toggle = TermToggle(self._db.get_current_term())
        self._term_toggle.term_changed.connect(self._on_term_changed)
        header.addWidget(self._term_toggle)

        header.addSpacing(8)

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
        # Update labels for language changes
        self._title.setText(tr("Report Card"))
        self._export_btn.setText(tr("Export PDF"))

        # Update year in title
        active_year = self._db.get_active_school_year()
        year_name = active_year["name"] if active_year else "-"
        term_str = f" - {self._current_term}° {tr('Term')}" if self._current_term else ""
        self._report_group.setTitle(f"{tr('Report Card')} - {year_name}{term_str}")
        
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

    def _export_pdf(self):
        """Export report card to PDF."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate
        except ImportError:
            QMessageBox.warning(
                self, "Missing Dependency",
                "PDF export requires the 'reportlab' library.\n\n"
                "Install it with:\n"
                "  Arch: sudo pacman -S python-reportlab\n"
                "  Pip: pip install reportlab"
            )
            return

        # Get data
        subjects = self._db.get_subjects_with_votes(term=self._current_term)
        if not subjects:
            QMessageBox.information(self, "No Data", "No grades to export.")
            return

        # Get save path
        active_year = self._db.get_active_school_year()
        year_name = active_year["name"].replace("/", "-") if active_year else "report"
        term_str = f"_term{self._current_term}" if self._current_term else ""
        default_name = f"report_card_{year_name}{term_str}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Report Card", default_name, "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        try:
            self._generate_pdf(file_path, subjects)
            QMessageBox.information(
                self, "Export Complete",
                f"Report card exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{e}")

    def _generate_pdf(self, file_path: str, subjects: list):
        """Generate a clean, minimal PDF report card."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.enums import TA_CENTER

        # Soft, minimal color palette
        text_dark = colors.HexColor("#2c3e50")
        text_muted = colors.HexColor("#95a5a6")
        text_light = colors.HexColor("#bdc3c7")
        bg_subtle = colors.HexColor("#f8f9fa")
        grade_green = colors.HexColor("#27ae60")
        grade_yellow = colors.HexColor("#e67e22")
        grade_red = colors.HexColor("#c0392b")

        doc = SimpleDocTemplate(
            file_path, pagesize=A4,
            leftMargin=30*mm, rightMargin=30*mm,
            topMargin=30*mm, bottomMargin=25*mm
        )

        # Styles
        title_style = ParagraphStyle(
            'Title',
            fontName='Helvetica',
            fontSize=28,
            textColor=text_dark,
            spaceAfter=12*mm,
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName='Helvetica',
            fontSize=11,
            textColor=text_muted,
            spaceAfter=18*mm,
            alignment=TA_CENTER
        )
        section_style = ParagraphStyle(
            'Section',
            fontName='Helvetica',
            fontSize=9,
            textColor=text_muted,
            spaceBefore=8*mm,
            spaceAfter=2*mm
        )
        note_style = ParagraphStyle(
            'Note',
            fontName='Helvetica',
            fontSize=8,
            textColor=text_light,
            leftIndent=2*mm
        )
        footer_style = ParagraphStyle(
            'Footer',
            fontName='Helvetica',
            fontSize=8,
            textColor=text_light,
            alignment=TA_CENTER
        )

        elements = []

        # Header
        active_year = self._db.get_active_school_year()
        year_name = active_year["name"] if active_year else "-"
        term_str = f"Term {self._current_term}" if self._current_term else "Full Year"

        elements.append(Paragraph("Report Card", title_style))
        elements.append(Paragraph(f"{year_name}  ·  {term_str}", subtitle_style))

        # Build table data
        if self._split_by_type:
            headers = ["Subject", "Type", "Votes", "Average", "Grade"]
        else:
            headers = ["Subject", "Votes", "Average", "Grade"]

        table_data = [headers]
        total_avg = 0
        count = 0

        for subject in sorted(subjects):
            votes = self._db.get_votes(subject, term=self._current_term)

            if self._split_by_type:
                written_votes = [v for v in votes if v.get("type") == "Written"]
                oral_votes = [v for v in votes if v.get("type") == "Oral"]

                if written_votes:
                    avg = calc_average(written_votes)
                    grade = round_report_card(avg)
                    table_data.append([subject, "Written", str(len(written_votes)), f"{avg:.2f}", str(grade)])
                    total_avg += avg
                    count += 1

                if oral_votes:
                    avg = calc_average(oral_votes)
                    grade = round_report_card(avg)
                    table_data.append([subject, "Oral", str(len(oral_votes)), f"{avg:.2f}", str(grade)])
                    total_avg += avg
                    count += 1
            else:
                avg = calc_average(votes)
                grade = round_report_card(avg)
                table_data.append([subject, str(len(votes)), f"{avg:.2f}", str(grade)])
                total_avg += avg
                count += 1

        # Table dimensions - generous spacing to prevent overlap
        if self._split_by_type:
            col_widths = [50*mm, 25*mm, 20*mm, 28*mm, 25*mm]
        else:
            col_widths = [70*mm, 25*mm, 30*mm, 25*mm]

        table = Table(table_data, colWidths=col_widths)

        # Grade color function
        def get_grade_color(avg):
            if avg < 5.5:
                return grade_red
            elif avg < 6:
                return grade_yellow
            return grade_green

        # Clean minimal table style - no borders, just spacing and subtle backgrounds
        style = [
            # Header - subtle, not loud
            ('BACKGROUND', (0, 0), (-1, 0), bg_subtle),
            ('TEXTCOLOR', (0, 0), (-1, 0), text_muted),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), text_dark),

            # Alignment
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Only a thin line below header
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, text_light),
        ]

        # Color grade cells
        grade_col = -1
        avg_col = -2

        for i, row in enumerate(table_data[1:], start=1):
            try:
                avg_val = float(row[avg_col])
                grade_color = get_grade_color(avg_val)
                style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), grade_color))
                style.append(('FONTNAME', (grade_col, i), (grade_col, i), 'Helvetica-Bold'))
                style.append(('FONTSIZE', (grade_col, i), (grade_col, i), 13))
            except (ValueError, IndexError):
                pass

        table.setStyle(TableStyle(style))
        elements.append(table)

        # Overall average
        if count > 0:
            overall = total_avg / count
            overall_grade = round_report_card(overall)
            overall_color = get_grade_color(overall)

            elements.append(Spacer(1, 4*mm))

            overall_data = [["Overall Average", f"{overall:.2f}", str(overall_grade)]]
            overall_table = Table(overall_data, colWidths=[90*mm, 30*mm, 30*mm])
            overall_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0, 0), (0, 0), text_dark),
                ('TEXTCOLOR', (1, 0), (1, 0), text_muted),
                ('TEXTCOLOR', (2, 0), (2, 0), overall_color),
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
                ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (1, 0), 10),
                ('FONTSIZE', (2, 0), (2, 0), 14),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('LINEABOVE', (0, 0), (-1, 0), 0.5, text_light),
            ]))
            elements.append(overall_table)

        # Rounding rules
        elements.append(Paragraph("Rounding Rules", section_style))
        elements.append(Paragraph("· Average ≥ 0.5 rounds up (5.50 → 6)  ·  Average < 0.5 rounds down (5.49 → 5)", note_style))

        # Footer
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph("Generated by VoteTracker", footer_style))

        doc.build(elements)

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle keyboard shortcuts for this page. Returns True if handled."""
        key = event.key()
        modifiers = event.modifiers()

        # Ctrl+P: Export PDF
        if modifiers == Qt.ControlModifier and key == Qt.Key_P:
            self._export_pdf()
            return True

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
