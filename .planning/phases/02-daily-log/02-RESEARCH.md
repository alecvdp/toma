# Phase 2: Daily Log - Research

**Researched:** 2026-03-08
**Domain:** Streamlit data grid UI, SQLite log schema, daily intake tracking
**Confidence:** HIGH

## Summary

Phase 2 builds the core daily logging interface: a grid with dates as rows and catalog items as columns, where cell values represent dosages taken. The existing Phase 1 foundation provides an `items` table, `item_service.py` CRUD layer, and Streamlit page infrastructure. Phase 2 needs a new `daily_logs` table (normalized row-per-entry, per prior decision), a `log_service.py`, and a new Streamlit page using `st.data_editor` for the grid.

The key technical challenge is bridging the normalized database schema (one row per item per day) with the pivoted grid view (dates x items matrix) that `st.data_editor` renders. Pandas pivot/melt operations handle this translation cleanly. The `st.data_editor` widget in Streamlit 1.55 supports `column_config` for per-column type control, `on_change` callbacks for persistence, and `column_order` for user-controlled column ordering (CAT-10).

**Primary recommendation:** Use `st.data_editor` with a pandas DataFrame pivoted from the normalized `daily_logs` table. Persist edits via the `on_change` callback by reading `st.session_state[key]["edited_rows"]` and writing back to the normalized table. Use `CheckboxColumn` for fixed-dose items (single-click taken) and `NumberColumn` for variable dosage.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LOG-01 | Grid view with dates as rows, items as columns, dosages as cells | `st.data_editor` with pivoted DataFrame; `column_order` param |
| LOG-02 | Single-click mark fixed-dose item as taken (auto-fill default dosage) | `CheckboxColumn` or `NumberColumn` with on_change callback writing default_dosage |
| LOG-03 | Variable dosage override for any item on any day | `NumberColumn` in column_config; edits detected via `edited_rows` |
| LOG-04 | "Take all" button for fixed-dose items | `st.button` that bulk-inserts default dosages for all fixed-dose items for current date |
| LOG-05 | Optional note on any individual log entry | `notes` column in `daily_logs` table; separate UI element (not in grid) |
| LOG-06 | Navigate to any date to view/edit that day's log | `st.date_input` date picker controlling which rows appear in grid |
| CAT-10 | Custom sort order for items in daily log view | `sort_order` column already exists on `items` table; use it for `column_order` param |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | 1.55.0 | UI framework, data_editor widget | Already in use; data_editor is the standard editable grid |
| pandas | >=2.2 | DataFrame pivot/melt for grid transform | Already in deps; required for data_editor data format |
| sqlite3 | stdlib | Database | Already in use via db.py |

### Supporting (no new deps needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Date handling, navigation | Date picker, log date storage |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| st.data_editor grid | Manual st.columns + st.checkbox per cell | data_editor handles scrolling, performance, and cell editing natively; manual approach doesn't scale |
| Pivoted DataFrame | Column-per-item schema | Decision already locked: normalized row-per-entry schema. Pivot at display time only |

**Installation:**
```bash
# No new packages needed. Existing deps cover Phase 2.
```

## Architecture Patterns

### Recommended Project Structure
```
services/
  item_service.py      # existing
  log_service.py       # NEW: daily log CRUD
pages/
  catalog.py           # existing
  daily_log.py         # NEW: grid UI page
db.py                  # extend init_db with daily_logs table
models.py              # optional: LogEntry dataclass
tests/
  test_log_service.py  # NEW: log service tests
  test_db.py           # extend with daily_logs schema test
```

### Pattern 1: Normalized Schema with Display-Time Pivot

**What:** Store one row per (date, item_id) in `daily_logs`. Pivot to a date-rows x item-columns DataFrame for display. Unpivot edits back to row operations.

**When to use:** Always -- this is the locked decision from Phase 1 research.

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date TEXT NOT NULL,          -- 'YYYY-MM-DD' format
    item_id INTEGER NOT NULL,
    dosage_taken REAL,               -- NULL = not logged, 0 = skipped, >0 = taken
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (item_id) REFERENCES items(id),
    UNIQUE(log_date, item_id)        -- one entry per item per day
);
CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(log_date);
CREATE INDEX IF NOT EXISTS idx_daily_logs_item ON daily_logs(item_id);
```

**Pivot logic:**
```python
import pandas as pd

