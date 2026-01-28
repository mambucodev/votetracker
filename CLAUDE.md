# CLAUDE.md - VoteTracker Development Guide

> **⚠️ IMPORTANT: UPDATE THIS FILE**
> Whenever you make changes to the codebase, **UPDATE THIS FILE** to reflect those changes.
> Keep class names, function signatures, dialog names, and file purposes up to date.

---

## Project Overview

**VoteTracker** is a modern school grade management application built with Python and PySide6 (Qt6). It allows students to track their grades across multiple subjects, school years, and terms (semesters), with features like grade simulation, statistics, calendar views, report card generation, and ClasseViva integration.

### Key Features
- Grade tracking with type (Written/Oral/Practical), weight, date, and descriptions
- Multi-year and multi-term support
- ClasseViva integration for automatic grade import from Italian electronic registers
- Smart subject mapping with fuzzy matching
- Grade simulator to calculate needed grades
- PDF report card export
- Undo/Redo system
- Full keyboard shortcuts
- English and Italian localization
- Statistics and charts

---

## How to Run

### Development
```bash
# From project root
python -m src.votetracker

# Or with run.py
python run.py
```

### Install and Run
```bash
# Install with pip
pip install .
votetracker

# Or install on Arch Linux
cd scripts && makepkg -si
votetracker
```

### Build
```bash
# Build standalone binary
python scripts/build.py --onefile

# Build Arch Linux package
cd scripts && makepkg
```

---

## Project Structure

```
votetracker/
├── src/votetracker/          # Main application package
│   ├── __init__.py           # Package metadata (version, author)
│   ├── __main__.py           # Entry point
│   ├── database.py           # SQLite database manager
│   ├── mainwindow.py         # Main application window
│   ├── dialogs.py            # All dialog windows
│   ├── widgets.py            # Custom Qt widgets
│   ├── undo.py               # Undo/redo manager
│   ├── utils.py              # Utility functions
│   ├── constants.py          # Application constants
│   ├── i18n.py               # Internationalization
│   ├── classeviva.py         # ClasseViva API client
│   ├── subject_matcher.py    # Smart subject matching/mapping
│   └── pages/                # Application pages
│       ├── __init__.py
│       ├── dashboard.py      # Overview page
│       ├── votes.py          # Grade list page
│       ├── subjects.py       # Subject management
│       ├── simulator.py      # Grade simulator
│       ├── calendar.py       # Calendar view
│       ├── report_card.py    # Report card with PDF export
│       ├── statistics.py     # Statistics and charts
│       └── settings.py       # Settings and data management
├── tests/                    # Unit tests
│   ├── test_database.py      # Database operations tests
│   └── test_utils.py         # Utility functions tests
├── scripts/                  # Build and install scripts
│   ├── build.py              # PyInstaller build script
│   ├── install.sh            # Linux install script
│   ├── uninstall.sh          # Linux uninstall script
│   ├── PKGBUILD              # Arch Linux package definition
│   └── votetracker.desktop   # Desktop entry file
├── pyproject.toml            # Python package configuration
├── VoteTracker.spec          # PyInstaller spec file
├── run.py                    # Quick run script
└── README.md                 # User documentation
```

---

## File Details

### Core Files

#### `src/votetracker/__init__.py`
**Purpose:** Package metadata
- `__version__`: Current version string
- `__author__`: Author information

#### `src/votetracker/__main__.py`
**Purpose:** Application entry point
- **Function:** `main()` - Initializes QApplication and shows main window

