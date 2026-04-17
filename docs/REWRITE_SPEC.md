# VoteTracker — Tauri Rewrite Feature Specification

> **Purpose.** This document is the contract the Tauri rewrite must satisfy.
> For every feature it defines the expected behavior, the canonical Python
> source snippet from the legacy app, and the Rust / React port plan.
>
> **Scope.** Covers everything visible or observable in VoteTracker 2.9.x:
> data model, domain math, undo, sync providers, import dedup, PDF export,
> pages, shortcuts, i18n, theming.
>
> **Pointer convention.** All `legacy-python/...` paths are relative to this
> repo on the `tauri-rewrite` branch. Every snippet block is a direct quote
> from that file at the time the legacy tree was stashed in commit
> `087978e`. Line numbers are included so the reader can cross-reference.

---

## 1. Data model & file paths

### 1.1 Storage location (unchanged from v2.x)

| OS      | Path                                                            |
|---------|-----------------------------------------------------------------|
| Linux   | `$XDG_DATA_HOME/votetracker/votes.db` (fallback `~/.local/share/votetracker/`) |
| macOS   | `~/Library/Application Support/votetracker/votes.db`            |
| Windows | `%APPDATA%/votetracker/votes.db`                                |

The Rust port opens the same path — users who had the Python app keep every
vote / subject / setting.

### 1.2 Tables

Quoted from [`legacy-python/src/votetracker/db_schema.py:22-96`](../legacy-python/src/votetracker/db_schema.py):

```python
# school_years
CREATE TABLE IF NOT EXISTS school_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    start_year INTEGER NOT NULL,
    is_active INTEGER DEFAULT 0
)

# subjects
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)

# settings  (key/value)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)

# grade_goals
CREATE TABLE IF NOT EXISTS grade_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    school_year_id INTEGER NOT NULL,
    term INTEGER NOT NULL,
    target_grade REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (school_year_id) REFERENCES school_years(id) ON DELETE CASCADE,
    UNIQUE(subject_id, school_year_id, term)
)

# votes
CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    school_year_id INTEGER,
    grade REAL NOT NULL,
    type TEXT DEFAULT 'Written',
    term INTEGER DEFAULT 1,
    date TEXT,
    description TEXT,
    weight REAL DEFAULT 1.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (school_year_id) REFERENCES school_years(id) ON DELETE CASCADE
)
```

Indices (same file, lines 130–150):

```sql
idx_votes_subject, idx_votes_year, idx_votes_term, idx_votes_date,
idx_votes_composite (subject_id, school_year_id, term),
idx_settings_key
```

### 1.3 Migrations

Only one in-place migration exists: adding `school_year_id` and `term` to
pre-multi-year `votes` tables. See
[`legacy-python/src/votetracker/db_schema.py:61-95`](../legacy-python/src/votetracker/db_schema.py):

```python
if votes_exists:
    cursor.execute("PRAGMA table_info(votes)")
    columns = [col[1] for col in cursor.fetchall()]
    if "school_year_id" not in columns:
        cursor.execute("ALTER TABLE votes ADD COLUMN school_year_id INTEGER")
        cursor.execute("ALTER TABLE votes ADD COLUMN term INTEGER DEFAULT 1")
```

### 1.4 Seed — Italian school year detection

```python
# legacy-python/src/votetracker/db_schema.py:98-111
now = datetime.now()
# Italian school year starts in September.
start_year = now.year if now.month >= 9 else now.year - 1
year_name = f"{start_year}/{start_year + 1}"
cursor.execute(
    "INSERT INTO school_years (name, start_year, is_active) VALUES (?, ?, 1)",
    (year_name, start_year),
)
```

Ported in [`src-tauri/src/db/schema.rs::seed_defaults`](../src-tauri/src/db/schema.rs).

### 1.5 Settings-key conventions

Everything non-schema (credentials, mappings, language, sync config, active
provider) is a row in `settings`. **Keys are namespaced by provider.**

