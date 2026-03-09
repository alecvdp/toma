# Phase 1: Foundation and Catalog - Research

**Researched:** 2026-03-08
**Domain:** Streamlit + SQLite CRUD application, catalog management UI
**Confidence:** HIGH

## Summary

Phase 1 establishes the entire project foundation: Python project structure, SQLite database with schema, a service layer for catalog CRUD, and a Streamlit UI for managing medication/supplement items. This is a greenfield project -- no code exists yet.

The stack is locked: Python 3.12+, Streamlit 1.55 (current as of March 2026), raw sqlite3 (no ORM), pandas for data display. The architecture follows a three-tier pattern (pages -> services -> db) with strict boundary rules. The database uses a normalized row-per-entry schema, not column-per-item.

**Primary recommendation:** Build bottom-up -- db.py first (schema + connection management), then item_service.py (CRUD logic), then the catalog page (UI). Use `st.Page`/`st.navigation` for multipage routing (the modern Streamlit API), `st.form` for item creation/editing, and `st.data_editor` or card-based layout for the catalog view.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CAT-01 | User can add a new item with name, default dosage, dosage unit, and category | st.form for input batching; item_service.create_item(); items table schema |
| CAT-02 | User can edit an existing catalog item's details | st.form pre-populated with current values; item_service.update_item(); session_state for edit mode |
| CAT-03 | User can remove an item from the catalog | Soft-delete via is_active flag; item_service.deactivate_item(); confirmation dialog |
| CAT-04 | User can assign categories/tags to items | category TEXT column on items table; st.selectbox or st.text_input for category |
| CAT-05 | User can set a default dosage and unit for each item | default_dosage REAL + dosage_unit TEXT columns; separate fields in form |
| CAT-06 | User can view catalog items as cards with description, dosage, category, and personal notes | st.container + st.columns for card layout; iterate over items list |
| CAT-09 | User can search and filter catalog items by name or category | st.text_input for search + st.selectbox for category filter; SQL LIKE queries |
| CAT-11 | User can add personal notes to any catalog item | notes TEXT column on items table; st.text_area in edit form |
| DATA-01 | All data persists in a local SQLite database file | sqlite3 stdlib; toma.db single file; WAL mode; schema init on startup |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Stable, good typing support |
| Streamlit | 1.55.0 | Web UI framework | Current release (March 2026). User has prior Streamlit experience. Built-in widgets cover all Phase 1 needs. |
| sqlite3 | stdlib | Database driver | Ships with Python. No external dependency. Raw SQL with parameterized queries -- ORM is overkill for 3-4 tables. |
| pandas | 2.2+ | Data manipulation | Streamlit widgets operate on DataFrames. Already a Streamlit dependency. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.9+ | Input validation | Optional. Use for validating dosage inputs if needed. Not required for Phase 1 MVP. |
| ruff | latest | Linter + formatter | Development only. Replaces flake8 + black + isort. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sqlite3 (raw SQL) | SQLAlchemy | ORM overhead not justified for 3-4 tables with simple queries |
| pandas | polars | Polars is faster but Streamlit widgets expect pandas DataFrames |
| streamlit pages/ dir | st.Page + st.navigation | st.navigation is the modern API (preferred); pages/ dir is legacy |

**Installation:**
```bash
# With uv (recommended)
uv init toma && cd toma
uv add streamlit pandas
uv add --dev ruff pytest

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install streamlit pandas
pip install ruff pytest --dev
```

## Architecture Patterns

### Recommended Project Structure
```
toma/
  app.py                    # Entrypoint: st.set_page_config, st.navigation, init_db()
  db.py                     # Connection management, schema init, query helpers
  services/
    __init__.py
    item_service.py         # Catalog CRUD operations
  pages/
    catalog.py              # Item management UI (add/edit/view/search)
  models.py                 # Dataclasses for Item (optional but clean)
  toma.db                   # SQLite database (gitignored)
  pyproject.toml            # Dependencies
  tests/
    __init__.py
    test_db.py              # Schema and connection tests
    test_item_service.py    # Catalog CRUD tests
```

**Note:** The `pages/` directory here is for code organization only. With `st.navigation`, page routing is defined programmatically in `app.py`, not by filesystem convention.

### Pattern 1: Entrypoint with st.navigation
**What:** Modern Streamlit multipage routing using st.Page and st.navigation.
**When:** Always. This is the current recommended approach (replaces the old pages/ directory convention).
**Example:**
```python
# app.py
import streamlit as st
from db import init_db

st.set_page_config(page_title="Toma", page_icon=":pill:", layout="wide")

# Initialize database on first run
init_db()

# Define pages
catalog_page = st.Page("pages/catalog.py", title="Catalog", icon=":material/medication:")

# Navigation
pg = st.navigation([catalog_page])
pg.run()
```
**Source:** [Streamlit multipage docs](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation)

