# CLI Contract: `taskflow`

Global option (before the sub-command): `--data PATH`.
Environment: `TASKFLOW_DATA` (data path fallback), `TASKFLOW_NOW` (fixed clock).

| Command | Arguments / options | stdout on success | FR |
|---------|--------------------|-------------------|----|
| `add TITLE` | `--priority {low,medium,high}`, `--tag T` (repeatable) | `Created task <id>` | FR-001–003, FR-016 |
| `show ID` | – | task JSON (indent 2, sorted keys) | FR-004 |
| `update ID` | `--title`, `--priority`, `--add-tag T`*, `--remove-tag T`* (≥1 required) | `Updated task <id>` | FR-005, FR-016 |
| `delete ID` | – | `Deleted task <id>` | FR-006, FR-016 |
| `status ID NEW` | NEW ∈ statuses | `Task <id>: <from> -> <to>` | FR-007, FR-014, FR-016 |
| `list` | `--tag T`*, `--status S`, `--sort {id,priority}`, `--json` | lines per FR-011 or JSON array | FR-008–011 |

## Errors (stderr, nothing on stdout)

| Condition | Exit | stderr |
|-----------|------|--------|
| Task id not found | 1 | `error: task <id> not found` |
| Invalid title | 2 | `error: title must be 1-200 characters` / `error: title contains control characters` |
| Invalid tag | 2 | `error: invalid tag '<tag>'` |
| > 10 tags | 2 | `error: a task may have at most 10 tags` |
| Invalid id (non-positive / non-integer) | 2 | `error: invalid task id '<raw>'` |
| Invalid transition | 2 | `error: invalid transition <from> -> <to>` |
| `update` without options | 2 | `error: nothing to update` |
| argparse usage error (unknown choice, missing arg) | 2 | argparse usage message |
| Invalid `TASKFLOW_NOW` | 2 | `error: invalid TASKFLOW_NOW` |
| Corrupt / invalid data file | 3 | `error: invalid data file: <reason>` |

Removing a tag that is not present is a no-op (still counts as an update).
