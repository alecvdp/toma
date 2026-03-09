# Architecture Patterns

**Domain:** Personal medication/supplement tracking web app
**Researched:** 2026-03-08
**Confidence:** MEDIUM (based on training data for Streamlit patterns; web verification unavailable)

## Recommended Architecture

Streamlit + SQLite, organized as a multi-page app with a shared data access layer. Three logical tiers, all running in a single Python process:

```
+----------------------------------------------------------+
|  Streamlit UI Layer (Pages)                               |
|  +----------------+  +-----------+  +------------------+ |
|  | Daily Log Grid |  | Catalog   |  | History/Filters  | |
|  +-------+--------+  +-----+-----+  +--------+---------+ |
|          |                  |                 |           |
+----------|------------------|-----------------|----------+
|          v                  v                 v           |
|  Service Layer (Python modules)                          |
|  +-------------+  +---------------+  +-----------------+ |
|  | log_service |  | item_service  |  | wiki_service    | |
|  +------+------+  +-------+-------+  +-----------------+ |
|         |                 |                              |
+---------|-----------------|------------------------------+
|         v                 v                              |
|  Data Access Layer                                       |
|  +----------------------------------------------------+ |
|  | db.py  (connection, migrations, queries)            | |
|  +------------------------+---------------------------+ |
|                           |                              |
|                     toma.db (SQLite file)                 |
+----------------------------------------------------------+
```

### Why This Structure

Streamlit reruns the entire page script on every user interaction. Without separation, database calls and business logic get tangled into UI code, making it hard to test or refactor. A thin service layer keeps pages focused on layout while services handle logic and data access handles persistence.

This is NOT a traditional web MVC. Streamlit has no request/response cycle -- it has a rerun model. The architecture respects that by keeping pages as "render functions" that call into services.

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **`app.py`** (entrypoint) | App config, navigation setup, shared sidebar | Pages via Streamlit multi-page routing |
| **`pages/daily_log.py`** | Grid UI for logging doses by date | `log_service`, `item_service` |
| **`pages/catalog.py`** | CRUD interface for medication/supplement items | `item_service`, `wiki_service` |
| **`pages/history.py`** | Date-range filtered view of past logs | `log_service`, `item_service` |
| **`services/log_service.py`** | Business logic for daily log entries (create, update, query by date range) | `db.py` |
| **`services/item_service.py`** | Business logic for catalog items (CRUD, default dosages, categories) | `db.py` |
| **`services/wiki_service.py`** | Fetch and cache Wikipedia descriptions | Wikipedia API, `db.py` (cache) |
| **`db.py`** | SQLite connection management, schema migrations, raw queries | `toma.db` file |
| **`toma.db`** | SQLite database file | Filesystem only |

### Boundary Rules

1. **Pages never import `db.py` directly.** Always go through a service.
2. **Services never import Streamlit.** They return plain Python objects (dicts, dataclasses, lists). This keeps services testable without a Streamlit runtime.
3. **`db.py` owns the schema.** All table creation and migration lives here, not scattered across services.
4. **Wikipedia fetching is isolated.** Network calls to external APIs live in their own service so failures are contained and cacheable.

## Data Flow

### Flow 1: Logging a Dose (Primary Action)

```
User clicks cell in grid
  -> pages/daily_log.py captures (date, item_id, dosage)
  -> log_service.record_dose(date, item_id, dosage)
  -> db.py: INSERT OR REPLACE INTO daily_log (date, item_id, dosage)
  -> Streamlit reruns page
  -> pages/daily_log.py calls log_service.get_log(date_range)
  -> db.py: SELECT ... FROM daily_log JOIN items
  -> Grid re-renders with updated data
```

### Flow 2: Adding a Catalog Item

```
User fills form (name, category, default_dosage, notes)
  -> pages/catalog.py collects input
  -> item_service.create_item(name, category, default_dosage, notes)
  -> db.py: INSERT INTO items (...)
  -> wiki_service.fetch_description(name) [async/background]
  -> db.py: UPDATE items SET description = ? WHERE id = ?
  -> Streamlit reruns, catalog refreshes
```

### Flow 3: Viewing History

```
User selects date range via date pickers
  -> pages/history.py captures (start_date, end_date)
  -> log_service.get_log(start_date, end_date)
  -> db.py: SELECT ... FROM daily_log JOIN items WHERE date BETWEEN ? AND ?
  -> Returns as pandas DataFrame
  -> Rendered as st.dataframe or custom grid
```

### Data Direction Summary

```
User Input -> Streamlit Widget -> Page -> Service -> db.py -> SQLite
SQLite -> db.py -> Service -> Page -> Streamlit Render -> User sees update
```