```
language                      → "en" | "it"
current_term                  → "1" | "2"
active_sync_provider          → "classeviva" | "axios"
onboarding_complete           → "1"
theme_preference              → "system" | "light" | "dark"    (new in 3.x)

{provider_id}_username        → base64(username)
{provider_id}_password        → base64(password)
{provider_id}_customer_id     → base64(customer_id)            (Axios)
{provider_id}_mapping_{src}   → VT subject name
{provider_id}_auto_sync       → "1" | "0"
{provider_id}_sync_interval   → "60"                            (minutes)
{provider_id}_last_sync       → ISO 8601 timestamp
{provider_id}_auto_login      → "1" | "0"

# Legacy ClasseViva keys kept for compatibility:
classeviva_username           → base64(username)
classeviva_password           → base64(password)
cv_mapping_{source_subject}   → VT subject name
```

Base64 is **obfuscation, not encryption** — see
[`legacy-python/src/votetracker/database.py:360-394`](../legacy-python/src/votetracker/database.py).

---

## 2. Domain math

### 2.1 Weighted average with `+/-` exclusion

`+` and `−` marks arrive as `grade = 0.0` and must not skew averages.

```python
# legacy-python/src/votetracker/utils.py:18-34
def calc_average(votes: list[dict]) -> float:
    if not votes:
        return 0.0
    valid_votes = [v for v in votes if v.get("grade", 0) > 0]
    if not valid_votes:
        return 0.0
    total = sum(v.get("grade", 0) * v.get("weight", 1.0) for v in valid_votes)
    weights = sum(v.get("weight", 1.0) for v in valid_votes)
    return total / weights if weights > 0 else 0.0
```

Rust port lives in
[`src-tauri/src/domain/average.rs`](../src-tauri/src/domain/average.rs) and
has unit tests that pin the zero-exclusion and weighted cases.

### 2.2 Italian report-card rounding

```python
# legacy-python/src/votetracker/utils.py:36-46
def round_report_card(average: float) -> int:
    if average <= 0:
        return 0
    decimal = average - int(average)
    if decimal >= 0.5:
        return int(average) + 1
    return int(average)
```

Ported in [`src-tauri/src/domain/rounding.rs`](../src-tauri/src/domain/rounding.rs).
Boundary tests cover `4.49 → 4`, `4.50 → 5`, `5.50 → 6`, `9.9 → 10`.

### 2.3 Simulator — needed grade for target average

From `legacy-python/src/votetracker/database.py::calculate_needed_grade`:

```python
total_weighted = sum(v['grade'] * v['weight'] for v in votes)
total_weight   = sum(v['weight'] for v in votes)
current_avg    = total_weighted / total_weight if total_weight > 0 else 0

if current_avg >= target_avg:
    return None                       # already at target

# (current_sum + needed*w) / (total_w + w) = target
needed = (target_avg * (total_weight + weight) - total_weighted) / weight
return min(needed, 10.0)              # cap at max grade
```

Ported in
[`src-tauri/src/domain/simulator.rs`](../src-tauri/src/domain/simulator.rs).

### 2.4 Grade color thresholds

```python
# legacy-python/src/votetracker/utils.py:63-69
def get_status_color(average: float) -> QColor:
    if average < GRADE_INSUFFICIENT:   # 5.5
        return StatusColors.FAILING     # red
    elif average < PASSING_GRADE:       # 6.0
        return StatusColors.WARNING     # yellow/orange
    return StatusColors.PASSING         # green
```

React equivalent (lives in `src/lib/format.ts`, to add in M3):

```ts
export function getGradeColor(avg: number): string {
  if (avg < 5.5) return "var(--grade-insufficient)";
  if (avg < 6.0) return "var(--grade-warning)";
  if (avg < 8.0) return "var(--grade-good)";
  return "var(--grade-excellent)";
}
```

### 2.5 Fuzzy subject matcher — confidence ladder

Source: [`legacy-python/src/votetracker/subject_matcher.py`](../legacy-python/src/votetracker/subject_matcher.py).

| Match case                                         | Confidence |
|----------------------------------------------------|------------|
| Exact normalized equality                          | 1.00       |
| Substring containment either direction             | 0.90       |
| Both names hit the same keyword group              | 0.85       |
| VT name is canonical, source hits its keyword set  | 0.80       |
| Jaccard word overlap                               | `0.7 * |A∩B| / |A∪B|` |
| Otherwise                                          | 0.00       |

