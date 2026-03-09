# Project Research Summary

**Project:** Toma -- Medication & Supplement Tracker
**Domain:** Personal health tracking (single-user web app)
**Researched:** 2026-03-08
**Confidence:** MEDIUM

## Executive Summary

Toma is a personal medication and supplement tracker designed to replace a spreadsheet workflow. This is a well-understood application category -- medication trackers are mature, table stakes features are stable, and the technical stack is straightforward. The recommended approach is Streamlit + SQLite + pandas, which plays to the developer's existing Streamlit experience and delivers the grid-based data entry UX that defines the product. No backend server, no authentication, no cloud infrastructure -- just a local Python app with a browser UI and a single database file.

The core technical challenge is not complexity but fit: Streamlit's rerun-on-every-interaction model is fundamentally at odds with a data-entry-heavy grid interface. Every widget click reruns the entire page, risking lost edits and scroll position resets. This must be solved in the first phase or the app will feel broken for its primary use case. The mitigation is well-documented -- use `st.data_editor` with explicit session state binding, isolate the grid from other widgets, and save changes immediately. A normalized database schema (rows per log entry, not columns per item) is the other non-negotiable architectural decision; getting this wrong forces a full rewrite.

The risk profile is low overall. The stack is simple, the domain is well-understood, and the user base is one person. The main risks are UX friction from Streamlit's limitations and the temptation to over-engineer features that a single-user tool does not need. Keep scope tight, validate the grid UX early, and this is a weekend-to-week project.

## Key Findings

### Recommended Stack

A minimal Python stack with no external services. Streamlit handles the UI, SQLite handles persistence, and pandas bridges the two for grid display.

**Core technologies:**
- **Python 3.12+**: Runtime -- stable, good typing support
- **Streamlit ~1.40+**: Web UI framework -- developer already uses it, fast to build, `st.data_editor` covers the grid use case
- **SQLite (stdlib)**: Database -- zero config, single file, trivially sufficient for single-user workloads
- **pandas ~2.2+**: Data manipulation -- bridges SQLite queries to Streamlit grid widgets via DataFrames
- **wikipedia-api ~0.7+**: Wikipedia integration -- cleaner than the older `wikipedia` package, handles disambiguation

**Key decision: No ORM.** Raw `sqlite3` with parameterized queries. The schema is 2-3 tables. SQLAlchemy would add dependency complexity for zero benefit.

### Expected Features

**Must have (table stakes):**
- Item catalog with add/edit/remove, categories, default dosages
- Grid-based daily log (the core interaction -- dates as rows, items as columns)
- Fixed-dose quick mark (tap-to-toggle with default dosage)
- Variable dosage entry (override default in-cell)
- Date navigation and history browsing
- SQLite persistence
- Search/filter on catalog
- Categories/tags for items

**Should have (differentiators over spreadsheets):**
- Wikipedia auto-fetch for item descriptions
- Color-coded adherence in grid view
- CSV export
- Item ordering/grouping in daily view
- Dosage unit support
- Quick "take all defaults" button

**Defer (v2+):**
- CSV/Excel import of historical data
- Streak/adherence statistics dashboard
- Per-entry notes
- Database backup/restore UI

**Anti-features (do not build):** Drug interaction checking, push notifications, multi-user auth, time-of-day tracking, barcode scanning, AI insights, social features, cloud sync, native mobile app.

### Architecture Approach

Three-layer architecture in a single Python process: Streamlit pages (UI) call into service modules (business logic) which call into a data access layer (db.py). Pages never touch the database directly. Services never import Streamlit. This separation keeps services testable and pages focused on layout. Multi-page Streamlit app with 3 pages: Daily Log, Catalog, History.

**Major components:**
1. **Pages (daily_log, catalog, history)** -- UI rendering, widget layout, user interaction
2. **Services (log_service, item_service, wiki_service)** -- business logic, data transformation, external API calls
3. **Data access (db.py)** -- SQLite connection management, schema migrations, parameterized queries
4. **Database (toma.db)** -- normalized schema with `items` and `daily_log` tables, ISO 8601 date strings

**Critical schema decision:** Normalized row-per-entry design (`daily_log` table with item_id FK), NOT column-per-item. The grid view is a pivot at the presentation layer, not the storage layer.

### Critical Pitfalls