### Pattern 2: Service Layer Separation
**What:** Business logic in plain Python modules, never in Streamlit page scripts.
**When:** Every database operation goes through a service.
**Rules:**
1. Pages never import db.py directly -- always go through a service.
2. Services never import streamlit -- they return plain Python objects (dicts, dataclasses, lists).
3. db.py owns the schema -- all table creation and migration lives here.

```python
# services/item_service.py
from db import get_connection

def create_item(name: str, category: str, default_dosage: float | None,
                dosage_unit: str, notes: str = "") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO items (name, category, default_dosage, dosage_unit, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (name, category, default_dosage, dosage_unit, notes)
        )
        return cursor.lastrowid

def get_active_items() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE is_active = 1 ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]
```

### Pattern 3: Connection Management via Context Manager
**What:** SQLite connections scoped to operations, not held globally.
**When:** Every database operation.

```python
# db.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "toma.db"

@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
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
**Source:** [Python sqlite3 docs](https://docs.python.org/3/library/sqlite3.html)

### Pattern 4: st.form for CRUD Input
**What:** Batch user input with st.form to prevent reruns on every keystroke.
**When:** Adding or editing catalog items.

```python
# pages/catalog.py -- add item form
with st.form("add_item_form", clear_on_submit=True):
    name = st.text_input("Name")
    category = st.selectbox("Category", ["supplement", "prescription", "vitamin", "other"])
    col1, col2 = st.columns(2)
    with col1:
        default_dosage = st.number_input("Default Dosage", min_value=0.0, step=0.1)
    with col2:
        dosage_unit = st.selectbox("Unit", ["mg", "mcg", "IU", "mL", "capsule", "tablet"])
    notes = st.text_area("Notes", placeholder="Personal notes about this item...")

    if st.form_submit_button("Add Item"):
        if name.strip():
            item_service.create_item(name.strip(), category, default_dosage, dosage_unit, notes)
            st.success(f"Added {name}")
            st.rerun()
        else:
            st.error("Name is required")
```
**Source:** [Streamlit forms docs](https://docs.streamlit.io/develop/concepts/architecture/forms)

### Pattern 5: Card Layout for Catalog View
**What:** Display catalog items as cards using st.container and st.columns.
**When:** CAT-06 requires cards showing description, dosage, category, and notes.

```python
# pages/catalog.py -- card view
items = item_service.get_active_items()
for item in items:
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.subheader(item["name"])
            if item["description"]:
                st.caption(item["description"])
            if item["notes"]:
                st.text(item["notes"])
        with col2:
            if item["default_dosage"]:
                st.metric("Dosage", f"{item['default_dosage']} {item['dosage_unit']}")
            st.badge(item["category"])
        with col3:
            if st.button("Edit", key=f"edit_{item['id']}"):
                st.session_state.editing_item = item["id"]
            if st.button("Delete", key=f"del_{item['id']}"):
                st.session_state.deleting_item = item["id"]
