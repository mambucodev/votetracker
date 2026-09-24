# Coding Style & UI Guidelines

## 1. Python Code Standards
- Target Python 3.8+.
- Always include `from __future__ import annotations` at the top of each module.
- Type hints are encouraged on all public functions and methods.
- Follow PEP 8 and verify with `ruff check src tests`.

## 2. UI Styling Conventions
- Never hardcode CSS styling strings inline when a reusable constant exists.
- Central typography, state, and container styles reside in `src/votetracker/styles.py` (`STYLE_PAGE_TITLE`, `STYLE_MUTED`, `STYLE_EMPTY_STATE`, etc.).
- Margins, paddings, and layout dimensions reside in `src/votetracker/constants.py` (`MARGIN_*`, `SPACING_*`, `COLOR_*`).
- When constructing dynamic styles (e.g. colored values based on average), use helpers from `styles.py` (e.g. `stat_value_colored`, `grade_cell`).

## 3. Internationalization (i18n)
- Never hardcode visible text strings in UI widgets or dialogs.
- Wrap all display strings in `tr("String")` from `src.votetracker.i18n`.
- Always add entries for new keys to both `"en"` and `"it"` dictionaries in `src/votetracker/i18n.py`.
- Handle language change events by reloading dynamic labels or connecting to `MainWindow._on_language_changed`.
