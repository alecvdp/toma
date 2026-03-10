# Phase 3: Enhancements - Research

**Researched:** 2026-03-09
**Domain:** Wikipedia API integration, date range history, CSV/Excel import/export
**Confidence:** HIGH

## Summary

Phase 3 adds four distinct features to the tracker: Wikipedia description auto-fetch (CAT-07, CAT-08), date range history browsing (DATA-02), CSV export (DATA-03), and CSV/Excel import (DATA-04). Each feature is self-contained and touches different parts of the stack.

The Wikipedia integration uses the free REST API at `en.wikipedia.org/api/rest_v1/page/summary/{title}` -- no API key or third-party library needed, just `urllib` from the standard library. The key pitfall is title case sensitivity; a search-then-fetch two-step pattern resolves this. History browsing uses Streamlit's native `st.date_input` with a tuple value for range selection. Export uses `pandas.DataFrame.to_csv()` with `st.download_button`. Import uses `st.file_uploader` with `pandas.read_csv()` / `pandas.read_excel()`, the latter requiring `openpyxl` as a new dependency.

**Primary recommendation:** Use stdlib `urllib` for Wikipedia API (zero new deps for that feature), add `openpyxl` as the only new dependency (for Excel import), and keep each feature as a separate service function + UI integration.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CAT-07 | Auto-fetch 1-3 sentence description from Wikipedia when adding an item | Wikipedia REST API `extract` field; opensearch for title resolution |
| CAT-08 | Edit auto-fetched descriptions | Existing `description` field on items table + `update_item` service already supports this |
| DATA-02 | Browse log history by selecting a date range | `st.date_input` with tuple value for range; new `get_logs_by_date_range` service function |
| DATA-03 | Export log data to CSV | `pandas.to_csv()` + `st.download_button` |
| DATA-04 | Import data from CSV or Excel | `st.file_uploader` + `pandas.read_csv` / `pandas.read_excel` + `openpyxl` |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | >=1.55 | UI framework | Already in use |
| pandas | >=2.2 | DataFrame operations | Already in use for grid |
| urllib (stdlib) | 3.13 | HTTP requests to Wikipedia API | Zero-dependency; simple GET requests only |

### New Dependency
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openpyxl | >=3.1 | Excel file reading engine | Required by `pandas.read_excel()` for `.xlsx` files |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| urllib | requests | requests is a transitive dep of streamlit (v2.32.5 available), but urllib avoids implicit dependency on streamlit internals |
| openpyxl | xlrd | xlrd only handles old `.xls` format; openpyxl handles modern `.xlsx` |
| Wikipedia REST API | `wikipedia` or `wikipediaapi` PyPI packages | Extra dependency for a single HTTP call; REST API is simpler |

**Installation:**
```bash
uv add openpyxl
```

## Architecture Patterns

### Recommended Project Structure
```
services/
  item_service.py       # Add fetch_wikipedia_description()
  log_service.py        # Add get_logs_by_date_range(), export_logs_csv()
  import_service.py     # NEW: CSV/Excel import logic (validation, mapping, upserts)
pages/
  catalog.py            # Add "Fetch Description" button to add/edit forms
  daily_log.py          # Add date range picker + history table
  import_export.py      # NEW page: import/export UI (or add to daily_log.py)
```

