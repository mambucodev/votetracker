# VoteTracker

<p align="center">
  <img src="icons/icon-256.png" alt="VoteTracker Icon" width="128" height="128">
</p>

> **100% Vibe Coded**
>
> This project is entirely written and maintained by AI. Not a single line of code was written by a human. Built with [Claude Code](https://claude.ai/code).

A modern school grade management application built with Python and PySide6 (Qt6).

## Features

### Core
- **Grade Tracking** - Record grades with type (Written/Oral/Practical), date, description, and weight
- **School Years** - Manage multiple school years with easy switching
- **Terms** - Split grades by semester (1st/2nd term)
- **Subjects** - Organize grades by subject with automatic averages

### Pages
- **Dashboard** - Overview with statistics and subject cards at a glance
- **Votes** - Full grade list with filtering, sorting, and CRUD operations
- **Subjects** - Subject management with per-subject statistics
- **Simulator** - Calculate what grade you need to reach a target average
- **Calendar** - View grades plotted on a calendar with highlighted dates
- **Report Card** - Simulated report card with Italian rounding rules and PDF export
- **Statistics** - Detailed analytics with grade distribution charts
- **Settings** - Import/export data, manage school years

### Quality of Life
- **Undo/Redo** - Ctrl+Z / Ctrl+Shift+Z for grade operations
- **Keyboard Shortcuts** - Full keyboard navigation (see below)
- **PDF Export** - Export report cards to clean, minimal PDFs
- **Localization** - English and Italian language support (auto-detects system language)
- **Onboarding** - First-run wizard to set up subjects
- **Cross-platform** - Works on Linux, Windows, and macOS
- **Native Theme** - Uses system Qt theme (Breeze on KDE, native elsewhere)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+1-8` | Jump to page (Dashboard, Votes, Subjects, Simulator, Calendar, Report, Statistics, Settings) |
| `PgUp/PgDown` | Navigate between pages |
| `Ctrl+Z` | Undo last grade operation |
| `Ctrl+Shift+Z` / `Ctrl+Y` | Redo |
| `?` | Show keyboard shortcuts help |
| `1` / `2` | Switch term (on applicable pages) |

### Votes Page
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | Add new grade |
| `Enter` | Edit selected grade |
| `Delete` | Delete selected grade |

### Settings Page
| Shortcut | Action |
|----------|--------|
| `Ctrl+I` | Import data |
| `Ctrl+E` | Export data |

## Installation

### Arch Linux (Recommended)
```bash
cd scripts && makepkg -si
```

### Quick Install (Linux)
```bash
# Install dependencies first:
# Arch: sudo pacman -S pyside6 python-reportlab
# Debian: sudo apt install python3-pyside6 python3-reportlab

./scripts/install.sh
votetracker
```

### pip
```bash
pip install .
votetracker
```

### Run Directly
```bash
pip install PySide6 reportlab
python -m votetracker
```

### Build Standalone Binary
```bash
pip install pyinstaller
python scripts/build.py --onefile
```

## Requirements

- Python 3.8+
- PySide6
- reportlab (for PDF export)
- requests (for ClasseViva integration)

### Optional Features

**Axios Italia Integration:**
- Requires `lxml` for HTML parsing
  ```bash
  # Arch Linux
  sudo pacman -S python-lxml

  # pip
  pip install lxml
  ```
- The Axios provider will automatically appear in Settings once lxml is installed

## Data Storage

Data is stored in SQLite at:
- **Linux**: `~/.local/share/votetracker/votes.db`
- **Windows**: `%APPDATA%/votetracker/votes.db`
- **macOS**: `~/Library/Application Support/votetracker/votes.db`

## Import/Export Format

```json
[
  {
    "subject": "Math",
    "grade": 7.5,
    "type": "Written",
    "term": 1,
    "date": "2025-01-15",
    "description": "Chapter 5 test",
    "weight": 1.0
  }
]
```

Also supports Italian field names: `materia`, `voto`, `tipo` (Scritto/Orale/Pratico), `quadrimestre`, `data`, `desc`, `peso`

## Project Structure

```
votetracker/
├── src/
│   └── votetracker/
│       ├── __init__.py      # Package info
│       ├── __main__.py      # Entry point
│       ├── database.py      # SQLite manager
│       ├── undo.py          # Undo/redo manager
│       ├── i18n.py          # Internationalization
│       ├── utils.py         # Helpers and colors
│       ├── widgets.py       # Custom Qt widgets
│       ├── dialogs.py       # Dialog windows
│       ├── mainwindow.py    # Main window
│       └── pages/
│           ├── dashboard.py
│           ├── votes.py
│           ├── subjects.py
│           ├── simulator.py
│           ├── calendar.py
│           ├── report_card.py
│           ├── statistics.py
│           └── settings.py
├── scripts/
│   ├── build.py             # PyInstaller build script
│   ├── install.sh           # Linux install script
│   ├── uninstall.sh         # Linux uninstall script
│   ├── PKGBUILD             # Arch Linux package
│   └── votetracker.desktop  # Desktop entry
├── pyproject.toml           # Python package config
└── README.md
```

## License

MIT License
