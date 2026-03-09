# Toma — Medication & Supplement Tracker

## What This Is

A personal web app for tracking daily medication and supplement intake, replacing manual Excel/Airtable spreadsheets. Features a grid-based daily log for recording what was taken and at what dosage, plus a catalog of all items with descriptions, dosage info, categories, and personal notes. Built with Streamlit and SQLite.

## Core Value

Quickly and reliably log daily medications/supplements with their dosages, and review history at a glance — replacing the friction of spreadsheet-based tracking.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Grid/spreadsheet daily log view (dates as rows, items as columns, dosages as values)
- [ ] Add/remove items to the catalog
- [ ] Catalog card view with item details (description, typical dosage, category/tags, personal notes)
- [ ] Auto-fetch item descriptions from Wikipedia with ability to edit
- [ ] Default dosages for items that are always the same dose (acts as a quick checkmark)
- [ ] Variable dosage entry for supplements where dose changes
- [ ] SQLite database storage (single portable file)
- [ ] Filter/view log history by date range

### Out of Scope

- Multi-user / authentication — single user for now
- Time-of-day tracking — not needed currently
- Drug interaction checking — not building a medical tool
- Mobile native app — web-first via Streamlit
- Cloud/remote database — local SQLite is sufficient
- Notifications/reminders — out of scope for v1

## Context

- Alec currently tracks medications and supplements in Excel/Airtable with columns per item and rows per date
- Many items have fixed dosages (just need a taken/not-taken marker), while supplements vary
- Has two existing Python web apps using Streamlit, so familiar with the framework
- Open to other frameworks but comfortable with Streamlit
- Single user — personal tracking tool
- Descriptions should be simple (1-3 sentences), not clinical/scientific data

## Constraints

- **Tech stack**: Python with Streamlit preferred (existing familiarity), SQLite for storage
- **Deployment**: Local use, no cloud infrastructure required
- **Data**: Single-file database for easy backup and portability

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Streamlit for UI | Existing familiarity, two other apps already built with it | — Pending |
| SQLite for storage | Portable single file, fast queries, no server needed | — Pending |
| Wikipedia for descriptions | Simple 1-3 sentence overviews, not clinical data | — Pending |
| Grid view for daily log | Matches existing Excel mental model | — Pending |

---
*Last updated: 2026-03-08 after initialization*