### Pattern 1: Wikipedia Two-Step Fetch (Search then Summary)
**What:** Use opensearch API to resolve the correct Wikipedia title, then fetch the summary extract.
**When to use:** Always -- item names like "Fish Oil" may not match Wikipedia's case-sensitive title format ("Fish_oil").
**Example:**
```python
# Source: verified against en.wikipedia.org API (tested 2026-03-09)
import json
import urllib.request
import urllib.parse

def fetch_wikipedia_description(search_term: str) -> str | None:
    """Fetch a 1-3 sentence description from Wikipedia.

    Returns the extract text or None if not found.
    """
    # Step 1: Search for the correct title
    encoded = urllib.parse.quote(search_term)
    search_url = (
        f"https://en.wikipedia.org/w/api.php"
        f"?action=opensearch&search={encoded}&limit=1&format=json"
    )
    req = urllib.request.Request(search_url, headers={"User-Agent": "Toma/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())

    if not data[1]:  # no search results
        return None

    # Step 2: Fetch summary using the resolved title
    title = data[1][0].replace(" ", "_")
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    req = urllib.request.Request(summary_url, headers={"User-Agent": "Toma/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        summary = json.loads(resp.read())

    extract = summary.get("extract", "")
    if not extract:
        return None

    # Truncate to ~3 sentences
    sentences = extract.split(". ")
    return ". ".join(sentences[:3]) + ("." if len(sentences) > 3 else "")
```

### Pattern 2: Date Range History Query
**What:** Query daily_logs with a date range and pivot into a multi-row grid.
**When to use:** DATA-02 history browsing.
**Example:**
```python
# Source: follows existing build_log_grid pattern in log_service.py
def get_logs_by_date_range(start_date: str, end_date: str) -> pd.DataFrame:
    """Build a multi-row grid: dates as rows, items as columns."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT i.name AS item_name, dl.log_date, dl.dosage_taken
               FROM items i
               LEFT JOIN daily_logs dl ON dl.item_id = i.id
                   AND dl.log_date BETWEEN ? AND ?
               WHERE i.is_active = 1
               ORDER BY i.sort_order, i.name""",
            (start_date, end_date),
        ).fetchall()
    # Pivot: rows=dates, columns=item_names
    df = pd.DataFrame([dict(r) for r in rows])
    if df.empty:
        return pd.DataFrame()
    return df.pivot_table(
        index="log_date", columns="item_name",
        values="dosage_taken", aggfunc="first"
    ).sort_index()
```

### Pattern 3: CSV Export with st.download_button
**What:** Convert DataFrame to CSV bytes and serve via download button.
**When to use:** DATA-03.
**Example:**
```python
# Source: Streamlit docs (st.download_button)
csv_data = df.to_csv().encode("utf-8")
st.download_button(
    label="Export to CSV",
    data=csv_data,
    file_name=f"toma_log_{start_date}_to_{end_date}.csv",
    mime="text/csv",
)
```

### Pattern 4: File Import with Validation
**What:** Upload CSV/Excel, validate columns, upsert into database.
**When to use:** DATA-04.
**Example:**
```python
# Source: Streamlit docs (st.file_uploader)
uploaded = st.file_uploader(
    "Import data",
    type=["csv", "xlsx"],
)
if uploaded is not None:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded, engine="openpyxl")
    # Validate and process...
```

### Anti-Patterns to Avoid
- **Blocking the UI on Wikipedia fetch:** Network calls freeze Streamlit. Use `st.spinner()` to show progress, and always set a timeout (5s max).
- **Trusting uploaded data blindly:** CSV/Excel imports must validate column names, data types, and handle duplicates gracefully.
- **Building a multi-row grid from scratch:** Reuse the existing `build_log_grid` query pattern with date range WHERE clause instead of writing a new join.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Wikipedia description fetch | Custom web scraper | REST API (`/api/rest_v1/page/summary/`) | Structured JSON, no HTML parsing, no rate limit issues |
| Wikipedia title resolution | Manual title formatting | OpenSearch API (`/w/api.php?action=opensearch`) | Handles case sensitivity, redirects, disambiguation |
| Excel file parsing | Custom `.xlsx` reader | `pandas.read_excel(engine="openpyxl")` | xlsx is a ZIP of XML files; openpyxl handles all edge cases |
| CSV generation | Manual string concatenation | `pandas.DataFrame.to_csv()` | Handles quoting, escaping, unicode correctly |
| Date range picker | Custom two-input widget | `st.date_input(value=(start, end))` | Native Streamlit widget with calendar UI |

**Key insight:** Every feature in this phase has a well-supported standard approach. The complexity is in validation and UX, not in the underlying technology.