```

### Anti-Patterns to Avoid
- **Database calls in widget callbacks:** Set a flag in session_state, handle the DB operation in the main page flow.
- **Global SQLite connection:** Streamlit runs multi-threaded. A shared connection causes "database is locked" errors. Use the context manager pattern.
- **Business logic in session_state:** Session state holds UI state only (which item is being edited, form values in progress). Compute derived values in services.
- **One giant page script:** Use multipage app with focused page scripts, even if Phase 1 only has one page.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form input batching | Custom rerun suppression | `st.form` + `st.form_submit_button` | Streamlit's built-in form prevents reruns on each widget change |
| Card/grid layout | Custom HTML/CSS components | `st.container(border=True)` + `st.columns` | Native Streamlit containers handle responsive layout |
| Search filtering | Custom JS search widget | `st.text_input` + SQL `LIKE` query | Simple and works; no need for full-text search at this scale |
| Date storage | Custom date formatting | ISO 8601 strings (`YYYY-MM-DD`) | SQLite sorts correctly, no parsing needed |
| Schema migration | Custom versioning system | `CREATE TABLE IF NOT EXISTS` + version check | Sufficient for 3-4 tables; Alembic is overkill |

## Common Pitfalls

### Pitfall 1: Streamlit Rerun Model Destroys In-Progress Edits
**What goes wrong:** Every widget interaction reruns the entire page script. Uncommitted form data disappears.
**Why it happens:** Streamlit's top-to-bottom rerun model. No partial page updates.
**How to avoid:** Use `st.form` to batch inputs. Minimize widgets outside forms on the same page. Save immediately on submit.
**Warning signs:** Users report "I typed something and it disappeared."

### Pitfall 2: Global SQLite Connection in Multi-Threaded Streamlit
**What goes wrong:** "database is locked" errors or data corruption from shared connection.
**Why it happens:** Streamlit server is multi-threaded. A module-level connection is shared across threads.
**How to avoid:** Context manager pattern -- each operation gets its own connection with `check_same_thread=False` not needed because connections are not shared.
**Warning signs:** Intermittent "database is locked" errors.

### Pitfall 3: Dosage as Structured Data Too Early
**What goes wrong:** Building unit conversion, numeric validation, and structured dosage parsing before the app works.
**Why it happens:** Over-engineering the data model. "500mg" feels like it should be parsed into (500, "mg").
**How to avoid:** Store default_dosage as REAL and dosage_unit as TEXT separately. Display as formatted string. No conversion logic needed for a tracker.
**Warning signs:** Code dealing with unit hierarchies, conversion factors, or dosage arithmetic.

### Pitfall 4: Not Using st.form for Item Creation
**What goes wrong:** Each text_input keystroke triggers a full page rerun, causing the grid/list below to flash and the app to feel sluggish.
**Why it happens:** Forgetting that Streamlit reruns on every widget change.
**How to avoid:** Wrap all item creation/edit inputs in `st.form`. Only submit triggers the rerun.
**Warning signs:** Page flickers during typing; database writes happening on every keystroke.

### Pitfall 5: Forgetting Soft Delete
**What goes wrong:** Hard-deleting catalog items breaks foreign key references from future daily_log entries (Phase 2).
**Why it happens:** Using SQL DELETE for item removal instead of setting is_active = 0.
**How to avoid:** Use `is_active` flag from day one. Filter active items in queries. This preserves historical log integrity.
**Warning signs:** Foreign key violations or orphaned log entries after deleting an item.

## Code Examples

### Database Schema for Phase 1
```sql
-- Source: Architecture research + requirements analysis
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT 'supplement',
    default_dosage REAL,
    dosage_unit TEXT DEFAULT 'mg',
    description TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_active ON items(is_active);
```

### Schema Initialization
```python
# db.py
def init_db():
    """Create tables if they don't exist. Called once at app startup."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'supplement',
                default_dosage REAL,
                dosage_unit TEXT DEFAULT 'mg',
                description TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
            CREATE INDEX IF NOT EXISTS idx_items_active ON items(is_active);
        """)