#### `src/votetracker/database.py`
**Purpose:** SQLite database operations
- **Class:** `Database`
  - **Methods:**
    - `get_db_path()` - Returns database file path
    - `get_data_dir()` - Returns application data directory
    - School Years:
      - `get_school_years()` - Get all school years
      - `get_active_school_year()` - Get currently active year
      - `set_active_school_year(year_id)` - Set active year
      - `add_school_year(start_year)` - Add new school year
      - `delete_school_year(year_id)` - Delete school year
    - Settings:
      - `get_setting(key, default)` - Get setting value
      - `set_setting(key, value)` - Set setting value
      - `get_current_term()` - Get current term (1 or 2)
      - `set_current_term(term)` - Set current term
    - ClasseViva Credentials:
      - `save_classeviva_credentials(username, password)` - Save credentials (base64 encoded)
      - `get_classeviva_credentials()` - Retrieve credentials
      - `clear_classeviva_credentials()` - Remove credentials
      - `has_classeviva_credentials()` - Check if stored
      - `get_last_sync_time()` - Get last sync timestamp
      - `set_last_sync_time(timestamp)` - Set last sync timestamp
      - `get_auto_sync_enabled()` - Check if auto-sync is on
      - `set_auto_sync_enabled(enabled)` - Enable/disable auto-sync
      - `get_sync_interval()` - Get sync interval in minutes
      - `set_sync_interval(minutes)` - Set sync interval
    - ClasseViva Subject Mappings:
      - `save_subject_mapping(cv_subject, vt_subject)` - Save CV→VT mapping
      - `get_subject_mapping(cv_subject)` - Get VT subject for CV subject
      - `get_all_subject_mappings()` - Get all mappings as dict
      - `clear_subject_mapping(cv_subject)` - Remove one mapping
      - `clear_all_subject_mappings()` - Remove all mappings
    - Subjects:
      - `get_subjects()` - Get all subject names
      - `get_subject_id(name)` - Get subject ID by name
      - `add_subject(name)` - Add new subject
      - `rename_subject(old_name, new_name)` - Rename subject
      - `delete_subject(name)` - Delete subject and votes
    - Votes:
      - `get_votes(subject, school_year_id, term)` - Get votes with filters
      - `add_vote(subject, grade, vote_type, date, description, term, weight, school_year_id)` - Add vote
      - `update_vote(vote_id, ...)` - Update existing vote
      - `get_vote(vote_id)` - Get single vote
      - `delete_vote(vote_id)` - Delete vote
      - `vote_exists(subject, grade, date, vote_type, school_year_id)` - Check duplicate
      - `get_subjects_with_votes(school_year_id, term)` - Get subjects that have votes
    - Grade Goals:
      - `set_grade_goal(subject, target_grade, school_year_id, term)` - Set or update grade goal
      - `get_grade_goal(subject, school_year_id, term)` - Get grade goal for subject
      - `delete_grade_goal(subject, school_year_id, term)` - Delete grade goal
      - `get_all_grade_goals(school_year_id, term)` - Get all goals for year/term
      - `calculate_needed_grade(subject, target, school_year_id, term, new_weight)` - Calculate grade needed to reach target
    - Import/Export:
      - `import_votes(votes, school_year_id)` - Import from JSON
      - `export_votes(school_year_id, term)` - Export to JSON
      - `clear_votes(school_year_id, term)` - Delete votes

#### `src/votetracker/mainwindow.py`
**Purpose:** Main application window
- **Class:** `MainWindow(QMainWindow)`
  - **Attributes:**
    - `_db`: Database instance
    - `_undo_manager`: UndoManager instance
    - `_page_stack`: QStackedWidget for pages
    - `_nav_buttons`: List of navigation buttons
    - `_pages`: List of page instances
  - **Methods:**
    - `_setup_ui()` - Create UI layout
    - `_create_navigation()` - Create sidebar navigation
    - `_create_pages()` - Initialize all pages
    - `_switch_page(index)` - Switch to page by index
    - `_refresh_all_pages()` - Refresh all page data
    - `_handle_undo()` - Handle Ctrl+Z
    - `_handle_redo()` - Handle Ctrl+Shift+Z
    - `keyPressEvent(event)` - Global keyboard shortcuts

