# VoteTracker v2.0

A school grade management application built with Python and PySide6 (Qt6).

## Features

- **Grade Tracking**: Record grades with type (Written/Oral/Practical), date, and weight
- **School Years**: Manage multiple school years with easy switching
- **Terms (Quadrimestri)**: Split grades by term (1st/2nd semester)
- **Dashboard**: Overview with statistics and subject cards
- **Simulator**: Calculate what grade you need to reach a target average
- **Report Card**: Simulated report card with rounding rules
- **Import/Export**: JSON support for backup and data transfer
- **Cross-platform**: Works on Linux, Windows, and macOS
- **Native Theme**: Uses system Qt theme (Breeze on KDE, native on Windows)

## Installation

### Option 1: Quick install script (Linux)
```bash
# First install PySide6:
# Arch:   sudo pacman -S pyside6
# Debian: sudo apt install python3-pyside6

# Then run installer
./install.sh

# Run from anywhere
votetracker
```

### Option 2: Arch Linux (PKGBUILD)
```bash
# Build and install with pacman
makepkg -si
```

### Option 3: Install with pip
```bash
pip install .
votetracker
```

### Option 4: Run directly (no install)
```bash
pip install PySide6  # or use system package
python -m votetracker
```

### Option 5: Create standalone binary
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
python build.py

# Or single-file binary
python build.py --onefile

# Or AppImage (Linux only, requires appimagetool)
python build.py --appimage
```

## Project Structure

```
votetracker/
├── install.sh          # Linux install script
├── uninstall.sh        # Linux uninstall script
├── PKGBUILD            # Arch Linux package
├── votetracker.desktop # Linux .desktop file
├── pyproject.toml      # pip install config
├── build.py            # PyInstaller/AppImage build
├── README.md
├── votetracker/
│   ├── __init__.py     # Package info
│   ├── __main__.py     # Entry point
│   ├── database.py     # SQLite manager
│   ├── utils.py        # Helpers and colors
│   ├── widgets.py      # Custom Qt widgets
│   ├── dialogs.py      # Dialog windows
│   ├── mainwindow.py   # Main window
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py
│       ├── votes.py
│       ├── subjects.py
│       ├── simulator.py
│       ├── report_card.py
│       └── settings.py
```

## Data Storage

Data is stored in SQLite at:
- **Linux**: `~/.local/share/votetracker/votes.db`
- **Windows**: `%APPDATA%/votetracker/votes.db`
- **macOS**: `~/Library/Application Support/votetracker/votes.db`

## JSON Import Format

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

Also supports Italian field names: `materia`, `voto`, `tipo` (Scritto/Orale), `quadrimestre`, `data`, `desc`, `peso`

## Platform Notes

- **Linux (KDE)**: Uses Breeze icons natively
- **Windows**: Uses emoji/text fallbacks for icons, native Windows theme
- **macOS**: Uses native macOS styling

## Requirements

- Python 3.8+
- PySide6

## License

MIT License