```

### Search and Filter Pattern
```python
# services/item_service.py
def search_items(query: str = "", category: str = "") -> list[dict]:
    """Search items by name (LIKE) and optionally filter by category."""
    sql = "SELECT * FROM items WHERE is_active = 1"
    params = []
    if query:
        sql += " AND name LIKE ?"
        params.append(f"%{query}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY name"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

def get_categories() -> list[str]:
    """Get distinct categories for filter dropdown."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM items WHERE is_active = 1 ORDER BY category"
        ).fetchall()
        return [row["category"] for row in rows]
```

### Edit Item with Session State
```python
# pages/catalog.py -- edit flow
if "editing_item" in st.session_state:
    item = item_service.get_item(st.session_state.editing_item)
    with st.form("edit_item_form"):
        name = st.text_input("Name", value=item["name"])
        category = st.selectbox("Category",
            ["supplement", "prescription", "vitamin", "other"],
            index=["supplement", "prescription", "vitamin", "other"].index(item["category"])
        )
        default_dosage = st.number_input("Default Dosage",
            value=float(item["default_dosage"] or 0), min_value=0.0, step=0.1)
        dosage_unit = st.selectbox("Unit",
            ["mg", "mcg", "IU", "mL", "capsule", "tablet"],
            index=["mg", "mcg", "IU", "mL", "capsule", "tablet"].index(item["dosage_unit"] or "mg")
        )
        notes = st.text_area("Notes", value=item["notes"] or "")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save"):
                item_service.update_item(item["id"], name=name, category=category,
                    default_dosage=default_dosage, dosage_unit=dosage_unit, notes=notes)
                del st.session_state.editing_item
                st.rerun()
        with col2:
            if st.form_submit_button("Cancel"):
                del st.session_state.editing_item
                st.rerun()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pages/` directory convention | `st.Page` + `st.navigation` | Streamlit ~1.36 (2024) | Programmatic page routing, more flexibility, page visibility control |
| `st.experimental_data_editor` | `st.data_editor` | Streamlit 1.23 (2023) | Stable API, column_config, num_rows options |
| `st.cache` (deprecated) | `@st.cache_data` / `@st.cache_resource` | Streamlit 1.18 (2023) | Separate caching for data vs. resources (connections) |
| Manual query params | Widget-bound query params | Streamlit 1.55 (2026) | Widgets can sync state with URL query parameters |

**Deprecated/outdated:**
- `st.experimental_data_editor`: Use `st.data_editor` instead
- `st.cache`: Use `@st.cache_data` or `@st.cache_resource`
- `pages/` directory auto-routing: Still works but `st.navigation` is preferred

## Open Questions

1. **Dosage unit as free-text or enum?**
   - What we know: Requirements say "mg, IU, capsules, etc." Common units are finite.
   - What's unclear: Whether the user wants to add custom units.
   - Recommendation: Use a selectbox with common units plus an "other" option with free-text fallback. Start with enum, add free-text if requested.

2. **Category as free-text or predefined list?**
   - What we know: Requirements mention "supplement, prescription, vitamin, etc."
   - What's unclear: Whether categories should be user-defined or fixed.
   - Recommendation: Start with a predefined list (supplement, prescription, vitamin, other). Allow adding new categories in a later iteration if needed.

3. **Delete confirmation UX**
   - What we know: Soft delete is the right approach for data integrity.
   - What's unclear: Best Streamlit pattern for confirmation dialogs.
   - Recommendation: Use `st.dialog` (available in Streamlit 1.55) or a two-step button pattern (click "Delete" -> shows "Confirm?" button).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (latest) |
| Config file | none -- Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAT-01 | Create item with name, dosage, unit, category | unit | `pytest tests/test_item_service.py::test_create_item -x` | Wave 0 |
| CAT-02 | Edit existing item details | unit | `pytest tests/test_item_service.py::test_update_item -x` | Wave 0 |
| CAT-03 | Remove item from catalog (soft delete) | unit | `pytest tests/test_item_service.py::test_deactivate_item -x` | Wave 0 |
| CAT-04 | Assign categories to items | unit | `pytest tests/test_item_service.py::test_item_category -x` | Wave 0 |
| CAT-05 | Set default dosage and unit | unit | `pytest tests/test_item_service.py::test_default_dosage -x` | Wave 0 |
| CAT-06 | View items as cards | manual-only | N/A -- UI layout verification | N/A |
| CAT-09 | Search and filter by name or category | unit | `pytest tests/test_item_service.py::test_search_items -x` | Wave 0 |
| CAT-11 | Add personal notes to item | unit | `pytest tests/test_item_service.py::test_item_notes -x` | Wave 0 |
| DATA-01 | Data persists in SQLite file | unit | `pytest tests/test_db.py::test_persistence -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` -- package init
- [ ] `tests/test_db.py` -- schema creation, connection management, persistence
- [ ] `tests/test_item_service.py` -- all CRUD operations, search, filter, soft delete
- [ ] `tests/conftest.py` -- shared fixture for in-memory SQLite database
- [ ] `pyproject.toml` -- pytest configuration section
- [ ] Framework install: `uv add --dev pytest` or `pip install pytest`

## Sources

### Primary (HIGH confidence)
- [Streamlit st.data_editor docs](https://docs.streamlit.io/develop/api-reference/data/st.data_editor) -- API signature, parameters, return types
- [Streamlit multipage apps docs](https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation) -- st.Page + st.navigation pattern
- [Streamlit 2026 release notes](https://docs.streamlit.io/develop/quick-reference/release-notes/2026) -- confirmed v1.55.0 as latest
- [Streamlit forms docs](https://docs.streamlit.io/develop/concepts/architecture/forms) -- st.form best practices
- [Python sqlite3 docs](https://docs.python.org/3/library/sqlite3.html) -- connection management, context managers
- Project research files (.planning/research/STACK.md, ARCHITECTURE.md, PITFALLS.md) -- stack decisions and patterns

### Secondary (MEDIUM confidence)
- [Streamlit st.connection docs](https://docs.streamlit.io/develop/api-reference/connections/st.connection) -- SQLConnection pattern (not used -- raw sqlite3 preferred per stack decision)

### Tertiary (LOW confidence)
- None -- all findings verified against official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions verified against current Streamlit release notes (1.55.0)
- Architecture: HIGH - patterns come from project's own architecture research + verified Streamlit docs
- Pitfalls: HIGH - well-established Streamlit + SQLite interaction patterns
- Validation: MEDIUM - pytest is standard but no existing test infrastructure to verify against

**Research date:** 2026-03-08
**Valid until:** 2026-04-07 (30 days -- stable stack, no fast-moving dependencies)
