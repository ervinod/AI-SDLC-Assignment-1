# Specification Analysis Report — 001-task-cli

Saved copy of the `/speckit-analyze` output (the command itself is read-only). Run on 2026-11-22
against spec.md, plan.md, tasks.md, data-model.md, contracts/cli.md and constitution v1.0.0.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification | MEDIUM | contracts/cli.md (last line); spec.md FR-005 | Contract says removing a tag that is not present is a no-op; spec is silent. Constitution I forbids behaviour absent from the spec. | Add the rule to FR-005. |
| U2 | Underspecification | MEDIUM | research.md R3, contracts/cli.md; spec.md FR-015 | Behaviour for an invalid `TASKFLOW_NOW` value (exit 2) exists only in plan-level docs. | Add to FR-015 and Edge Cases. |
| U3 | Underspecification | LOW | research.md R5; spec.md Edge Cases | Data-file validation rules (unique ids, ids < next_id) only in research. | Mention in spec Edge Cases. |
| F1 | Inconsistency | LOW | spec.md US3 AS-1 vs contracts/cli.md | Spec says default order is "ascending id"; contract exposes `--sort id` explicitly. Compatible. | No change; note only. |

**Coverage Summary Table:**

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T005, T009, T011, T012 | |
| FR-002 | Yes | T011, T012 | |
| FR-003 | Yes | T005, T009, T011 | |
| FR-004 | Yes | T011, T013 | |
| FR-005 | Yes | T011, T012 | see U1 |
| FR-006 | Yes | T011, T012 | |
| FR-007 | Yes | T015, T016, T017 | |
| FR-008 | Yes | T018, T019 | |
| FR-009 | Yes | T018, T019 | |
| FR-010 | Yes | T018, T019 | |
| FR-011 | Yes | T018, T020 | |
| FR-012 | Yes | T006, T010, T014 | |
| FR-013 | Yes | T007, T014 | |
| FR-014 | Yes | T015, T016 | |
| FR-015 | Yes | T005, T008 | see U2 |
| FR-016 | Yes | T011, T013 | |
| SC-001 | Yes | T011, T015, T018 | |
| SC-002 | Yes | T022 | |
| SC-003 | Yes | T022 | |
| SC-004 | Yes | T006, T022 | |

**Constrained-Field Coverage:**

| Field | Canonical Location | Implementing Task IDs | Notes |
|-------|--------------------|-----------------------|-------|
| Task.id | data-model.md › Task | T009, T012 | consistent |
| Task.title | data-model.md › Task | T009 | consistent |
| Task.priority | data-model.md › Task | T009 | consistent |
| Task.status | data-model.md › Task / state machine | T009, T016 | consistent |
| Task.tags | data-model.md › Task | T009 | consistent |
| Task.created_at | data-model.md › Task | T008 | consistent |
| Task.updated_at | data-model.md › Task | T008 | consistent |

**Constitution Alignment Issues:** none (U1/U2 are flagged because of Principle I but are
resolvable by spec amendment).

**Unmapped Tasks:** T001–T004 (setup/harness), T023–T025 (harness/review) — infrastructure, expected.

**Metrics:** Requirements 20 (16 FR + 4 SC) · Tasks 25 · Coverage 100% · Ambiguity 0 ·
Duplication 0 · Critical 0

**Next Actions:** No CRITICAL issues. Apply U1–U3 as a spec revision before `/speckit-implement`
(remediation applied in the following commit, on the student's standing instruction).
