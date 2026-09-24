# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

See [GEMINI.md](file:///home/mambuco/Projects/votetracker/GEMINI.md) for full project architecture, safety rules, and development guidelines.

## Quick Reference

- **Run Dev**: `python -m votetracker` or `python run.py` (or `nix run .` / `nix-shell --run "python run.py"`)
- **Run Tests**: `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p "test_*.py"`
- **Lint**: `ruff check src tests`
- **Safety**:
  - Never modify `~/.local/share/votetracker/votes.db` during tests or automation.
  - Zero-grade rule: grades <= 0.0 (+/- marks) must not affect averages or be counted as failing.
  - Sync import matching: match by `(subject, date, type)`, update if different, skip if identical.
  - Localization: Wrap all user-facing strings in `tr(...)` from `src.votetracker.i18n`.
