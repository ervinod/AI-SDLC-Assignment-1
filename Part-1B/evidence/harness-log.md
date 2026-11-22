# Harness Log — Part 1B (RemindMe agent, feature 001-reminder-agent)

## 1. Model / configuration (no secrets)

| Item | Value |
|------|-------|
| Provider | `anthropic` (default) or `ollama` (local, FR-011) — recorded per run in `eval-results.json` › meta |
| Model | `claude-opus-5-5` (env `REMINDME_MODEL`) or local `llama3.2:3b` (env `REMINDME_OLLAMA_MODEL`) |
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

### Spec revision — FR-011 local provider (constitution 1.1.0)

No Anthropic API key is available to the student, so a local-model provider (Ollama, no key) was
added through the SDD flow: constitution amendment, spec FR-011 with a Revision History entry,
a plan Amendment section, tasks T028–T030, offline tests `tests/test_ollama.py` (red before
implementation), and a re-lock. The coding agent then implemented T029. The dataset, expected
results and thresholds were **not** changed.

### run-003 — 2026-11-22 — after T029, `REMINDME_PROVIDER=ollama` — **FAIL**

| Gate | Result | Evidence |
|------|--------|----------|
| integrity | PASS | 29 files |
| lint | PASS | |
| unit_tests | **FAIL** | 97 passed, **7 failed** (all in `tests/test_extractor_cli.py`) |
| evaluation | INCONCLUSIVE | 66/72 `service_error: could not connect to the Ollama server` (Ollama not installed yet) |

**Failure analysis.** The 7 failing tests cover the Anthropic path and assume the default
provider. The harness ran with `REMINDME_PROVIDER=ollama` exported, and the tests inherited it,
so `handle()` chose the Ollama extractor. With the variable unset, all 104 tests pass. The
defect is in the tests (they depend on the caller's environment), not in `src/`.

**Repair.** T031 adds an autouse fixture in `tests/conftest.py` that clears all provider-related
variables before every test. This makes the tests deterministic and removes no assertions.
Re-locked.

### run-004 — 2026-11-22 — after T031, same environment — integrity/lint/unit tests **PASS**, evaluation INCONCLUSIVE

| Gate | Result | Evidence |
|------|--------|----------|
| integrity | PASS | |
| lint | PASS | |
| unit_tests | PASS | 104 passed; coverage 91% |
| evaluation | INCONCLUSIVE | Ollama server not running (local model not downloaded yet) |

### run-005+ — live evaluation with local model — *pending*

Requires `brew install ollama`, `ollama serve`, `ollama pull llama3.2:3b`, then
`REMINDME_PROVIDER=ollama .harness/run_harness.sh --label "live evaluation"`.

## 5. Human review

> **To be completed by the student. Neither the harness nor the AI agent fills this in.**

- Decision (ACCEPT / REJECT):
- Reviewed by / date:
- Justification:
- Known limitations:
- Residual risks:
