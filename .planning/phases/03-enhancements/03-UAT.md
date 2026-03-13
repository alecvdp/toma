---
status: diagnosed
phase: 03-enhancements
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md
started: 2026-03-10T01:30:00Z
updated: 2026-03-10T01:35:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Fetch Wikipedia Description (Add Item)
expected: On the Catalog page, open the Add Item form. Enter an item name (e.g. "Magnesium"). Click "Fetch Description". A 1-3 sentence description from Wikipedia populates the description field. Submit the form — the item is created with the fetched description visible on its card.
result: issue
reported: "Fetch gives success message but description doesn't visually appear in text area until after submitting. Also confusing UX: separate 'Item name to look up' field alongside the main 'Name' field — fetch should use the main Name field directly."
severity: major

### 2. Fetch Wikipedia Description (Edit Item)
expected: On the Catalog page, click edit on an existing item. Click "Fetch Description" — the description field updates with a Wikipedia summary. Save the edit — the updated description persists on the card.
result: issue
reported: "Green 'fetched from Wikipedia' message appears but description does not appear, even after saving — unlike add flow where it showed after submit."
severity: major

### 3. Edit Auto-Fetched Description
expected: After fetching a Wikipedia description (via add or edit), modify the text in the description field before saving. The custom-edited version persists, not the original auto-fetched text.
result: pass

### 4. Fetch Description for Unknown Item
expected: Enter a nonsensical item name (e.g. "xyzzyplugh123"). Click "Fetch Description". No crash or error — the description field remains empty or shows a "not found" message.
result: pass

### 5. Browse History by Date Range
expected: On the Daily Log page, select a date range using the date range picker (e.g. last 7 days). A multi-row grid appears showing dates as rows and items as columns, with dosage values filled in for logged entries.
result: pass

### 6. Export Log Data to CSV
expected: On the Daily Log page with a date range selected, click "Export to CSV". A CSV file downloads with dates as rows, item names as column headers, and dosage values as cell data.
result: pass

### 7. Import Data from CSV
expected: Navigate to the Import/Export page. Upload a CSV file with a "date" column and item name columns matching catalog items. A preview of the data appears. Click confirm — the data imports and appears in the daily log.
result: issue
reported: "Three problems: (1) 'Date' with capital D errors — must be lowercase 'date'. (2) All item columns listed as 'unrecognized' even though they match catalog items — column matching broken. (3) Confirm Import crashes with ValueError: could not convert string to float: '750mg' — dosages with units like '750mg' not handled. Import/Export page also wasn't registered in app.py (fixed during test)."
severity: blocker

### 8. Import Validation (Unrecognized Columns)
expected: Upload a CSV with columns that don't match any catalog items. A warning displays listing the unrecognized columns (they will be skipped). Recognized columns still import successfully.
result: issue
reported: "Warning shows and lists unrecognized columns, but preview still displays the unrecognized columns which is misleading. Says 'Will import up to 215 entries for 1 items across 219 dates' — preview should only show recognized/matching columns."
severity: minor

### 9. Import Data from Excel
expected: Upload an .xlsx file with the same format as CSV (date column + item columns). Preview appears, confirm imports the data successfully.
result: skipped
reason: User unable to create .xlsx file on current machine

## Summary

total: 9
passed: 4
issues: 4
pending: 0
skipped: 1

## Gaps

- truth: "Fetched Wikipedia description visually populates the description field before form submit, and fetch uses the main Name field"
  status: failed
  reason: "User reported: Fetch gives success message but description doesn't visually appear in text area until after submitting. Also confusing UX: separate 'Item name to look up' field alongside the main 'Name' field — fetch should use the main Name field directly."
  severity: major
  test: 1
  root_cause: "Streamlit keyed widget state caching: st.text_area with key='add_description' ignores the value= param after first render, reading from st.session_state['add_description'] instead. Code sets fetched_description but never updates the widget key. Name field is outside st.form() (required by Streamlit) causing visual separation."
  artifacts:
    - path: "pages/catalog.py"
      issue: "line 67-72: value= param on keyed textarea ignored after first render"
    - path: "pages/catalog.py"
      issue: "line 44-62: Name + Fetch button outside form border creates UX confusion"
  missing:
    - "Set st.session_state['add_description'] = desc after fetch to update widget key directly"
    - "Remove fetched_description session state variable, use widget key directly"
    - "Restructure layout so Name field appears visually connected to form"
  debug_session: ".planning/debug/fetch-desc-no-visual-update.md"
- truth: "Import page visible in navigation, accepts CSV with case-insensitive date column, matches item columns to catalog, handles dosages with units"
  status: failed
  reason: "User reported: (1) Import/Export page not in nav (fixed). (2) 'Date' capital D errors. (3) All item columns listed as unrecognized despite matching catalog. (4) ValueError on '750mg' — float() can't parse dosages with units."
  severity: blocker
  test: 7
  root_cause: "Three bugs: (1) validate_import checks for literal 'date' against raw column names — no normalization. (2) Item matching uses original case names against raw columns — case mismatch. (3) import_logs calls float(value) directly — crashes on '750mg'. Working tree has partial fixes in import_service.py but pages/import_export.py UI matching still broken."
  artifacts:
    - path: "services/import_service.py"
      issue: "No column normalization; case-sensitive item matching; float() on unit strings"
    - path: "pages/import_export.py"
      issue: "lines 72-76: item_columns comparison uses original case against lowered columns"
  missing:
    - "Commit working tree fixes in import_service.py (column normalization, _parse_numeric, case-insensitive matching)"
    - "Fix pages/import_export.py to use case-insensitive item name matching"
    - "Add test coverage for case-insensitive columns and unit dosage parsing"
  debug_session: ".planning/debug/import-csv-bugs.md"
- truth: "Fetched Wikipedia description appears in the edit form and persists after saving"
  status: failed
  reason: "User reported: Green 'fetched from Wikipedia' message appears but description does not appear, even after saving."
  severity: major
  test: 2
  root_cause: "Same Streamlit widget state caching bug as Test 1: code sets st.session_state.edit_fetched_description but the text_area uses key='edit_description'. After rerun, Streamlit reads from the widget key (stale) and ignores the value= parameter."
  artifacts:
    - path: "pages/catalog.py"
      issue: "line 107: sets edit_fetched_description but never updates widget key edit_description"
  missing:
    - "Set st.session_state['edit_description'] = desc after fetch to update widget key directly"
  debug_session: ""
- truth: "Preview only shows recognized/matching columns, not unrecognized ones that will be skipped"
  status: failed
  reason: "User reported: Warning shows and lists unrecognized columns, but preview still displays the unrecognized columns. Says 'Will import up to 215 entries for 1 items across 219 dates' — preview should only show recognized columns."
  severity: minor
  test: 8
  root_cause: "Preview renders import_df.head(10) — the raw unfiltered dataframe. The item_columns filter is computed after the preview and only used for the summary text, never applied to filter the preview."
  artifacts:
    - path: "pages/import_export.py"
      issue: "line 69: st.dataframe(import_df.head(10)) shows all columns unfiltered"
    - path: "pages/import_export.py"
      issue: "lines 72-76: item_columns computed after preview, only used for summary"
  missing:
    - "Move item_columns computation before preview"
    - "Filter preview to import_df[['date'] + item_columns].head(10)"
  debug_session: ".planning/debug/import-preview-unrecognized-cols.md"
