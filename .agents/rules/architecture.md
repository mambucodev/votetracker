# Architecture Rules & Conventions

## 1. Component Ownership & Data Flow
- `MainWindow` owns the singleton `Database` (`self._db`) and `UndoManager`.
- Pages do not instantiate their own `Database`; they receive `self._db` in `__init__`.
- Pages perform CRUD operations on `self._db` and then emit relevant signals:
  - `vote_changed` from `VotesPage`
  - `subject_changed` from `SubjectsPage`
  - `data_imported`, `school_year_changed`, `language_changed` from `SettingsPage`
- `MainWindow` handles these signals by calling `_refresh_all()`, which computes global stats in a single pass and reloads the active page.

## 2. Sync Provider Abstraction
- Providers subclass `SyncProvider` (`src/votetracker/sync_provider.py`).
- Providers implement:
  - `get_provider_name() -> str`
  - `get_credential_fields() -> list[dict]`
  - `login(credentials: dict[str, str]) -> tuple[bool, str]`
  - `get_grades() -> tuple[bool, list[dict], str]`
- Optional provider dependencies (e.g. `lxml`) must be guarded at registration time in `src/votetracker/providers/__init__.py`.

## 3. Database Cache Invalidation
- `Database` caches school years (`_year_cache`) and subjects (`_subject_cache`).
- Any operation that modifies `school_years` or `subjects` table MUST invalidate the cache by setting the attribute to `None`.

## 4. Undo/Redo Scope
- `UndoManager` covers only vote CRUD (`add`, `edit`, `delete`).
- It does not cover subjects, settings, or school year mutations.
- When recording actions, always keep `school_year_id` so that undone/redone votes are restored to their proper academic year.
