---
phase: 3
slug: enhancements
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | CAT-07 | unit | `pytest tests/test_wikipedia.py -x` | No -- Wave 0 | pending |
| 3-01-02 | 01 | 1 | CAT-07 | unit | `pytest tests/test_wikipedia.py -x` | No -- Wave 0 | pending |
| 3-01-03 | 01 | 1 | CAT-08 | unit | `pytest tests/test_item_service.py::test_update_item -x` | Yes | pending |
| 3-02-01 | 02 | 1 | DATA-02 | unit | `pytest tests/test_log_service.py::test_get_logs_by_date_range -x` | No -- Wave 0 | pending |
| 3-02-02 | 02 | 1 | DATA-03 | unit | `pytest tests/test_export.py -x` | No -- Wave 0 | pending |
| 3-02-03 | 02 | 1 | DATA-04 | unit | `pytest tests/test_import.py -x` | No -- Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_wikipedia.py` -- stubs for CAT-07 (mock urllib, test search+fetch pattern)
- [ ] `tests/test_log_service.py::test_get_logs_by_date_range` -- add to existing file for DATA-02
- [ ] `tests/test_export.py` -- stubs for DATA-03 (CSV generation)
- [ ] `tests/test_import.py` -- stubs for DATA-04 (validation + upsert)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Wikipedia fetch button appears in add/edit forms | CAT-07 | UI layout verification | Open catalog, click add item, verify "Fetch Description" button exists next to description field |
| Date range picker shows calendar widget | DATA-02 | UI widget rendering | Open daily log, verify date range picker appears and returns correct tuple |
| Download button triggers browser download | DATA-03 | Browser interaction | Click "Export to CSV", verify .csv file downloads with correct content |
| File uploader accepts CSV and xlsx | DATA-04 | Browser file dialog | Click upload, verify file type filter shows csv/xlsx |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