def get_log_grid(start_date, end_date):
    """Fetch logs and pivot into grid format for st.data_editor."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT dl.log_date, i.name, dl.dosage_taken
            FROM daily_logs dl
            JOIN items i ON dl.item_id = i.id
            WHERE dl.log_date BETWEEN ? AND ?
              AND i.is_active = 1
            ORDER BY dl.log_date
        """, (start_date, end_date)).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(r) for r in rows])
    grid = df.pivot(index="log_date", columns="name", values="dosage_taken")
    return grid
```

### Pattern 2: on_change Callback for Persistence

**What:** Use `st.data_editor` with a `key` parameter. On change, read `st.session_state[key]["edited_rows"]` to get `{row_index: {"column_name": new_value}}` and write changes back to SQLite.

**When to use:** Every time the user edits a cell in the grid.

**Example:**
```python
def handle_grid_edit():
    """Persist edits from data_editor back to daily_logs."""
    changes = st.session_state["log_grid"]["edited_rows"]
    for row_idx, col_changes in changes.items():
        log_date = grid_df.index[row_idx]  # date from row index
        for item_name, new_dosage in col_changes.items():
            upsert_log_entry(log_date, item_name, new_dosage)

edited = st.data_editor(
    grid_df,
    key="log_grid",
    on_change=handle_grid_edit,
    hide_index=False,  # show dates as row labels
    column_order=ordered_item_names,
)
```

### Pattern 3: Single-Click Fixed-Dose Toggle (LOG-02)

**What:** For items with a default_dosage, a single click should toggle between "taken at default dose" and "not taken." Two approaches:

**Approach A (Recommended): NumberColumn with default fill.**
Cells show the dosage number. Clicking into a cell and pressing Enter or tabbing auto-fills from default. The on_change callback writes the value. Empty/0 = not taken.

**Approach B: Separate checkbox + value columns.**
More complex UI, harder to maintain grid metaphor.

**Recommendation:** Use NumberColumn for all items. For "single click" taking, provide a "Take All" button (LOG-04) that fills all empty cells with defaults for today. Individual cells can be edited to override.

### Anti-Patterns to Avoid
- **Column-per-item in the database:** Violates normalization, makes adding/removing items require ALTER TABLE.
- **Clearing edited_rows directly:** `st.session_state[key]["edited_rows"] = {}` does not work. Track processed changes separately if needed.
- **Storing dates as integers or timestamps:** Use ISO 'YYYY-MM-DD' text for SQLite -- consistent, sortable, human-readable.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Editable grid | Custom HTML/JS grid | `st.data_editor` | Handles scrolling, cell types, keyboard nav, mobile |
| DataFrame pivot | Manual dict-of-dicts manipulation | `pandas.DataFrame.pivot()` / `pivot_table()` | Edge cases with missing data, type handling |
| Date navigation | Custom prev/next buttons with state mgmt | `st.date_input` | Built-in calendar picker, range selection |
| Upsert logic | Check-then-insert-or-update | `INSERT OR REPLACE` / `ON CONFLICT` | Atomic, avoids race conditions |

**Key insight:** The entire grid editing UX is handled by `st.data_editor`. The service layer just needs CRUD on the normalized table and a pivot function.

## Common Pitfalls

### Pitfall 1: "Not Taken" vs "Not Logged" Ambiguity
**What goes wrong:** A NULL/empty cell is ambiguous -- did the user skip the item or just not log yet?
**Why it happens:** No explicit "skipped" state in the data model.
**How to avoid:** Use a convention: NULL/missing row = not yet logged, 0 = explicitly skipped, >0 = taken with that dosage. Document this in the UI with a legend or tooltip.
**Warning signs:** Users confused about whether they took something on a past date.

### Pitfall 2: data_editor edited_rows Accumulation
**What goes wrong:** `edited_rows` in session_state accumulates ALL edits across reruns in the same session. Processing them naively causes duplicate writes.
**Why it happens:** Streamlit doesn't clear the edit dict between reruns.
**How to avoid:** Use `INSERT OR REPLACE` (upsert) so re-processing the same edit is idempotent. The upsert approach means duplicate processing has no side effects.
**Warning signs:** Database shows duplicate entries or unexpected values.

### Pitfall 3: Grid Column Mismatch After Catalog Changes
**What goes wrong:** If user adds/removes catalog items, the grid columns and the database entries can go out of sync.
**Why it happens:** Grid is built from active items; logs reference item_ids that may have been deactivated.
**How to avoid:** Always build grid columns from current active items. Join on items table when querying logs. Deactivated items don't appear as columns but their historical data remains in daily_logs.
**Warning signs:** KeyError or missing columns in pivoted DataFrame.

### Pitfall 4: Empty Grid on First Use
**What goes wrong:** No logs exist yet, so the pivoted DataFrame is empty and data_editor shows nothing useful.
**Why it happens:** Pivot needs at least one row of data.
**How to avoid:** Pre-populate the grid DataFrame with today's date and all active items set to NaN/None. This shows the full grid structure even with no data.
**Warning signs:** Blank page on first visit to daily log.

### Pitfall 5: Date Index Display in data_editor
**What goes wrong:** Using date as DataFrame index causes it to render as an uneditable row label, which is desired, but `hide_index=True` would hide the dates.
**Why it happens:** data_editor treats index differently from data columns.
**How to avoid:** Keep `hide_index=False` (default) so dates show as row labels. Or use date as a regular disabled column.
**Warning signs:** Dates not visible or editable when they shouldn't be.

## Code Examples

### Database Schema Extension (db.py)
```python
# Add to init_db():
conn.execute("""
    CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_date TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        dosage_taken REAL,
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (item_id) REFERENCES items(id),
        UNIQUE(log_date, item_id)
    )
""")
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(log_date)
""")
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_logs_item ON daily_logs(item_id)
""")
```

### Upsert Log Entry (log_service.py)
```python
def upsert_log_entry(log_date, item_id, dosage_taken, notes=""):
    """Insert or update a daily log entry."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO daily_logs (log_date, item_id, dosage_taken, notes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(log_date, item_id)
            DO UPDATE SET
                dosage_taken = excluded.dosage_taken,
                notes = excluded.notes,
                updated_at = datetime('now')
        """, (log_date, item_id, dosage_taken, notes))
