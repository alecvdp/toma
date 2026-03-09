# Domain Pitfalls

**Domain:** Medication & Supplement Tracking (Personal Web App)
**Stack:** Streamlit + SQLite
**Researched:** 2026-03-08
**Overall Confidence:** MEDIUM (based on training data; web verification unavailable)

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or fundamental UX failure.

### Pitfall 1: Streamlit Rerun Model Destroys In-Progress Edits

**What goes wrong:** Streamlit reruns the entire script on every widget interaction. If a user is editing a dosage in the grid and clicks something else (a filter, a date picker, a sidebar toggle), the entire page re-executes and the uncommitted edit is lost. This is the single most frustrating issue for data-entry-heavy Streamlit apps.

**Why it happens:** Streamlit's execution model is top-to-bottom rerun on every interaction. There is no partial page update. Every widget change triggers a full rerun. If the grid/form state is not explicitly persisted in `st.session_state` before the rerun, it vanishes.

**Consequences:**
- Users lose partially entered dosages
- Grid scrolls back to top on every interaction
- Feels broken for daily data entry workflows

**Warning signs:**
- Users reporting "I typed something and it disappeared"
- Testing reveals that clicking any widget outside the grid resets grid content
- Scroll position jumps to top after interactions

**Prevention:**
- Use `st.data_editor` with a `key` parameter to bind to session state
- Minimize widgets on the same page as the editable grid -- fewer reruns
- Save edits to the database immediately on change (use `on_change` callbacks or detect diffs in `st.data_editor` return value vs. input)
- Consider a "save" button pattern rather than relying on auto-persist
- Structure pages so the daily log grid is isolated from other controls

**Phase to address:** Phase 1 (Daily Log Grid). Must be solved from day one or the core feature feels broken.

**Confidence:** HIGH -- well-documented Streamlit behavior.

---

### Pitfall 2: st.data_editor Is Not a Spreadsheet

**What goes wrong:** Developers expect `st.data_editor` to behave like Excel or Google Sheets -- supporting arbitrary cell formulas, rich keyboard navigation, copy-paste across ranges, undo/redo, and smooth scroll on large datasets. It does not. It is a basic editable DataFrame widget with significant limitations.

**Why it happens:** The project explicitly wants a "grid/spreadsheet daily log view (dates as rows, items as columns)" which maps to a spreadsheet mental model. `st.data_editor` looks like a spreadsheet but behaves more like a simple HTML table with editable cells.

**Consequences:**
- Grid becomes sluggish with many columns (20+ supplements) or rows (months of history)
- No native "check/uncheck all" for a row
- Column reordering or hiding is limited
- Copy-paste behavior is inconsistent across browsers
- No keyboard shortcut for "fill down" or "fill right"

**Warning signs:**
- Performance degrades as the catalog grows
- Users want features that require custom JavaScript (which Streamlit makes hard)
- Frustration with data entry speed compared to the Excel workflow being replaced

**Prevention:**
- Limit the visible date range (show 7-14 days at a time, not months)
- Limit visible columns (allow filtering by category/tag)
- For fixed-dose items, use boolean checkboxes in the grid (True/False columns) rather than numeric entry
- For variable-dose items, use numeric columns with the default dose pre-filled
- Test with the actual number of items the user tracks (sounds like potentially 15-30+)
- If `st.data_editor` proves too limiting, have a fallback plan: per-item entry with `st.checkbox`/`st.number_input` in a more traditional form layout

**Phase to address:** Phase 1 (Daily Log Grid). Validate early that the grid approach works at the user's actual scale.

**Confidence:** HIGH -- these are well-known `st.data_editor` constraints.

---

### Pitfall 3: SQLite Schema That Cannot Evolve

**What goes wrong:** Designing the schema with items as columns (mirroring the Excel layout) instead of a normalized row-per-entry design. When the user adds a new supplement, a column-per-item schema requires an ALTER TABLE, which is fragile and does not scale.

**Why it happens:** The Excel mental model (columns = items, rows = dates) is the user's current workflow, so developers mirror it directly in the database.

**Consequences:**
- Adding/removing items requires schema migration
- SQLite ALTER TABLE is limited (cannot drop columns in older SQLite versions)
- Queries become harder as column names are dynamic
- Backup/restore becomes version-dependent

**Warning signs:**
- Code that dynamically generates ALTER TABLE statements
- Column names in the database that are supplement names (e.g., `vitamin_d`, `magnesium`)
- Difficulty querying "what did I take on date X?" because it requires checking N columns

**Prevention:**
- Use a normalized schema from the start:
  - `items` table: id, name, description, default_dose, category, notes
  - `log_entries` table: id, item_id (FK), date, dose_taken (nullable -- null means not taken)
  - The grid view is constructed via a PIVOT query or Python DataFrame pivot
- The grid is a *view concern*, not a *storage concern*
- This makes adding/removing items trivial (just insert/delete from `items`)

**Phase to address:** Phase 1 (Database Design). Getting this wrong means a rewrite.

**Confidence:** HIGH -- standard database normalization wisdom.

---

### Pitfall 4: SQLite Connection Handling in Streamlit

