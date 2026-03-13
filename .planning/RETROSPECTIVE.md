# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-13
**Phases:** 3 | **Plans:** 8 | **Sessions:** ~8

### What Was Built
- SQLite-backed catalog with card view, search, filter, and soft-delete
- Grid-based daily log with Take All, variable dosage, date navigation, and notes
- Wikipedia auto-fetch for item descriptions with direct widget-key bridging
- History browsing with date range picker and CSV export
- CSV/Excel import with case-insensitive matching, unit parsing, and filtered preview

### What Worked
- TDD in Phase 1 gave confidence for all subsequent phases — 45 tests caught real bugs
- Three-phase structure (data layer → UI → enhancements) kept dependencies clean
- UAT after Phase 3 caught 4 real bugs that automated tests missed (Streamlit widget state, case sensitivity)
- Gap closure plans (03-03, 03-04) fixed UAT failures surgically without disrupting completed work

### What Was Inefficient
- Initial Wikipedia fetch implementation used value= parameter which Streamlit ignores after first render — required a gap closure plan
- Import service didn't normalize columns on first pass — had to fix at both UI and service layers
- models.py Item dataclass was created but never used (all services return dict(row))

### Patterns Established
- Direct widget key assignment (`st.session_state[key] = value`) for Streamlit state bridging
- Normalize data at both UI entry point and service layer (idempotent, catches mismatches)
- dict(row) from services for easy Streamlit/pandas integration
- Soft-delete with is_active flag for safe item removal
- UAT after phase execution catches runtime issues automated tests miss

### Key Lessons
1. Streamlit's keyed widget caching means `value=` is ignored after first render — always use session_state[key] assignment
2. Case-insensitive matching should be the default for any user-facing data matching
3. UAT is essential for Streamlit apps — widget state, rerun behavior, and visual rendering can't be tested programmatically

### Cost Observations
- Model mix: ~60% opus (execution), ~30% sonnet (verification), ~10% haiku
- 8 plans executed across 3 phases in 5 days
- Notable: Gap closure plans (03-03, 03-04) were very efficient — surgical fixes with minimal context

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~8 | 3 | Established TDD, UAT, gap closure workflow |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 45 | Service layer fully covered | 0 (stdlib urllib for Wikipedia) |

### Top Lessons (Verified Across Milestones)

1. TDD for data layers, UAT for UI layers — different verification strategies for different concerns
2. Normalize early and often — case sensitivity bugs are trivial to prevent, painful to debug
