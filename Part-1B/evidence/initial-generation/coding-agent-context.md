# Coding-agent context for the initial generation (`/speckit-implement`)

- **Agent**: a separate Claude Code sub-agent (Claude Opus 5.5) acting as the coding agent. It had
  no access to `tests/`, `evals/` or `.harness/`, and no API key, so it made no model calls.
- **Date**: 2026-11-22
- **Spec context handed over**: constitution v1.0.0, `specs/001-reminder-agent/{spec,plan,research,data-model,quickstart,tasks}.md`,
  `contracts/extraction.schema.json`, the `speckit-implement` skill.
- **Tasks implemented**: T008–T010, T012–T015, T017, T019, T021.
- **Prompt summary**: implement `src/remindme/` and `prompts/system_prompt.md` exactly per plan.md
  (public API, R-1…R-11); prompt first line `PROMPT_VERSION: 1` with canary `RMD-CANARY-7731`;
  `AnthropicExtractor` with lazy client, `claude-opus-5-5`, effort `low`, structured output, no
  sampling params, stop_reason refusal/max_tokens and SDK errors → `ServiceError`. Rules: write
  only `src/` and `prompts/`, no tests, no harness, no commits, lint limits stated.

## Interpretations the coding agent reported

1. GR-1 length check is applied after trimming.
2. Any non-`ServiceError` exception raised by an extractor is wrapped as `ServiceError`.
3. `recurrence` null → `none` for create; unknown value → clarify (`time`).
4. When an action is downgraded to clarify, a fixed question is generated from `missing`.
5. For action intents the model's `missing` list is ignored; validated fields decide.
6. Snooze falls back to `time_spec.offset_minutes` when `snooze_minutes` is null.
7. Recurring reminders whose time has passed roll forward; `monthly` clamps day-of-month.
8. Non-existent local times (DST gap) are normalised through UTC.
9. Prompt policy: vague times ("tomorrow morning") → clarify; pure injection / off-topic → reject;
   "push back by X" → snooze.
10. Unverified (no key): whether the API accepts `null` inside schema `enum` lists.
