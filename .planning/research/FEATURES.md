# Feature Landscape

**Domain:** Medication & supplement tracking (personal use)
**Researched:** 2026-03-08
**Confidence:** MEDIUM (based on training knowledge of mature app category; no live web verification available)

## Table Stakes

Features users expect from any medication/supplement tracker. Missing these and the tool feels broken or incomplete compared to alternatives (or even to the spreadsheet it replaces).

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Item catalog (add/edit/remove) | Core data model. Users need to define what they take. | Low | Already in scope. Include name, category, default dosage, notes. |
| Daily log entry | The primary action. "Did I take X today?" | Medium | Grid/spreadsheet view matches Alec's mental model from Excel. This IS the app. |
| Fixed-dose quick mark | Most meds are the same dose daily. Tap-to-toggle is expected. | Low | Boolean taken/not-taken with pre-filled default dosage. Reduces friction to near-zero. |
| Variable dosage entry | Supplements often vary (e.g., Vitamin D 2000 vs 5000 IU). | Low | Input field that overrides default. Must be fast -- not a modal dialog. |
| History view / date navigation | Users check "did I take X last Tuesday?" constantly. | Medium | Scrollable grid or calendar picker. Date range filtering is the minimum. |
| Data persistence | Data must survive app restarts. | Low | SQLite is perfect. Single file, no server, easy backup. |
| Search/filter catalog | Once you track 15+ items, scrolling a flat list is painful. | Low | Text search + category filter on the catalog view. |
| Categories/tags for items | Organization. Medications vs supplements vs vitamins vs nootropics. | Low | Simple tag or category field. Don't over-engineer taxonomy. |
| Bulk daily entry | Entering 10+ items one-by-one is a dealbreaker vs spreadsheets. | Medium | The grid view solves this -- all items visible, mark across a row. Critical UX. |

## Differentiators

Features that set Toma apart from generic trackers or spreadsheets. Not expected by default, but add real value for a personal tracking tool.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Auto-fetch descriptions from Wikipedia | Removes tedious manual data entry when adding items. No other simple tracker does this well. | Medium | Use Wikipedia API, extract first 1-3 sentences. Allow manual edit. Already in scope. |
| Streak/adherence tracking | "I've taken Magnesium 28 of the last 30 days" -- motivating and informative. | Medium | Calculated from log data. Simple percentage per item over configurable window. |
| CSV/Excel import | Alec has existing data in spreadsheets. Zero-friction migration. | Medium | Import historical data so day-one isn't empty. One-time feature but high impact for onboarding. |
| CSV/Excel export | Data portability. Never feel locked in. | Low | Simple dump of log table. Peace of mind feature. |
| Grid view with color coding | Visual scan of adherence patterns -- green for taken, red for missed, yellow for partial. | Low | Leverages the spreadsheet mental model. Immediate visual feedback. |
| Item ordering/grouping in daily view | Show morning items first, evening items last. Group by category. | Low | Custom sort order field on catalog items. Small effort, big UX improvement. |
| Dosage unit support | mg, mcg, IU, mL, capsules, tablets -- proper units prevent confusion. | Low | Enum or free-text unit field on catalog items. |
| Quick "take all defaults" button | One click to mark all fixed-dose items as taken. | Low | For days when you took everything as usual. Massive time saver for 10+ item regimens. |
| Notes per log entry | "Took half dose because stomach upset" or "Switched brands" | Low | Optional text field per cell in the daily grid. |
| Database backup/restore | Single-file SQLite makes this trivial. Explicit backup button adds confidence. | Low | Copy .db file with timestamp. Restore = replace file. |

## Anti-Features

Features to explicitly NOT build. These add complexity without serving the core use case, or actively harm the product.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Drug interaction checking | Medical liability, requires a maintained clinical database, way out of scope for a personal tool. | Link to drugs.com or similar if user wants to check. Add a disclaimer. |
| Push notifications / reminders | Requires background services, mobile integration, notification permissions. Alec explicitly scoped this out. | The app is a log, not an alarm. Users who want reminders use their phone's alarm app. |
| Multi-user / authentication | Adds auth complexity, database multi-tenancy, permission models. Single-user tool. | If ever needed, add a simple password gate, not a user system. |
| Time-of-day tracking (AM/PM/specific times) | Adds columns/complexity to the data model, complicates the grid view, and Alec said not needed. | Track by day only. If needed later, add as optional metadata, never as a required field. |
| Barcode/pill scanning | Requires camera integration, OCR, product databases. Massive scope for marginal value in a personal tool. | Manual entry with Wikipedia auto-fill is sufficient. |
| AI-powered health insights | Gimmick in most tracker apps. Requires ML infrastructure, medical knowledge, liability concerns. | Simple adherence stats (streak, percentage) are more honest and useful. |
| Social features / sharing | Community features are irrelevant for a personal tracking tool. | Keep it private and local. |
| Pharmacy integration / refill tracking | Requires API integrations with pharmacy systems. Enterprise-grade complexity. | Out of scope. Users track refills in their pharmacy's own app. |
| Cloud sync | Adds server infrastructure, hosting costs, data privacy concerns. SQLite file is explicitly chosen for portability. | Local-only. Backup the .db file to cloud storage manually if desired. |
| Mobile native app | Requires separate codebase (or React Native/Flutter), app store deployment, maintenance burden. | Streamlit web app works on mobile browsers. Good enough for personal use. |

## Feature Dependencies

```
Item Catalog --> Daily Log (can't log items that don't exist)
Item Catalog --> Wikipedia Auto-fetch (fetches descriptions for catalog items)
Daily Log --> History View (history is past daily logs)
Daily Log --> Streak/Adherence Tracking (calculated from log entries)
Daily Log --> CSV Export (exports log data)
Categories/Tags --> Search/Filter (filtering requires categories to exist)
Default Dosages --> Quick "Take All" Button (needs defaults to know what to fill)
Default Dosages --> Fixed-Dose Quick Mark (tap-to-toggle uses default dosage)
```

## MVP Recommendation

**Prioritize (Phase 1 -- the "replace my spreadsheet" release):**
1. Item catalog with add/edit/remove, categories, default dosages
2. Grid-based daily log view (the core interaction)
3. Fixed-dose quick mark (taken/not-taken toggle)
4. Variable dosage entry
5. Date navigation / history browsing
6. SQLite persistence

**Phase 2 -- "better than my spreadsheet":**
1. Wikipedia auto-fetch for item descriptions
2. Search/filter on catalog
3. Color-coded adherence in grid view
4. CSV export
5. Item ordering in daily view
6. Dosage units

**Defer (nice-to-have, build if motivated):**
- CSV/Excel import of historical data
- Streak/adherence statistics dashboard
- Quick "take all defaults" button
- Per-entry notes
- Database backup/restore UI

**Rationale:** Phase 1 achieves feature parity with the spreadsheet approach. Phase 2 makes the tool clearly better than a spreadsheet. Deferred features add polish but aren't blocking adoption since this is a single-user tool -- Alec will use it as soon as it replaces his spreadsheet.

## Sources

- Training knowledge of medication tracking app landscape (Medisafe, MyTherapy, Round Health, Pill Reminder, Pillsy, Care Zone, Mango Health)
- Training knowledge of supplement tracking apps and communities
- Project requirements from PROJECT.md
- No live web sources available (WebSearch/WebFetch unavailable during research)

**Confidence note:** The medication/supplement tracking app category is mature and well-established. Table stakes features are extremely stable across the category and unlikely to have shifted since training cutoff. The recommendations above are tailored to Alec's specific use case (personal, single-user, spreadsheet replacement) rather than the broader commercial app market.