Matches below **0.6** are reported as "no match". Ported with the same
table in [`src-tauri/src/domain/subject_match.rs`](../src-tauri/src/domain/subject_match.rs) in M2.

---

## 3. Undo / redo

Vote operations **only** — not subjects, settings, school years.

```python
# legacy-python/src/votetracker/undo.py:84-90
def _push_undo(self, action: UndoAction):
    self._undo_stack.append(action)
    if len(self._undo_stack) > self._max_history:  # max_history = 50
        self._undo_stack.pop(0)                    # FIFO drop oldest
    self._redo_stack.clear()
    self.state_changed.emit()
```

Undoing a DELETE re-adds the vote, which gets a new id; the action's
`vote_id` is updated so redo can re-delete it:

```python
# legacy-python/src/votetracker/undo.py:114-131
elif action.action_type == ActionType.DELETE:
    data = action.vote_data
    self._db.add_vote(
        data["subject"], data["grade"], data["type"],
        data["date"], data["description"],
        term=data["term"], weight=data.get("weight", 1.0)
    )
    votes = self._db.get_votes(subject=data["subject"])
    for v in votes:
        if (v["grade"] == data["grade"] and
            v["date"] == data["date"] and
            v["type"] == data["type"]):
            action.vote_id = v["id"]
            break
```

`state_changed` emits after every push/undo/redo/clear so the frontend can
toggle menu items (⌘Z / ⌘⇧Z) and sidebar buttons. In the Rust port this is
a `undo-state` Tauri event with payload:

```rust
// src-tauri/src/events.rs
pub struct UndoStatePayload {
    pub can_undo: bool,
    pub can_redo: bool,
    pub undo_text: Option<String>,
    pub redo_text: Option<String>,
}
```

---

## 4. Import / sync

### 4.1 Canonical grade shape

All providers return grades as a uniform dict / struct, which the import
engine then maps via subject mapping before writing to `votes`:

```json
{
  "subject": "MATEMATICA",        // provider's raw subject name
  "grade":   7.25,                // float 0..10
  "type":    "Written",           // English: Written | Oral | Practical
  "date":    "2024-10-15",        // ISO YYYY-MM-DD
  "description": "Test algebra",  // optional
  "weight":  1.0,                 // default 1.0
  "term":    1                    // 1 | 2
}
```

### 4.2 Dedup algorithm — **new / updated / skipped**

Match by `(subject, date, type)` — **never** including grade, because
teachers amend grades after the fact:

```python
# legacy-python/src/votetracker/database.py::find_vote_by_metadata
WHERE v.subject_id = ? AND v.school_year_id = ?
  AND v.date = ? AND v.type = ?
```

- Exact match (same grade too) → **Skipped**
- Metadata match, different grade/weight/description → **Updated**
- No metadata match → **New** (INSERT)

Reported to UI as `"X new, Y updated (Z skipped)"`.

Ported in `src-tauri/src/sync/import.rs` in M5:

```rust
pub enum ImportOutcome { New, Updated, Skipped }

pub fn import_one(db: &Database, raw: &RawGrade, provider_id: &str) -> ImportOutcome {
    let subject = db.settings().get_mapping(provider_id, &raw.subject)
        .unwrap_or_else(|| raw.subject.clone());

    match db.votes().find_by_metadata(&subject, &raw.date, raw.kind) {
        Some(existing) if existing_matches_raw(&existing, raw) => ImportOutcome::Skipped,
        Some(existing) => { db.votes().update_from_raw(existing.id.unwrap(), raw); ImportOutcome::Updated }
        None           => { db.votes().add_from_raw(&subject, raw); ImportOutcome::New }
    }
}
```

### 4.3 JSON import/export format

```json
[
  {
    "subject": "Math",
    "grade": 8.5,
    "type": "Written",
    "term": 1,
    "date": "2025-01-15",
    "description": "Chapter 5 test",
    "weight": 1.0
  }
]
```

Container variants accepted on import:

- Direct array: `[ {...}, {...} ]`
- `{"votes": [...]}`
- `{"voti": [...]}` (Italian)