```

### Take All Fixed-Dose Items (log_service.py)
```python
def take_all_fixed_dose(log_date):
    """Insert default dosage for all fixed-dose active items not yet logged today."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO daily_logs (log_date, item_id, dosage_taken)
            SELECT ?, id, default_dosage
            FROM items
            WHERE is_active = 1
              AND default_dosage IS NOT NULL
              AND id NOT IN (
                  SELECT item_id FROM daily_logs WHERE log_date = ?
              )
        """, (log_date, log_date))
```

### Build Grid DataFrame (log_service.py)
```python
def build_log_grid(target_date, items):
    """Build a single-row DataFrame for target_date with all active items as columns."""
    import pandas as pd

    item_names = [i["name"] for i in items]

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT i.name, dl.dosage_taken
            FROM items i
            LEFT JOIN daily_logs dl ON dl.item_id = i.id AND dl.log_date = ?
            WHERE i.is_active = 1
            ORDER BY i.sort_order, i.name
        """, (target_date,)).fetchall()

    data = {r["name"]: r["dosage_taken"] for r in rows}
    df = pd.DataFrame([data], index=[target_date])
    return df
```

### Grid Page Skeleton (pages/daily_log.py)
```python
import streamlit as st
from datetime import date

st.title("Daily Log")

# Date navigation (LOG-06)
selected_date = st.date_input("Date", value=date.today())
log_date_str = selected_date.strftime("%Y-%m-%d")

# Build grid
items = get_active_items_ordered()  # ordered by sort_order (CAT-10)
grid_df = build_log_grid(log_date_str, items)

# Column config: NumberColumn for each item
col_config = {}
for item in items:
    col_config[item["name"]] = st.column_config.NumberColumn(
        item["name"],
        help=f"Default: {item['default_dosage']} {item['dosage_unit']}" if item["default_dosage"] else None,
        min_value=0.0,
        format="%.1f",
    )

# Take All button (LOG-04)
if st.button("Take All Defaults"):
    take_all_fixed_dose(log_date_str)
    st.rerun()

# Editable grid (LOG-01, LOG-02, LOG-03)
edited = st.data_editor(
    grid_df,
    key="log_grid",
    on_change=handle_grid_edit,
    column_config=col_config,
    hide_index=False,
    num_rows="fixed",
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| st.experimental_data_editor | st.data_editor | Streamlit 1.23 (2023) | Stable API, edited_rows format changed |
| Manual grid with st.columns | st.data_editor with column_config | Streamlit 1.28+ | Native cell editing, type validation, keyboard nav |
| column-per-item schema | Normalized row-per-entry | Phase 1 decision | Flexible schema, no ALTER TABLE on item changes |

**Deprecated/outdated:**
- `st.experimental_data_editor`: Removed. Use `st.data_editor`.
- `edited_cells` key format: Replaced by `edited_rows` dict format.

## Open Questions

1. **Single-click toggle UX for fixed-dose items (LOG-02)**
   - What we know: `NumberColumn` requires typing a value. `CheckboxColumn` gives boolean only, not a dosage number.
   - What's unclear: Whether a single click can both toggle and auto-fill a dosage in one action within `st.data_editor`.
   - Recommendation: Implement "Take All Defaults" button (LOG-04) as the primary single-click experience. Individual cells use NumberColumn for manual entry/override. If a cell is empty and user types any value, it logs. The "single click" requirement is best satisfied by the Take All button rather than per-cell checkbox behavior.

2. **Log entry notes UI (LOG-05)**
   - What we know: Grid cells can only hold one value. Notes need a separate interaction.
   - What's unclear: Best UX for per-cell notes within the grid metaphor.
   - Recommendation: Use an expander or popover below the grid. When user selects/clicks a cell, show a text input for that entry's note. Or add a "Notes" row/column. Simplest approach: a separate section below the grid showing notes for the selected date.

3. **Multi-date view vs single-date view**
   - What we know: Requirement says "dates as rows" (plural) and "navigate to any date."
   - What's unclear: Whether the default view shows a range of dates or just one date at a time.
   - Recommendation: Default to showing the current week (7 rows). Allow date range selection for browsing. Single-date editing for the "Take All" workflow.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (via uv dev dependency) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LOG-01 | Grid data built from logs + items | unit | `python -m pytest tests/test_log_service.py::test_build_log_grid -x` | No - Wave 0 |
| LOG-02 | Upsert with default dosage | unit | `python -m pytest tests/test_log_service.py::test_upsert_default_dosage -x` | No - Wave 0 |
| LOG-03 | Upsert with custom dosage override | unit | `python -m pytest tests/test_log_service.py::test_upsert_custom_dosage -x` | No - Wave 0 |
| LOG-04 | Take-all inserts defaults for unfilled items | unit | `python -m pytest tests/test_log_service.py::test_take_all_fixed_dose -x` | No - Wave 0 |
| LOG-05 | Log entry with notes | unit | `python -m pytest tests/test_log_service.py::test_log_entry_notes -x` | No - Wave 0 |
| LOG-06 | Query logs by date range | unit | `python -m pytest tests/test_log_service.py::test_get_logs_by_date -x` | No - Wave 0 |
| CAT-10 | Items ordered by sort_order | unit | `python -m pytest tests/test_log_service.py::test_items_sort_order -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_log_service.py` -- covers LOG-01 through LOG-06, CAT-10
- [ ] `tests/test_db.py` -- extend with daily_logs schema test
- [ ] Existing `conftest.py` test_db fixture is sufficient (creates isolated SQLite, calls init_db)

## Sources

### Primary (HIGH confidence)
- [st.data_editor API docs](https://docs.streamlit.io/develop/api-reference/data/st.data_editor) - full parameter list, return format, column_config
- [st.column_config API docs](https://docs.streamlit.io/develop/api-reference/data/st.column_config) - CheckboxColumn, NumberColumn, all column types
- [Streamlit Dataframes concepts](https://docs.streamlit.io/develop/concepts/design/dataframes) - edited_rows session state structure
- Installed Streamlit version: 1.55.0 (verified locally)

### Secondary (MEDIUM confidence)
- [Handling data_editor changes exactly once](https://discuss.streamlit.io/t/handling-st-data-editor-changes-exactly-once/45734) - edited_rows accumulation behavior, workarounds
- [data_editor on_change concurrency issue #11679](https://github.com/streamlit/streamlit/issues/11679) - known callback threading issues

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new deps, all verified installed
- Architecture: HIGH - normalized schema is locked decision, pivot pattern is standard pandas
- Pitfalls: HIGH - verified via official docs and community reports
- LOG-02 single-click UX: MEDIUM - data_editor may not support true single-click toggle with auto-fill; "Take All" button is the pragmatic solution

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (Streamlit API is stable at this point)
