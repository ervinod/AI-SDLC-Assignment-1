---
description: "Task list for 001-task-cli"
---

# Tasks: TaskFlow – Smart Todo & Task CLI

**Input**: Design documents from `/specs/001-task-cli/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: REQUIRED (constitution III — test-derived acceptance). Test tasks are authored from the
spec and contracts *before* implementation and are frozen by the harness integrity gate; the
coding agent implements `src/` only.

**Organization**: grouped by user story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create `pyproject.toml` with package `taskflow` (src layout), console script `taskflow = taskflow.cli:main`, Python ≥ 3.12, dev extras pytest, pytest-cov, ruff, bandit
- [ ] T002 [P] Create harness configuration `.harness/ruff.toml` and `.harness/bandit.yaml` (lint + SAST gates per constitution "Engineering Constraints")
- [ ] T003 [P] Create harness runner `.harness/run_harness.sh` (gates: integrity → lint → security → tests; per-run evidence under `evidence/harness-results/run-<n>/`; summary JSON; non-zero exit on any failure)
- [ ] T004 Create `.harness/integrity.sha256` lock of spec, tests and harness config, and the integrity gate that verifies it (enforces "agent must not weaken tests/spec/harness")

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T005 [P] Write unit tests for validation of `data-model.md` Task.title, Task.priority, Task.tags and the clock (FR-001, FR-003, FR-015) in `tests/unit/test_models.py`
- [ ] T006 [P] Write unit tests for store load/validate/atomic save (FR-012, exit 3, SC-004) in `tests/unit/test_store.py`
- [ ] T007 Create error hierarchy with exit codes (FR-013) in `src/taskflow/errors.py`
- [ ] T008 [P] Implement `Clock` honouring `TASKFLOW_NOW` (FR-015, data-model.md Task.created_at / Task.updated_at) in `src/taskflow/clock.py`
- [ ] T009 [P] Implement `Task` dataclass, `Priority`/`Status` enums, title and tag validation (data-model.md Task.id, Task.title, Task.priority, Task.status, Task.tags) in `src/taskflow/models.py`
- [ ] T010 Implement `JsonStore` with schema validation and atomic `os.replace` writes (data-model.md Task store) in `src/taskflow/store.py`

**Checkpoint**: foundation ready.

---

## Phase 3: User Story 1 – Create, view, edit and delete tasks (P1) 🎯 MVP

**Goal**: CRUD with persistence. **Independent test**: contract tests US1 pass.

- [ ] T011 [P] [US1] Write contract tests for US1 acceptance scenarios 1–6 and edge cases (titles, tags, ids, nothing-to-update, not-found) in `tests/contract/test_cli_crud.py`
- [ ] T012 [US1] Implement `TaskService.add/get/update/delete` with id allocation from `next_id` (FR-001–FR-006, data-model.md Task.id) in `src/taskflow/service.py`
- [ ] T013 [P] [US1] Implement JSON task rendering and success messages (FR-004, FR-016) in `src/taskflow/formatting.py`
- [ ] T014 [US1] Implement argparse CLI `add/show/update/delete`, `--data`/`TASKFLOW_DATA` resolution and error→exit-code mapping (FR-012, FR-013) in `src/taskflow/cli.py` and `src/taskflow/__main__.py`

---

## Phase 4: User Story 2 – Status workflow (P1)

**Goal**: guarded transitions. **Independent test**: contract tests US2 pass.

- [ ] T015 [P] [US2] Write contract tests for every allowed and a representative set of forbidden transitions, including same-status and re-open (FR-007, FR-014) in `tests/contract/test_cli_status.py`
- [ ] T016 [US2] Implement transition table and `TaskService.transition` (data-model.md Task.status state machine) in `src/taskflow/service.py`
- [ ] T017 [US2] Add `status ID NEW` sub-command in `src/taskflow/cli.py`

---

## Phase 5: User Story 3 – Filter and sort (P2)

**Goal**: list with tag/status filters and priority sort. **Independent test**: contract tests US3 pass.

- [ ] T018 [P] [US3] Write contract tests for list default order, priority sort with ties, AND tag filter, status filter, empty result, `--json` (FR-008–FR-011) in `tests/contract/test_cli_list.py`
- [ ] T019 [US3] Implement `TaskService.list(tags, status, sort)` (FR-008–FR-010) in `src/taskflow/service.py`
- [ ] T020 [US3] Implement human tab-separated and JSON list rendering (FR-011) in `src/taskflow/formatting.py`
- [ ] T021 [US3] Add `list` sub-command in `src/taskflow/cli.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T022 [P] Write determinism (SC-003), no-mutation-on-failure (SC-004) and 1,000-task performance (SC-002) tests in `tests/contract/test_cli_nonfunctional.py`
- [ ] T023 Run `.harness/run_harness.sh`; snapshot first generation to `evidence/initial-generation/`; record outcome in `evidence/harness-log.md`
- [ ] T024 Repair any harness failures from recorded evidence (src only), re-run the same gates, snapshot to `evidence/final-generation/`
- [ ] T025 Human review: record ACCEPT/REJECT, limitations and justification in `evidence/harness-log.md`

---

## Dependencies & Execution Order

- Setup (T001–T004) → Foundational (T005–T010) → US1 (T011–T014) → US2 (T015–T017) and US3
  (T018–T021) → Polish (T022–T025).
- US2 and US3 depend only on US1's service/CLI skeleton and can proceed in parallel.
- All test-writing tasks (T005, T006, T011, T015, T018, T022) precede the corresponding
  implementation tasks and are locked by T004 before `/speckit-implement` runs.

## Parallel Example: User Story 1

```text
T011 (tests/contract/test_cli_crud.py)  ∥  T013 (src/taskflow/formatting.py)
```

## Implementation Strategy

1. Write and lock all specification-derived tests (red).
2. Hand spec, plan, data model, contract and tasks to the coding agent; it implements `src/` (green).
3. Harness decides; failures are fed back as evidence; repair; re-run; human decision.