Italian field-name aliases accepted: `materia`, `voto`, `tipo` (Scritto /
Orale / Pratico), `quadrimestre`, `data`, `desc`, `peso`.

### 4.4 ClasseViva (REST) — `legacy-python/src/votetracker/classeviva.py`

Endpoint base: `https://web.spaggiari.eu/rest/v1`

Required headers on every request:

```
User-Agent: CVVS/std/4.2.3 Android/12
Z-Dev-ApiKey: Tg1NWEwNGIgIC0K
Content-Type: application/json
Z-Auth-Token: <token>   (after login)
```

Login:

```json
POST /auth/login
{ "ident": null, "uid": "S1234567", "pass": "…" }

→ 200
{
  "token": "…",
  "ident": "S1234567",
  "expire": "<iso>",
  "firstName": "Ada",
  "lastName":  "Lovelace"
}
```

Fetch grades:

```
GET /students/{ident}/grades   with Z-Auth-Token
```

Each grade contains `decimalValue`, `subjectDesc`, `componentDesc` (Orale /
Scritto / Grafico / Laboratorio), `notesForFamily`, `evtDate`
(YYYY-MM-DD), `weightFactor`, `periodPos`, `periodDesc`, `canceled`.

Normalization rules:

- `periodPos > 1` ⇒ `term = 2`; else `term = 1`.
- `componentDesc` → `type`: *Orale* → Oral; *Scritto* / *Grafico* →
  Written; *Pratico* / *Laboratorio* → Practical; otherwise keep original.
- Drop grades where `canceled == true`.

Mapping prefix: **`cv`** (legacy compat).

### 4.5 Axios (HTML scrape) — `legacy-python/src/votetracker/providers/axios_provider.py`

Base: `https://registrofamiglie.axioscloud.it`

Login is multi-phase:

1. `GET /Pages/SD/SD_Login.aspx` → establishes `JSESSIONID` cookie.
2. `POST` same URL with form data `customerid`, `username`, `password`.
3. Response redirects; extract auth token via regex
   `id='_AXToken' value='([^']+)'`.
4. Subsequent AJAX uses the token in the custom `RVT` header.

Term list:

```
GET /Pages/APP/APP_Ajax_Get.aspx?Action=FAMILY_VOTI&_=<epoch_ms>
→ { "errorcode": "0", "html": "<select id='fiFrazId'>…" }
```

Parse `<option>` entries to get term IDs. Label match rules:

- `"TRIMESTRE"` *without* `"PENTA"` → Term 1
- `"PENTAMESTRE"` or starts with `"2°"` → Term 2

Grade list per term:

```
POST /Pages/APP/APP_Ajax_Get.aspx?Action=FAMILY_VOTI       { "iFrazId": "FRAZ_001" }
POST /Pages/APP/APP_Ajax_Get.aspx?Action=FAMILY_VOTI_ELENCO_LISTA
     { "draw": 1, "start": 0, "length": 1000, "frazione": "<id>" }
```

Rows come back in DataTables shape. **Grade decoding** is the subtle
part — the human-visible text is one of `7`, `7+`, `7-`, `7½`, `7,25`,
`7.25`, and the numeric value is sometimes hidden in
`title='Voto: 7+ … Valore: 7,25'`:

- Prefer `Valore:` from the title if present.
- Else: `7+` → 7.25, `7-` → 6.75, `7½` / `7 1/2` → 7.50.
- Decimal commas → decimal points (`7,25` → `7.25`).