#### `src/votetracker/dialogs.py`
**Purpose:** All dialog windows
- **Classes:**
  - `AddVoteDialog(QDialog)` - Add/edit vote dialog
    - `get_vote_data()` - Returns vote dict
  - `AddSubjectDialog(QDialog)` - Add new subject
    - `get_name()` - Returns subject name
  - `EditSubjectDialog(QDialog)` - Edit/delete subject
    - `action`: "rename" or "delete"
    - `new_name`: New name if renaming
  - `AddSchoolYearDialog(QDialog)` - Add school year
    - `get_start_year()` - Returns start year int
  - `ManageSchoolYearsDialog(QDialog)` - Manage all years
    - `was_changed()` - Returns bool if changes made
  - `ShortcutsHelpDialog(QDialog)` - Keyboard shortcuts help
  - `OnboardingWizard(QDialog)` - First-run setup wizard
  - `SubjectMappingDialog(QDialog)` - Map ClasseViva subjects to VoteTracker subjects
    - Constructor: `(cv_subjects: List[str], db: Database, parent)`
    - `get_mappings()` - Returns Dict[cv_subject, vt_subject]
    - Shows table with auto-suggestions based on fuzzy matching
    - Color-coded confidence levels
  - `ManageSubjectMappingsDialog(QDialog)` - View/edit existing subject mappings
    - Constructor: `(db: Database, parent)`
    - `was_changed()` - Returns bool if changes made
    - Shows table of all current ClasseViva→VoteTracker mappings
    - Allows editing and deleting individual mappings

#### `src/votetracker/widgets.py`
**Purpose:** Custom Qt widgets
- **Classes:**
  - `SubjectCard(QWidget)` - Dashboard subject card with average
  - `VoteTableWidget(QTableWidget)` - Enhanced table for votes
  - `ChartWidget(QWidget)` - Base chart widget
  - `GradeDistributionChart(ChartWidget)` - Histogram chart
  - `GradeTrendChart(ChartWidget)` - Line chart over time

#### `src/votetracker/undo.py`
**Purpose:** Undo/redo functionality
- **Class:** `UndoManager`
  - **Methods:**
    - `record_add(vote_data)` - Record vote addition
    - `record_delete(vote_data)` - Record vote deletion
    - `record_edit(old_data, new_data)` - Record vote edit
    - `undo()` - Undo last action
    - `redo()` - Redo last undone action
    - `can_undo()` - Check if undo available
    - `can_redo()` - Check if redo available
    - `clear()` - Clear history

#### `src/votetracker/utils.py`
**Purpose:** Utility functions
- **Functions:**
  - `get_grade_color(grade)` - Returns color for grade (red/yellow/green)
  - `get_symbolic_icon(name)` - Returns QIcon for icon name
  - `format_grade(grade)` - Format grade to 2 decimals
  - `calculate_average(votes, weights)` - Calculate weighted average
  - `round_italian(value)` - Italian rounding (0.5 rounds up)

#### `src/votetracker/constants.py`
**Purpose:** Application-wide constants
- **Constants:**
  - Grade constants: PASSING_GRADE, MIN_GRADE, MAX_GRADE, GRADE_EXCELLENT, GRADE_GOOD, GRADE_SUFFICIENT, GRADE_INSUFFICIENT
  - UI dimensions: SIDEBAR_WIDTH, NAV_BUTTON_WIDTH, NAV_BUTTON_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
  - Layout constants: MARGIN_SMALL, MARGIN_MEDIUM, MARGIN_LARGE, SPACING_SMALL, SPACING_MEDIUM, SPACING_LARGE
  - Color constants: COLOR_EXCELLENT, COLOR_GOOD, COLOR_SUFFICIENT, COLOR_FAIL
  - Vote types: VOTE_TYPE_WRITTEN, VOTE_TYPE_ORAL, VOTE_TYPE_PRACTICAL
  - Chart constants: CHART_BAR_WIDTH, CHART_POINT_SIZE, CHART_LINE_WIDTH
  - Database constants: CACHE_ENABLED, MAX_UNDO_HISTORY

