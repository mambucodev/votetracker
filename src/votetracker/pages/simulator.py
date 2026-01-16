"""
Simulator page for VoteTracker.
Calculate required grades to reach target averages.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QFormLayout, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt

from ..database import Database
from ..utils import calc_average, get_grade_style
from ..i18n import tr


class SimulatorPage(QWidget):
    """Grade simulator page."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self._title = QLabel(tr("Simulator"))
        self._title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self._title)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(16)

        # Input group
        self._input_group = QGroupBox(tr("Grade Needed"))
        input_layout = QFormLayout(self._input_group)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)

        self._subject_combo = QComboBox()
        self._subject_combo.setMinimumWidth(150)
        self._subject_combo.currentTextChanged.connect(self._calculate)
        self._subject_label = QLabel(tr("Subject") + ":")
        input_layout.addRow(self._subject_label, self._subject_combo)

        self._target_spin = QDoubleSpinBox()
        self._target_spin.setRange(1.0, 10.0)
        self._target_spin.setValue(6.0)
        self._target_spin.setSingleStep(0.5)
        self._target_spin.valueChanged.connect(self._calculate)
        self._target_label = QLabel(tr("Target Average") + ":")
        input_layout.addRow(self._target_label, self._target_spin)

        content.addWidget(self._input_group)

        # Result group
        self._result_group = QGroupBox(tr("Calculate"))
        result_layout = QVBoxLayout(self._result_group)
        result_layout.setContentsMargins(16, 16, 16, 16)
        result_layout.setSpacing(8)

        self._current_avg_label = QLabel(tr("Average") + ": -")
        self._votes_count_label = QLabel(tr("Total Votes") + ": 0")
        self._result_label = QLabel("-")
        self._result_label.setStyleSheet("font-size: 16px;")

        result_layout.addWidget(self._current_avg_label)
        result_layout.addWidget(self._votes_count_label)
        result_layout.addSpacing(8)
        result_layout.addWidget(self._result_label)
        result_layout.addStretch()

        content.addWidget(self._result_group)
        layout.addLayout(content)

        # Scenarios
        self._scenarios_group = QGroupBox()
        scenarios_widget = QWidget()
        self._scenarios_layout = QHBoxLayout(scenarios_widget)
        self._scenarios_layout.setContentsMargins(12, 12, 12, 12)
        self._scenarios_layout.setSpacing(8)

        # Center scenarios
        scenarios_outer = QHBoxLayout(self._scenarios_group)
        scenarios_outer.addStretch()
        scenarios_outer.addWidget(scenarios_widget)
        scenarios_outer.addStretch()

        layout.addWidget(self._scenarios_group)
        layout.addStretch()
    
    def refresh(self):
        """Refresh subject list and recalculate."""
        # Update labels for language changes
        self._title.setText(tr("Simulator"))
        self._input_group.setTitle(tr("Grade Needed"))
        self._subject_label.setText(tr("Subject") + ":")
        self._target_label.setText(tr("Target Average") + ":")
        self._result_group.setTitle(tr("Calculate"))

        current = self._subject_combo.currentText()
        self._subject_combo.blockSignals(True)
        self._subject_combo.clear()

        for subject in self._db.get_subjects_with_votes():
            self._subject_combo.addItem(subject)

        idx = self._subject_combo.findText(current)
        if idx >= 0:
            self._subject_combo.setCurrentIndex(idx)

        self._subject_combo.blockSignals(False)
        self._calculate()
    
    def _calculate(self):
        """Calculate required grade and scenarios."""
        subject = self._subject_combo.currentText()

        if not subject:
            self._current_avg_label.setText(tr("Average") + ": -")
            self._votes_count_label.setText(tr("Total Votes") + ": 0")
            self._result_label.setText(tr("Subject"))
            self._clear_scenarios()
            return

        votes = self._db.get_votes(subject)

        if not votes:
            self._current_avg_label.setText(tr("Average") + ": -")
            self._votes_count_label.setText(tr("Total Votes") + ": 0")
            self._result_label.setText(tr("Add Vote"))
            self._clear_scenarios()
            return

        avg = calc_average(votes)
        num_votes = len(votes)
        target = self._target_spin.value()

        self._current_avg_label.setText(f"{tr('Average')}: <b>{avg:.2f}</b>")
        self._current_avg_label.setStyleSheet(get_grade_style(avg))
        self._votes_count_label.setText(f"{tr('Total Votes')}: {num_votes}")

        # Calculate required grade
        required = (target * (num_votes + 1)) - (avg * num_votes)

        if required <= 0:
            self._result_label.setText("✓")
            self._result_label.setStyleSheet(
                "color: #27ae60; font-size: 16px; font-weight: bold;"
            )
        elif required > 10:
            self._result_label.setText("✗")
            self._result_label.setStyleSheet(
                "color: #e74c3c; font-size: 16px; font-weight: bold;"
            )
        else:
            self._result_label.setText(f"<b>{required:.1f}</b>")
            self._result_label.setStyleSheet("font-size: 16px;")
        
        # Update scenarios
        self._clear_scenarios()
        
        for grade in range(2, 11):  # 2 to 10
            new_avg = (avg * num_votes + grade) / (num_votes + 1)
            
            box = QGroupBox(f"If {grade}")
            box.setFixedWidth(65)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(6, 6, 6, 6)
            
            value = QLabel(f"<b>{new_avg:.2f}</b>")
            value.setStyleSheet(get_grade_style(new_avg))
            value.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(value)
            
            self._scenarios_layout.addWidget(box)
    
    def _clear_scenarios(self):
        """Clear all scenario boxes."""
        while self._scenarios_layout.count():
            item = self._scenarios_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
