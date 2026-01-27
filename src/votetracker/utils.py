"""
Utility functions for VoteTracker.
Contains calculation helpers, color utilities, and icon helpers.
"""

from typing import List, Dict
from PySide6.QtGui import QColor, QIcon


# ============================================================================
# GRADE CALCULATIONS
# ============================================================================

def calc_average(votes: List[Dict]) -> float:
    """Calculate the average grade from a list of votes."""
    if not votes:
        return 0.0
    total = sum(v.get("grade", 0) * v.get("weight", 1.0) for v in votes)
    weights = sum(v.get("weight", 1.0) for v in votes)
    return total / weights if weights > 0 else 0.0


def round_report_card(average: float) -> int:
    """
    Round average to report card grade.
    Italian system: >= 0.5 rounds up, < 0.5 rounds down.
    """
    if average <= 0:
        return 0
    decimal = average - int(average)
    if decimal >= 0.5:
        return int(average) + 1
    return int(average)


# ============================================================================
# STATUS COLORS
# ============================================================================

class StatusColors:
    """Color constants for grade status indicators."""

    FAILING = QColor("#e74c3c")      # Red - below 5.5
    WARNING = QColor("#f39c12")      # Yellow/Orange - 5.5 to 6
    PASSING = QColor("#27ae60")      # Green - 6 and above
    
    WRITTEN = QColor("#a855f7")      # Purple for written grades
    ORAL = QColor("#06b6d4")         # Cyan for oral grades
    PRACTICAL = QColor("#f97316")    # Orange for practical grades


def get_status_color(average: float) -> QColor:
    """Get the status color based on average grade."""
    if average < 5.5:
        return StatusColors.FAILING
    elif average < 6:
        return StatusColors.WARNING
    return StatusColors.PASSING


def get_type_color(vote_type: str) -> QColor:
    """Get color for vote type."""
    type_colors = {
        "Written": StatusColors.WRITTEN,
        "Oral": StatusColors.ORAL,
        "Practical": StatusColors.PRACTICAL,
    }
    return type_colors.get(vote_type, StatusColors.WRITTEN)


def get_grade_style(grade: float) -> str:
    """Get CSS style string for grade display."""
    color = get_status_color(grade).name()
    return f"font-weight: bold; color: {color};"


def get_status_icon_name(average: float) -> str:
    """Get Breeze theme icon name based on average."""
    if average < 5.5:
        return "data-error"
    elif average < 6:
        return "data-warning"
    return "data-success"


# ============================================================================
# ICON HELPERS
# ============================================================================

# Fallback text/emoji for systems without Breeze icons
ICON_FALLBACKS = {
    # Navigation
    "go-home": "🏠",
    "user-home": "🏠",
    "view-dashboard": "📊",
    "dashboard-show": "📊",
    "view-list-details": "📋",
    "folder": "📁",
    "bookmarks": "🔖",
    "office-chart-line": "📈",
    "x-office-document": "📄",
    "text-x-generic": "📄",
    "application-pdf": "📄",
    "office-report": "📄",
    "view-statistics": "📊",
    "input-keyboard": "⌨️",
    "configure": "⚙️",
    # Actions
    "list-add": "+",
    "edit-delete": "✕",
    "document-edit": "✎",
    "edit-rename": "✎",
    "document-save": "💾",
    "document-import": "📥",
    "document-export": "📤",
    "document-open": "📂",
    "dialog-cancel": "✕",
    # Arrows
    "go-previous": "◀",
    "go-next": "▶",
    # Status
    "data-success": "●",
    "data-warning": "●",
    "data-error": "●",
}


def get_symbolic_icon(name: str) -> QIcon:
    """
    Try to get symbolic icon from theme, fallback to regular.
    Returns null icon if not found (use has_icon to check).
    """
    # Try symbolic version first - they adapt to theme colors
    icon = QIcon.fromTheme(f"{name}-symbolic")
    if icon.isNull():
        icon = QIcon.fromTheme(name)
    return icon


def has_icon(name: str) -> bool:
    """Check if a theme icon is available."""
    return not get_symbolic_icon(name).isNull()


def get_icon_fallback(name: str) -> str:
    """Get fallback text/emoji for an icon."""
    return ICON_FALLBACKS.get(name, "•")


# ============================================================================
# DATE HELPERS
# ============================================================================

def get_school_year_name(start_year: int) -> str:
    """Generate school year name from start year (e.g., 2025 -> '2025/2026')."""
    return f"{start_year}/{start_year + 1}"


def get_short_year_name(start_year: int) -> str:
    """Generate short school year name (e.g., 2025 -> '25/26')."""
    return f"{start_year % 100}/{(start_year + 1) % 100}"
