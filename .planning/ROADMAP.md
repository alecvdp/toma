# Roadmap: Toma

## Overview

Toma delivers a personal medication and supplement tracker in three phases: first, a working item catalog backed by SQLite (so items exist to log against); second, the grid-based daily log that is the core interaction; third, enhancements that make the tool clearly better than a spreadsheet (Wikipedia descriptions, history browsing, data import/export).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation and Catalog** - Database schema, item CRUD, catalog UI with categories and default dosages
- [ ] **Phase 2: Daily Log** - Grid-based daily logging with fixed-dose quick mark, variable dosage, and date navigation
- [ ] **Phase 3: Enhancements** - Wikipedia auto-fetch, history browsing, CSV export, and data import

## Phase Details

### Phase 1: Foundation and Catalog
**Goal**: User can manage a complete catalog of medications and supplements with categories, dosages, and notes
**Depends on**: Nothing (first phase)
**Requirements**: CAT-01, CAT-02, CAT-03, CAT-04, CAT-05, CAT-06, CAT-09, CAT-11, DATA-01
**Success Criteria** (what must be TRUE):
  1. User can add a new item with name, default dosage, unit, and category, and it persists across app restarts
  2. User can edit and delete existing catalog items
  3. User can view all items as cards showing description, dosage, category, and personal notes
  4. User can search and filter items by name or category
  5. All data is stored in a single SQLite file that can be copied for backup
**Plans:** 2 plans

Plans:
- [ ] 01-01-PLAN.md — Project setup, database layer, and item service CRUD with TDD
- [ ] 01-02-PLAN.md — Catalog UI with card view, forms, search, filter, and human verification

### Phase 2: Daily Log
**Goal**: User can log daily medication/supplement intake via a grid interface that mirrors their existing spreadsheet workflow
**Depends on**: Phase 1
**Requirements**: LOG-01, LOG-02, LOG-03, LOG-04, LOG-05, LOG-06, CAT-10
**Success Criteria** (what must be TRUE):
  1. User sees a grid with dates as rows and items as columns, with dosages as cell values
  2. User can mark a fixed-dose item as taken with a single click (default dosage auto-fills)
  3. User can enter a variable dosage for any item on any day, overriding the default
  4. User can navigate to past dates and edit or review that day's log
  5. User can control the column order of items in the grid view
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Enhancements
**Goal**: User has tools that make the tracker clearly better than a spreadsheet -- auto-fetched descriptions, history browsing, and data portability
**Depends on**: Phase 2
**Requirements**: CAT-07, CAT-08, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. User can auto-fetch a 1-3 sentence description from Wikipedia when adding or editing an item
  2. User can edit auto-fetched descriptions to customize them
  3. User can browse log history by selecting a date range
  4. User can export log data to CSV and import data from CSV or Excel
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Catalog | 0/2 | Planning complete | - |
| 2. Daily Log | 0/? | Not started | - |
| 3. Enhancements | 0/? | Not started | - |
