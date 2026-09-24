# Testing & Environment Rules

## 1. Running Tests
- Test framework: Python standard `unittest`.
- Headless execution: Because PySide6 requires a display server by default, all automated tests must run with `QT_QPA_PLATFORM=offscreen`.
```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p "test_*.py"
```

## 2. NixOS / Linux Development
- On NixOS or systems using Nix, run with `shell.nix`:
```bash
nix-shell --run "QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p 'test_*.py'"
```
- Entering the shell: `nix-shell` provides Python 3, PySide6, ReportLab, Requests, lxml, and Ruff with all system shared libraries correctly resolved.

## 3. Test Isolation
- All unit tests must be self-contained and clean up temporary files in `tearDown`.
- Never rely on pre-existing user databases or network access to third-party school portals in unit tests.
- Use mocks (like `tests/mock_axios.py`) for external provider network operations.
