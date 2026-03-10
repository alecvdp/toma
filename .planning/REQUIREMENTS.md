# Requirements: Toma

**Defined:** 2026-03-08
**Core Value:** Quickly and reliably log daily medications/supplements with their dosages, and review history at a glance

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Catalog

- [x] **CAT-01**: User can add a new item to the catalog with name, default dosage, dosage unit, and category
- [x] **CAT-02**: User can edit an existing catalog item's details
- [x] **CAT-03**: User can remove an item from the catalog
- [x] **CAT-04**: User can assign categories/tags to items (supplement, prescription, vitamin, etc.)
- [x] **CAT-05**: User can set a default dosage and unit for each item (mg, IU, capsules, etc.)
- [x] **CAT-06**: User can view catalog items as cards with description, dosage, category, and personal notes
- [x] **CAT-07**: User can auto-fetch a 1-3 sentence description from Wikipedia when adding an item
- [x] **CAT-08**: User can edit the auto-fetched description
- [x] **CAT-09**: User can search and filter catalog items by name or category
- [x] **CAT-10**: User can set a custom sort order for items in the daily log view
- [x] **CAT-11**: User can add personal notes to any catalog item

### Daily Log

- [x] **LOG-01**: User can view a grid with dates as rows and items as columns, with dosages as cell values
- [x] **LOG-02**: User can mark a fixed-dose item as taken with a single click (auto-fills default dosage)
- [x] **LOG-03**: User can enter a variable dosage that overrides the default for a specific day
- [x] **LOG-04**: User can mark all fixed-dose items as taken with a single "take all" button
- [x] **LOG-05**: User can add an optional note to any individual log entry
- [x] **LOG-06**: User can navigate to any date to view or edit that day's log

### Data & History

- [x] **DATA-01**: All data persists in a local SQLite database file
- [x] **DATA-02**: User can browse log history by selecting a date range
- [x] **DATA-03**: User can export log data to CSV
- [x] **DATA-04**: User can import existing medication/supplement data from CSV or Excel

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Visual Enhancements

- **VIS-01**: Color-coded adherence in grid view (green=taken, red=missed)
- **VIS-02**: Streak/adherence statistics per item (e.g., "28 of last 30 days")

### Data Management

- **DATM-01**: Database backup and restore via UI

## Out of Scope

| Feature | Reason |
|---------|--------|
| Drug interaction checking | Medical liability, requires clinical database, out of scope for personal tool |
| Push notifications / reminders | Requires background services, mobile integration; app is a log, not an alarm |
| Multi-user / authentication | Single-user tool; no need for auth complexity |
| Time-of-day tracking | Not needed currently; track by day only |
| Barcode/pill scanning | Massive scope for marginal value; manual entry with Wikipedia is sufficient |
| AI-powered health insights | Gimmick; simple adherence stats are more honest |
| Social features / sharing | Irrelevant for personal tracking tool |
| Cloud sync | Adds infrastructure complexity; local SQLite is sufficient |
| Native mobile app | Streamlit web app works on mobile browsers |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CAT-01 | Phase 1 | Complete |
| CAT-02 | Phase 1 | Complete |
| CAT-03 | Phase 1 | Complete |
| CAT-04 | Phase 1 | Complete |
| CAT-05 | Phase 1 | Complete |
| CAT-06 | Phase 1 | Complete |
| CAT-07 | Phase 3 | Complete |
| CAT-08 | Phase 3 | Complete |
| CAT-09 | Phase 1 | Complete |
| CAT-10 | Phase 2 | Complete |
| CAT-11 | Phase 1 | Complete |
| LOG-01 | Phase 2 | Complete |
| LOG-02 | Phase 2 | Complete |
| LOG-03 | Phase 2 | Complete |
| LOG-04 | Phase 2 | Complete |
| LOG-05 | Phase 2 | Complete |
| LOG-06 | Phase 2 | Complete |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 3 | Complete |
| DATA-03 | Phase 3 | Complete |
| DATA-04 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 after roadmap creation*