#### `src/votetracker/i18n.py`
**Purpose:** Internationalization (i18n)
- **Functions:**
  - `get_language()` - Get current language code
  - `set_language(lang)` - Set language ("en" or "it")
  - `tr(key)` - Translate key to current language
  - `get_translated_subjects()` - Get translated preset subjects
- **Constants:**
  - `PRESET_SUBJECTS`: List of common subject names (English)
  - `TRANSLATIONS`: Dict of all translations (en/it)

#### `src/votetracker/classeviva.py`
**Purpose:** ClasseViva API integration
- **Class:** `ClasseVivaClient`
  - **Methods:**
    - `login(username, password)` - Authenticate with CV
    - `get_grades()` - Fetch grades from CV
    - `logout()` - Clear session
    - `is_authenticated()` - Check if logged in
    - `get_user_display_name()` - Get user's full name
- **Functions:**
  - `convert_classeviva_to_votetracker(grades)` - Convert CV format to VT format
  - `_map_grade_type(component_desc)` - Map CV type to VT type
  - `_parse_term(period_desc)` - Parse term number from period

#### `src/votetracker/subject_matcher.py`
**Purpose:** Smart subject matching for ClasseViva import
- **Constants:**
  - `SUBJECT_KEYWORDS`: Dict mapping canonical names to keyword lists
- **Functions:**
  - `normalize_subject(subject)` - Lowercase and strip
  - `find_best_match(cv_subject, vt_subjects)` - Find best VT match for CV subject
  - `suggest_canonical_name(cv_subject)` - Suggest canonical subject name
  - `get_auto_suggestions(cv_subject, vt_subjects)` - Get full suggestion with action

---

### Pages

#### `src/votetracker/pages/dashboard.py`
**Purpose:** Overview page with subject cards
- **Class:** `DashboardPage(QWidget)`
  - Shows active school year and term
  - Displays subject cards with averages
  - Shows overall average
  - **Methods:**
    - `refresh()` - Reload data
    - `handle_key(event)` - Handle term switching (1/2 keys)

#### `src/votetracker/pages/votes.py`
**Purpose:** Grade list with CRUD operations
- **Class:** `VotesPage(QWidget)`
  - Table view of all votes
  - Filter by subject and vote type
  - Add/edit/delete operations
  - Undo/redo integration
  - **Signals:**
    - `data_changed` - Emitted when votes modified
  - **Methods:**
    - `refresh()` - Reload vote list
    - `_add_vote()` - Open add dialog
    - `_edit_vote()` - Open edit dialog
    - `_delete_vote()` - Delete selected vote
    - `handle_key(event)` - Keyboard shortcuts

#### `src/votetracker/pages/subjects.py`
**Purpose:** Subject management
- **Class:** `SubjectsPage(QWidget)`
  - List of all subjects
  - Add/rename/delete subjects
  - Shows vote count per subject
  - **Signals:**
    - `data_changed` - Emitted when subjects modified
  - **Methods:**
    - `refresh()` - Reload subject list
    - `_add_subject()` - Open add dialog
    - `_edit_subject()` - Open edit dialog
    - `handle_key(event)` - Keyboard shortcuts

#### `src/votetracker/pages/simulator.py`
**Purpose:** Grade simulation/calculation
- **Class:** `SimulatorPage(QWidget)`
  - Select subject and target average
  - Enter future grade and weight
  - Calculates required grade to reach target
  - Filter by vote type
  - **Methods:**
    - `refresh()` - Reload subjects
    - `_calculate()` - Run simulation
    - `handle_key(event)` - Term switching

#### `src/votetracker/pages/calendar.py`
**Purpose:** Calendar view of grades
- **Class:** `CalendarPage(QWidget)`
  - QCalendarWidget with highlighted dates
  - Shows votes on selected date
  - Filter by subject
  - **Methods:**
    - `refresh()` - Reload calendar
    - `_on_date_selected(date)` - Show votes for date
    - `handle_key(event)` - Term switching

