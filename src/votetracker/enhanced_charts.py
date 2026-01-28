"""
Enhanced interactive charts for VoteTracker.
Provides rich visualizations with hover tooltips, animations, and better styling.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QToolTip
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
from datetime import datetime


class InteractiveBarChart(QFrame):
    """
    Enhanced horizontal bar chart with hover effects and tooltips.
    Shows detailed information on hover and smooth animations.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # List of (label, value, color, detail_text)
        self._hovered_index = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(200)
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)

    def set_data(self, data: list):
        """
        Set chart data. Each item: (label, value, color, detail_text)
        detail_text is shown in tooltip
        """
        self._data = data
        self._update_chart()

    def _update_chart(self):
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._data:
            empty = QLabel("No data available")
            empty.setStyleSheet("color: gray; font-size: 14px;")
            empty.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(empty)
            return

        max_val = max(d[1] for d in self._data) if self._data else 1
        if max_val == 0:
            max_val = 1

        for idx, item in enumerate(self._data):
            label = item[0]
            value = item[1]
            color = item[2]
            detail = item[3] if len(item) > 3 else ""

            bar_widget = AnimatedBarRow(
                label=label,
                value=value,
                max_value=max_val,
                color=color,
                detail=detail,
                index=idx
            )
            bar_widget.hovered.connect(self._on_bar_hovered)
            self._layout.addWidget(bar_widget)

    def _on_bar_hovered(self, index: int, detail: str, pos: QPoint):
        """Handle bar hover event."""
        if detail and index >= 0:
            # Show rich tooltip with styling
            QToolTip.showText(
                self.mapToGlobal(pos),
                f"<div style='padding: 4px;'><b>{self._data[index][0]}</b><br>{detail}</div>",
                self
            )


class AnimatedBarRow(QFrame):
    """Single animated bar row with hover effect."""
    from PySide6.QtCore import Signal
    hovered = Signal(int, str, QPoint)

    def __init__(self, label: str, value: float, max_value: float,
                 color: str, detail: str = "", index: int = -1, parent=None):
        super().__init__(parent)
        self._label = label
        self._value = value
        self._max_value = max_value
        self._color = QColor(color)
        self._detail = detail
        self._index = index
        self._current_width = 0
        self._is_hovered = False
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        self._animate_in()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Label
        self._label_widget = QLabel(self._label)
        self._label_widget.setFixedWidth(140)
        self._label_widget.setStyleSheet("""
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self._label_widget)

        # Bar container
        self._bar_container = QFrame()
        self._bar_container.setFixedHeight(32)
        self._bar_container.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f5f5f5, stop:1 #e8e8e8);
            border: 1px solid #d0d0d0;
            border-radius: 6px;
        """)
        bar_layout = QHBoxLayout(self._bar_container)
        bar_layout.setContentsMargins(2, 2, 2, 2)
        bar_layout.setSpacing(0)

        # Bar fill
        self._bar_fill = QFrame()
        # Start at 0% width for animation
        bar_layout.addWidget(self._bar_fill, 0)
        bar_layout.addStretch(100)

        layout.addWidget(self._bar_container, 1)

        # Value label
        self._value_widget = QLabel(f"{self._value:.2f}")
        self._value_widget.setFixedWidth(60)
        self._value_widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value_widget.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
        """)
        layout.addWidget(self._value_widget)

        self.setFixedHeight(40)

    def _animate_in(self):
        """Animate the bar growing from 0 to target width."""
        width_percent = int((self._value / self._max_value) * 100) if self._max_value > 0 else 0

        # Update bar with gradient
        gradient_style = f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._color.name()},
                stop:1 {self._color.lighter(120).name()});
            border-radius: 4px;
        """
        self._bar_fill.setStyleSheet(gradient_style)

        # Get the bar layout
        bar_layout = self._bar_container.layout()
        bar_layout.setStretch(0, width_percent)
        bar_layout.setStretch(1, 100 - width_percent)

    def enterEvent(self, event):
        """Handle mouse enter."""
        self._is_hovered = True
        # Brighten the bar on hover
        hover_style = f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._color.lighter(110).name()},
                stop:1 {self._color.lighter(130).name()});
            border-radius: 4px;
        """
        self._bar_fill.setStyleSheet(hover_style)

        # Emit hover signal
        if self._detail:
            self.hovered.emit(self._index, self._detail, self.mapToGlobal(event.pos()))

    def leaveEvent(self, event):
        """Handle mouse leave."""
        self._is_hovered = False
        # Restore original color
        gradient_style = f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._color.name()},
                stop:1 {self._color.lighter(120).name()});
            border-radius: 4px;
        """
        self._bar_fill.setStyleSheet(gradient_style)


