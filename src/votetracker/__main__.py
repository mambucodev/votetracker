"""
Entry point for VoteTracker application.
Run with: python -m votetracker
"""

import sys
from PySide6.QtWidgets import QApplication

from .mainwindow import MainWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("VoteTracker")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("VoteTracker")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
