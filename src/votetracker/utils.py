"""
Utility functions for VoteTracker.
Contains calculation helpers, color utilities, and icon helpers.
"""

from typing import List, Dict
from PySide6.QtGui import QColor, QIcon
from .constants import (
    PASSING_GRADE, GRADE_INSUFFICIENT,
    COLOR_FAIL, COLOR_SUFFICIENT, COLOR_GOOD
)


# ============================================================================
# GRADE CALCULATIONS
# ============================================================================

def calc_average(votes: List[Dict]) -> float:
    """
    Calculate the average grade from a list of votes.
    Excludes grades that are 0.00 (e.g., + or - marks that don't count toward average).
    """
    if not votes:
        return 0.0

    # Filter out grades that are 0 (+ or - marks)
    valid_votes = [v for v in votes if v.get("grade", 0) > 0]

    if not valid_votes:
        return 0.0

    total = sum(v.get("grade", 0) * v.get("weight", 1.0) for v in valid_votes)
    weights = sum(v.get("weight", 1.0) for v in valid_votes)
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

    FAILING = QColor(COLOR_FAIL)         # Red - below 5.5
    WARNING = QColor(COLOR_SUFFICIENT)   # Yellow/Orange - 5.5 to 6
    PASSING = QColor(COLOR_GOOD)         # Green - 6 and above

    WRITTEN = QColor("#a855f7")      # Purple for written grades
    ORAL = QColor("#06b6d4")         # Cyan for oral grades
    PRACTICAL = QColor("#f97316")    # Orange for practical grades


def get_status_color(average: float) -> QColor:
    """Get the status color based on average grade."""
    if average < GRADE_INSUFFICIENT:
        return StatusColors.FAILING
    elif average < PASSING_GRADE:
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
    if average < GRADE_INSUFFICIENT:
        return "data-error"
    elif average < PASSING_GRADE:
        return "data-warning"
    return "data-success"


# ============================================================================
# ICON HELPERS
# ============================================================================

# Import the new icon provider system
from .icon_provider import get_icon as _get_icon, has_icon as _has_icon, get_icon_fallback as _get_icon_fallback


def get_symbolic_icon(name: str) -> QIcon:
    """
    Get icon using the new cross-platform icon provider.
    Now optimized for Windows with no emoji fallbacks.

    Returns a QIcon that's never null.
    """
    return _get_icon(name)


def has_icon(name: str) -> bool:
    """Check if an icon is available (always True with new system)."""
    return _has_icon(name)


def get_icon_fallback(name: str) -> str:
    """Get text fallback for an icon (no emojis, just simple text)."""
    return _get_icon_fallback(name)


# ============================================================================
# DATE HELPERS
# ============================================================================

def get_school_year_name(start_year: int) -> str:
    """Generate school year name from start year (e.g., 2025 -> '2025/2026')."""
    return f"{start_year}/{start_year + 1}"


def get_short_year_name(start_year: int) -> str:
    """Generate short school year name (e.g., 2025 -> '25/26')."""
    return f"{start_year % 100}/{(start_year + 1) % 100}"
