# Safety and Data Integrity Rules

## 1. Production Database Protection
- The production database resides at `~/.local/share/votetracker/votes.db` (or Windows/macOS equivalent).
- **Rule**: NEVER write, delete, or modify files in the real application data directory during automated test execution, debugging scripts, or test suite runs.
- Always use `:memory:` or `tempfile.NamedTemporaryFile` for SQLite connections during tests.

## 2. Sync Credentials Protection
- Credentials for sync providers (ClasseViva, Axios, etc.) are stored base64-encoded in the `settings` table.
- **Rule**: Never print, log, or export plaintext passwords or auth tokens in debugging logs or console output.
- Never commit test accounts or real student credentials to git.

## 3. Grade Data Integrity & Zero Grades
- In the Italian school system, marks of `+` or `−` have no numeric weight and are imported as `0.0`.
- **Rule**: A grade of `0.0` or `< 0.0` must NEVER be included in average calculations (`calc_average`), must NEVER count as a failing grade in counts/statistics, and must NOT be reported as the "lowest grade".
- Grade calculation formulas must always respect vote weights (`weight`) and ignore non-numeric grades (`grade <= 0`).

## 4. Duplicate Avoidance on Provider Sync
- Providers can re-import grades periodically.
- **Rule**: Never insert duplicate grades. Always match incoming items against existing items using `(subject, date, type)` via `Database.find_vote_by_metadata()`.
  - If identical: SKIP.
  - If modified (teacher edited grade or description): UPDATE.
  - If new: INSERT.

## 5. Non-Destructive Schema Evolution
- Schema changes in `db_schema.py` must use `IF NOT EXISTS` or guard column additions via `PRAGMA table_info`.
- **Rule**: Do not drop tables or execute unversioned destructive DDL.
