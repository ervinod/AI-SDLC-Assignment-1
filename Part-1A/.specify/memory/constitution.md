# TaskFlow CLI Constitution

## Core Principles

### I. Specification Is the Source of Truth (NON-NEGOTIABLE)

- Every behaviour of the application MUST trace to a numbered functional requirement (FR-xxx) or
  acceptance scenario in the approved feature specification.
- Code MUST NOT implement behaviour that is absent from the specification. Ambiguities discovered
  during implementation MUST be resolved by amending the specification (via `/speckit-clarify` or
  a spec revision recorded in git history) before code changes.
- Acceptance criteria MUST be binary (pass/fail) and expressed with exact inputs, outputs, exit
  codes and persisted state so that tests can be derived mechanically.

Rationale: the assignment evaluates traceability from spec to code to validation.

### II. Deterministic Behaviour

- Given the same input arguments, the same data file and the same injected clock, every command
  MUST produce byte-identical stdout, stderr, exit code and data file.
- Sorting MUST be total (no ties left to insertion order or hash order); every sort MUST define a
  final tie-breaker on task id.
- The current time MUST be obtained through a single injectable clock so tests never depend on
  wall-clock time.

### III. Test-Derived Acceptance (NON-NEGOTIABLE)

- Every FR MUST be covered by at least one automated test whose name or docstring cites the FR id.
- Tests are authored from the specification, not from the implementation. Tests MUST NOT be
  deleted, skipped, marked xfail or have their assertions weakened in order to obtain a PASS.
- Line coverage of `src/` MUST be at least 90% as measured by `pytest-cov`.

### IV. Safe Persistence

- Task data MUST be stored as UTF-8 JSON at a path supplied by `--data` or the `TASKFLOW_DATA`
  environment variable (default `./tasks.json`).
- Writes MUST be atomic (write to a temporary file in the same directory, then `os.replace`). A
  failed command MUST leave the data file unchanged.
- A corrupt or schema-invalid data file MUST cause exit code 3 with a diagnostic on stderr; the
  application MUST NOT silently overwrite or "repair" it.

### V. Simplicity and Minimal Dependencies

- Runtime code MUST use only the Python standard library (Python >= 3.12).
- Development/harness dependencies are limited to: pytest, pytest-cov, ruff, bandit.
- No network access, no `eval`/`exec`, no `pickle`, no `shell=True` subprocess calls.

## Engineering Constraints

- Lint gate: `ruff check` and `ruff format --check` MUST report zero violations.
- Security gate: `bandit -r src` MUST report zero findings of severity MEDIUM or higher.
- Test gate: `pytest` MUST pass with zero failures and coverage >= 90%.
- Performance: any single command on a data file of 1,000 tasks MUST complete in under 1 second
  on a developer laptop (verified by a test).
- Exit codes are part of the contract: 0 success, 1 not found, 2 usage/validation error,
  3 data-file error.
- Secrets: the project handles no credentials; no secret, token or `.env` file may be committed.

## Development Workflow and Quality Gates

- Flow: constitution → specify → clarify → plan → tasks → analyze → implement → harness.
- The first implementation produced by the coding agent MUST be snapshotted to
  `evidence/initial-generation/` before any harness-driven repair.
- The harness (`.harness/run_harness.sh`) runs lint, security and test gates in that order, records
  stdout/stderr per gate to `evidence/harness-results/run-<n>/`, and returns a non-zero exit code if
  any gate fails.
- The coding agent MUST NOT edit harness scripts, gate thresholds, the specification or tests to
  obtain a PASS. Failures are repaired in `src/` unless the failure reveals a genuine spec defect,
  which is fixed upstream in the spec and documented in `evidence/harness-log.md`.
- After an automated PASS a human reviewer records ACCEPT or REJECT in `evidence/harness-log.md`.

## Governance

- This constitution supersedes any other guidance for this project. Plans and tasks MUST include a
  Constitution Check that references these principles.
- Amendments require: a written reason, a version bump (semantic versioning: MAJOR for principle
  removal/redefinition, MINOR for additions, PATCH for wording) and a git commit.
- Reviewers verify compliance at the human review step; any violation is grounds for REJECT.

**Version**: 1.0.0 | **Ratified**: 2026-11-22 | **Last Amended**: 2026-11-22
