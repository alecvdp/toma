---
status: diagnosed
trigger: "UAT Test 8: Import preview shows unrecognized columns that will be skipped"
created: 2026-03-13T00:00:00Z
updated: 2026-03-13T00:00:00Z
---

## Current Focus

hypothesis: Preview dataframe is not filtered to recognized columns before display
test: Read preview rendering code
expecting: Missing column filter
next_action: Return diagnosis

## Symptoms

expected: Preview only shows recognized/matching columns, not unrecognized ones
actual: Warning lists unrecognized columns but preview still displays them
errors: none (functional bug, not crash)
reproduction: Upload CSV with unrecognized columns, observe preview
started: Since implementation

## Eliminated

(none needed - root cause found on first pass)

## Evidence

- timestamp: 2026-03-13
  checked: pages/import_export.py line 69
  found: st.dataframe(import_df.head(10)) uses raw unfiltered dataframe
  implication: All columns including unrecognized ones are displayed

- timestamp: 2026-03-13
  checked: pages/import_export.py lines 72-76
  found: item_columns filtering exists for summary but is computed AFTER the preview render
  implication: The recognized-column filter logic exists but is not applied to the preview

## Resolution

root_cause: pages/import_export.py line 69 renders st.dataframe(import_df.head(10)) using the raw unfiltered dataframe. The item_columns filter (lines 72-76) is only used for the summary text, never applied to filter the preview dataframe.
fix: empty
verification: empty
files_changed: []
