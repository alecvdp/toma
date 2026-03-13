---
status: diagnosed
trigger: "UAT Test 7: Import CSV — case-sensitive date, broken column matching, ValueError on dosages with units"
created: 2026-03-13T00:00:00Z
updated: 2026-03-13T00:00:00Z
---

## Current Focus

hypothesis: All three bugs confirmed in committed code; working tree has partial fixes for issues 1 and 3 but not issue 2
test: Compared committed vs working tree via git diff
expecting: Identify each root cause location
next_action: Return diagnosis

## Symptoms

expected: Import accepts CSV with case-insensitive date column, matches item columns to catalog, handles dosages with units like '750mg'
actual: (1) 'Date' with capital D errors. (2) All item columns listed as 'unrecognized'. (3) Confirm Import crashes with ValueError on '750mg'.
errors: ValueError: could not convert string to float: '750mg'
reproduction: Upload CSV with 'Date' column, item names matching catalog, dosage values like '750mg'
started: Current committed code

## Eliminated

(none)

## Evidence

- timestamp: 2026-03-13
  checked: git diff services/import_service.py (committed vs working tree)
  found: |
    COMMITTED code (HEAD) has all three bugs:
    1. No column normalization — validate_import checks "date" against raw column names
    2. Case-sensitive matching — uses {item["name"] for item in active_items} without lowering
    3. Direct float(value) — calls float(value) instead of _parse_numeric, crashes on '750mg'

    WORKING TREE has fixes for issues 1 and 3:
    - Added df.columns.str.strip().str.lower() normalization
    - Added _parse_numeric() function with regex extraction
    - Changed import_logs to use _parse_numeric instead of float(value)
  implication: Issues 1 and 3 are fixed in import_service.py working tree but not committed.

- timestamp: 2026-03-13
  checked: git diff pages/import_export.py
  found: No changes. Still has case-sensitive item matching on lines 72-76.
  implication: Issue 2 is NOT fixed anywhere — still a live bug even with working tree changes.

- timestamp: 2026-03-13
  checked: pages/import_export.py lines 72-76 (summary section)
  found: |
    item_columns = [c for c in import_df.columns if c != "date" and c in {item["name"] for item in active_items}]
    After validate_import lowercases columns (working tree fix), "vitamin d" != "Vitamin D".
    So item_columns is always empty, showing "0 entries for 0 items" in summary.
  implication: UI page needs its own case-insensitive matching for the summary.

- timestamp: 2026-03-13
  checked: tests/test_import.py
  found: |
    All tests use exact-case column names matching item names (e.g., "Item A" column with "Item A" item).
    No tests for: case-insensitive date column, case-insensitive item matching, string dosage values like '750mg'.
  implication: Test coverage gaps allowed these bugs to ship.

## Resolution

root_cause: |
  COMMITTED CODE (HEAD):
    Issue 1: validate_import has no column normalization — checks for literal "date" against raw CSV columns.
    Issue 2: Both validate_import and import_logs use exact-case item name matching.
    Issue 3: import_logs calls float(value) directly — crashes on strings like '750mg'.

  WORKING TREE (uncommitted):
    Issues 1 and 3: Fixed in import_service.py (column normalization + _parse_numeric).
    Issue 2: Still broken in pages/import_export.py — summary uses original-case item names
             against lowered column names. Even with import_service fixes, the UI summary
             shows 0 matched items. import_logs itself works (it does its own lowered matching),
             so data WOULD import correctly, but the user sees misleading "0 items" summary.

fix:
verification:
files_changed: []
