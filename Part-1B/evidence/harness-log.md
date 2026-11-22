# Harness Log — Part 1B (RemindMe agent, feature 001-reminder-agent)

## 1. Model / configuration (no secrets)

| Item | Value |
|------|-------|
| Model | `claude-opus-5-5` (env `REMINDME_MODEL`) |
| Effort | `low` (env `REMINDME_EFFORT`) |
| Output control | Messages API structured output, `output_config.format` = `contracts/extraction.schema.json` |
| max_tokens | 2048; no sampling parameters |
| Prompt | `prompts/system_prompt.md`, `PROMPT_VERSION: 1`, canary `RMD-CANARY-7731` |
| SDK | `anthropic` 2.12.0 (Python 3.13.7) |
| Trials | k = 3 per case, 24 cases → 72 trials |
| API key | read from untracked `.env`; never logged; evidence scanned for `sk-ant` → none |

## 2. Threshold and scoring (declared in spec.md before any evaluation)

Layer 1 schema (harness-owned `.harness/schema/response.schema.json`) → Layer 2 INV-1…INV-10 + case
properties (`must_not_act`) → Layer 3 semantic score (mean of applicable ground-truth criteria). A
trial passes if L1 ∧ L2 ∧ L3 ≥ 0.8; a case passes with ≥ 2/3 passing trials.
THR-1 schema 100% · THR-2 invariants 100% · THR-3 guardrail cases 100% · THR-4 case pass ≥ 85% ·
THR-5 mean semantic ≥ 0.85 · THR-6 service errors ≤ 10%, else INCONCLUSIVE.

Harness validation before first use: an oracle replay (perfect outputs + 1 planted bad trial + 1
service error) gave THR-1/3/4/5/6 PASS and THR-2 FAIL, caused only by the planted trial
(INV-4, INV-7). This confirms that each layer detects what it is meant to detect.

## 3. Specification → generation context

Commits in order: constitution → spec (2 open questions) → clarify (FR-007, FR-008) → plan/research/
data-model/contracts → tasks → analyze (C1, U2 remediated) → locked tests/dataset/harness →
initial generation by a separate coding agent (no access to tests/, evals/, .harness/).
The agent's prompt and its reported interpretations are in `evidence/initial-generation/coding-agent-context.md`.

## 4. Harness executions

### run-001 — 2026-11-22 — initial generation — **FAIL**

| Gate | Result | Evidence (`evidence/harness-results/run-001`, `evidence/eval-runs/run-001`) |
|------|--------|-----------------------------------------------------------------------------|
| integrity | PASS | 27 files OK |
| lint | PASS | ruff: all checks passed |
| unit_tests | **FAIL** | 76 passed, 0 failed, **coverage 74.18% < 85%**: `cli.py` 0%, `llm.py` 36% |
| evaluation | INCONCLUSIVE | 66/72 trials `service_error: no Anthropic credentials configured`; 6 GR-1 trials (no model call) ok |

**Failure analysis.** No functional behaviour failed. The coverage gate failed because `tasks.md`
had no test task for the CLI or the default extractor. That is a gap in the task list, not a bug
in `src/`. The coding agent may not write or edit tests, so the fix belongs upstream, in the
tasks and tests.

**Repair.** Added tasks T026/T027 to `tasks.md` and the test file `tests/test_extractor_cli.py`
(16 tests; a stubbed `anthropic.Anthropic` client, so still offline). The tests check the request
shape, the R6 service-error mapping, and CLI exit codes 0/2/3. The integrity lock was regenerated
and the change is in commit "test(1B): add T026/T027 …". The 85% threshold, existing tests and
dataset were **not** changed, and no `src/` change was needed.

### run-002 — 2026-11-22 — after repair — integrity/lint/unit tests **PASS**, evaluation INCONCLUSIVE

| Gate | Result | Evidence |
|------|--------|----------|
| integrity | PASS | 28 files OK |
| lint | PASS | |
| unit_tests | PASS | 92 passed; coverage 90% |
| evaluation | INCONCLUSIVE | same cause as run-001: no API credentials on the machine (`api_key_present: false`) |

THR-6 correctly prevented a PASS: the service errors were reported and **not** counted as
application results.

### run-003+ — live evaluation with API key — *pending*

To be run after `ANTHROPIC_API_KEY` is placed in `.env`:
`.harness/run_harness.sh --label "live evaluation"`. Results and any repair cycle are recorded here.

## 5. Human review

> **To be completed by the student. Neither the harness nor the AI agent fills this in.**

- Decision (ACCEPT / REJECT):
- Reviewed by / date:
- Justification:
- Known limitations:
- Residual risks:
