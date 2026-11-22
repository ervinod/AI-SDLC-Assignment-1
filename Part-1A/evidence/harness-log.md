# Harness Log — Part 1A (TaskFlow CLI, feature 001-task-cli)

## 1. Specification → generation context

| Step | Artifact | Commit message (git log) |
|------|----------|--------------------------|
| constitution | `.specify/memory/constitution.md` v1.0.0 | docs(1A): ratify constitution v1.0.0 |
| specify | `specs/001-task-cli/spec.md` (FR-001…FR-016, SC-001…SC-004) | docs(1A): feature spec … 2 open clarifications |
| clarify | spec.md › Clarifications (FR-009 AND-filter, FR-014 re-open) | docs(1A): resolve FR-009 and FR-014 |
| plan | plan.md, research.md, data-model.md, contracts/cli.md, quickstart.md | docs(1A): technical plan … |
| tasks | tasks.md (T001–T025) | docs(1A): dependency-ordered tasks.md |
| analyze | analysis-report.md (0 critical; U1–U3 fixed in spec) | docs(1A): /speckit-analyze report; amend FR-005, FR-015 |
| tests + harness | tests/ (102 tests), .harness/, integrity lock | test(1A): spec-derived tests + harness gates … |
| implement | src/taskflow/ by a separate coding agent | feat(1A): initial coding-agent generation … |

The coding agent's prompt, the artifacts it received and the interpretations it reported are in
`evidence/initial-generation/coding-agent-context.md`. It could not see `tests/` or `.harness/`.

## 2. Harness gates

| Gate | Tool / command | Pass condition |
|------|----------------|----------------|
| 0 integrity | `shasum -a 256 -c .harness/integrity.sha256` | spec, tests, harness config unchanged since lock |
| 1 lint | `ruff check` + `ruff format --check` (`.harness/ruff.toml`) | zero violations |
| 2 security | `bandit -c .harness/bandit.yaml -r src -ll` | no MEDIUM/HIGH findings |
| 3 tests | `pytest --cov=src/taskflow --cov-fail-under=90` | 0 failures, coverage ≥ 90% |

Each run writes `evidence/harness-results/run-NNN/` (per-gate stdout/stderr, `junit.xml`,
`summary.json`, `feedback.md` = structured feedback for the coding agent).

## 3. Harness executions

### run-001 — 2026-11-22 — initial generation — **PASS**

| Gate | Result | Evidence |
|------|--------|----------|
| integrity | PASS | 25 locked files OK |
| lint | PASS | "All checks passed!", 19 files already formatted |
| security | PASS | bandit: 0 Low / 0 Medium / 0 High |
| tests | PASS | 102 passed in 0.75 s; coverage 93.32% (threshold 90%) |

Uncovered lines (for information): `__main__.py` (entry shim), `store.py` OS-error branches.

## 4. Failure-and-repair cycles

**None occurred.** The first generation passed every gate on its first harness execution, so no
failure evidence was fed back and no repair was made. `evidence/final-generation/src` is
byte-identical to `evidence/initial-generation/src` (`diff -r` reports no differences). Following
the assignment rules, no failure was manufactured against the application.

## 5. Harness self-test (validating the harness, NOT the application history)

To confirm that each gate can actually fail, the harness was run on four throw-away copies of the
project, each with one deliberately planted defect. These runs did not happen in the project's own
history; outputs are in `evidence/harness-selftest/`.

| Planted defect | integrity | lint | security | tests | Overall |
|----------------|-----------|------|----------|-------|---------|
| Priority sort tie-breakers removed (`service.py`) | PASS | PASS | PASS | **FAIL** (2 tests) | FAIL |
| `subprocess.run(..., shell=True)` added | PASS | **FAIL** | **FAIL** | PASS | FAIL |
| Unused `import os` added | PASS | **FAIL** | PASS | PASS | FAIL |
| Test assertion weakened (`== [4,5,2,3,1]` → `len(...) == 5`) | **FAIL** | PASS | PASS | PASS | FAIL |

The last row matters most. Once the assertion was weakened, the tests passed, and only the
integrity gate caught it.

## 6. Human review

> **To be completed by the student. Neither the harness nor the AI agent fills this in.**

- Decision (ACCEPT / REJECT):
- Reviewed by / date:
- Justification:
- Known limitations:
- Residual risks:
