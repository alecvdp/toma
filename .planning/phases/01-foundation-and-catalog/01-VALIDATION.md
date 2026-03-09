---
phase: 1
slug: foundation-and-catalog
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (latest) |
| **Config file** | none — Wave 0 installs |
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
| 01-01-01 | 01 | 1 | DATA-01 | unit | `pytest tests/test_db.py::test_persistence -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | CAT-01 | unit | `pytest tests/test_item_service.py::test_create_item -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | CAT-02 | unit | `pytest tests/test_item_service.py::test_update_item -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | CAT-03 | unit | `pytest tests/test_item_service.py::test_deactivate_item -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | CAT-04 | unit | `pytest tests/test_item_service.py::test_item_category -x` | ❌ W0 | ⬜ pending |
| 01-01-06 | 01 | 1 | CAT-05 | unit | `pytest tests/test_item_service.py::test_default_dosage -x` | ❌ W0 | ⬜ pending |
| 01-01-07 | 01 | 1 | CAT-09 | unit | `pytest tests/test_item_service.py::test_search_items -x` | ❌ W0 | ⬜ pending |
| 01-01-08 | 01 | 1 | CAT-11 | unit | `pytest tests/test_item_service.py::test_item_notes -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CAT-06 | manual-only | N/A — UI layout | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package init
- [ ] `tests/conftest.py` — shared fixture for in-memory SQLite database
- [ ] `tests/test_db.py` — schema creation, connection management, persistence
- [ ] `tests/test_item_service.py` — all CRUD operations, search, filter, soft delete
- [ ] `pyproject.toml` — pytest configuration section
- [ ] Framework install: `uv add --dev pytest` or `pip install pytest`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| View items as cards with description, dosage, category, notes | CAT-06 | UI layout verification — Streamlit renders visually | Launch app, add items, verify card display shows all fields |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