class InteractiveDistributionChart(QFrame):
    """
    Enhanced grade distribution histogram with hover effects.
    Shows count and percentage on hover.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._total_count = 0
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(20, 10, 20, 40)
        self._layout.setSpacing(8)
        self._layout.setAlignment(Qt.AlignBottom)

    def set_data(self, grades: list):
        """Set distribution data from list of grades."""
        # Define ranges with better colors
        ranges = [
            ("2-3", 2, 4, "#c0392b", "Very Low"),
            ("4-5", 4, 5.5, "#e74c3c", "Insufficient"),
            ("5.5-6", 5.5, 6, "#f39c12", "Almost Passing"),
            ("6-7", 6, 7, "#f1c40f", "Sufficient"),
            ("7-8", 7, 8, "#2ecc71", "Good"),
            ("8-9", 8, 9, "#3498db", "Very Good"),
            ("9-10", 9, 10.01, "#9b59b6", "Excellent"),
        ]

        self._data = {}
        self._total_count = len(grades)

        for label, low, high, color, description in ranges:
            count = sum(1 for g in grades if low <= g < high)
            percentage = (count / self._total_count * 100) if self._total_count > 0 else 0
            self._data[label] = (count, color, description, percentage)

        self._update_chart()

    def _update_chart(self):
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._data:
            empty = QLabel("No data available")
            empty.setStyleSheet("color: gray; font-size: 14px;")
            self._layout.addWidget(empty)
            return

        max_count = max(c for c, _, _, _ in self._data.values()) if self._data else 1
        if max_count == 0:
            max_count = 1

        for label, (count, color, description, percentage) in self._data.items():
            bar = DistributionBar(
                label=label,
                count=count,
                max_count=max_count,
                color=color,
                description=description,
                percentage=percentage
            )
            self._layout.addWidget(bar)


class DistributionBar(QFrame):
    """Single bar in distribution chart with animation."""

    def __init__(self, label: str, count: int, max_count: int,
                 color: str, description: str, percentage: float, parent=None):
        super().__init__(parent)
        self._label = label
        self._count = count
        self._max_count = max_count
        self._color = QColor(color)
        self._description = description
        self._percentage = percentage
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignBottom)

        # Count label (on top)
        self._count_label = QLabel(str(self._count))
        self._count_label.setAlignment(Qt.AlignCenter)
        self._count_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
        """)
        layout.addWidget(self._count_label)

        # Bar
        height = int((self._count / self._max_count) * 120) if self._max_count > 0 else 0
        self._bar = QFrame()
        self._bar.setFixedWidth(45)
        self._bar.setFixedHeight(max(height, 8))

        # Gradient effect
        self._bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self._color.lighter(110).name()},
                stop:1 {self._color.name()});
            border: 2px solid {self._color.darker(120).name()};
            border-radius: 6px;
        """)
        layout.addWidget(self._bar, 0, Qt.AlignCenter)

        # Range label (at bottom)
        self._range_label = QLabel(self._label)
        self._range_label.setAlignment(Qt.AlignCenter)
        self._range_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 500;
            color: #34495e;
        """)
        layout.addWidget(self._range_label)

    def enterEvent(self, event):
        """Show tooltip on hover."""
        tooltip = f"""
        <div style='padding: 6px;'>
            <b>{self._description}</b><br>
            Range: {self._label}<br>
            Count: {self._count} grades<br>
            Percentage: {self._percentage:.1f}%
        </div>
        """
        QToolTip.showText(self.mapToGlobal(event.pos()), tooltip, self)

        # Brighten bar on hover
        self._bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self._color.lighter(130).name()},
                stop:1 {self._color.lighter(110).name()});
            border: 2px solid {self._color.name()};
            border-radius: 6px;
        """)

    def leaveEvent(self, event):
        """Restore original style."""
        self._bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self._color.lighter(110).name()},
                stop:1 {self._color.name()});
            border: 2px solid {self._color.darker(120).name()};
            border-radius: 6px;
        """)


