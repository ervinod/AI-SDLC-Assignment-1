# Implementation Plan: RemindMe – Natural-Language Reminder Agent

**Branch**: `001-reminder-agent` | **Date**: 2026-11-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-reminder-agent/spec.md`

## Summary

A deterministic shell around one structured LLM call. The model (Claude, via the Anthropic SDK with
JSON-schema-constrained output) only *extracts* an `Extraction` object: the intent, the task text and
a symbolic `time_spec` (offset minutes / day offset / weekday / explicit date / clock time). Python
code does all date arithmetic, timezone resolution, snooze arithmetic, target validation and
guardrail enforcement (constitution II), producing the final `Response` defined by SCH-1…SCH-4. A
separate evaluation harness runs the dataset through the real model k = 3 times per case and scores
it in three layers (structural → property → semantic) against the declared threshold.

## Technical Context

**Language/Version**: Python ≥ 3.12 (developed on 3.13)

**Primary Dependencies**: runtime `anthropic` (official SDK); dev/harness `pytest`, `pytest-cov`,
`ruff`, `jsonschema` (harness-only, independent schema validation)

**Model configuration**: `claude-opus-5-5`, `output_config.effort = "low"` (simple extraction),
`output_config.format` = JSON schema of `Extraction`, `max_tokens = 2048`, no sampling parameters
(this model does not accept them). Overridable via `REMINDME_MODEL` / `REMINDME_EFFORT`; recorded in
every evaluation run.

**Storage**: none (stateless; reminders are passed in the request)

**Testing**: offline pytest for deterministic code using a fake extractor; evaluation harness
(`.harness/run_eval.py`) for model behaviour

**Target Platform**: macOS / Linux CLI + importable Python API

**Project Type**: CLI / library

**Performance Goals**: p95 ≤ 20 s per request (SC-002)

**Constraints**: no secrets in repo/evidence; model/service errors separated from app failures

## Constitution Check

| Principle | Compliance | Status |
|-----------|------------|--------|
| I. Specified boundaries | Response built and validated in code against SCH; INV enforced in post-processing | PASS |
| II. Deterministic shell | Model returns a symbolic `time_spec`; Python resolves dates/tz/snooze; invalid model output → safe `clarify`/`reject` | PASS |
| III. Safety | GR-1 pre-check before the model call; GR-2/GR-3 in prompt + canary check; GR-4…6 enforced in code | PASS |
| IV. Evaluation before acceptance | Dataset + THR frozen and hash-locked before the first evaluation run | PASS |
| V. Simplicity / secrets | 1 runtime dependency; key only from env/.env (gitignored); evidence stores no headers or keys | PASS |

Post-design re-check: PASS.

## Public Contracts

### Python API (used by CLI, tests and harness)

```python
from remindme.agent import handle, ServiceError, RequestError
response: dict = handle(request: dict, extractor: Callable[[dict], dict] | None = None)
```

- `request` per FR-001. Invalid request (missing keys, unparsable `now` or `now` without offset,
  unknown timezone, `reminders` not a list of `{id, task, due_at}`) → `RequestError`; no model call.
- GR-1 (empty after trimming / > 500 chars) → returns a `reject` response with `reason`
  `"input is empty"` / `"input is longer than 500 characters"` **without** calling `extractor`.
- `extractor(request) -> dict` returns an `Extraction` (contracts/extraction.schema.json).
  Default = `remindme.llm.AnthropicExtractor()`.
- `ServiceError` is raised when the extractor raises `ServiceError` (API/network errors, HTTP 4xx/5xx,
  `stop_reason` `refusal` or `max_tokens`). `handle` never fabricates a response in that case (FR-010).
- An extraction that is not a dict / violates the Extraction schema is NOT a service error: it is
  converted to a safe `clarify` (R-8).

### CLI

`remindme [--now ISO] [--tz ZONE] [--reminders FILE] TEXT` → response JSON on stdout (indent 2,
sorted keys), exit 0. `--now` defaults to the current time in `--tz` (default `UTC`). Exit 2 on
`RequestError`, exit 3 on `ServiceError` (message on stderr).

### Resolution rules (deterministic, `postprocess.py`)

- **R-1** `time_spec.offset_minutes` set → `due = now + offset`.
- **R-2** otherwise the date part is: `date` (explicit) > `day_offset` (today + n) > `weekday` (first
  such day strictly after today's local date).
- **R-3** `time` with no date part → FR-007 next occurrence (today if after `now`, else tomorrow).
- **R-4** a date part without `time` → GR-4 clarify (`missing ["time"]`). No time information at all
  for create/reschedule → clarify (`missing ["time"]`).
- **R-5** localise with `zoneinfo.ZoneInfo(timezone)` (DST-aware); format
  `YYYY-MM-DDTHH:MM:SS±HH:MM`; seconds = 00 except for offset-based times, which keep `now`'s seconds.
- **R-6** `due <= now` → clarify (`time`) (GR-5); `due > now + 365 days` → clarify (`time`) (INV-7).
- **R-7** recurrence `weekdays`: if the resolved date is Saturday/Sunday move it forward to Monday.
  Recurrence other than `none` with a time already passed today → next valid day (FR-008).
- **R-8** safe fallbacks: invalid extraction, intent/field mismatch, `target_id` not in the request
  (GR-6/INV-9), canary token in any string (INV-10) → `clarify` with the relevant `missing` item
  (`target` for target problems, `time` for time problems, else `task`) and a fixed question; if
  the extraction intent was `reject`, keep `reject` with its reason (or `"request refused"`).
- **R-9** `snooze` → `due_at = target.due_at + snooze_minutes` (snooze_minutes must be 1–1440, else
  clarify `time`); `reschedule` uses R-1…R-6.
- **R-10** model-provided `missing` items are de-duplicated and ordered `task, time, target`.
- **R-11** the final response is validated against SCH in code before being returned; strings longer
  than the SCH limits are truncated on a word boundary (task 120, question/reason 200).

## Amendment: local provider (FR-011)

- `remindme.llm.default_extractor()` returns `OllamaExtractor()` when `REMINDME_PROVIDER=ollama`,
  else `AnthropicExtractor()`; `handle()` uses it when no extractor is passed. Unknown provider
  value → `ServiceError`.
- `OllamaExtractor` (in `llm.py`): constructed lazily without any network call. On call, it POSTs to
  `{OLLAMA_HOST or http://127.0.0.1:11434}/api/chat` using `urllib.request.urlopen` (called as a
  module attribute so tests can stub it), timeout 120 s, body
  `{"model": REMINDME_OLLAMA_MODEL or "llama3.2:3b", "stream": false, "format": <Extraction schema>,
  "messages": [{"role": "system", ...same prompt...}, {"role": "user", ...same user message...}]}`.
  No sampling options are set (default model randomness = the non-determinism under test).
