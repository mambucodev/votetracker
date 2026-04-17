# VoteTracker 3.0 (Tauri rewrite — in progress)

<p align="center">
  <img src="src-tauri/icons/icon.png" alt="VoteTracker" width="128" height="128">
</p>

> **Status:** active rewrite on the `tauri-rewrite` branch.
> The stable Python/PySide6 implementation lives under
> [`legacy-python/`](legacy-python/) and continues to ship from `main` until
> the Tauri version reaches feature parity (milestone **M9**).

VoteTracker is a minimal desktop app that tracks school grades —
multi-year and multi-term, with averages, simulator, calendar, PDF report
cards, statistics, and one-tap sync from Italian electronic registers
(ClasseViva, Axios).

This branch rebuilds the app on **Tauri 2** with a **Rust** backend and a
**React + TypeScript + SCSS** frontend. Highlights of the rewrite:

- Claude.ai-inspired minimal design with a single warm coral accent gradient.
- Light/dark themes with OS auto-detect and manual override.
- Recharts-powered charts (subject averages, grade histogram, trend line).
- First-class native menu bar on macOS, Linux, and Windows.
- Auto-sync on app launch (plus interval-based auto-sync).
- Same `votes.db` schema as the Python app — existing installs open without conversion.

## Repository layout

```
votetracker/
├── docs/
│   └── REWRITE_SPEC.md      # feature spec (per-feature Python snippets + Rust/React port plan)
├── legacy-python/           # untouched Python tree — inspiration + reference until M9
├── src-tauri/               # Rust backend
│   └── src/
│       ├── db/              # schema, migrations, CRUD
│       ├── domain/          # pure business logic (averages, rounding, simulator, matching)
│       ├── undo/            # 50-entry vote-scoped undo stack
│       ├── sync/            # SyncProvider trait + ClasseViva + Axios
│       ├── pdf/             # printpdf report-card export
│       ├── commands.rs      # #[tauri::command] IPC surface
│       ├── events.rs        # typed event payloads
│       ├── menu.rs          # native menu
│       └── i18n.rs          # en/it translation
├── src/                     # React frontend (Vite)
│   ├── theme/               # tokens.scss, ThemeProvider, global.scss
│   ├── styles/              # per-component SCSS
│   ├── pages/               # Dashboard, Votes, Subjects, Simulator, Calendar, ReportCard, Statistics, Settings, Onboarding
│   ├── components/          # Sidebar, TopBar, charts, dialogs, primitives
│   └── lib/                 # ipc.ts, i18n, hooks, format helpers
└── package.json             # React + Vite
```

## Develop

### Prerequisites

- Rust ≥ 1.77 (`rustup toolchain install stable`)
- Node ≥ 20 and npm
- Tauri 2 system deps (Linux):
  `webkit2gtk-4.1`, `gtk3`, `libsoup3`, `libayatana-appindicator3`,
  `librsvg` — on Arch: `sudo pacman -S webkit2gtk-4.1 gtk3 libsoup3 libayatana-appindicator`

### Run the dev app

```bash
npm install
npm run tauri:dev
```

Vite serves the React frontend at `http://localhost:1420`; Tauri wraps it
in a native window and exposes Rust commands via `invoke()`.

### Tests

```bash
# Rust — unit + integration
cd src-tauri && cargo test

# Frontend type-check
npm run build
```

### Build release bundles

```bash
npm run tauri:build
```

This produces `.deb` / `.AppImage` on Linux, `.dmg` on macOS, and `.msi`
/ `.exe` on Windows, under `src-tauri/target/release/bundle/`.

## Feature spec

Every behavior in the rewrite is documented in
[`docs/REWRITE_SPEC.md`](docs/REWRITE_SPEC.md). When something in the
Rust / React code needs to match the Python app exactly — averages,
Italian rounding, the `7+ → 7.25` grade-symbol decoder, the
`new / updated / skipped` import triage — the spec is the contract,
and the original Python snippet is quoted inline.

## Data

Database path (unchanged from the Python app):

| OS      | Path                                                     |
|---------|----------------------------------------------------------|
| Linux   | `$XDG_DATA_HOME/votetracker/votes.db` (default: `~/.local/share/votetracker/`) |
| macOS   | `~/Library/Application Support/votetracker/votes.db`     |
| Windows | `%APPDATA%/votetracker/votes.db`                         |

## License

MIT. See [LICENSE](LICENSE).