class GradeTrendChart(QFrame):
    """
    Interactive line chart showing grade trends over time.
    Displays grade progression with hover to see exact values and dates.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_points = []  # List of (date, grade, description)
        self._hovered_point = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(250)
        self.setStyleSheet("""
            background: white;
            border: 1px solid #d0d0d0;
            border-radius: 8px;
        """)

    def set_data(self, votes: list):
        """
        Set data from list of votes.
        Each vote should have 'date', 'grade', and 'type' keys.
        """
        if not votes:
            self._data_points = []
            self.update()
            return

        # Sort votes by date
        sorted_votes = sorted(votes, key=lambda v: v.get('date', ''))

        self._data_points = [
            (
                v.get('date', ''),
                v.get('grade', 0),
                f"{v.get('type', 'Unknown')} - {v.get('description', 'No description')}"
            )
            for v in sorted_votes
        ]

        self.update()

    def paintEvent(self, event):
        """Custom paint to draw the line chart."""
        super().paintEvent(event)

        if not self._data_points:
            painter = QPainter(self)
            painter.setPen(QColor("#999"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No grade data to display")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate drawing area (with margins)
        margin_left = 50
        margin_right = 20
        margin_top = 30
        margin_bottom = 50

        width = self.width() - margin_left - margin_right
        height = self.height() - margin_top - margin_bottom

        # Find min/max grades for scaling
        grades = [d[1] for d in self._data_points]
        min_grade = max(0, min(grades) - 1)
        max_grade = min(10, max(grades) + 1)
        grade_range = max_grade - min_grade

        if grade_range == 0:
            grade_range = 1

        # Draw background grid
        painter.setPen(QPen(QColor("#e0e0e0"), 1, Qt.DashLine))
        for i in range(5):
            y = margin_top + (height * i / 4)
            painter.drawLine(margin_left, int(y), margin_left + width, int(y))

            # Draw grade labels on Y-axis
            grade_val = max_grade - (grade_range * i / 4)
            painter.setPen(QColor("#666"))
            painter.drawText(5, int(y + 5), f"{grade_val:.1f}")
            painter.setPen(QPen(QColor("#e0e0e0"), 1, Qt.DashLine))

        # Draw threshold lines
        # Passing line (6.0)
        if min_grade <= 6 <= max_grade:
            passing_y = margin_top + height * (1 - (6 - min_grade) / grade_range)
            painter.setPen(QPen(QColor("#27ae60"), 2, Qt.DashLine))
            painter.drawLine(margin_left, int(passing_y), margin_left + width, int(passing_y))

        # Calculate points
        points = []
        for i, (date, grade, desc) in enumerate(self._data_points):
            x = margin_left + (width * i / (len(self._data_points) - 1)) if len(self._data_points) > 1 else margin_left + width / 2
            y = margin_top + height * (1 - (grade - min_grade) / grade_range)
            points.append((x, y, grade, date, desc))

        # Draw gradient area under line
        if len(points) >= 2:
            path = QPainterPath()
            path.moveTo(points[0][0], self.height() - margin_bottom)
            path.lineTo(points[0][0], points[0][1])

            for x, y, _, _, _ in points[1:]:
                path.lineTo(x, y)

            path.lineTo(points[-1][0], self.height() - margin_bottom)
            path.closeSubpath()

            gradient = QLinearGradient(0, margin_top, 0, self.height() - margin_bottom)
            gradient.setColorAt(0, QColor(52, 152, 219, 100))
            gradient.setColorAt(1, QColor(52, 152, 219, 20))
            painter.fillPath(path, QBrush(gradient))

        # Draw line connecting points
        if len(points) >= 2:
            painter.setPen(QPen(QColor("#3498db"), 3))
            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]), int(points[i][1]),
                    int(points[i + 1][0]), int(points[i + 1][1])
                )

        # Draw data points
        for i, (x, y, grade, date, desc) in enumerate(points):
            # Determine point color based on grade
            if grade >= 6:
                point_color = QColor("#27ae60")
            elif grade >= 5.5:
                point_color = QColor("#f39c12")
            else:
                point_color = QColor("#e74c3c")

            # Larger point if hovered
            if i == self._hovered_point:
                painter.setBrush(QBrush(point_color.lighter(120)))
                painter.setPen(QPen(QColor("white"), 3))
                painter.drawEllipse(QPointF(x, y), 8, 8)
            else:
                painter.setBrush(QBrush(point_color))
                painter.setPen(QPen(QColor("white"), 2))
                painter.drawEllipse(QPointF(x, y), 5, 5)

        # Draw date labels on X-axis (only first, middle, last to avoid crowding)
        painter.setPen(QColor("#666"))
        if len(points) > 0:
            # First date
            date_str = self._format_date(points[0][3])
            painter.drawText(int(points[0][0]) - 30, self.height() - 20, date_str)

            # Last date
            if len(points) > 1:
                date_str = self._format_date(points[-1][3])
                painter.drawText(int(points[-1][0]) - 30, self.height() - 20, date_str)

            # Middle date
            if len(points) > 2:
                mid_idx = len(points) // 2
                date_str = self._format_date(points[mid_idx][3])
                painter.drawText(int(points[mid_idx][0]) - 30, self.height() - 20, date_str)

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%b %d")
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str

    def mouseMoveEvent(self, event):
        """Handle mouse move to show tooltips."""
        if not self._data_points:
            return

        margin_left = 50
        margin_right = 20
        margin_top = 30
        margin_bottom = 50

        width = self.width() - margin_left - margin_right
        height = self.height() - margin_top - margin_bottom

        grades = [d[1] for d in self._data_points]
        min_grade = max(0, min(grades) - 1)
        max_grade = min(10, max(grades) + 1)
        grade_range = max_grade - min_grade

        if grade_range == 0:
            grade_range = 1

        # Calculate point positions and check for hover
        old_hovered = self._hovered_point
        self._hovered_point = -1

        for i, (date, grade, desc) in enumerate(self._data_points):
            x = margin_left + (width * i / (len(self._data_points) - 1)) if len(self._data_points) > 1 else margin_left + width / 2
            y = margin_top + height * (1 - (grade - min_grade) / grade_range)

            # Check if mouse is near this point
            distance = ((event.pos().x() - x) ** 2 + (event.pos().y() - y) ** 2) ** 0.5
            if distance < 15:  # Hit radius
                self._hovered_point = i

                # Show tooltip
                tooltip = f"""
                <div style='padding: 6px;'>
                    <b>Grade: {grade:.2f}</b><br>
                    Date: {self._format_date(date)}<br>
                    {desc}
                </div>
                """
                QToolTip.showText(self.mapToGlobal(event.pos()), tooltip, self)
                break

        # Repaint if hover state changed
        if old_hovered != self._hovered_point:
            self.update()

    def leaveEvent(self, event):
        """Clear hover state when mouse leaves."""
        if self._hovered_point != -1:
            self._hovered_point = -1
            self.update()