#### `src/votetracker/pages/report_card.py`
**Purpose:** Report card view with PDF export
- **Class:** `ReportCardPage(QWidget)`
  - Shows subjects with averages
  - Italian rounding (0.5 rounds up)
  - Displays final average
  - Export to PDF
  - **Methods:**
    - `refresh()` - Reload report card
    - `_export_pdf()` - Generate PDF report
    - `handle_key(event)` - Term switching

#### `src/votetracker/pages/statistics.py`
**Purpose:** Statistics and charts
- **Class:** `StatisticsPage(QWidget)`
  - Grade distribution histogram
  - Grade trend over time
  - Filter by subject
  - **Methods:**
    - `refresh()` - Reload charts
    - `handle_key(event)` - Term switching

#### `src/votetracker/pages/settings.py`
**Purpose:** Settings, import/export, ClasseViva
- **Class:** `SettingsPage(QWidget)`
  - **Signals:**
    - `data_imported` - Emitted when data imported
    - `school_year_changed` - Emitted when year changed
    - `language_changed` - Emitted when language changed
  - **Structure:** Scrollable page with organized sections (no tabs)
    - **General:** Language selector, school years management, current term display
    - **Data Management:**
      - Database location display
      - Import section (JSON text input and file import)
      - Export section (export to file button)
      - Clear data section (delete current term/year buttons)
    - **ClasseViva Integration:** Complete CV integration
      - Account credentials (username/password)
      - Save credentials checkbox
      - Test connection button
      - Manual import section with progress bar
      - Auto-sync settings (enable, interval, notifications)
      - Import options (skip duplicates, current year only, term filter)
      - Subject mappings management button
    - **Help & Info:** Keyboard shortcuts button and version display
  - **Methods:**
    - `refresh()` - Reload settings (updates years, term labels)
    - `_manage_years()` - Open year management dialog
    - `_show_shortcuts()` - Show shortcuts help
    - `_import_json()` - Import from JSON text
    - `_import_from_file()` - Import from JSON file
    - `_export_to_file()` - Export to JSON file
    - `_clear_term_votes()` - Delete term votes
    - `_clear_year_votes()` - Delete year votes
    - ClasseViva methods:
      - `_load_cv_credentials()` - Load saved credentials
      - `_test_cv_connection()` - Test login
      - `_clear_cv_credentials()` - Clear saved credentials
      - `_import_from_classeviva()` - Import grades from CV
      - `_manage_subject_mappings()` - Open subject mappings dialog
      - `_on_auto_sync_toggled(state)` - Handle auto-sync toggle
      - `_on_sync_interval_changed(index)` - Handle interval change
      - `_start_auto_sync()` - Start sync timer
      - `_stop_auto_sync()` - Stop sync timer
      - `_auto_sync_tick()` - Perform sync
      - `_on_language_changed(index)` - Handle language selection
    - `handle_key(event)` - Keyboard shortcuts (Ctrl+I/E)

---

## Important Concepts

### Database Schema
- **school_years**: id, name, start_year, is_active
- **subjects**: id, name
- **votes**: id, subject_id, school_year_id, grade, type, term, date, description, weight, created_at
- **grade_goals**: id, subject_id, school_year_id, term, target_grade, created_at
- **settings**: key, value (stores ClasseViva credentials, mappings, sync settings, etc.)

### ClasseViva Subject Mappings
Subject mappings are stored in the settings table with keys like `cv_mapping_{classeviva_subject_name}`.
- Example: `cv_mapping_MATEMATICA` → `Math`
- Use `Database.get_all_subject_mappings()` to retrieve all
- Mappings persist across imports
- Used during ClasseViva import to map CV subject names to VT subject names

### Data Flow
1. User actions trigger page methods
2. Pages interact with Database
3. Database emits signals for changes
4. MainWindow refreshes affected pages
5. Undo/redo records operations on votes

### Undo/Redo System
Only applies to vote operations (add/edit/delete), not subjects or settings.
History stored in `UndoManager`, max 50 operations.

