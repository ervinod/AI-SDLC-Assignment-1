# Research: RemindMe Agent

## R1 – How to get stable structure out of a non-deterministic model
- **Decision**: Anthropic structured outputs (`output_config.format` with a JSON schema) for the
  `Extraction`, then independent validation in code.
- **Rationale**: constrained decoding makes schema violations rare. The app still re-validates
  (constitution II), because the output contract must hold even if the API, model or SDK changes.
- **Alternatives**: free-text JSON + regex parsing (fragile); tool use with `strict: true`
  (equivalent, but more plumbing for a single extraction).

## R2 – Who resolves dates
- **Decision**: the model returns a *symbolic* `time_spec` (offset / day offset / weekday / explicit
  date / HH:MM). `zoneinfo` resolves it in Python.
- **Rationale**: LLMs are unreliable at timezone offsets, DST and calendar arithmetic. Splitting the
  work this way makes `due_at` exactly comparable with ground truth (THR layer 3), and INV-7/INV-8
  are guaranteed by construction.

## R3 – Model choice
- **Decision**: `claude-opus-5-5` at effort `low`.
- **Rationale**: current default Claude model. Extraction is simple, so low effort keeps latency and
  cost down. Thinking cannot be disabled on this model; effort is the control. About 20 cases × 3
  trials ≈ 60 short calls per evaluation run, roughly $0.30–$0.60.

## R4 – Prompt-injection detection
- **Decision**: a canary token (`RMD-CANARY-7731`) in the system prompt. Any response field
  containing it is treated as a leak (INV-10). The user text goes inside a delimited block that the
  prompt says to treat as data.

## R5 – Evaluating non-determinism
- **Decision**: k = 3 trials per case; case passes on ≥ 2/3; report per-case consistency.
- **Rationale**: a single trial can't tell a flaky behaviour from a stable one, and k = 3 keeps
  cost small.

## R6 – Service vs application failures
- **Decision**: map `anthropic.APIConnectionError`, `APIStatusError` (incl. 429/5xx),
  `stop_reason in {"refusal", "max_tokens"}` to `ServiceError`. The harness records these as
  `service_error` and excludes them from scoring (THR-6).
