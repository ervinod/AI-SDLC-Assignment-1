# Data Model: RemindMe Agent

## Request (input)

| Field | Type | Rules |
|-------|------|-------|
| text | str | GR-1: 1–500 chars after trimming, else `reject` without model call |
| now | str | ISO-8601 with UTC offset, e.g. `2026-11-23T09:00:00+05:30` |
| timezone | str | valid IANA name (`zoneinfo`) |
| reminders | list[ExistingReminder] | may be empty |

## ExistingReminder

| Field | Type | Rules |
|-------|------|-------|
| id | str | non-empty, unique in the list |
| task | str | non-empty |
| due_at | str | ISO-8601 with offset |

## Extraction (model output) — see `contracts/extraction.schema.json`

## Response (output) — SCH-1/SCH-2

| Field | Type | Non-null when |
|-------|------|---------------|
| intent | enum create/reschedule/snooze/cancel/clarify/reject | always |
| task | str (1–120) | create |
| due_at | str `YYYY-MM-DDTHH:MM:SS±HH:MM` | create, reschedule, snooze |
| recurrence | enum none/daily/weekly/weekdays/monthly | create |
| target_id | str ∈ request reminder ids | reschedule, snooze, cancel |
| snooze_minutes | int 1–1440 | snooze |
| missing | list ⊆ {task, time, target}, unique, ordered task,time,target | non-empty iff clarify |
| question | str (1–200) | clarify |
| reason | str (1–200) | reject |

Intent → field matrix = INV-1…INV-6 in spec.md.

## Evaluation case (`evals/dataset.json`)

```json
{
  "id": "C01", "category": "normal|boundary|ambiguous|missing_info|malformed|adversarial",
  "description": "...", "requirements": ["FR-004", "INV-1"],
  "request": { "text": "...", "now": "...", "timezone": "...", "reminders": [] },
  "expected": {
    "intent": "create",
    "due_at": "2026-11-24T18:00:00+05:30",
    "recurrence": "none",
    "target_id": null,
    "missing": [],
    "task_keywords": ["call", "mom"],
    "forbidden_keywords": [],
    "guardrail": false
  }
}
```

Only keys present in `expected` are scored (Layer 3). `guardrail: true` marks cases counted by THR-3.