All data flows are synchronous and same-process. No message queues, no async event loops, no API servers.

## Database Schema

```sql
-- Items in the catalog (medications, supplements)
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,              -- e.g., 'medication', 'supplement', 'vitamin'
    default_dosage TEXT,        -- e.g., '10mg', '1 capsule' (NULL = variable)
    description TEXT,           -- 1-3 sentences, from Wikipedia or manual
    notes TEXT,                 -- personal notes
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Daily log entries (one row per item per date)
CREATE TABLE daily_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,         -- ISO 8601 date: '2026-03-08'
    item_id INTEGER NOT NULL,
    dosage TEXT,                -- actual dosage taken (or NULL = taken at default)
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (item_id) REFERENCES items(id),
    UNIQUE(date, item_id)      -- one entry per item per date
);

-- Index for the primary query pattern
CREATE INDEX idx_daily_log_date ON daily_log(date);
CREATE INDEX idx_daily_log_date_item ON daily_log(date, item_id);
```

### Schema Design Decisions

- **`dosage` as TEXT, not NUMERIC:** Dosages come in many forms ("10mg", "2 capsules", "1/2 tablet", "500 IU"). Storing as text avoids unit conversion complexity. The app is a tracker, not a calculator.
- **`UNIQUE(date, item_id)`:** Enforces one log entry per item per day at the database level. Upsert via `INSERT OR REPLACE`.
- **`is_active` flag:** Soft-delete for items no longer taken. Preserves historical log integrity -- you can stop tracking an item without losing past data.
- **`default_dosage` on items table:** When present, the daily log can store NULL for dosage meaning "took the default." This enables the quick-checkmark UX from requirements.
- **Dates as TEXT (ISO 8601):** SQLite has no native date type. ISO 8601 strings sort correctly and work with SQLite date functions.

## Patterns to Follow

### Pattern 1: Service Layer Separation

**What:** Business logic in plain Python modules, not in Streamlit page scripts.
**When:** Always. Every database operation goes through a service.

```python
# services/log_service.py
import db

def record_dose(date: str, item_id: int, dosage: str | None = None) -> None:
    db.execute(
        "INSERT OR REPLACE INTO daily_log (date, item_id, dosage) VALUES (?, ?, ?)",
        (date, item_id, dosage)
    )

def get_log_for_date_range(start: str, end: str) -> list[dict]:
    return db.query(
        """SELECT d.date, i.name, i.default_dosage, d.dosage
           FROM daily_log d JOIN items i ON d.item_id = i.id
           WHERE d.date BETWEEN ? AND ?
           ORDER BY d.date DESC, i.sort_order""",
        (start, end)
    )
```

```python
# pages/daily_log.py (page only handles UI)
import streamlit as st
from services import log_service, item_service

date = st.date_input("Date", value=datetime.date.today())
items = item_service.get_active_items()
log_data = log_service.get_log_for_date_range(str(date), str(date))
# ... render grid ...
```

### Pattern 2: Streamlit Caching for Read-Heavy Data

**What:** Use `@st.cache_data` for database reads that do not change within a single interaction.
**When:** Item catalog list (changes rarely), not for daily log (changes frequently).

```python
@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_active_items():
    return item_service.get_active_items()
```

**Caution:** Clear cache explicitly after writes (`st.cache_data.clear()`) to avoid stale data.

### Pattern 3: Connection Management via Context Manager

**What:** SQLite connections scoped to operations, not held globally.
**When:** Every database operation.

```python
# db.py
import sqlite3
from contextlib import contextmanager

DB_PATH = "toma.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### Pattern 4: Schema Migration on Startup

**What:** Check and apply schema changes when the app starts, not scattered across modules.
**When:** App initialization in `app.py` or `db.py`.

```python
# db.py
def init_db():
    with get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS items (...)")
        conn.execute("CREATE TABLE IF NOT EXISTS daily_log (...)")
        # Future migrations: check a version table and apply deltas
```

### Pattern 5: DataFrame as Grid Transport

**What:** Convert query results to pandas DataFrames for grid display.
**When:** Daily log view, history view.

```python
import pandas as pd

def get_log_as_grid(date: str) -> pd.DataFrame:
    rows = log_service.get_log_for_date_range(date, date)
    # Pivot: rows=dates, columns=item names, values=dosage
    df = pd.DataFrame(rows)
    return df.pivot(index='date', columns='name', values='display_dosage')
