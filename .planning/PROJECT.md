# Toma — Medication & Supplement Tracker

## What This Is

A personal web app for tracking daily medication and supplement intake, replacing manual Excel/Airtable spreadsheets. Features a grid-based daily log, a catalog with Wikipedia-powered descriptions, history browsing, and CSV/Excel data import/export. Built with Streamlit and SQLite.

## Core Value

Quickly and reliably log daily medications/supplements with their dosages, and review history at a glance — replacing the friction of spreadsheet-based tracking.

## Requirements

### Validated

- ✓ Grid/spreadsheet daily log view (dates as rows, items as columns, dosages as values) — v1.0
- ✓ Add/edit/remove items in the catalog with card-based display — v1.0
- ✓ Auto-fetch item descriptions from Wikipedia with ability to edit — v1.0
- ✓ Default dosages with single-click "take all" for fixed-dose items — v1.0
- ✓ Variable dosage entry for items where dose changes — v1.0
- ✓ SQLite database storage (single portable file) — v1.0
- ✓ Filter/view log history by date range with CSV export — v1.0
- ✓ Import data from CSV or Excel files — v1.0

### Active

- [ ] Color-coded adherence in grid view (green=taken, red=missed)
- [ ] Streak/adherence statistics per item
- [ ] Database backup and restore via UI

### Out of Scope

- Multi-user / authentication — single user tool
- Time-of-day tracking — not needed currently
- Drug interaction checking — not building a medical tool
- Mobile native app — Streamlit web app works on mobile browsers
- Cloud/remote database — local SQLite is sufficient
- Notifications/reminders — app is a log, not an alarm
- Barcode/pill scanning — manual entry with Wikipedia is sufficient

## Context

Shipped v1.0 with 1,683 LOC Python across 18 files.
Tech stack: Streamlit, SQLite (WAL mode), pandas, pytest.
45 tests, all passing. 3 phases, 8 plans executed in 5 days.

Known tech debt:
- `models.py` Item dataclass is orphaned (never imported, services use dict(row))
- CAT-10 sort_order has DB infrastructure but no catalog UI to set it

## Constraints

- **Tech stack**: Python with Streamlit, SQLite for storage
- **Deployment**: Local use, no cloud infrastructure required
- **Data**: Single-file database for easy backup and portability

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit for UI | Existing familiarity, two other apps already built with it | ✓ Good — rapid development, works well |
| SQLite for storage | Portable single file, fast queries, no server needed | ✓ Good — WAL mode handles concurrent reads |
| Wikipedia for descriptions | Simple 1-3 sentence overviews, not clinical data | ✓ Good — stdlib urllib, no extra deps |
| Grid view for daily log | Matches existing Excel mental model | ✓ Good — st.data_editor works well |
| dict(row) returns from services | Easy Streamlit/pandas integration | ✓ Good — makes Item dataclass unnecessary |
| Soft-delete with is_active flag | Preserves data integrity, no cascading deletes | ✓ Good — simple and safe |
| Direct widget key assignment for Streamlit state | Solves value= caching bug | ✓ Good — required for fetch-to-textarea bridging |
| Normalize columns at both UI and service layers | Idempotent, catches case mismatches early | ✓ Good — fixed CSV import bugs |

---
*Last updated: 2026-03-13 after v1.0 milestone*
