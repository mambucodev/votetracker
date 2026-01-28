"""
Entry point for VoteTracker application.
Run with: python -m votetracker
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .mainwindow import MainWindow
from .windows_style import apply_windows_style


def main():
    """Main entry point."""
    # Windows-specific optimizations (must be set before QApplication creation)
    if sys.platform == "win32":
        # Enable high DPI scaling for Windows
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        # Set DPI awareness (helps with text rendering on Windows)
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
        # Improve font rendering on Windows
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Note: AA_EnableHighDpiScaling is enabled by default in Qt6, no need to set it

    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("VoteTracker")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("VoteTracker")

    # Improve font rendering on Windows
    if sys.platform == "win32":
        # Use Segoe UI on Windows (native Windows 10/11 font)
        font = QFont("Segoe UI", 9)
        app.setFont(font)

    # Apply Windows-specific styling
    apply_windows_style(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