**What goes wrong:** Opening a new SQLite connection on every Streamlit rerun (which happens on every interaction) is wasteful. But caching the connection with `st.cache_resource` can cause issues if the connection object is shared across threads or if the database file is moved/deleted.

**Why it happens:** Streamlit's rerun model means naive code opens a connection at the top of the script, which runs hundreds of times per session. Developers then try to cache it but hit threading or staleness issues.

**Consequences:**
- "database is locked" errors if multiple connections are opened
- Stale data if queries are cached too aggressively with `st.cache_data`
- Connection objects that become invalid after the SQLite file is moved

**Warning signs:**
- Intermittent "database is locked" errors
- Data not updating after writes (stale cache)
- Errors after moving or renaming the .db file

**Prevention:**
- Use `st.cache_resource` for the connection, but set `check_same_thread=False` on the SQLite connection
- Use `st.cache_data` with a short TTL (or no TTL) for read queries that should reflect recent writes
- Clear relevant caches after writes: `st.cache_data.clear()` or use cache keys
- Consider a simple connection helper function that returns the same connection per session
- For a single-user local app, connection management is simpler -- but still needs to handle Streamlit's threading model

**Phase to address:** Phase 1 (Database Layer). Foundation that everything else depends on.

**Confidence:** HIGH -- well-known Streamlit + SQLite interaction pattern.

---

## Moderate Pitfalls

### Pitfall 5: Wikipedia API Fetching That Blocks the UI

**What goes wrong:** Fetching Wikipedia descriptions synchronously during page render blocks the entire Streamlit app. If Wikipedia is slow or down, the app hangs.

**Why it happens:** Streamlit runs top-to-bottom. If a Wikipedia API call is in the render path, the page waits for it.

**Warning signs:**
- App takes 3-10 seconds to load when adding a new item
- App hangs entirely when Wikipedia is unreachable
- Timeout errors appearing in the Streamlit UI

**Prevention:**
- Fetch Wikipedia descriptions only once, at item creation time, and store in the database
- Use `st.cache_data` with a long TTL for Wikipedia lookups
- Add a timeout (2-3 seconds) to the Wikipedia API call with a graceful fallback ("Description not found -- add manually")
- Make the fetch async or triggered by a button ("Fetch description") rather than automatic
- Never fetch descriptions during the daily log page render

**Phase to address:** Phase 2 (Catalog/Item Management). Not needed for the daily log but important when building the item catalog.

**Confidence:** HIGH -- standard async/network pitfall.

---

### Pitfall 6: Confusing "Not Taken" vs "Not Logged"

**What goes wrong:** The data model cannot distinguish between "I did not take this today" and "I have not logged today yet." Both show as empty/null. This makes historical views unreliable -- was that blank cell a missed dose or an unlogged day?

**Why it happens:** Simple boolean or nullable dose fields treat absence of data as "not taken." But the user might just not have logged yet.

**Consequences:**
- Historical views show gaps that might be incomplete logging, not missed doses
- Adherence statistics are unreliable
- User loses trust in the data

**Warning signs:**
- User asks "did I take X on Tuesday?" and the app shows blank but the user is not sure if they logged
- Statistics showing low adherence rates that do not match reality

**Prevention:**
- Add a "day completed" or "day logged" flag to mark when the user has finished logging for a date
- Or: use a three-state model per entry: taken (with dose), explicitly skipped, not yet logged
- Display unlogged days differently from days with no items taken (e.g., gray vs. red)
- For the MVP, this can be simple: a "Mark day complete" button that timestamps the log

**Phase to address:** Phase 1 or 2. Even a simple "logged" flag prevents data ambiguity from the start.

**Confidence:** MEDIUM -- domain-specific insight from medication tracking UX patterns.

---

### Pitfall 7: Date and Timezone Handling

**What goes wrong:** Storing dates as strings (e.g., "2026-03-08") or using Python's `datetime.now()` without considering that "today" might change during a late-night logging session. A user logging at 11:55 PM might have their entry recorded for the wrong date if the system clock ticks past midnight.

**Why it happens:** Date handling seems trivial for a single-user local app but edge cases creep in.

**Consequences:**
- Entries recorded on the wrong date near midnight
- Date comparison bugs when mixing date formats
- Confusing behavior if the user's system timezone changes

**Warning signs:**
- Entries appearing on the wrong day in the grid
- Date filter queries returning unexpected results
- SQLite date comparisons not working as expected

**Prevention:**
- Store dates as ISO 8601 strings (`YYYY-MM-DD`) in SQLite -- this sorts correctly and is unambiguous
- Let the user select the log date explicitly (default to today but allow changing)
- Use `datetime.date.today()` not `datetime.now()` for date-only operations
- Consider a "logging for yesterday" shortcut since late-night logging is common

**Phase to address:** Phase 1 (Database + Daily Log). Get date handling right from the first table creation.

**Confidence:** HIGH -- universal date handling wisdom.

---

### Pitfall 8: No Data Backup or Export Strategy

**What goes wrong:** SQLite is a single file, which is great for portability. But without a backup strategy, one accidental deletion or corruption event loses all tracking history.

