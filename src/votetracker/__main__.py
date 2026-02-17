"""
Entry point for VoteTracker application.
Run with: python -m votetracker
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

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
    # Note: AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps are enabled by default in Qt6

    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("VoteTracker")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("VoteTracker")
    app.setDesktopFileName("votetracker")

    # Set application icon
    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        # Fallback to system theme icon (installed via PKGBUILD to hicolor)
        theme_icon = QIcon.fromTheme("votetracker")
        if not theme_icon.isNull():
            app.setWindowIcon(theme_icon)

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
