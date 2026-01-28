"""
Windows-specific styling for VoteTracker.
Provides a modern, clean look optimized for Windows 10/11.
"""

WINDOWS_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #f5f5f5;
}

/* Navigation Buttons */
QToolButton {
    color: #333333;
    border: none;
    border-radius: 4px;
    padding: 4px;
    background-color: transparent;
}

QToolButton:hover {
    background-color: #e3e3e3;
}

QToolButton:checked {
    background-color: #0078d4;
    color: white;
}

QToolButton:pressed {
    background-color: #005a9e;
}

/* GroupBox */
QGroupBox {
    font-weight: bold;
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    background-color: white;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: #333333;
}

/* Push Buttons */
QPushButton {
    background-color: #f0f0f0;
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    padding: 6px 12px;
    color: #333333;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #e5e5e5;
    border-color: #adadad;
}

QPushButton:pressed {
    background-color: #d4d4d4;
}

QPushButton:disabled {
    background-color: #f5f5f5;
    color: #a0a0a0;
    border-color: #e0e0e0;
}

/* Primary Action Buttons */
QPushButton[class="primary"] {
    background-color: #0078d4;
    border-color: #0078d4;
    color: white;
}

QPushButton[class="primary"]:hover {
    background-color: #106ebe;
}

QPushButton[class="primary"]:pressed {
    background-color: #005a9e;
}

/* Line Edit */
QLineEdit {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
    selection-background-color: #0078d4;
}

QLineEdit:focus {
    border-color: #0078d4;
}

QLineEdit:disabled {
    background-color: #f5f5f5;
    color: #a0a0a0;
}

/* Combo Box */
QComboBox {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QComboBox:hover {
    border-color: #adadad;
}

QComboBox:focus {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #333333;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    border: 1px solid #d4d4d4;
    background-color: white;
    selection-background-color: #0078d4;
    selection-color: white;
}

/* Check Box */
QCheckBox {
    spacing: 8px;
    color: #333333;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #d4d4d4;
    border-radius: 3px;
    background-color: white;
}

QCheckBox::indicator:hover {
    border-color: #adadad;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
    image: none;
}

QCheckBox::indicator:checked:after {
    content: "✓";
    color: white;
}

/* Spin Box */
QSpinBox, QDoubleSpinBox {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #0078d4;
}

/* Date Edit */
QDateEdit {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
}

QDateEdit:focus {
    border-color: #0078d4;
}

/* Calendar Widget */
QCalendarWidget {
    background-color: white;
}

QCalendarWidget QToolButton {
    color: #333333;
    background-color: transparent;
}

QCalendarWidget QToolButton:hover {
    background-color: #e3e3e3;
}

QCalendarWidget QAbstractItemView {
    selection-background-color: #0078d4;
    selection-color: white;
}

/* Table Widget */
QTableWidget {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    background-color: white;
    gridline-color: #e0e0e0;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #0078d4;
    color: white;
}

QTableWidget QHeaderView::section {
    background-color: #f0f0f0;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #d4d4d4;
    border-right: 1px solid #e0e0e0;
    font-weight: bold;
    color: #333333;
}

/* Scroll Bar */
QScrollBar:vertical {
    border: none;
    background-color: #f5f5f5;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #c1c1c1;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a8a8a8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #f5f5f5;
    height: 12px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #c1c1c1;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a8a8a8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    background-color: #f0f0f0;
    text-align: center;
    color: #333333;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #d4d4d4;
    border-radius: 4px;
    background-color: white;
}

QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #d4d4d4;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #333333;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom-color: white;
}

QTabBar::tab:hover:!selected {
    background-color: #e5e5e5;
}

/* Tooltip */
QToolTip {
    border: 1px solid #d4d4d4;
    background-color: white;
    color: #333333;
    padding: 4px;
    border-radius: 4px;
}

/* Menu */
QMenu {
    background-color: white;
    border: 1px solid #d4d4d4;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #e5e5e5;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

/* Label */
QLabel {
    color: #333333;
}

/* Frame */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    /* HLine and VLine */
    color: #d4d4d4;
}
"""


def apply_windows_style(app):
    """
    Apply Windows-specific styling to the application.

    Args:
        app: QApplication instance
    """
    import sys
    if sys.platform == "win32":
        app.setStyleSheet(WINDOWS_STYLESHEET)