```

This gives the spreadsheet-like view the user expects, matching the Excel mental model.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Database Calls in Widget Callbacks

**What:** Calling `db.execute()` directly inside `st.button()` or `st.on_change` handlers.
**Why bad:** Streamlit's rerun model means callbacks execute before the page rerenders. Mixing DB calls into callbacks creates hard-to-debug ordering issues and makes the code untestable.
**Instead:** Set a flag in `st.session_state`, then handle the DB operation in the main page flow.

### Anti-Pattern 2: Global SQLite Connection

**What:** Creating one `sqlite3.connect()` at module level and reusing it.
**Why bad:** Streamlit runs in a multi-threaded server. A single connection shared across sessions will cause "database is locked" errors or data corruption.
**Instead:** Use the context manager pattern (Pattern 3). Each operation gets its own connection.

### Anti-Pattern 3: Business Logic in Session State

**What:** Storing computed values, validation results, or derived data in `st.session_state`.
**Why bad:** Session state should hold UI state (which tab is selected, form values in progress). Putting business logic there makes it invisible, hard to test, and prone to stale state bugs.
**Instead:** Compute derived values in services. Use session state only for transient UI state.

### Anti-Pattern 4: One Giant Page Script

**What:** Putting all functionality (catalog, daily log, history) in a single `app.py`.
**Why bad:** Streamlit reruns the entire script on every interaction. A monolithic script means every click reruns everything, causing performance issues and state management nightmares.
**Instead:** Multi-page app with focused page scripts.

## Suggested Directory Structure

```
toma/
  app.py                    # Entrypoint: st.set_page_config, navigation, init_db()
  db.py                     # Connection management, schema, migrations
  services/
    __init__.py
    item_service.py         # Catalog CRUD
    log_service.py          # Daily log operations
    wiki_service.py         # Wikipedia description fetching
  pages/
    1_Daily_Log.py          # Grid-based daily logging view
    2_Catalog.py            # Item management (add/edit/view)
    3_History.py            # Date-filtered historical view
  models.py                 # Dataclasses for Item, LogEntry (optional but clean)
  toma.db                   # SQLite database (gitignored)
  requirements.txt          # streamlit, pandas, requests
```

**File naming for pages:** Streamlit uses filename-based routing. The numeric prefix (`1_`, `2_`, `3_`) controls sidebar ordering. Underscores become spaces in the nav.

## Suggested Build Order

Build order is driven by data dependencies: you need items before you can log doses, and you need logs before history is useful.

### Phase 1: Foundation (db.py + models + item_service)
- Database schema and connection management
- Item CRUD service
- Basic catalog page (add/view items)
- **Rationale:** Everything else depends on having items in the database. This is the prerequisite for all other features.

### Phase 2: Core Feature (log_service + daily log page)
- Daily log service (record/query doses)
- Grid-based daily log page
- Default dosage logic (quick-checkmark vs. variable entry)
- **Rationale:** This is the primary user action. It depends on Phase 1 (items exist). Building the grid view is the hardest UI challenge and should be tackled early.

### Phase 3: Polish and History
- History page with date range filtering
- Wikipedia description fetching
- Catalog card view with full item details
- **Rationale:** These features enhance the core but are not blocking. History is just a different query over the same data. Wikipedia fetching is a nice-to-have enhancement.

### Dependency Graph

```
db.py (schema, connections)
  |
  v
item_service + Catalog page     <-- Phase 1
  |
  v
log_service + Daily Log page    <-- Phase 2
  |
  v
History page                    <-- Phase 3
wiki_service (independent)      <-- Phase 3
```

## Scalability Considerations

| Concern | At 1 user (current) | At 5 years of data | Notes |
|---------|---------------------|---------------------|-------|
| Database size | ~100KB | ~5-10MB | SQLite handles this trivially. 365 days x 20 items = 7,300 rows/year. |
| Query speed | Instant | Instant | SQLite can handle millions of rows. Proper indexes make this a non-issue. |
| Concurrent access | N/A (single user) | N/A | WAL mode handles occasional concurrent reads from Streamlit's threading. |
| Backup | Copy `toma.db` | Copy `toma.db` | Single-file portability is a feature. |

This app will never hit scalability limits. SQLite with WAL mode and proper indexes can handle orders of magnitude more data than this use case will ever produce.

## Sources

- Streamlit documentation (architecture model, session state, multi-page apps, caching) -- based on training data, not live-verified
- SQLite documentation (WAL mode, foreign keys, date handling) -- based on training data
- **Confidence note:** Web search and fetch were unavailable during research. All patterns are based on established Streamlit/SQLite conventions from training data. Core architectural concepts (rerun model, session state, multi-page routing, SQLite connection management) are stable and well-established, so confidence remains MEDIUM rather than LOW.
