"""
Centralized style constants and helpers for VoteTracker UI.

Use these instead of inline ``setStyleSheet()`` calls. Keeping styling in one
place makes the UI consistent, makes global tweaks (theme, dark mode) trivial,
and keeps pages focused on layout instead of cosmetics.

Convention:
- ``STYLE_*`` constants are complete stylesheet strings, ready to pass to
  ``widget.setStyleSheet()``.
- Helper functions build strings that depend on a runtime value (e.g. a color
  computed from a grade).
- Layout numbers (margins, spacing) live in :mod:`.constants`, not here.
"""
from __future__ import annotations

# ============================================================================
# TYPOGRAPHY
# ============================================================================

STYLE_PAGE_TITLE = "font-size: 20px; font-weight: bold;"
STYLE_SECTION_TITLE = "font-size: 16px; font-weight: bold;"
STYLE_STAT_VALUE = "font-size: 24px; font-weight: bold;"
STYLE_BOLD = "font-weight: bold;"

# ============================================================================
# MUTED / SECONDARY TEXT
# ============================================================================

STYLE_MUTED = "color: gray;"
STYLE_MUTED_CAPTION = "color: gray; font-size: 12px;"
STYLE_MUTED_SMALL = "color: gray; font-size: 11px;"
STYLE_MUTED_ITALIC_SMALL = "color: gray; font-style: italic; font-size: 11px;"

# ============================================================================
# EMPTY STATES
# ============================================================================

STYLE_EMPTY_STATE = "color: gray; padding: 20px;"
STYLE_EMPTY_STATE_LARGE = "color: gray; font-weight: bold; padding: 40px;"

# ============================================================================
# SEPARATORS / DIVIDERS
# ============================================================================

STYLE_SEPARATOR = "background-color: rgba(128, 128, 128, 0.3);"

# ============================================================================
# HELPERS (dynamic styles)
# ============================================================================

def stat_value_colored(color: str) -> str:
    """Stat value style with an explicit color (e.g. red for failing count)."""
    return f"font-size: 24px; font-weight: bold; color: {color};"


def grade_cell(grade_style: str) -> str:
    """Compose the grade-color style (from ``utils.get_grade_style``) with the
    standard bold/medium sizing used for grade cells in lists."""
    return grade_style + "font-weight: bold; font-size: 16px;"
