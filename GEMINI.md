# GEMINI.md - VoteTracker

This document provides project architecture, development workflows, rules, and guidelines for AI agents working on **VoteTracker**.

---

## 1. Project Overview

**VoteTracker** is a desktop application written in Python and PySide6 (Qt for Python) designed for Italian and international students to manage school grades across multiple school years and academic terms.

Key features include:
- Multi-year and multi-term (quadrimestri) tracking.
- Weighted averages and simulated report cards.
- Grade simulator calculating target grades needed to reach passing or desired averages.
- PDF report card export (via ReportLab).
- Sync providers for Italian electronic grade registers (ClasseViva, Axios Italia).
- Local-first SQLite database storage with undo/redo capabilities.

---

## 2. Quick Commands

```bash
# Run application in development
python -m votetracker
# or shortcut
python run.py

# Run with Nix environment (Linux / NixOS)
nix-shell --run "python run.py"
# or via Flake
nix run .

# Run tests (headless)
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p "test_*.py"

# Run tests via nix-shell
nix-shell --run "QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p 'test_*.py'"

# Run single test module / test case
python -m unittest tests.test_database
python -m unittest tests.test_database.TestDatabase.test_add_vote

# Code linting
ruff check src tests

# Build standalone executable with PyInstaller
python scripts/build.py
python scripts/build.py --onefile

# Build Arch Linux package (makepkg)
cd scripts && makepkg -si
```

---

## 3. Architecture & Core Concepts

### 3.1 Data Flow
- **Interaction**: User interaction occurs on a `PageClass` widget (e.g. `VotesPage`, `SubjectsPage`).
- **Persistence**: Page calls methods on singleton `Database` instance (`self._db`).
- **Signals**: On mutation, the page emits a signal (`vote_changed`, `subject_changed`, `data_imported`, etc.).
- **Refresh**: `MainWindow` catches signals, calls `_refresh_all()` which updates global stats and delegates `refresh()` to the active page.

### 3.2 Database (`database.py` & `db_schema.py`)
- SQLite database stored at `~/.local/share/votetracker/votes.db` (or Windows `%APPDATA%/votetracker/votes.db`).
- Tables: `school_years`, `subjects`, `votes`, `grade_goals`, `settings`.
- DDL, seed data, indices, and ALTER migrations live in `db_schema.py`.
- `Database._init_db()` orchestrates schema creation and migrations.
- In-memory cache dictionaries (`_subject_cache`, `_year_cache`) in `Database` must be invalidated (`None`) whenever their respective tables are modified.

### 3.3 Italian Grade System & Zero Grades
- Italian grades range from 1.0 to 10.0 (passing is 6.0).
- Italian `+` and `−` symbols import from registers as `0.0`.
- **Zero grades (`<= 0`) must never count towards averages or be counted as failing grades**.
- Always use `utils.calc_average(votes)` for averages. In SQL queries, filter with `v.grade > 0` whenever aggregating averages.

### 3.4 Sync Provider Architecture
- Providers subclass `SyncProvider` in `src/votetracker/sync_provider.py`.
- Registered via `src/votetracker/providers/__init__.py::register_all_providers()`.
- Optional dependencies (e.g., `lxml` for Axios) must be conditionally guarded so core functionality remains functional without them.
- Settings convention for credentials & configuration:
  - `{provider_id}_{field_name}` (base64 encoded credentials)
  - `{provider_id}_mapping_{source_subject}` (mapping to local subject)
  - `{provider_id}_auto_sync`, `{provider_id}_sync_interval`, `{provider_id}_last_sync`
- Legacy ClasseViva keys (`classeviva_username`, `cv_mapping_*`) are maintained for backward compatibility.

### 3.5 Import Duplicate Detection (Critical Rule)
When importing grades from external providers:
1. Match existing grades by `(subject, date, type)` via `Database.find_vote_by_metadata()`.
2. If matched but grade, weight, or description differs: **UPDATE**.
3. If exact match: **SKIP**.
4. If not found: **ADD**.

### 3.6 Undo / Redo
- Managed by `UndoManager` in `src/votetracker/undo.py`.
- Scoped to vote operations (`add`, `edit`, `delete`).
- `record_add(vote_id, vote_data)`, `record_edit(vote_id, previous_data, new_data)`, `record_delete(vote_id, vote_data)`.
- Always preserve `school_year_id` on actions to restore votes in the correct school year.

---

## 4. Safety & Security Rules

1. **User Database Safety**:
   - Automated tests and development scripts must NEVER modify the user's real database (`~/.local/share/votetracker/votes.db`).
   - Tests must always use `:memory:` or temporary files via `tempfile.NamedTemporaryFile`.
2. **Credential Safety**:
   - Never log passwords or authentication tokens in cleartext.
   - Do not commit credentials, real student IDs, or school tax codes to the repository.
3. **Schema Migrations**:
   - Never use destructive SQL (`DROP TABLE`) without explicit safety migrations.
   - Use `CREATE TABLE IF NOT EXISTS` and check column existence before `ALTER TABLE`.
4. **GUI Responsiveness**:
   - Network calls to registers (ClasseViva, Axios) should not block the main Qt event loop.

---

## 5. Coding & UI Conventions

- **Python Version**: Python 3.8+ compatibility. Use `from __future__ import annotations`.
- **Styling**: Use constants in `src/votetracker/styles.py` (`STYLE_PAGE_TITLE`, `STYLE_MUTED`, etc.) and layout constants in `constants.py` (`MARGIN_*`, `SPACING_*`, `COLOR_*`).
- **i18n**: All user-visible strings must use `tr("Text")` from `src/votetracker/i18n.py`. Add translations to both `en` and `it` dictionaries in `TRANSLATIONS`.
- **Commits**: Follow Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`).
- **Versioning**: SemVer. Update version in BOTH `pyproject.toml` and `src/votetracker/__init__.py`.
