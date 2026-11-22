# Data Model: TaskFlow CLI

## Task

| Field | Type | Rules | FR |
|-------|------|-------|----|
| id | int | ≥ 1, unique, assigned from `next_id`, never reused | FR-002 |
| title | str | trimmed, 1–200 chars, no control chars | FR-001 |
| priority | enum | `low` \| `medium` \| `high`; default `medium` | FR-001 |
| status | enum | `todo` \| `in_progress` \| `done` \| `cancelled`; new → `todo` | FR-007 |
| tags | list[str] | lower-cased, unique, sorted, each `^[a-z0-9-]{1,30}$`, max 10 | FR-003 |
| created_at | str | ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ` | FR-015 |
| updated_at | str | same format; = created_at on creation | FR-005, FR-015 |

## Status state machine (FR-007, FR-014)

```text
todo ──► in_progress ──► done
 │  ◄──      │             │
 │           ▼             │
 └──────► cancelled        │
 ▲            │            │
 └────────────┴────────────┘   (done→todo, cancelled→todo: re-open)
```

Allowed set:
`{todo→in_progress, todo→cancelled, in_progress→todo, in_progress→done, in_progress→cancelled,
done→todo, cancelled→todo}`. Everything else (including X→X) is invalid.

A successful transition sets `updated_at`.

## Task store (data file)

```json
{
  "version": 1,
  "next_id": 3,
  "tasks": [ { "id": 1, "title": "...", "priority": "medium", "status": "todo",
               "tags": [], "created_at": "2026-11-22T10:00:00Z",
               "updated_at": "2026-11-22T10:00:00Z" } ]
}
```

Serialised with `indent=2`, `sort_keys=True`, `ensure_ascii=False`, trailing newline; tasks stored
in ascending id order.