### Keyboard Navigation
- Global shortcuts in `MainWindow.keyPressEvent()`
- Page-specific shortcuts in `PageClass.handle_key()`
- MainWindow delegates unhandled keys to active page

---

## Common Tasks

### Adding a New Dialog
1. Create dialog class in `dialogs.py`
2. Inherit from `QDialog`
3. Implement `_setup_ui()` for layout
4. Add getter methods for user input
5. Import in page that uses it

### Adding a New Page
1. Create file in `pages/` directory
2. Create class inheriting `QWidget`
3. Implement `refresh()` method
4. Optional: Implement `handle_key(event)` for shortcuts
5. Import in `mainwindow.py`
6. Add to `_create_pages()` and navigation

### Modifying Database Schema
1. Update `database.py` `_init_db()` method
2. Add migration logic for existing databases
3. Update relevant CRUD methods
4. Test with existing database file

### Adding Translation
1. Update `TRANSLATIONS` dict in `i18n.py`
2. Add keys for both "en" and "it"
3. Use `tr(key)` to get translated string
4. Update UI to use `tr()` instead of hardcoded strings

---

## Dependencies

### Required
- **PySide6** (>=6.4.0) - Qt6 Python bindings
- **reportlab** (>=4.0.0) - PDF generation
- **requests** (>=2.31.0) - HTTP client for ClasseViva API

### Optional
- **PyInstaller** - For building standalone executables

---

## Data Locations

### Database
- Linux: `~/.local/share/votetracker/votes.db`
- Windows: `%APPDATA%/votetracker/votes.db`
- macOS: `~/Library/Application Support/votetracker/votes.db`

### Settings
Stored in database `settings` table with key-value pairs:
- `onboarding_complete`: "1" if wizard shown
- `language`: "en" or "it"
- `current_term`: "1" or "2"
- `classeviva_username`: Base64 encoded username
- `classeviva_password`: Base64 encoded password
- `classeviva_last_sync`: Last sync timestamp
- `classeviva_auto_sync`: "1" if enabled
- `classeviva_sync_interval`: Minutes between syncs
- `cv_mapping_{subject}`: ClasseViva subject mappings

---

## Development Tips

### Testing ClasseViva Integration
- Create test credentials or use mock data
- Test subject mapping dialog with various subject names
- Verify duplicate detection works correctly
- Check error handling for network issues

### UI Consistency
- Use `get_symbolic_icon()` for all icons
- Use `tr()` for all user-facing strings
- Follow Qt layout patterns (margins: 12-20px, spacing: 8-12px)
- Use `QGroupBox` for logical sections

### Performance
- Database queries are synchronous (single-threaded)
- Large datasets (>1000 votes) may slow UI
- Consider pagination for votes table in future

---

## Versioning and Release Management

### Versioning Scheme

VoteTracker follows **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

- **MAJOR** (X.0.0) - Breaking changes, major rewrites, incompatible API changes
- **MINOR** (0.X.0) - New features, significant additions (backward compatible)
- **PATCH** (0.0.X) - Bug fixes, minor improvements (backward compatible)

**Version must be updated in:**
1. `pyproject.toml` - `version = "X.Y.Z"`
2. `src/votetracker/__init__.py` - `__version__ = "X.Y.Z"`

### Commit Guidelines

**⚠️ CRITICAL: Commits MUST be feature-based, NOT bulk commits**

#### DO:
✅ Make **separate commits** for each feature/fix/change
✅ Write clear, descriptive commit messages
✅ Use imperative mood ("Add feature" not "Added feature")
✅ Group related changes logically

#### DON'T:
❌ Combine multiple unrelated features in one commit
❌ Make giant "misc changes" commits
❌ Use vague messages like "updates" or "fixes"

