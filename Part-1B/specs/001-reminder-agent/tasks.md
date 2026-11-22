---
description: "Task list for 001-reminder-agent"
---

# Tasks: RemindMe – Natural-Language Reminder Agent

**Input**: Design documents from `/specs/001-reminder-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/extraction.schema.json

**Tests**: REQUIRED (constitution IV). Offline tests, the evaluation dataset and the harness are
written from the spec before implementation and locked by the integrity gate. The coding agent
implements `src/` and `prompts/` only.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [ ] T001 Create `pyproject.toml` (package `remindme`, src layout, console script `remindme = remindme.cli:main`, runtime dep `anthropic`, dev extras pytest, pytest-cov, ruff, jsonschema), `.env.example`, `.gitignore` entry for `.env`
- [ ] T002 [P] Create independent response JSON Schema (SCH-1/SCH-2) in `.harness/schema/response.schema.json`
- [ ] T003 [P] Create evaluation dataset (≥ 15 cases across normal, boundary, ambiguous, missing-info, malformed, adversarial; each with requirement refs and ground truth per data-model.md › Evaluation case) in `evals/dataset.json`
- [ ] T004 Create evaluators: structural (`.harness/evaluators/structural.py`), property/invariant INV-1…INV-10 + case properties (`properties.py`), semantic Layer-3 score (`semantic.py`), aggregate THR-1…THR-6 (`aggregate.py`)
- [ ] T005 Create evaluation runner with live (k = 3) and `--replay` modes, service-error separation, per-trial latency + p95 (SC-002) and structured failure feedback in `.harness/run_eval.py`
- [ ] T006 Create `.harness/run_harness.sh` (integrity → lint → offline tests → evaluation) and `.harness/lock_integrity.sh`; lock spec, tests, dataset, harness

---

## Phase 2: Foundational

- [ ] T007 [P] Write offline tests for request validation and GR-1 (data-model.md › Request.text, Request.now, Request.timezone, Request.reminders) in `tests/test_request.py`
- [x] T008 Create `RequestError`, `ServiceError` in `src/remindme/errors.py`
- [x] T009 Implement request parsing/validation and GR-1 precheck (data-model.md › Request.text, Request.now, Request.timezone, Request.reminders, ExistingReminder.id, ExistingReminder.due_at) in `src/remindme/request.py`
- [x] T010 Implement response construction and SCH validation (data-model.md › Response.intent … Response.reason) in `src/remindme/response.py`

---

## Phase 3: User Story 1 – Create (P1) 🎯 MVP

- [ ] T011 [P] [US1] Write offline tests for R-1…R-7 time resolution, recurrence and create invariants using a fake extractor in `tests/test_create.py`
- [x] T012 [US1] Implement R-1…R-7, R-10, R-11 (data-model.md › Response.due_at, Response.recurrence, Response.task) in `src/remindme/postprocess.py`
- [x] T013 [US1] Implement `handle()` orchestration in `src/remindme/agent.py`
- [x] T014 [US1] Write versioned system prompt with canary in `prompts/system_prompt.md` and implement `AnthropicExtractor` (model config per plan, structured output with contracts/extraction.schema.json, error mapping per research R6) in `src/remindme/llm.py`
- [x] T015 [US1] Implement CLI in `src/remindme/cli.py` and `src/remindme/__main__.py`

## Phase 4: User Story 2 – Reschedule / snooze / cancel (P1)

- [ ] T016 [P] [US2] Write offline tests for R-9, INV-2…INV-4, INV-9 in `tests/test_modify.py`
- [x] T017 [US2] Implement reschedule/snooze/cancel handling and target validation (data-model.md › Response.target_id, Response.snooze_minutes) in `src/remindme/postprocess.py`

## Phase 5: User Story 3 – Clarify (P1)

- [ ] T018 [P] [US3] Write offline tests for GR-4…GR-6 and INV-5 in `tests/test_clarify_safety.py`
- [x] T019 [US3] Implement clarify conversions and R-8 safe fallbacks (data-model.md › Response.missing, Response.question) in `src/remindme/postprocess.py`

## Phase 6: User Story 4 – Safety (P2)

- [ ] T020 [P] [US4] Extend `tests/test_clarify_safety.py` with GR-1, INV-6, INV-10 and ServiceError propagation tests
- [x] T021 [US4] Implement reject handling and canary detection (data-model.md › Response.reason) in `src/remindme/postprocess.py`

## Phase 7: Evaluation, repair, review

- [ ] T022 Run `.harness/run_harness.sh`; snapshot the first generation to `evidence/initial-generation/`
- [ ] T023 Feed structured failure evidence back to the coding agent; repair `src/` or `prompts/`; re-run the same harness
- [ ] T024 Snapshot `evidence/final-generation/`, write `evidence/eval-results.json` and `evidence/harness-log.md`
- [ ] T025 Human review: ACCEPT/REJECT, limitations, residual risks

## Phase 8: Tasks added after harness run-001 (coverage gap, see evidence/harness-log.md)

Harness run-001 failed the unit-test gate: coverage was 74.18% against the required 85%
(constitution "Engineering Constraints"). `cli.py` and `llm.py` were not covered because the
original task list had no test task for them. These two tasks were added. Test-only, threshold
unchanged.

- [x] T026 [P] Write offline tests for the default extractor with a stubbed `anthropic.Anthropic` client: request shape (model, structured output, no sampling params, canary in system prompt, delimited user text), env overrides, R6 service-error mapping (stop reasons, connection, 401/429/5xx), unparsable reply → clarify, in `tests/test_extractor_cli.py`
- [x] T027 [P] Write CLI tests (SCH-4 JSON stdout; exit 0/2/3; reminders file; default `--now`) in `tests/test_extractor_cli.py`

## Phase 9: FR-011 local provider (spec revision 2026-11-22)

- [x] T028 [P] Write offline tests for provider selection and `OllamaExtractor` (stubbed `urllib.request.urlopen`: request body, success, `done_reason` length, connection/HTTP/timeout errors, invalid body, unparsable content → clarify) in `tests/test_ollama.py`
- [x] T029 Implement `default_extractor()`, `OllamaExtractor` and use it from `handle()` per plan.md › Amendment in `src/remindme/llm.py` and `src/remindme/agent.py`
- [x] T030 Record provider/model in evaluation metadata in `.harness/run_eval.py`

- [x] T031 Isolate tests from provider environment variables (autouse fixture in `tests/conftest.py`); found by harness run-003, where `REMINDME_PROVIDER=ollama` leaked into 7 Anthropic-path tests

## Dependencies

Setup (T001–T006) → Foundational (T007–T010) → US1 (T011–T015) → US2, US3, US4 (parallel) → T022–T025.
All test/dataset tasks are completed and locked before the coding agent starts.

## Parallel Example

```text
T016 tests/test_modify.py ∥ T018 tests/test_clarify_safety.py
```

## Implementation Strategy

Spec-derived tests and evaluation first (locked) → coding agent implements → harness decides →
evidence-driven repair → human decision.