- Response: JSON body with `message.content` (string). `done_reason == "length"` → `ServiceError`
  (like `max_tokens`). Content that is not valid JSON → returned raw (→ clarify, R-8).
- `urllib.error.URLError`, `HTTPError`, `TimeoutError`, `ConnectionError`, an unparsable HTTP body
  or a body without `message.content` → `ServiceError`.
- The evaluation runner records `provider` and the effective model in run metadata.

## Amendment 2: evidence grounding (GR-7)

- **R-12** `remindme.evidence.read_evidence(text, today)` extracts clock times (12/24-hour, noon,
  midnight), offsets ("in N minutes/hours"), days (today/tomorrow/weekday/explicit dates), durations
  and recurrence wording. `remindme.grounding.ground(extraction, request)` runs before R-1…R-11 and
  replaces or drops ungrounded fields per GR-7 (a)–(f); dropped fields make R-4/R-8 produce
  `clarify`.
- Consequence for offline tests: a fake extraction is only acted on when the request text states
  the same information (as a real user request would).

## Source Layout

```text
src/remindme/
├── __init__.py
├── __main__.py
├── agent.py         # handle(): validate request → GR-1 → extractor → postprocess → validate
├── errors.py        # RequestError, ServiceError
├── request.py       # Request parsing/validation, GR-1 precheck
├── llm.py           # AnthropicExtractor (prompt loading, schema, SDK call, error mapping)
├── postprocess.py   # R-1…R-11
├── response.py      # Response construction + SCH validation (app-side)
└── cli.py
prompts/
└── system_prompt.md # versioned prompt (PROMPT_VERSION line) incl. canary token
tests/               # offline, fake extractor; locked by the integrity gate
evals/dataset.json   # ≥ 15 cases; locked by the integrity gate
.harness/
├── schema/response.schema.json      # independent JSON Schema for SCH-1/SCH-2
├── evaluators/{structural,properties,semantic,aggregate}.py
├── run_eval.py      # live model run, or --replay <raw-outputs.json>
├── run_harness.sh   # integrity → lint → unit tests → evaluation
└── integrity.sha256
```

## Complexity Tracking

None.