**Why it happens:** "It is just a local file" thinking leads to no backup plan. SQLite files can corrupt if the process is killed during a write (rare but possible).

**Consequences:**
- Months of medication tracking history lost
- No way to recover from accidental item deletion or bad edits
- No way to export data for a doctor visit or switching tools

**Warning signs:**
- No backup copies of the .db file exist
- No "undo" for deletions
- User asks "can I export to CSV?" and the answer is no

**Prevention:**
- Add a CSV export function (easy with pandas + Streamlit download button)
- Store the database in a folder that is backed up (e.g., synced to cloud storage)
- Consider an "export all data" page as an early feature
- Add soft-delete for items (mark inactive rather than DELETE)
- Use SQLite's WAL mode for better crash resilience

**Phase to address:** Phase 2 or 3. Not MVP-critical but should come before the user has months of data.

**Confidence:** HIGH -- standard data management practice.

---

## Minor Pitfalls

### Pitfall 9: Over-Engineering the Catalog

**What goes wrong:** Building elaborate category hierarchies, tagging systems, dosage unit conversions, and rich metadata fields when the user just needs a name, a default dose, and a short description.

**Prevention:**
- Start with: name, description (text), default_dose (text, not numeric -- "500mg" is fine), category (single string), notes (text)
- Do not build unit conversion, dosage validation, or nested categories in v1
- Let the user's actual needs drive what metadata matters

**Phase to address:** Phase 2 (Catalog). Keep it minimal.

**Confidence:** HIGH -- YAGNI principle.

---

### Pitfall 10: Streamlit Page Navigation State Loss

**What goes wrong:** When using `st.navigation` or multi-page Streamlit apps, navigating away from the daily log and coming back resets the page state (selected date, scroll position, unsaved edits).

**Prevention:**
- Persist the current date selection in `st.session_state`
- Save edits to the database before allowing page navigation
- Minimize the number of pages -- for a simple tracker, 2-3 pages max (Daily Log, Catalog, History/Settings)

**Phase to address:** Phase 1-2. Plan the page structure early.

**Confidence:** MEDIUM -- depends on Streamlit version and navigation approach used.

---

### Pitfall 11: Pivot Table Performance at Scale

**What goes wrong:** Building the daily log grid by pivoting the normalized `log_entries` table in Python/pandas. With many items and a large date range, the pivot operation and the resulting DataFrame become slow.

**Prevention:**
- Always filter to a small date window before pivoting (7-14 days)
- Cache the pivoted DataFrame with `st.cache_data` keyed on the date range
- For history views, use summary/aggregate queries rather than full pivots
- Index the `log_entries` table on `(date, item_id)` for fast lookups

**Phase to address:** Phase 1 (Daily Log) and Phase 3 (History Views).

**Confidence:** MEDIUM -- depends on actual data volume, but good practice.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Database schema design | Column-per-item schema (Pitfall 3) | Normalize from day one: items table + log_entries table |
| Daily log grid | Rerun model kills edits (Pitfall 1) | Isolate grid widget, save on change, use session state |
| Daily log grid | st.data_editor limitations (Pitfall 2) | Validate with real item count early; have fallback plan |
| Database connection | Locked DB or stale cache (Pitfall 4) | Use cache_resource with check_same_thread=False |
| Catalog management | Wikipedia blocking UI (Pitfall 5) | Fetch-and-store pattern with timeout and manual fallback |
| Catalog management | Over-engineering metadata (Pitfall 9) | Text fields, not structured units; expand later if needed |
| Data model | Not taken vs. not logged ambiguity (Pitfall 6) | Add "day logged" flag or three-state model |
| All phases | Date handling bugs (Pitfall 7) | ISO 8601 strings, explicit date selection, date.today() |
| Post-MVP | Data loss with no backup (Pitfall 8) | CSV export, soft deletes, WAL mode |
| Multi-page app | State loss on navigation (Pitfall 10) | Session state persistence, save before navigate |
| History views | Slow pivot on large data (Pitfall 11) | Filter date range before pivot, index on (date, item_id) |

## Summary of Risk Priority

1. **Schema normalization** (Pitfall 3) -- if wrong, everything must be rewritten
2. **Rerun model and data loss** (Pitfall 1) -- if wrong, the core feature is unusable
3. **st.data_editor limitations** (Pitfall 2) -- if too limiting, need alternative UI approach
4. **Connection handling** (Pitfall 4) -- if wrong, intermittent errors undermine trust
5. **Not-taken vs. not-logged** (Pitfall 6) -- if ignored, historical data is ambiguous forever

## Sources

- Streamlit documentation (caching, session state, data_editor) -- training data, not live-verified
- SQLite documentation (WAL mode, ALTER TABLE limitations) -- training data
- General database normalization and medication tracking UX patterns -- training data

**Note:** Web search and fetch were unavailable during this research session. All findings are based on training data (cutoff: May 2025). Core Streamlit and SQLite pitfalls are well-established and unlikely to have changed, but verify against current Streamlit docs for any `st.data_editor` improvements or new caching APIs.