#### Commit Message Format:
```
<type>: <short description>

<optional longer description>

<optional footer with references>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Formatting, missing semicolons, etc (no code change)
- `refactor:` - Code refactoring (no feature change)
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks (dependencies, build config)

**Examples:**
```bash
# Good commits
git commit -m "feat: Add ClasseViva subject mapping management dialog"
git commit -m "fix: Correct SCIENZE MOTORIE mapping in subject matcher"
git commit -m "docs: Update CLAUDE.md with versioning guidelines"

# Bad commits
git commit -m "updates"
git commit -m "added features and fixed bugs"
git commit -m "misc changes"
```

### Release Process

**For EVERY new feature or significant change:**

#### 1. Update Version
```bash
# Edit version in both files
vim pyproject.toml          # version = "2.6.0"
vim src/votetracker/__init__.py  # __version__ = "2.6.0"
```

#### 2. Commit Version Bump
```bash
git add pyproject.toml src/votetracker/__init__.py
git commit -m "chore: Bump version to 2.6.0"
```

#### 3. Create Git Tag
```bash
git tag -a v2.6.0 -m "Version 2.6.0: Subject mapping management"
git push origin main
git push origin v2.6.0
```

#### 4. Create GitHub Release
```bash
# Using gh CLI
gh release create v2.6.0 \
  --title "v2.6.0 - Subject Mapping Management" \
  --notes "$(cat <<EOF
## What's New

### Features
- Added subject mapping management dialog for ClasseViva integration
- Users can now view and edit existing ClasseViva → VoteTracker subject mappings
- Added 'Manage Subject Mappings' button in Settings > ClasseViva tab
- Mappings can be edited, deleted individually, or cleared all at once

### Changes
- Enhanced Settings page with new Subject Mappings section
- Improved ClasseViva import workflow

### Bug Fixes
- Fixed incorrect default mapping for SCIENZE MOTORIE E SPORTIVE (now maps to Physical Education)

## Technical Details
- New dialog: \`ManageSubjectMappingsDialog\` in dialogs.py
- Added \`_manage_subject_mappings()\` method to SettingsPage
- Updated CLAUDE.md with comprehensive development guide
EOF
)"
```

#### 5. Build and Attach Release Assets (if applicable)
```bash
# Build Arch Linux package
cd scripts && makepkg
gh release upload v2.6.0 votetracker-2.6.0-1-any.pkg.tar.zst

# Build standalone binary (optional)
python scripts/build.py --onefile
gh release upload v2.6.0 dist/votetracker
```

### Changelog Format

Each release should include:

**Required Sections:**
- **What's New** - High-level summary
- **Features** - New functionality added
- **Changes** - Modifications to existing features
- **Bug Fixes** - Issues resolved

**Optional Sections:**
- **Breaking Changes** - For major versions
- **Deprecations** - Features being phased out
- **Technical Details** - For developers
- **Known Issues** - Current limitations

**Example Full Changelog:**
```markdown
## v2.6.0 - Subject Mapping Management (2026-01-27)

### What's New
Added the ability to view and edit ClasseViva subject mappings directly in the app.

### Features
- New 'Manage Subject Mappings' dialog accessible from Settings
- View all existing ClasseViva → VoteTracker subject mappings in a table
- Edit mappings by selecting different VoteTracker subjects
- Delete individual mappings or clear all at once
- Automatic subject creation when mapping to non-existent subjects

### Changes
- Enhanced Settings page ClasseViva tab with Subject Mappings section
- Improved import workflow with better mapping visibility

### Bug Fixes
- Fixed SCIENZE MOTORIE E SPORTIVE incorrectly mapping to Science instead of Physical Education

### Technical Details
- New class: `ManageSubjectMappingsDialog` in `src/votetracker/dialogs.py`
- New method: `_manage_subject_mappings()` in `src/votetracker/pages/settings.py`
- Updated documentation in CLAUDE.md

### Installation
**Arch Linux:**
```bash
cd scripts && makepkg -si
```

**pip:**
```bash
pip install --upgrade votetracker
```
```

### Quick Release Workflow