## Common Pitfalls

### Pitfall 1: Wikipedia Title Case Sensitivity
**What goes wrong:** `Fish_Oil` returns HTTP error; correct title is `Fish_oil`.
**Why it happens:** Wikipedia REST API requires exact title casing.
**How to avoid:** Always use the opensearch API first to resolve the correct title, then fetch the summary.
**Warning signs:** 404 or "Internal error" responses from the summary endpoint.

### Pitfall 2: Wikipedia API Rate Limiting
**What goes wrong:** Requests get throttled or blocked.
**Why it happens:** Wikipedia requires a descriptive User-Agent header; generic or missing agents are blocked.
**How to avoid:** Always include `User-Agent: Toma/1.0 (personal medication tracker)` header. Add a timeout of 5 seconds.
**Warning signs:** 403 responses or connection timeouts.

### Pitfall 3: st.date_input Range Returns Variable Tuple Length
**What goes wrong:** Code assumes 2 dates but gets 0 or 1 during user interaction.
**Why it happens:** `st.date_input` with range returns a tuple of 0-2 dates. While the user is selecting the end date, only 1 date is in the tuple.
**How to avoid:** Always check `len(date_range) == 2` before using the values. Show a prompt if incomplete.
**Warning signs:** `IndexError` or `ValueError` when destructuring the tuple.

### Pitfall 4: Import Column Mapping Ambiguity
**What goes wrong:** Imported CSV has columns like "Vitamin D" but the item doesn't exist in the catalog, or column names don't match exactly.
**Why it happens:** External data doesn't conform to the app's item naming.
**How to avoid:** Show a preview of uploaded data, validate item names against existing catalog, and let the user map/skip unrecognized columns.
**Warning signs:** Silent data loss when unmatched columns are dropped.

### Pitfall 5: Import Overwrites Existing Logs
**What goes wrong:** Importing data silently replaces existing log entries.
**Why it happens:** The `upsert_log_entry` ON CONFLICT pattern updates existing rows.
**How to avoid:** Show a summary of what will change (new entries vs. overwrites) before committing. Consider a "skip existing" vs. "overwrite" option.
**Warning signs:** User loses manually-entered data after import.

## Code Examples

### Wikipedia API Response Structure (verified 2026-03-09)
```json
{
  "type": "standard",
  "title": "Magnesium supplement",
  "extract": "Magnesium salts are available as a medication in a number of formulations...",
  "extract_html": "<p>Magnesium salts are available...</p>",
  "description": "Pharmaceutical preparation",
  "content_urls": { "desktop": { "page": "https://..." } }
}
```
Key fields: `extract` (plain text summary), `description` (short Wikidata description), `type` ("standard" for real articles).

### st.date_input Range Mode (verified from Streamlit docs)
```python
from datetime import date, timedelta

date_range = st.date_input(
    "Select date range",
    value=(date.today() - timedelta(days=7), date.today()),
    max_value=date.today(),
)
if len(date_range) == 2:
    start, end = date_range
    # Use start and end dates
```

