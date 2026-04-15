# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**VoteTracker** is a Python/PySide6 desktop app for tracking school grades, with multi-year/multi-term support, grade simulation, statistics, PDF report cards, and import from Italian electronic registers (ClasseViva, Axios).

## Commands

```bash
# Run in development
python -m votetracker
python run.py                   # equivalent shortcut

# Editable install
pip install -e .

# Tests (unittest, no pytest configured)
python -m unittest discover -s tests -p "test_*.py"
python -m unittest tests.test_database                                  # single module
python -m unittest tests.test_database.TestDatabase.test_add_vote       # single test

# Build Arch Linux package
cd scripts && makepkg -si

# Build standalone binary
python scripts/build.py --onefile
```

No ruff/basedpyright/pytest is configured in `pyproject.toml` — rely on manual inspection and the unittest suite.

## Architecture

### Data flow
User interaction → `PageClass` method → `Database` CRUD → page emits `data_changed` / `data_imported` / `school_year_changed` signal → `MainWindow` calls `_refresh_all_pages()` → each page's `refresh()` reloads from DB.

`MainWindow` owns the singleton `Database` instance (`self._db`) and `UndoManager`. It wires every page via a `QStackedWidget` and delegates unhandled keyboard events to the active page's `handle_key()`.

### Sync providers (adding a new one)
Providers live in `src/votetracker/providers/` and implement the `SyncProvider` ABC from `sync_provider.py`. To add one:
1. Subclass `SyncProvider`, implement `get_provider_name()`, `get_credential_fields()`, `login()`, `get_grades()`.
2. Register it in `providers/__init__.py::register_all_providers()`. Guard optional dependencies (see how Axios is only registered when `lxml` is importable).
3. Return grades in VoteTracker format (dicts with `subject`, `grade`, `type`, `date`, `description`, `weight`, `term`).

The `SyncProviderRegistry` is a singleton — providers are instantiated lazily and cached per `Database`.

### Settings keys (provider-agnostic namespacing)
Everything non-schema lives in the `settings` table as key/value. Conventions:
- `{provider_id}_mapping_{source_subject}` → VoteTracker subject name (e.g. `axios_mapping_MATEMATICA` → `Math`)
- `{provider_id}_{field_name}` → credentials, base64-encoded (e.g. `axios_username`)
- `{provider_id}_auto_sync` / `{provider_id}_sync_interval` / `{provider_id}_last_sync`
- Legacy ClasseViva keys (`cv_mapping_*`, `classeviva_username`, …) still exist — do not break compatibility when refactoring.

### Database
- SQLite at `~/.local/share/votetracker/votes.db` (or XDG equivalent on Win/macOS).
- Schema: `school_years`, `subjects`, `votes`, `grade_goals`, `settings`.
- DDL, migrations, seed data, and indices live in `db_schema.py` (split out of `database.py`). `Database._init_db()` is just an orchestrator that calls `create_schema`, `migrate_votes_table`, `seed_defaults`, `create_indices` in order.
- There is no versioned migration system. New ALTER TABLEs go in `migrate_votes_table()` (or a new migration function in `db_schema.py`); new CREATE TABLEs go in `create_schema()`.
- Caches (`_subject_cache`, `_year_cache`) in `Database` must be invalidated whenever the underlying tables are mutated.

### Import logic (critical — easy to get wrong)
When a sync provider pulls grades, the app must distinguish **new**, **updated**, and **duplicate** grades:
- Match existing votes by `(subject, date, type)` via `Database.find_vote_by_metadata()` — **not** by grade value.
- If a match exists with a different grade/weight/description → **UPDATE** (teachers can change grades after the fact).
- If no match exists → **ADD**.
- Exact match (including grade value) via `vote_exists()` → **SKIP**.
- Status is reported as `"X new, Y updated (Z skipped)"`.

### Averages and zero grades
`utils.calc_average()` **excludes grades ≤ 0**. Italian `+` / `−` marks import as `0.0` and must not affect averages. The Python-side helper filters them; some raw SQL aggregations in `database.py` do not — prefer the Python helper for anything user-facing.

### Undo/redo
`UndoManager` covers only vote add/edit/delete — not subjects, settings, or school years. History cap: 50. It emits `state_changed` so `MainWindow` can enable/disable the Ctrl+Z/Ctrl+Shift+Z shortcuts.

### i18n
Strings live in `i18n.TRANSLATIONS` (`en` / `it`). Use `tr(key)` everywhere user-facing; never hardcode strings. Language is persisted in `settings.language` and auto-detected on first launch.

## Project layout

```
src/votetracker/
  mainwindow.py, database.py, dialogs.py, widgets.py, undo.py, i18n.py
  styles.py                 # centralized stylesheet constants + helpers
  constants.py              # layout numbers, colors, grade thresholds
  db_schema.py              # DDL, migrations, seeds, indices (imported by database.py)
  sync_provider.py          # SyncProvider ABC + registry
  classeviva.py             # low-level CV client — impl detail of classeviva_provider
  providers/                # sync provider implementations
  pages/                    # one file per page in the QStackedWidget
tests/                      # unittest modules
scripts/                    # build.py, PKGBUILD, install.sh, .desktop
docs/                       # release notes, publishing guides
```

`src/votetracker/classeviva.py` is the low-level HTTP client and should be treated as an implementation detail of `providers/classeviva_provider.py`. `pages/settings.py` still imports it directly to drive a legacy "direct import" UI section that predates the provider abstraction — **this legacy section is known tech debt** and should be removed once the provider-based UI fully replaces it.

`pages/settings.py` is the largest page (~1750 LOC). Its `_setup_ui()` is a thin orchestrator that calls dedicated `_build_title_bar` / `_build_general_section` / `_build_data_section` / `_build_sync_section` / `_build_help_section` methods. When editing the settings UI, locate the section builder first rather than scanning the whole class.

## Conventions

- **Styling**: `styles.py` defines named stylesheet constants (`STYLE_PAGE_TITLE`, `STYLE_MUTED`, `STYLE_EMPTY_STATE`, …) and helpers (`stat_value_colored`, `grade_cell`). `constants.py` defines `MARGIN_*`, `SPACING_*`, `COLOR_*`. Use both instead of hardcoded numbers or inline `setStyleSheet()` strings. Dynamic color stylesheets (e.g. `f"color: {hex};"`) are still inline in some places — migrating them is welcome but not urgent.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`). One commit per logical change — no bulk commits.
- **Versioning**: SemVer. Bump in **both** `pyproject.toml` and `src/votetracker/__init__.py`, then tag `vX.Y.Z`.
- **Before committing code changes**: run `python -m votetracker` and have the user verify the actual UI. Automated tests alone are not sufficient for UI work.

## Keep this file updated

When architecture, data flow, conventions, or commands change, update this file. Do **not** document every class/method here — the code is the source of truth for that. This file is for things you can't learn by reading a single file.