```bash
# 1. Make feature commits (separate commits for each feature)
git add src/votetracker/dialogs.py
git commit -m "feat: Add ManageSubjectMappingsDialog for viewing/editing CV mappings"

git add src/votetracker/pages/settings.py
git commit -m "feat: Add Subject Mappings section in Settings with manage button"

git add CLAUDE.md
git commit -m "docs: Update CLAUDE.md with new dialog and versioning guidelines"

# 2. Bump version
vim pyproject.toml src/votetracker/__init__.py
git add pyproject.toml src/votetracker/__init__.py
git commit -m "chore: Bump version to 2.6.0"

# 3. Tag and release
git tag -a v2.6.0 -m "Version 2.6.0: Subject mapping management"
git push origin main --tags

# 4. Create GitHub release with detailed changelog
gh release create v2.6.0 --title "v2.6.0 - Subject Mapping Management" --notes-file RELEASE_NOTES.md
```

---

## Version History

- **2.7.0** - Performance enhancements: database indices, connection pooling, caching, grade goals foundation, constants extraction, comprehensive unit tests
- **2.6.0** - Subject mapping management dialog and Settings page restructure
- **2.5.0** - Added ClasseViva integration with smart subject mapping
- **2.4.0** - Added simulator vote type filter
- **2.3.0** - Added school years and terms
- **2.2.0** - Added undo/redo system
- **2.1.0** - Added keyboard shortcuts
- **2.0.0** - Complete rewrite with PySide6
- **1.0.0** - Initial release

---

## Testing Workflow

**⚠️ CRITICAL: NEVER commit code without proper testing**

### Required Testing Process

**For EVERY code change, follow this exact order:**

1. **Write automated test script** (if applicable)
   - Create test script to verify the specific functionality
   - Test should cover edge cases and the exact user scenario
   - Run the script to verify the fix works programmatically

2. **Run the actual application**
   - Execute `python -m src.votetracker` for the user to test
   - Let the user interact with the real UI and verify the fix
   - Check exit code: `0` = user closed it safely, non-zero = crash
   - **DO NOT re-run unless asked or if exit code indicates crash**

3. **User approval required**
   - User MUST test and confirm the fix works
   - Do NOT assume automated tests are sufficient
   - Do NOT commit until user explicitly confirms

4. **Only then commit**
   - After user approval, create proper commit message
   - Follow commit message format guidelines
   - Reference the issue that was fixed

### Test Script Guidelines

- Use test scripts for YOUR troubleshooting, not as replacement for user testing
- Test scripts help verify logic but don't replace real UI interaction
- Always run the actual app for user testing before committing

### Example Workflow

```bash
# 1. Make code changes
vim src/votetracker/pages/settings.py

# 2. Create and run test script for troubleshooting
python test_feature.py

# 3. Run app for user testing
python -m src.votetracker

# 4. Wait for user approval
# User tests... User says "looks good!"

# 5. Now commit
git add src/votetracker/pages/settings.py
git commit -m "fix: Description of what was fixed"

# 6. Clean up test script
rm test_feature.py
```

### What NOT to Do

❌ Commit before running the app for user testing
❌ Assume your test script proves the fix works
❌ Re-run the app when user closed it (exit code 0)
❌ Skip user approval and commit immediately

---

## Remember

**⚠️ ALWAYS UPDATE THIS FILE WHEN:**
- Adding new classes or methods
- Changing function signatures
- Adding new dialogs or pages
- Modifying database schema
- Adding new features
- Changing file structure
- Adding new dependencies

**⚠️ ALWAYS FOLLOW RELEASE PROCESS WHEN:**
- Adding new features (bump MINOR version)
- Fixing bugs (bump PATCH version)
- Making breaking changes (bump MAJOR version)
- Completing any significant work

**⚠️ ALWAYS MAKE SEPARATE COMMITS FOR:**
- Each distinct feature
- Each bug fix
- Each documentation update
- Version bumps

Keep this file as the **source of truth** for Claude Code to quickly navigate and understand the project.
