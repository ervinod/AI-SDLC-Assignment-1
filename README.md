# Assignment 1: Spec-Driven Development & Harness Engineering

Course: AI-Augmented Software Development Life Cycle (SE ZG534).

| Part | Application | Kind | Folder |
|------|-------------|------|--------|
| 1A | **TaskFlow**: Smart Todo & Task CLI (CRUD, tag filter, priority sort, status transitions, JSON persistence) | deterministic | [`Part-1A/`](Part-1A/) |
| 1B | **RemindMe**: natural-language reminder agent (create / reschedule / snooze / cancel / clarify / reject) using Claude | non-deterministic | [`Part-1B/`](Part-1B/) |

Both parts follow the GitHub Spec Kit flow (`specify init --integration claude`):
constitution → specify → clarify → plan → tasks → analyze → implement → harness → repair → human
decision. Each step is a separate git commit, so `git log` shows the order of the steps.

## Where to look

| What | Part 1A | Part 1B |
|------|---------|---------|
| Constitution | `Part-1A/.specify/memory/constitution.md` | `Part-1B/.specify/memory/constitution.md` |
| Spec (+ Clarifications) | `Part-1A/specs/001-task-cli/spec.md` | `Part-1B/specs/001-reminder-agent/spec.md` (schema SCH, invariants INV, guardrails GR, threshold THR) |
| Plan / research / data model / contracts | `Part-1A/specs/001-task-cli/` | `Part-1B/specs/001-reminder-agent/` |
| Tasks + analyze report | `tasks.md`, `analysis-report.md` | `tasks.md`, `analysis-report.md` |
| Source | `Part-1A/src/taskflow/` | `Part-1B/src/remindme/`, `Part-1B/prompts/` |
| Tests | `Part-1A/tests/` (spec-derived, 102 tests) | `Part-1B/tests/` (offline, fake model) |
| Evaluation dataset | – | `Part-1B/evals/dataset.json` (24 cases) |
| Harness | `Part-1A/.harness/` | `Part-1B/.harness/` |
| Evidence + harness log | `Part-1A/evidence/` | `Part-1B/evidence/` |

## Setup

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
cd Part-1A && uv venv && uv pip install -e ".[dev]" && cd ..
cd Part-1B && uv venv && uv pip install -e ".[dev]" && cd ..
```

## Run the Part 1A harness

```bash
Part-1A/.harness/run_harness.sh --label "my run"
```

The gates run in this order: integrity (SHA-256 lock of the spec, tests and harness) → lint (ruff) →
security (bandit) → tests (pytest, coverage ≥ 90%). Each run writes its results to
`Part-1A/evidence/harness-results/run-NNN/`.

Try the CLI:

```bash
cd Part-1A
export TASKFLOW_DATA=/tmp/demo.json
.venv/bin/taskflow add "Ship report" --priority high --tag work
.venv/bin/taskflow status 1 in_progress
.venv/bin/taskflow list --sort priority
```

## Run the Part 1B harness

Part 1B can use either a free local model or the Anthropic API (spec FR-011).

Option 1: local model, no key needed.

```bash
brew install ollama && ollama serve        # keep ollama serve running in its own terminal
ollama pull llama3.2:3b
cd Part-1B && REMINDME_PROVIDER=ollama .harness/run_harness.sh --label "local model run"
```

Option 2: Anthropic API. Use your own key and never commit it:

```bash
cd Part-1B
cp .env.example .env    # then edit .env and set ANTHROPIC_API_KEY
.harness/run_harness.sh --label "my run"
```

The gates run in this order: integrity → lint → offline unit tests (coverage ≥ 85%) → live
evaluation. The live evaluation runs 24 cases × 3 trials and applies three layers of checks:
structural, then invariants/properties, then semantic. Each run writes `raw-outputs.json`,
`eval-results.json` and `feedback.md` to `evidence/eval-runs/run-NNN/`.

To re-score a recorded run without an API key:

```bash
.venv/bin/python .harness/run_eval.py --replay evidence/eval-runs/run-NNN/raw-outputs.json
```

## Secrets

`.env` is gitignored. No API key, credential or token is committed or written to the evidence files.

## AI use

The specs, code, tests, harness and evaluation dataset were produced with AI assistance (Claude Code)
through the Spec Kit workflow. The assignment policy allows this. The coding agent that implemented
`src/` was a separate agent that worked only from the Spec Kit artifacts and could not see the tests
or the harness. The human review decisions in each `evidence/harness-log.md` and the reflection
report are the student's own work.
