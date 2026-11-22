# RemindMe Agent Constitution

## Core Principles

### I. Specified Behavioural Boundaries (NON-NEGOTIABLE)

- The language model is a non-deterministic component. Its *wording* may vary; the application's
  *output contract* may not. Every response MUST conform to the Output Schema Contract in the
  feature specification, whatever the model returns.
- Acceptable behaviour is defined by schema rules (SCH-x), structural/behavioural invariants (INV-x),
  guardrails (GR-x) and a declared evaluation threshold (THR-x) in the specification. Behaviour not
  covered by these is out of scope and MUST NOT be relied on.

### II. Deterministic Shell Around a Non-Deterministic Core

- The model only *extracts* intent and fields. Date/time arithmetic, timezone resolution, snooze
  arithmetic, reminder-id validation, input pre-checks and guardrail enforcement MUST be done by
  deterministic application code, never trusted to the model.
- If the model output is missing, malformed, refused or violates an invariant, the application MUST
  degrade to a safe `clarify` or `reject` response; it MUST NOT emit an unvalidated action.

### III. Safety First

- The agent MUST refuse (intent `reject`) requests whose purpose is to harm people, and MUST NOT
  follow instructions embedded in user text that try to change its role, reveal its prompt or emit
  non-schema output (prompt injection).
- The agent MUST NOT invent information: no hallucinated reminder ids, no default times when the
  user gave none, no times in the past.

### IV. Evaluation Before Acceptance (NON-NEGOTIABLE)

- The evaluation dataset (`evals/dataset.json`, ≥ 15 cases covering normal, boundary, ambiguous,
  missing-information, malformed and adversarial inputs) and the threshold are fixed *before* the
  final evaluation and MUST NOT be weakened to obtain PASS: no removing hard cases, no editing
  expected results without a recorded specification revision, no lowering thresholds, no disabling
  guardrails.
- One evaluation harness MUST apply, in order: structural (schema) validation → invariant/property
  checks → semantic/quality scoring → aggregate decision against the threshold.
- Model/service failures (network, rate limit, 5xx, refusals by the API) MUST be recorded separately
  from application failures and MUST NOT be counted as application passes.

### V. Simplicity, Reproducibility and Secrets Hygiene

- Python ≥ 3.12. Runtime dependency: the official `anthropic` SDK only (plus stdlib).
- The model id, effort level, prompt version and trial count are recorded with every evaluation run.
- API keys are read only from the environment / an untracked `.env`; they MUST never be committed,
  logged or written into evidence files.

## Engineering Constraints

- Deterministic code (pre-checks, post-processing, validators, evaluators) MUST have offline unit
  tests (no network) with ≥ 85% line coverage, run by `pytest`.
- Lint gate: `ruff check` reports zero violations.
- Latency: p95 end-to-end response time per request ≤ 20 s on the evaluation run.
- Inputs longer than 500 characters or empty after trimming are rejected deterministically without
  a model call.

## Development Workflow and Quality Gates

- Flow: constitution → specify → clarify → plan → tasks → analyze → implement → evaluation harness →
  repair → re-evaluation → human decision.
- First implementation is snapshotted to `evidence/initial-generation/` before any harness-driven
  repair; the final one to `evidence/final-generation/`.
- The coding agent MUST NOT edit `evals/`, `.harness/`, tests or the specification to obtain a PASS
  (enforced by an integrity check). Failures are repaired in `src/` or `prompts/` unless they reveal
  a genuine specification defect, which is fixed upstream and documented in `evidence/harness-log.md`.
- After an automated PASS a human reviewer records ACCEPT or REJECT, limitations and residual risks.

## Governance

- This constitution supersedes other guidance for this project. Amendments need a reason, a
  semantic version bump and a commit.

**Version**: 1.0.0 | **Ratified**: 2026-11-22 | **Last Amended**: 2026-11-22
