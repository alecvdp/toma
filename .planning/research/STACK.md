# Technology Stack

**Project:** Toma -- Medication & Supplement Tracker
**Researched:** 2026-03-08
**Overall Confidence:** MEDIUM (versions based on training data up to early 2025; verify with `pip install` at project start)

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12+ | Runtime | Stable, well-supported, good typing support. Avoid 3.13 unless confirmed stable for all deps. | HIGH |
| Streamlit | ~1.40+ | Web UI framework | User already has two Streamlit apps and is comfortable with it. For a single-user personal tool, Streamlit is the right call -- fast to build, no frontend code, built-in `st.data_editor` covers the grid use case. | HIGH (choice), MEDIUM (version) |
| SQLite | Built-in | Database | Ships with Python via `sqlite3`. Zero config, single-file, portable, fast for single-user workloads. No reason to use anything else for this use case. | HIGH |

### Data Layer

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| sqlite3 (stdlib) | N/A | Database driver | Built into Python. No external dependency needed. Use directly -- an ORM is overkill for this project's ~3-4 tables. | HIGH |
| pandas | ~2.2+ | Data manipulation & grid display | Streamlit's `st.data_editor` operates on DataFrames. Pandas is the natural bridge between SQLite queries and Streamlit grid views. Already a Streamlit dependency. | HIGH (choice), MEDIUM (version) |

### Wikipedia Integration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| wikipedia-api | ~0.7+ | Fetch item descriptions | Clean Python wrapper around the MediaWiki API. Returns structured page summaries. Simpler and more reliable than the older `wikipedia` package (which has known issues with disambiguation). | MEDIUM |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| streamlit-extras | latest | Utility widgets | Only if a specific widget is needed (e.g., card layouts for catalog). Do not install preemptively. |
| pydantic | ~2.9+ | Data validation / settings | Use for validating dosage inputs and catalog entries. Optional but recommended for cleaner code. |

### Development Tools

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| uv | latest | Package manager | Faster than pip, handles venvs. Recommended for new Python projects. If unfamiliar, plain `pip` + `venv` is fine. | MEDIUM |
| ruff | latest | Linter + formatter | Replaces flake8, black, isort in one tool. Fast. | HIGH |

## Key Decision: Use Raw SQL, Not an ORM

For a personal app with 3-4 tables and straightforward queries, raw `sqlite3` with parameterized queries is the right approach.

**Why not SQLAlchemy / Peewee / SQLModel:**
- Adds dependency complexity for minimal benefit
- The query patterns are simple (INSERT/SELECT/UPDATE on a few tables)
- Pandas `read_sql` works directly with `sqlite3` connections
- Alembic migrations are overkill -- a simple `schema.sql` file with version checks is sufficient

**The schema is small enough to manage manually:**
- `items` table (catalog of medications/supplements)
- `daily_log` table (date + item_id + dosage entries)
- Possibly a `categories` table if tags grow complex

## Key Decision: Streamlit Over Alternatives

Streamlit is the correct choice here. Here is why the alternatives are worse for this specific project:

| Alternative | Why Not for This Project |
|-------------|--------------------------|
| **Flask/Django + React** | Massively over-engineered for a single-user personal tool. Weeks of work for what Streamlit does in days. |
| **NiceGUI** | Newer, smaller ecosystem. No clear advantage over Streamlit for data-grid use cases. |
| **Gradio** | Designed for ML demos, not CRUD apps. Poor fit. |
| **Dash (Plotly)** | Better for dashboards/analytics, worse for data entry. Callback model is more complex than Streamlit's rerun model for simple CRUD. |
| **Panel (HoloViz)** | Less community support, less polished for form-based UIs. |
| **Reflex** | Full-stack React under the hood -- more powerful but more complex. Overkill for a personal tracker. |

**The one caveat with Streamlit:** The rerun-on-interaction model can be surprising. Every widget interaction reruns the script top-to-bottom. This matters for:
- Database connections (use `st.connection` or cache them)
- Expensive operations (use `@st.cache_data` / `@st.cache_resource`)
- Form submissions (use `st.form` to batch inputs)

This is manageable for a small app, but worth knowing upfront.

## Key Decision: st.data_editor for the Grid View

Streamlit's `st.data_editor` is the core component for the daily log grid. It provides:
- Editable cells in a DataFrame-like grid
- Column type configuration (checkboxes, numbers, text, selectbox)
- Add/delete row support
- Returns a modified DataFrame that can be diffed against the original

This maps directly to the "dates as rows, items as columns, dosages as values" requirement from PROJECT.md. The default dosage feature can be implemented as pre-filled values in the grid.

**Limitations to plan around:**
- Dynamic columns (adding a new supplement should add a column) require reshaping the DataFrame before display
- Large date ranges may need pagination or a date-range filter (already in requirements)
- Checkbox vs. numeric entry per column will need column config (fixed-dose items get checkboxes, variable-dose items get number inputs)

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Framework | Streamlit | Flask + htmx | More work, more flexibility than needed |
| Database | sqlite3 (stdlib) | SQLAlchemy | ORM overhead not justified for 3-4 tables |
| Data manipulation | pandas | polars | Polars is faster but Streamlit's widgets expect pandas DataFrames |
| Package manager | uv | pip + venv | Either works; uv is faster but optional |
| Wikipedia | wikipedia-api | wikipedia (older pkg) | Older package has disambiguation bugs and is less maintained |
| Wikipedia | wikipedia-api | Direct requests to MediaWiki API | More code for the same result; library handles edge cases |

## Installation

```bash
# Create project with uv (or use pip + venv if preferred)
uv init toma
cd toma
uv add streamlit pandas wikipedia-api

# Dev dependencies
uv add --dev ruff

# Or with pip:
pip install streamlit pandas wikipedia-api
pip install ruff --dev
```

## Version Verification Note

**IMPORTANT:** The specific version numbers above are based on training data through early 2025. Before starting development, verify current versions:

```bash
# Check latest versions
pip index versions streamlit
pip index versions pandas
pip index versions wikipedia-api
```

Pin versions in `pyproject.toml` or `requirements.txt` after confirming.

## Sources

- Training data knowledge of Streamlit API (st.data_editor, st.cache_data, st.form, st.connection) -- MEDIUM confidence on exact current API
- Training data knowledge of Python sqlite3 stdlib -- HIGH confidence (stable API)
- Training data knowledge of pandas DataFrame integration with Streamlit -- HIGH confidence (core pattern)
- Training data knowledge of wikipedia-api package -- MEDIUM confidence (verify package is still maintained)
- Project context from .planning/PROJECT.md -- direct requirements
