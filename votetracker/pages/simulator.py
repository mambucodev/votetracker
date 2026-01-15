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
        
        title = QLabel("Simulator")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        # Main content
        content = QHBoxLayout()
        content.setSpacing(16)
        
        # Input group
        input_group = QGroupBox("What grade do I need?")
        input_layout = QFormLayout(input_group)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        
        self._subject_combo = QComboBox()
        self._subject_combo.setMinimumWidth(150)
        self._subject_combo.currentTextChanged.connect(self._calculate)
        input_layout.addRow("Subject:", self._subject_combo)
        
        self._target_spin = QDoubleSpinBox()
        self._target_spin.setRange(1.0, 10.0)
        self._target_spin.setValue(6.0)
        self._target_spin.setSingleStep(0.5)
        self._target_spin.valueChanged.connect(self._calculate)
        input_layout.addRow("Target:", self._target_spin)
        
        content.addWidget(input_group)
        
        # Result group
        result_group = QGroupBox("Result")
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(16, 16, 16, 16)
        result_layout.setSpacing(8)
        
        self._current_avg_label = QLabel("Current Average: -")
        self._votes_count_label = QLabel("Recorded Votes: 0")
        self._result_label = QLabel("-")
        self._result_label.setStyleSheet("font-size: 16px;")
        
        result_layout.addWidget(self._current_avg_label)
        result_layout.addWidget(self._votes_count_label)
        result_layout.addSpacing(8)
        result_layout.addWidget(self._result_label)
        result_layout.addStretch()
        
        content.addWidget(result_group)
        layout.addLayout(content)
        
        # Scenarios
        scenarios_group = QGroupBox("Possible Scenarios")
        scenarios_widget = QWidget()
        self._scenarios_layout = QHBoxLayout(scenarios_widget)
        self._scenarios_layout.setContentsMargins(12, 12, 12, 12)
        self._scenarios_layout.setSpacing(8)
        
        # Center scenarios
        scenarios_outer = QHBoxLayout(scenarios_group)
        scenarios_outer.addStretch()
        scenarios_outer.addWidget(scenarios_widget)
        scenarios_outer.addStretch()
        
        layout.addWidget(scenarios_group)
        layout.addStretch()
    
    def refresh(self):
        """Refresh subject list and recalculate."""
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
            self._current_avg_label.setText("Current Average: -")
            self._votes_count_label.setText("Recorded Votes: 0")
            self._result_label.setText("Select a subject")
            self._clear_scenarios()
            return
        
        votes = self._db.get_votes(subject)
        
        if not votes:
            self._current_avg_label.setText("Current Average: -")
            self._votes_count_label.setText("Recorded Votes: 0")
            self._result_label.setText("Add at least one vote")
            self._clear_scenarios()
            return
        
        avg = calc_average(votes)
        num_votes = len(votes)
        target = self._target_spin.value()
        
        self._current_avg_label.setText(f"Current Average: <b>{avg:.2f}</b>")
        self._current_avg_label.setStyleSheet(get_grade_style(avg))
        self._votes_count_label.setText(f"Recorded Votes: {num_votes}")
        
        # Calculate required grade
        required = (target * (num_votes + 1)) - (avg * num_votes)
        
        if required <= 0:
            self._result_label.setText("Target already reached!")
            self._result_label.setStyleSheet(
                "color: #27ae60; font-size: 16px; font-weight: bold;"
            )
        elif required > 10:
            self._result_label.setText("Impossible with a single test")
            self._result_label.setStyleSheet(
                "color: #e74c3c; font-size: 16px; font-weight: bold;"
            )
        else:
            self._result_label.setText(f"You need at least: <b>{required:.1f}</b>")
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