1. **Streamlit rerun model destroys in-progress edits** -- Use `st.data_editor` with `key` parameter bound to session state. Save edits immediately on change. Isolate the grid from other widgets to minimize reruns.
2. **st.data_editor is not a spreadsheet** -- Limit visible date range to 7-14 days. Use boolean checkboxes for fixed-dose items. Test with actual item count (15-30+) early. Have a fallback plan (per-item checkbox/input layout).
3. **Schema that cannot evolve** -- Normalize from day one. Items table + log entries table. The grid is a view concern, not a storage concern.
4. **SQLite connection handling** -- Use context manager pattern (not global connection). Set `check_same_thread=False`. Clear caches after writes.
5. **"Not taken" vs "not logged" ambiguity** -- Add a "day completed" flag or three-state model. Without this, historical adherence data is unreliable.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation and Data Layer
**Rationale:** Everything depends on having a correct schema and working database layer. Getting the normalized schema right is the single highest-risk decision (Pitfall 3). Item catalog must exist before daily logging is possible (dependency chain).
**Delivers:** Database schema, connection management, item CRUD service, basic catalog page (add/edit/view items with categories and default dosages)
**Addresses:** Item catalog, categories/tags, default dosages, SQLite persistence
**Avoids:** Schema-that-cannot-evolve (Pitfall 3), connection handling bugs (Pitfall 4), date handling errors (Pitfall 7)

### Phase 2: Daily Log Grid
**Rationale:** This IS the app. The grid-based daily log is the primary user interaction and the hardest UI challenge. It depends on Phase 1 (items must exist). Must validate early that `st.data_editor` works at the user's actual scale.
**Delivers:** Grid-based daily logging, fixed-dose quick mark, variable dosage entry, date navigation
**Addresses:** Daily log entry, fixed-dose quick mark, variable dosage entry, bulk daily entry, history view
**Avoids:** Rerun model killing edits (Pitfall 1), st.data_editor limitations (Pitfall 2), not-taken vs not-logged ambiguity (Pitfall 6)

### Phase 3: Polish and Enhancements
**Rationale:** With the core loop working (add items, log doses, browse history), this phase makes the tool clearly better than a spreadsheet. Wikipedia fetching, search/filter, visual polish, and data export add value without structural risk.
**Delivers:** Wikipedia auto-fetch, catalog search/filter, color-coded grid, CSV export, item ordering, dosage units
**Addresses:** Wikipedia auto-fetch, search/filter, color-coded adherence, CSV export, item ordering, dosage units
**Avoids:** Wikipedia blocking UI (Pitfall 5), over-engineering catalog (Pitfall 9), no backup/export strategy (Pitfall 8)

### Phase Ordering Rationale

- **Data dependencies drive order:** Items before logs, logs before history. This is not negotiable.
- **Risk-first:** The grid UX (Phase 2) is the highest-risk UI challenge. It must be validated early, not deferred. If `st.data_editor` proves too limiting, a fallback approach must be chosen before investing in polish features.
- **Polish is last:** Phase 3 features are valuable but none of them block daily use. The app is usable after Phase 2.
- **Three phases, not five:** This is a small personal tool. More granular phasing adds planning overhead without benefit.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Daily Log Grid):** The `st.data_editor` pivot-table pattern (normalized data -> DataFrame pivot -> editable grid -> diff detection -> write back) is the most complex implementation detail. Verify current `st.data_editor` API, column configuration options, and change detection behavior against live Streamlit docs.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** SQLite schema design, CRUD services, and basic Streamlit forms are well-documented. No research needed.
- **Phase 3 (Polish):** Wikipedia API calls, CSV export, and UI styling are straightforward. No research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Streamlit + SQLite + pandas is the obvious choice for this use case. No controversial decisions. |
| Features | MEDIUM | Feature landscape is well-understood but based on training data, not live app analysis. Table stakes are stable. |
| Architecture | MEDIUM | Patterns are sound but specific Streamlit API details (st.data_editor config, caching APIs) should be verified against current docs. |
| Pitfalls | HIGH | The top pitfalls (rerun model, schema normalization, connection handling) are well-established and unlikely to have changed. |

**Overall confidence:** MEDIUM -- the architectural approach and feature priorities are solid, but specific Streamlit API behavior should be verified at development time.

### Gaps to Address

- **st.data_editor current API:** Verify column configuration, change detection, and checkbox column support in the current Streamlit version. The pivot-grid pattern is the core UX and must work well.
- **wikipedia-api package status:** Confirm the package is still maintained and working. If not, direct MediaWiki API calls via `requests` are a simple fallback.
- **"Not taken" vs "not logged" UX:** Research did not converge on a single best approach (day-completed flag vs three-state model). Decide during Phase 2 planning.
- **Streamlit version pinning:** All version numbers are from training data (early 2025). Run `pip index versions` to confirm current stable versions before starting.

## Sources

### Primary (HIGH confidence)
- Python sqlite3 stdlib documentation -- stable API, high confidence
- SQLite documentation (WAL mode, foreign keys, date handling) -- stable, well-established
- General database normalization patterns -- textbook knowledge

### Secondary (MEDIUM confidence)
- Streamlit documentation (architecture model, session state, multi-page apps, caching, st.data_editor) -- based on training data, not live-verified
- Medication tracking app landscape (Medisafe, MyTherapy, Round Health) -- training data knowledge of mature category
- wikipedia-api package -- training data, verify current status

### Tertiary (LOW confidence)
- Specific version numbers for all packages -- based on early 2025 training data, must verify

---
*Research completed: 2026-03-08*
*Ready for roadmap: yes*
