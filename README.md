# VoteTracker 3.0

<p align="center">
  <img src="src-tauri/icons/icon.png" alt="VoteTracker" width="128" height="128">
</p>

VoteTracker is a minimal desktop app that tracks school grades —
multi-year and multi-term, with averages, a simulator, a calendar view,
PDF report cards, statistics, and one-tap sync from Italian electronic
registers (ClasseViva, Axios).

Version 3.0 is a complete rewrite on **Tauri 2** with a **Rust** backend
and a **React + TypeScript + SCSS** frontend. The Python/PySide6
implementation that shipped through 2.x has been retired; a copy of the
last Python release lives on the `feat/axios-integration` and legacy
release tags.

## Highlights

- Claude.ai-inspired minimal design with a single warm coral accent gradient.
- Light / dark themes with OS auto-detect and manual override.
- Recharts-powered graphs (subject averages, grade histogram, trend line, radar).
- First-class native menu bar on macOS, Linux, and Windows.
- Auto-sync at app launch plus interval-based auto-sync via Tokio.
- Same `votes.db` schema as the Python app — existing installs open without conversion.

## Repository layout

```
votetracker/
├── docs/
│   └── REWRITE_SPEC.md      # the contract: every feature, every Python snippet, every Rust port
├── src-tauri/               # Rust backend
│   └── src/
│       ├── db/              # schema, migrations, CRUD, settings, school years
│       ├── domain/          # pure business logic (averages, rounding, simulator, matching)
│       ├── undo/            # 50-entry vote-scoped undo stack
│       ├── sync/            # SyncProvider trait + ClasseViva + Axios + import engine
│       ├── pdf/             # printpdf report-card export
│       ├── commands.rs      # #[tauri::command] IPC surface
│       ├── events.rs        # typed event payloads
│       ├── menu.rs          # native menu bar
│       └── i18n.rs          # language detection
├── src/                     # React frontend (Vite)
│   ├── theme/               # tokens.scss, ThemeProvider, global.scss
│   ├── styles/              # per-component SCSS
│   ├── pages/               # Dashboard, Votes, Subjects, Simulator, Calendar, ReportCard, Statistics, Settings, Onboarding
│   ├── components/          # Sidebar, TopBar, primitives/, dialogs/
│   └── lib/                 # ipc.ts, i18n, hooks, format helpers, zustand store
├── scripts/                 # PKGBUILD + votetracker.desktop
└── package.json             # React + Vite
```

## Develop

### Prerequisites

- Rust ≥ 1.77 (`rustup toolchain install stable`)
- Node ≥ 20 and npm
- Tauri 2 system deps (Linux, Arch): `sudo pacman -S webkit2gtk-4.1 gtk3 libsoup3 libayatana-appindicator librsvg`

### Run the dev app

```bash
npm install
npm run tauri:dev
```

Vite serves the React frontend at `http://localhost:1420`; Tauri wraps
it in a native window and exposes Rust commands via `invoke()`.

### Tests

```bash
cd src-tauri && cargo test     # 38 unit tests across schema, domain, undo, subject matcher
npm run build                  # tsc --noEmit + vite production build
```

### Build release bundles

```bash
npm run tauri:build
```

Produces `.deb` / `.AppImage` on Linux, `.dmg` on macOS, and `.msi` /
`.exe` on Windows under `src-tauri/target/release/bundle/`.

Arch Linux users can also install from `scripts/PKGBUILD`:

```bash
cd scripts && makepkg -si
```

## Feature specification

Every behavior in the app is documented in
[`docs/REWRITE_SPEC.md`](docs/REWRITE_SPEC.md), with references to the
original Python source where the behavior was first defined.

## Data

Database path:

| OS      | Path                                                     |
|---------|----------------------------------------------------------|
| Linux   | `$XDG_DATA_HOME/votetracker/votes.db` (default: `~/.local/share/votetracker/`) |
| macOS   | `~/Library/Application Support/votetracker/votes.db`     |
| Windows | `%APPDATA%/votetracker/votes.db`                         |

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+1…8` | Jump to page |
| `PgUp / PgDn` | Prev / next page |
| `Ctrl+Z` / `Ctrl+Shift+Z` | Undo / redo |
| `Ctrl+N` | New vote (on Votes page) |
| `Ctrl+I` / `Ctrl+E` | Import / export JSON |
| `Ctrl+R` | Sync Now |
| `Ctrl+Shift+T` | Toggle theme |
| `?` | Keyboard shortcuts help |

## License

MIT. See [LICENSE](LICENSE).
