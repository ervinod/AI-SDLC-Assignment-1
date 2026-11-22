# Implementation Plan: TaskFlow – Smart Todo & Task CLI

**Branch**: `001-task-cli` | **Date**: 2026-11-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-task-cli/spec.md`

## Summary

A single-user command-line task manager (`taskflow`) that supports task CRUD, tag filtering
(AND semantics), priority sorting with a total order, and a guarded status state machine. Data is
persisted atomically to a versioned JSON file. The design separates a pure domain core (validation,
state machine, sorting, filtering) from thin I/O layers (JSON store, argparse CLI) so that every
functional requirement can be tested deterministically through an injected clock.

## Technical Context

**Language/Version**: Python ≥ 3.12 (standard library only at runtime)

**Primary Dependencies**: none at runtime; dev/harness: pytest, pytest-cov, ruff, bandit

**Storage**: Local JSON file (`--data` > `TASKFLOW_DATA` > `./tasks.json`), atomic replace

**Testing**: pytest — unit tests for the domain core, contract tests that execute the CLI
entry point (`main(argv)`) and assert exact stdout/stderr/exit code/data file

**Target Platform**: macOS / Linux terminal

**Project Type**: CLI

**Performance Goals**: any command on 1,000 tasks < 1 s (SC-002)

**Constraints**: deterministic output (SC-003); failed commands never modify the data file (SC-004)

**Scale/Scope**: ≤ 10,000 tasks, single process

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan complies | Status |
|-----------|-----------------------|--------|
| I. Spec is source of truth | Every module maps to FR ids (see contracts/cli.md); no extra features | PASS |
| II. Deterministic behaviour | Injectable `Clock` (FR-015); total sort order with id tie-breaker; JSON dumped with `sort_keys=True` | PASS |
| III. Test-derived acceptance | Tests cite FR/AS ids; coverage ≥ 90% enforced by harness via `--cov-fail-under=90` | PASS |
| IV. Safe persistence | `tempfile.NamedTemporaryFile` in same dir + `os.replace`; load validates schema → exit 3 | PASS |
| V. Simplicity | stdlib only; no eval/exec/pickle/shell | PASS |
| Engineering constraints | Harness gates: ruff check + format, bandit (MEDIUM+), pytest+cov | PASS |

Post-design re-check (after Phase 1): PASS — no new dependencies or violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-task-cli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── tasks.md            # created by /speckit-tasks
```

### Source Code (repository root = Part-1A/)

```text
src/taskflow/
├── __init__.py
├── __main__.py      # python -m taskflow
├── errors.py        # TaskFlowError hierarchy carrying exit codes (FR-013)
├── clock.py         # Clock: now() honouring TASKFLOW_NOW (FR-015)
├── models.py        # Task dataclass, enums, validation (FR-001, FR-003)
├── service.py       # TaskService: CRUD, transitions, filter, sort (FR-002, FR-005..FR-010, FR-014)
├── store.py         # JsonStore: load/validate/atomic save (FR-012, constitution IV)
├── formatting.py    # human/JSON output (FR-004, FR-011, FR-016)
└── cli.py           # argparse wiring, main(argv) -> int

tests/
├── conftest.py
├── unit/            # models, service, store, clock
└── contract/        # CLI end-to-end via main(argv)

.harness/
├── run_harness.sh   # runs gates in order, records evidence
├── ruff.toml
└── bandit.yaml

pyproject.toml       # package metadata, entry point `taskflow`, pytest config
```

**Structure Decision**: single-project layout with a `src/` package; harness configuration lives in
`.harness/` so the coding agent's source tree and the validation controls are physically separate.

## Complexity Tracking

No constitution violations to justify.