Date is `DD/MM/YYYY` → convert to `YYYY-MM-DD`. Weight defaults to `1.0`
(Axios doesn't publish it).

Mapping prefix: **`axios`**.

### 4.6 Provider registry

```python
# legacy-python/src/votetracker/providers/__init__.py
def register_all_providers():
    SyncProviderRegistry.register("classeviva", ClasseVivaProvider)
    if _is_axios_available():   # lxml importable
        SyncProviderRegistry.register("axios", AxiosProvider)
```

Lazy singleton per provider id. Rust port:

```rust
// src-tauri/src/sync/mod.rs (M5)
#[async_trait]
pub trait SyncProvider: Send + Sync {
    fn id(&self) -> &'static str;
    fn display_name(&self) -> &'static str;
    fn credential_fields(&self) -> Vec<CredentialField>;
    async fn login(&mut self, creds: &HashMap<String, String>) -> Result<String, SyncError>;
    async fn fetch_grades(&self) -> Result<Vec<RawGrade>, SyncError>;
    fn mapping_prefix(&self) -> &'static str;
}
```

### 4.7 Auto-sync

Two triggers:

1. **Startup** — after the main window fires its ready event, for each
   provider with `{id}_auto_sync == "1"` and saved credentials, spawn a
   Tokio task: `login → fetch_grades → import_all → emit sync-status →
   write {id}_last_sync`. Never blocks the UI.
2. **Interval** — `tokio::time::interval(Duration::from_secs(
   {id}_sync_interval * 60))`. A `(provider_id, enabled, interval)` mpsc
   channel from the Settings commands restarts the interval when config
   changes.

---

## 5. Pages (React)

All pages live under `src/pages/`. They're routed via React Router and
share the persistent `Sidebar` + `TopBar`.

### 5.1 Dashboard (`Dashboard.tsx`)

- 4 hero stat cards: Overall Avg, Failing Count, Total Votes, Subjects.
  Background: `--accent-gradient-soft`. Big numbers use `tabular-nums`.
- Right column: 6 most-recent grades (sorted DESC by `date`).
- Below: responsive grid of `SubjectCard`s — 3 cols ≥1280px, 2 cols
  ≥768px, 1 col otherwise. Each card shows: subject name, current avg
  (colored via `getGradeColor`), split written/oral/practical micro-bars,
  and goal progress if one exists.

Reference: [`legacy-python/src/votetracker/pages/dashboard.py`](../legacy-python/src/votetracker/pages/dashboard.py).

### 5.2 Votes (`Votes.tsx`)

- Virtualized table (TanStack Table + react-virtual) — columns: Date,
  Subject, Description, Term, Type, Grade, weight.
- Inline filter chips: subject select, type radio, term toggle (1/2).
- Add FAB → `AddVoteDialog`. Row actions: Edit (Enter or double-click),
  Delete (Del or right-click).
- Keyboard: `Ctrl+N` new, `Enter` edit selected, `Delete` delete selected.

### 5.3 Subjects (`Subjects.tsx`)

Grid of cards — one per subject. Card click → edit (rename / delete).
`Add Subject` button at top calls `AddSubjectDialog`.

### 5.4 Simulator (`Simulator.tsx`)

Left: inputs (subject select including "Overall", target avg spinner
(1.0–10.0, step 0.5, default 6.0), filter radios Written/Oral/Both).

Right: live-computed cards: *needed grade*, *current avg*, *projected
avg*, feasibility badge (green if needed ≤ 8, yellow if ≤ 10, red if
> 10 / `None`).

Math: `src-tauri/src/domain/simulator.rs::calculate_needed_grade`.

### 5.5 Calendar (`Calendar.tsx`)

Custom month grid in SCSS — no external calendar library. Each day cell
shows a colored dot per vote, with a count badge on multi-vote days.
Click → slide-out drawer listing that day's grades. Month nav arrows +
year jump in the top bar.

### 5.6 Report Card (`ReportCard.tsx`)

Preview table with term switch and "Split written/oral" toggle.
**Export PDF** button calls the Rust command `export_report_card_pdf`
(printpdf under the hood). Italian rounding note rendered under the
table.

### 5.7 Statistics (`Statistics.tsx`)

Four tiles, all Recharts:

1. **Subject averages** — horizontal bar chart, each bar colored by grade
   status, sorted DESC.
2. **Grade histogram** — 0.5-wide bins from 0 to 10.
3. **Trend line** — average per date.
4. **Subject radar** — one axis per subject (only when ≥ 4 subjects).

All charts use the `--chart-*` CSS variables for axis/grid colors and
apply `var(--accent-gradient)` fills via SVG `<linearGradient>`.

### 5.8 Settings (`Settings.tsx`)

Sections:

- **General** — theme (system/light/dark) + language (en/it).
- **Data** — Import JSON, Export JSON, Open Data Folder.
- **School Years** — list + active selector + add / delete.
- **Sync Providers** — one collapsible panel per registered provider:
  credential form (fields from `credential_fields()`), Test Connection
  button, Auto-sync toggle + interval spinner (5/15/30/60 min),
  last-sync timestamp, **Configure Subject Mapping…** button that opens
  `SubjectMappingDialog` seeded from `subject_match::get_auto_suggestions`.
- **About** — version, data path, link to GitHub.

### 5.9 Onboarding (`Onboarding.tsx`)

Shown when `is_onboarding_complete()` → false. 4 steps:

1. Welcome
2. Add subjects — preset list from `i18n::PRESET_SUBJECTS` with add-all
   and custom-add
3. Optional provider setup
4. Finish (sets `onboarding_complete = "1"`)

---

## 6. Keyboard shortcuts

Single hook (`useShortcuts` in `src/lib/hooks/useShortcuts.ts`) — the menu
accelerators emit the same events, so there's one source of truth.

| Scope          | Key                   | Action                          |
|----------------|-----------------------|---------------------------------|
| Global         | `Ctrl+1 … Ctrl+8`     | Jump to Dashboard … Settings    |
| Global         | `PgUp` / `PgDn`       | Prev / next page                |
| Global         | `Ctrl+Z`              | Undo                            |
| Global         | `Ctrl+Shift+Z`, `Ctrl+Y` | Redo                         |
| Global         | `?`                   | Show shortcuts help             |
| Global         | `Ctrl+R`              | Sync now                        |
| Global         | `Ctrl+Shift+T`        | Toggle theme                    |
| Votes          | `Ctrl+N`              | New vote                        |
| Votes          | `Enter`               | Edit selected                   |
| Votes          | `Delete`              | Delete selected                 |
| Settings       | `Ctrl+I`              | Import JSON                     |
| Settings       | `Ctrl+E`              | Export JSON                     |
| Report Card    | `1` / `2`             | Switch term                     |

macOS maps `Ctrl` → `Cmd` automatically via the menu's accelerator model.

---

## 7. Native menu (macOS / Linux / Windows)

Built in `src-tauri/src/menu.rs` (M7). Mirrors shortcuts above.

- **App** (macOS only): About · Preferences (⌘,) · Hide · Quit
- **File**: New Vote · Import JSON · Export JSON · Export Report Card PDF · Close
- **Edit**: Undo · Redo · Cut/Copy/Paste · Find
- **View**: Dashboard…Settings · Previous/Next Page · Toggle Theme
- **Sync**: Sync Now · Enable Auto-Sync · Configure Providers
- **Help**: Keyboard Shortcuts · Open Data Folder · About

Each menu click emits a Tauri event (`menu://new-vote`,
`menu://sync-now`, …) consumed by the frontend router.

---

## 8. Theme

- 3-state preference: `system` | `light` | `dark`. Persisted in
  localStorage **and** in SQLite (`theme_preference` setting) so Rust
  side can read it for menu check-marks.
- `ThemeProvider` watches `(prefers-color-scheme: dark)`. Changes apply
  via `<html data-theme="…">` — tokens in
  [`src/theme/tokens.scss`](../src/theme/tokens.scss).
- Transition: 200ms ease on `color` + `background-color` only; no
  animation on structural properties.
- `prefers-reduced-motion` is respected globally in
  [`src/theme/global.scss`](../src/theme/global.scss).

### 8.1 Design tokens (excerpt)

```scss
// light
--surface: #faf9f5;
--text:    #201f1d;
--accent-500: #d97757;
--accent-gradient: linear-gradient(135deg, #d97757 0%, #f2bf9b 100%);

// dark
--surface: #1f1d1b;
--text:    #e9e6df;
--accent-500: #e28963;
```

Grade status colors are theme-dependent — dark-mode variants bump
lightness so red/green stay distinguishable.

---

## 9. i18n

English + Italian, 250+ keys. Source:
[`legacy-python/src/votetracker/i18n.py`](../legacy-python/src/votetracker/i18n.py).
Ported to `src/lib/i18n/en.ts` and `src/lib/i18n/it.ts` in M7.

Auto-detect from `LANG` / `navigator.language`:

```python
# legacy-python/src/votetracker/i18n.py
def get_system_language() -> str:
    # returns "it" if locale starts with "it", else "en"
```

Persisted in `settings.language`.

Preset subjects list used by the onboarding wizard (translated at display
time):

```
Italian, Math, English, History, Philosophy, Physics, Science,
Latin, Art, Physical Education, Computer Science, Religion,
Geography, Chemistry, Biology
```

---

## 10. IPC surface (Tauri commands)

Grouped by concern. All return JSON; errors are `Result<_, String>` on
the wire.

**Votes:** `list_votes`, `add_vote`, `update_vote`, `delete_vote`, `get_vote`, `find_vote_by_metadata`.
**Subjects:** `list_subjects`, `add_subject`, `rename_subject`, `delete_subject`, `subject_stats`.
**Years / terms:** `list_years`, `add_year`, `delete_year`, `set_active_year`, `get_current_term`, `set_current_term`.
**Stats:** `grade_statistics`, `subject_distribution`, `grade_trend`.
**Simulator:** `calculate_needed_grade`.
**Goals:** `set_grade_goal`, `get_grade_goal`, `list_grade_goals`, `delete_grade_goal`.
**Import/export:** `import_json`, `export_json`, `import_from_provider`.
**Providers:** `list_providers`, `save_provider_credentials`, `test_provider_login`, `save_provider_mapping`, `list_provider_mappings`, `set_auto_sync`, `set_sync_interval`, `trigger_sync_now`.
**Undo:** `undo`, `redo`, `undo_state`.
**Misc:** `get_setting`, `set_setting`, `open_data_dir`, `export_report_card_pdf`.
**Theme:** `get_theme_preference`, `set_theme_preference`.
**Onboarding:** `is_onboarding_complete`, `mark_onboarding_complete`.

Events emitted from Rust:

| Event                  | Payload                                |
|------------------------|----------------------------------------|
| `data-changed`         | none (just a pulse)                    |
| `data-imported`        | `{ new, updated, skipped }`            |
| `school-year-changed`  | `{ school_year_id }`                   |
| `undo-state`           | `UndoStatePayload`                     |
| `sync-status`          | `SyncStatusPayload` (tagged union)     |
| `theme-changed`        | `{ preference, resolved }`             |

---

## 11. PDF export

Port of [`legacy-python/src/votetracker/pages/report_card.py`](../legacy-python/src/votetracker/pages/report_card.py)'s
reportlab renderer to the `printpdf` crate in
`src-tauri/src/pdf/report_card.rs` (M4). Layout:

- A4 portrait, 20mm margins.
- Header — school year + generated timestamp.
- Optional header block with student name (from active provider display
  name, if any).
- Table columns: *Subject | Written | Oral | Final (rounded)* when Split
  mode; otherwise *Subject | Final*.
- Final grade uses `round_report_card()`.
- Footer — small gray "Generated by VoteTracker 3.0".

---

## 12. Verification checklist

- [ ] `cargo test` passes all unit tests for `db::schema`, `domain::*`, `undo`, `sync::import`.
- [ ] Open a copy of the current Python `votes.db`; every row visible in the React UI.
- [ ] Manual walk-through: Dashboard, Votes, Subjects, Simulator, Calendar, Report Card, Statistics, Settings, Onboarding.
- [ ] Shortcuts: `Ctrl+1..8`, `Ctrl+Z / Ctrl+Shift+Z`, `Ctrl+N/I/E/R`, `?`, `PgUp/PgDn`, `Ctrl+Shift+T`.
- [ ] Theme: OS toggle propagates without reload; manual override persists.
- [ ] Menu visible on macOS menubar; visible as window menu on Linux / Windows; each item fires the right action.
- [ ] Startup auto-sync fires for each configured provider; `sync-status` toast appears; `last_sync` timestamp updates.
- [ ] Sync totals match legacy app: `"X new, Y updated (Z skipped)"` identical for the same source data.
- [ ] Report card PDF — column counts, totals, rounding match legacy output.
- [ ] Language toggle en ↔ it re-renders every label.