### Import Validation Pattern
```python
REQUIRED_COLUMNS = {"date"}  # minimum required
# Remaining columns should match item names

def validate_import(df: pd.DataFrame, active_items: list[dict]) -> tuple[bool, list[str]]:
    """Validate imported DataFrame against catalog items.

    Returns (is_valid, list_of_warnings).
    """
    warnings = []
    item_names = {item["name"] for item in active_items}

    if "date" not in df.columns:
        return False, ["Missing required 'date' column"]

    data_columns = set(df.columns) - {"date"}
    unmatched = data_columns - item_names
    if unmatched:
        warnings.append(f"Unrecognized items (will be skipped): {', '.join(unmatched)}")

    matched = data_columns & item_names
    if not matched:
        return False, ["No columns match existing catalog items"]

    return True, warnings
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `wikipedia` PyPI package | Wikipedia REST API direct | REST API stable since 2017 | No third-party dependency needed |
| Custom date picker widgets | `st.date_input(value=tuple)` | Streamlit 1.0+ | Native range support, no custom component |
| `xlrd` for Excel files | `openpyxl` via pandas | xlrd dropped xlsx support in 2.0 (2020) | Must use openpyxl for modern Excel files |

**Deprecated/outdated:**
- `xlrd>=2.0`: Only supports old `.xls` format, not `.xlsx`
- `wikipedia` PyPI package: Last release 2014, uses old MediaWiki API, has disambiguation issues

## Open Questions

1. **Import format: grid-style or long-form?**
   - What we know: The daily_log page shows a grid (dates as rows, items as columns), which is natural for export. Import should accept the same format.
   - What's unclear: Should we also support a long-form format (date, item_name, dosage per row)?
   - Recommendation: Support grid format (matching export) as the primary import format. This is what users would get from their existing spreadsheets.

2. **Should Wikipedia fetch happen in add form or as a separate action?**
   - What we know: CAT-07 says "when adding or editing an item"
   - What's unclear: Inline in the form, or a separate button?
   - Recommendation: A "Fetch Description" button next to the description field in both add and edit forms. This avoids auto-fetching on every keystroke and gives user control.

3. **History page: separate page or extend daily log?**
   - What we know: Daily log currently shows one date. History needs a range.
   - What's unclear: Whether to add range mode to existing page or create a new page.
   - Recommendation: Add a "History" section or mode to the existing daily log page, toggled by a date range widget. Avoids navigation complexity.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed in dev deps) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAT-07 | Wikipedia fetch returns 1-3 sentence description | unit | `pytest tests/test_wikipedia.py -x` | No -- Wave 0 |
| CAT-07 | Fetch handles missing/ambiguous items gracefully | unit | `pytest tests/test_wikipedia.py -x` | No -- Wave 0 |
| CAT-08 | Description field editable after auto-fetch | unit | `pytest tests/test_item_service.py::test_update_item -x` | Yes (existing) |
| DATA-02 | Date range query returns correct multi-day grid | unit | `pytest tests/test_log_service.py::test_get_logs_by_date_range -x` | No -- Wave 0 |
| DATA-03 | Export produces valid CSV with correct headers | unit | `pytest tests/test_export.py -x` | No -- Wave 0 |
| DATA-04 | Import validates columns against catalog | unit | `pytest tests/test_import.py::test_validate_import -x` | No -- Wave 0 |
| DATA-04 | Import upserts log entries correctly | unit | `pytest tests/test_import.py::test_import_logs -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_wikipedia.py` -- covers CAT-07 (mock urllib to avoid network calls)
- [ ] `tests/test_log_service.py::test_get_logs_by_date_range` -- covers DATA-02 (add to existing file)
- [ ] `tests/test_export.py` -- covers DATA-03
- [ ] `tests/test_import.py` -- covers DATA-04 (validation + upsert)

## Sources

### Primary (HIGH confidence)
- Wikipedia REST API -- tested live against `en.wikipedia.org/api/rest_v1/page/summary/` and `en.wikipedia.org/w/api.php?action=opensearch` (2026-03-09)
- Streamlit docs (st.date_input) -- verified range tuple behavior
- Streamlit docs (st.download_button) -- verified CSV download pattern
- Streamlit docs (st.file_uploader) -- verified type parameter and return type
- Existing codebase -- `db.py`, `services/`, `pages/`, `tests/` fully reviewed

### Secondary (MEDIUM confidence)
- pandas.read_excel documentation -- openpyxl engine requirement for xlsx
- openpyxl PyPI -- version >=3.1 for current pandas compatibility

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified all APIs against live endpoints and official docs
- Architecture: HIGH - patterns follow existing codebase conventions exactly
- Pitfalls: HIGH - Wikipedia API pitfalls verified through actual HTTP testing (case sensitivity, User-Agent)

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable APIs, unlikely to change)
