# CLAUDE.md

Guidance for Claude Code when working in this repository.

**VoteTracker 3.0** is a Tauri 2 app (Rust backend + React/TS/SCSS
frontend) that tracks school grades with multi-year / multi-term
support, averages, a simulator, calendar, PDF report cards, statistics,
and sync from ClasseViva / Axios electronic registers. The 2.x PySide6
app has been retired; version 3 is the only active implementation.

## Commands

```bash
# Dev (Vite + Tauri together)
npm install
npm run tauri:dev

# Frontend only (useful for quick iteration)
npm run dev

# Tests
cd src-tauri && cargo test          # 38 unit tests
npm run build                        # tsc --noEmit + vite prod build

# Release bundles (.deb/.AppImage/.dmg/.msi)
npm run tauri:build
```

## Architecture

### Data flow

React component → `src/lib/ipc.ts` wrapper → Tauri `invoke()` →
`#[tauri::command]` in `src-tauri/src/commands.rs` → DB / domain.
Every mutation emits `data-changed` / `data-imported` / `undo-state`.
Components listen via `src/lib/hooks/useDataRefresh.ts` and re-fetch.

### Rust backend (`src-tauri/src/`)

- `db/` — `rusqlite` + `r2d2` pool. Schema in `db/schema.rs` is a
  verbatim port of the Python app's schema (same file, same indices),
  so an existing `votes.db` opens without conversion.
- `domain/` — pure business logic: `average::calc_average`
  (excludes grade ≤ 0), `rounding::round_report_card` (Italian ≥ 0.5 →
  up), `simulator::calculate_needed_grade`, `subject_match::*` fuzzy
  matcher. Every function has unit tests.
- `undo/` — 50-entry FIFO stack covering vote add/edit/delete only.
- `sync/` — `SyncProvider` trait + ClasseViva (REST) + Axios
  (HTML-scrape skeleton). `import::import_all` implements the exact
  Python dedup: match `(subject, date, kind)` → new / updated / skipped.
- `pdf/report_card.rs` — A4 PDF via `printpdf` crate.
- `menu.rs` — native menu bar with `Ctrl+1..8` nav, undo/redo, sync
  now, theme toggle. Menu clicks fire `menu://<id>` events.
- `commands.rs` — IPC surface (votes/subjects/years/settings/undo/
  providers/PDF/open_data_dir/…).
- `lib.rs` — wires everything + spawns startup + interval auto-sync
  per provider via Tokio.

### React frontend (`src/`)

- `theme/` — light/dark tokens in SCSS, `ThemeProvider` with 3-state
  preference (system/light/dark) persisted to both localStorage and
  the backend `theme_preference` setting.
- `lib/store.ts` — Zustand store for current year + current term.
- `lib/hooks/` — `useDataRefresh` (auto-refetch on events),
  `useShortcuts` (keyboard matrix).
- `components/` — Sidebar, TopBar, primitives (Modal, Button, Field),
  dialogs (AddVote, AddSubject).
- `pages/` — Dashboard, Votes, Subjects, Simulator, Calendar,
  ReportCard, Statistics, Settings, Onboarding.

### Settings keys (namespaced by provider)

- `{provider_id}_{field}` → base64-obfuscated credential
- `{provider_id}_mapping_{source_subject}` → VT subject name
- `{provider_id}_auto_sync` / `{provider_id}_sync_interval` /
  `{provider_id}_last_sync`
- ClasseViva uses mapping prefix `cv` (legacy), Axios uses `axios`.

### Import pipeline (easy to get wrong)

`sync::import::import_all`:
1. Map source subject → VT subject via `cv_mapping_*` / `axios_mapping_*`.
2. Match existing vote by `(subject, date, type)` — **not** grade.
3. Exact match (same grade/weight/description) → **Skip**.
4. Metadata match, different grade → **Update**.
5. No match → **Add**.

Reported to UI as `"X new, Y updated (Z skipped)"`.

### Averages

`domain::average::calc_average` excludes grades ≤ 0 (`+/−` marks).
Weighted sum / weight-sum. Fall back to 0 when no valid votes.

### Italian rounding

`domain::rounding::round_report_card`: decimals ≥ 0.5 round up.

## Conventions

- **Styling**: SCSS only — no Tailwind. Tokens in `src/theme/tokens.scss`.
- **State**: Zustand for cross-page (year/term/theme), pure hooks for per-page.
- **IPC**: every command is a typed wrapper in `src/lib/ipc.ts`. Pages
  never touch `invoke()` directly.
- **Commits**: Conventional Commits (`feat:`, `fix:`, etc.). One commit
  per logical change — no bulk commits.
- **Versioning**: SemVer. Bump `package.json`, `src-tauri/Cargo.toml`,
  `src-tauri/tauri.conf.json`, and the sidebar version string together.
- **Before committing UI changes**: `npm run tauri:dev` and verify the
  actual UI. Type-check alone is not enough.

## Feature spec

[`docs/REWRITE_SPEC.md`](docs/REWRITE_SPEC.md) is the source of truth
for app behavior. Quote from it (not from memory) when implementing
something that touches averages, import dedup, provider HTTP, etc.

## Keep this file updated

When architecture, data flow, or conventions change, update this file.
This file is for things you can't learn by reading any single file.
