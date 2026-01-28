"""
Constants for VoteTracker application.
"""

# ============================================================================
# GRADE CONSTANTS
# ============================================================================

PASSING_GRADE = 6.0
MIN_GRADE = 0.0
MAX_GRADE = 10.0

GRADE_EXCELLENT = 9.0
GRADE_GOOD = 8.0
GRADE_SUFFICIENT = 6.0
GRADE_INSUFFICIENT = 5.5

# ============================================================================
# UI CONSTANTS
# ============================================================================

# Sidebar
SIDEBAR_WIDTH = 96
NAV_BUTTON_WIDTH = 80
NAV_BUTTON_HEIGHT = 64
NAV_BUTTON_ICON_SIZE = 24

# Window
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700

# Margins and spacing
MARGIN_SMALL = 8
MARGIN_MEDIUM = 12
MARGIN_LARGE = 20

SPACING_SMALL = 4
SPACING_MEDIUM = 8
SPACING_LARGE = 12

# ============================================================================
# COLOR CONSTANTS
# ============================================================================

# Grade colors
COLOR_EXCELLENT = "#27ae60"  # Green
COLOR_GOOD = "#27ae60"       # Green
COLOR_SUFFICIENT = "#f39c12"  # Orange/Yellow
COLOR_INSUFFICIENT = "#e74c3c"  # Red
COLOR_FAIL = "#e74c3c"       # Red

# UI colors
COLOR_ACCENT = "#0078d4"     # Windows blue
COLOR_SUCCESS = "#27ae60"
COLOR_WARNING = "#f39c12"
COLOR_ERROR = "#e74c3c"

# ============================================================================
# VOTE TYPE CONSTANTS
# ============================================================================

VOTE_TYPE_WRITTEN = "Written"
VOTE_TYPE_ORAL = "Oral"
VOTE_TYPE_PRACTICAL = "Practical"

VOTE_TYPES = [VOTE_TYPE_WRITTEN, VOTE_TYPE_ORAL, VOTE_TYPE_PRACTICAL]

# ============================================================================
# TERM CONSTANTS
# ============================================================================

TERM_FIRST = 1
TERM_SECOND = 2

# ============================================================================
# WEIGHT CONSTANTS
# ============================================================================

DEFAULT_WEIGHT = 1.0
MIN_WEIGHT = 0.1
MAX_WEIGHT = 10.0

# ============================================================================
# DATABASE CONSTANTS
# ============================================================================

DB_NAME = "votes.db"

# ============================================================================
# SYNC CONSTANTS
# ============================================================================

DEFAULT_SYNC_INTERVAL = 60  # minutes
FLASH_DURATION = 800  # milliseconds
