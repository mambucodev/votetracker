"""
Cross-platform icon provider for VoteTracker.
Provides icons with proper fallbacks for Windows and other platforms.
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QStyle, QApplication
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvg import QSvgRenderer
from typing import Optional


# Mapping of our icon names to Qt StandardPixmap icons
# Note: Only using StandardPixmap for icons that look good across all platforms
STANDARD_ICON_MAP = {
    # Actions
    "edit-delete": QStyle.StandardPixmap.SP_TrashIcon,
    "document-save": QStyle.StandardPixmap.SP_DialogSaveButton,
    "document-open": QStyle.StandardPixmap.SP_DialogOpenButton,
    "dialog-cancel": QStyle.StandardPixmap.SP_DialogCancelButton,
    # Network
    "network-transmit-receive": QStyle.StandardPixmap.SP_DriveNetIcon,
    # Arrows
    "go-previous": QStyle.StandardPixmap.SP_ArrowBack,
    "go-next": QStyle.StandardPixmap.SP_ArrowForward,
    # Files
    "folder": QStyle.StandardPixmap.SP_DirIcon,
    "x-office-document": QStyle.StandardPixmap.SP_FileIcon,
}


def create_simple_svg_icon(icon_type: str, size: int = 24, color: str = "#000000") -> QIcon:
    """
    Create a simple SVG icon programmatically.
    This replaces emoji fallbacks with clean, scalable vector graphics.
    """
    svg_templates = {
        "home": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 12 l9 -9 l9 9 v10 h-18 Z" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="miter"/>
            <rect x="9" y="14" width="6" height="7" fill="{color}"/>
        </svg>''',

        "dashboard": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="8" height="8" fill="{color}"/>
            <rect x="13" y="3" width="8" height="8" fill="{color}"/>
            <rect x="3" y="13" width="8" height="8" fill="{color}"/>
            <rect x="13" y="13" width="8" height="8" fill="{color}"/>
        </svg>''',

        "list": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="4" width="3" height="3" fill="{color}"/>
            <rect x="8" y="4" width="13" height="3" fill="{color}"/>
            <rect x="3" y="10" width="3" height="3" fill="{color}"/>
            <rect x="8" y="10" width="13" height="3" fill="{color}"/>
            <rect x="3" y="16" width="3" height="3" fill="{color}"/>
            <rect x="8" y="16" width="13" height="3" fill="{color}"/>
        </svg>''',

        "bookmark": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 3 h14 v18 l-7 -5 l-7 5 Z" fill="{color}"/>
        </svg>''',

        "chart-line": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <polyline points="3,18 7,12 12,14 16,8 21,10" stroke="{color}"
                      stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="3" y1="21" x2="21" y2="21" stroke="{color}" stroke-width="2"/>
            <line x1="3" y1="3" x2="3" y2="21" stroke="{color}" stroke-width="2"/>
        </svg>''',

        "calendar": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="5" width="18" height="16" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
            <line x1="3" y1="9" x2="21" y2="9" stroke="{color}" stroke-width="2"/>
            <line x1="7" y1="3" x2="7" y2="7" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <line x1="17" y1="3" x2="17" y2="7" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',

        "document": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 2 h8 l6 6 v14 a2 2 0 0 1 -2 2 h-12 a2 2 0 0 1 -2 -2 v-18 a2 2 0 0 1 2 -2 Z"
                  fill="none" stroke="{color}" stroke-width="2"/>
            <polyline points="14,2 14,8 20,8" fill="none" stroke="{color}" stroke-width="2"/>
        </svg>''',

        "chart-bar": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="14" width="3" height="7" fill="{color}"/>
            <rect x="10" y="8" width="3" height="13" fill="{color}"/>
            <rect x="16" y="11" width="3" height="10" fill="{color}"/>
        </svg>''',

        "settings": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="3" fill="none" stroke="{color}" stroke-width="2"/>
            <path d="M12 2 l1 4 l3 1 l3 -2 l2 3 l-2 3 l1 3 l4 1 v4 l-4 1 l-1 3 l2 3 l-2 3 l-3 -2 l-3 1 l-1 4 h-4 l-1 -4 l-3 -1 l-3 2 l-2 -3 l2 -3 l-1 -3 l-4 -1 v-4 l4 -1 l1 -3 l-2 -3 l2 -3 l3 2 l3 -1 Z"
                  fill="none" stroke="{color}" stroke-width="1.5"/>
        </svg>''',

        "add": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',

        "import": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <polyline points="7,14 12,19 17,14" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="21" x2="19" y2="21" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',

        "export": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="19" x2="12" y2="5" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
            <polyline points="7,10 12,5 17,10" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="21" x2="19" y2="21" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',

        "network": f'''<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" fill="none" stroke="{color}" stroke-width="2"/>
            <path d="M2 12 h20 M12 2 a10 10 0 0 1 0 20 a10 10 0 0 1 0 -20" fill="none" stroke="{color}" stroke-width="2"/>
        </svg>''',
    }

    svg_data = svg_templates.get(icon_type, svg_templates["document"])

    # Create pixmap from SVG
    renderer = QSvgRenderer(svg_data.encode())
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def get_icon(name: str, fallback_type: Optional[str] = None) -> QIcon:
    """
    Get an icon with intelligent fallback system optimized for Windows.

    Priority order:
    1. Qt Standard Icons (platform-native)
    2. Theme icons (if available on the system)
    3. Simple SVG icons (clean, no emojis)

    Args:
        name: Icon name (freedesktop standard name)
        fallback_type: Type of SVG icon to create if all else fails

    Returns:
        QIcon object (never null)
    """
    # Try Qt Standard Icons first (platform-native, work great on Windows)
    if name in STANDARD_ICON_MAP:
        app = QApplication.instance()
        if app:
            icon = app.style().standardIcon(STANDARD_ICON_MAP[name])
            if not icon.isNull():
                return icon

    # Try theme icons (works on Linux with icon themes)
    icon = QIcon.fromTheme(name)
    if not icon.isNull():
        return icon

    # Try with -symbolic suffix
    icon = QIcon.fromTheme(f"{name}-symbolic")
    if not icon.isNull():
        return icon

    # Create simple SVG icon as last resort (no emojis!)
    if fallback_type:
        return create_simple_svg_icon(fallback_type)

    # Map icon names to SVG types
    svg_type_map = {
        "view-dashboard": "dashboard",
        "dashboard-show": "dashboard",
        "go-home": "home",
        "user-home": "home",
        "view-list-details": "list",
        "bookmarks": "bookmark",
        "office-chart-line": "chart-line",
        "view-calendar": "calendar",
        "office-report": "document",
        "x-office-document": "document",
        "text-x-generic": "document",
        "application-pdf": "document",
        "view-statistics": "chart-bar",
        "configure": "settings",
        "list-add": "add",
        "document-import": "import",
        "document-export": "export",
        "document-open": "document",
        "network-transmit-receive": "network",
    }

    svg_type = svg_type_map.get(name, "document")
    return create_simple_svg_icon(svg_type)


def has_icon(name: str) -> bool:
    """
    Check if an icon is available (always returns True now since we have SVG fallbacks).
    """
    return True  # We always have a fallback


def get_icon_fallback(name: str) -> str:
    """
    Get text fallback for an icon (for accessibility/debugging).
    No longer uses emojis.
    """
    return "●"  # Simple bullet point
