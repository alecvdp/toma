---
phase: 2
slug: daily-log
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (via uv dev dependency) |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | LOG-01 | unit | `python -m pytest tests/test_log_service.py::test_build_log_grid -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | LOG-02 | unit | `python -m pytest tests/test_log_service.py::test_upsert_default_dosage -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | LOG-03 | unit | `python -m pytest tests/test_log_service.py::test_upsert_custom_dosage -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | LOG-04 | unit | `python -m pytest tests/test_log_service.py::test_take_all_fixed_dose -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | LOG-05 | unit | `python -m pytest tests/test_log_service.py::test_log_entry_notes -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | LOG-06 | unit | `python -m pytest tests/test_log_service.py::test_get_logs_by_date -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 1 | CAT-10 | unit | `python -m pytest tests/test_log_service.py::test_items_sort_order -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_log_service.py` — stubs for LOG-01 through LOG-06, CAT-10
- [ ] `tests/test_db.py` — extend with daily_logs schema test
- [ ] Existing `conftest.py` test_db fixture is sufficient

*Existing test infrastructure from Phase 1 covers framework setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grid renders dates as rows, items as columns | LOG-01 | Visual layout verification | Open app, verify grid layout matches spreadsheet format |
| Single-click "Take All" fills defaults | LOG-02, LOG-04 | UI interaction | Click "Take All", verify all fixed-dose items auto-fill |
| Date navigation works | LOG-06 | UI interaction | Use date picker to navigate to past dates, verify data loads |
| Column order matches sort_order | CAT-10 | Visual layout | Reorder items in catalog, verify grid columns update |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
