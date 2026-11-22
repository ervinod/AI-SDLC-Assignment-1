# Feature Specification: TaskFlow – Smart Todo & Task CLI

**Feature Branch**: `001-task-cli`

**Created**: 2026-11-22

**Status**: Draft

**Input**: User description: "Smart Todo & Task CLI: task CRUD, tag filtering, JSON persistence,
priority sorting and task-status transitions. Single-user command-line tool whose behaviour is
fully deterministic so that every acceptance criterion can be checked by an automated test."

## Clarifications

### Session 2026-11-22

Answers below are the recommended options proposed during `/speckit-clarify`; the student delegated
the choice to the coding agent ("do every step on my behalf"), so each was accepted as recommended.

- Q: When several `--tag` values are given to `list`, must a task have ALL of them or ANY of them? → A: ALL (logical AND); `--status` combines with tags by AND as well.
- Q: Can a task in `done` or `cancelled` be re-opened? → A: Yes, only back to `todo` (`done→todo`, `cancelled→todo`); no other transition leaves those states.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create, view, edit and delete tasks (Priority: P1)

A user records tasks from the terminal, reads a task back, corrects its title, priority or tags and
removes tasks they no longer need. Tasks survive between invocations.

**Why this priority**: Without CRUD and persistence there is no product.

**Independent Test**: Run `add`, `show`, `update`, `delete` against an empty data file and inspect
stdout, exit code and the resulting data file.

**Acceptance Scenarios**:

1. **Given** no data file exists, **When** the user runs `add "Buy milk"`, **Then** stdout is exactly
   `Created task 1`, exit code is 0, and the data file contains one task with id 1, title
   `Buy milk`, priority `medium`, status `todo`, tags `[]`.
2. **Given** task 1 exists, **When** the user runs `add "Pay rent" --priority high --tag Home
   --tag bills`, **Then** stdout is `Created task 2` and task 2 has priority `high` and tags
   `["bills", "home"]` (lower-cased, sorted).
3. **Given** task 1 exists, **When** the user runs `show 1`, **Then** stdout is the task as JSON
   (2-space indent, keys sorted) and exit code is 0.
4. **Given** task 1 exists, **When** the user runs `update 1 --title "Buy oat milk" --priority low`,
   **Then** stdout is `Updated task 1`, the title and priority change and `updated_at` is set to the
   current time while `created_at` is unchanged.
5. **Given** task 1 exists, **When** the user runs `delete 1`, **Then** stdout is `Deleted task 1`
   and a subsequent `show 1` exits with code 1 and stderr `error: task 1 not found`.
6. **Given** tasks 1 and 2 exist and task 2 is deleted, **When** the user adds a task, **Then** it
   receives id 3 (ids are never reused).

---

### User Story 2 - Move tasks through a status workflow (Priority: P1)

A user moves a task from `todo` to `in_progress` to `done`, or cancels it. Invalid moves are
rejected so the history of work stays meaningful.

**Why this priority**: Status transitions are an explicit requirement of the problem statement.

**Independent Test**: Create a task, call `status` with each allowed and disallowed target and
check stdout/stderr/exit code and the stored status.

**Acceptance Scenarios**:

1. **Given** task 1 has status `todo`, **When** the user runs `status 1 in_progress`, **Then** stdout
   is `Task 1: todo -> in_progress` and exit code is 0.
2. **Given** task 1 has status `todo`, **When** the user runs `status 1 done`, **Then** exit code is 2,
   stderr is `error: invalid transition todo -> done`, and the stored status is still `todo`.
3. **Given** task 1 has status `in_progress`, **When** the user runs `status 1 in_progress`, **Then**
   exit code is 2 and stderr is `error: invalid transition in_progress -> in_progress`.
4. **Given** task 1 has status `done`, **When** the user runs `status 1 todo`, **Then** stdout is
   `Task 1: done -> todo` and exit code is 0.
5. **Given** task 1 has status `cancelled`, **When** the user runs `status 1 in_progress`, **Then**
   exit code is 2 and stderr is `error: invalid transition cancelled -> in_progress`.

---

### User Story 3 - Filter by tag and sort by priority (Priority: P2)

A user lists tasks, optionally narrowed to certain tags and/or a status, and sorted by priority so
the most important work is first.

**Why this priority**: Valuable for daily use, but depends on stories 1–2.

**Independent Test**: Seed a data file with known tasks, run `list` with each filter/sort option
and compare stdout with the exact expected lines.

**Acceptance Scenarios**:

1. **Given** tasks exist, **When** the user runs `list`, **Then** tasks are printed one per line in
   ascending id order, in the format defined by FR-011.
2. **Given** tasks with priorities low, high, medium, high, **When** the user runs
   `list --sort priority`, **Then** the order is high, high, medium, low, with ties broken by
   `created_at` ascending and then id ascending.
3. **Given** tasks tagged `work`, `home` and `work,urgent`, **When** the user runs
   `list --tag work --tag urgent`, **Then** only the task tagged `work,urgent` is listed.
4. **Given** no task matches, **When** the user lists, **Then** stdout is exactly `No tasks found.`
   and exit code is 0.
5. **Given** tasks exist, **When** the user runs `list --json`, **Then** stdout is a JSON array of the
   selected tasks in the selected order.

---

### Edge Cases

- Title empty, whitespace only, or longer than 200 characters after trimming → exit 2.
- Tag not matching `^[a-z0-9-]{1,30}$` after lower-casing → exit 2; more than 10 tags → exit 2.
- Unknown priority, status or sort key → exit 2.
- Non-integer or non-positive task id → exit 2; well-formed id that does not exist → exit 1.
- `update` with no change options → exit 2 `error: nothing to update`.
- Data file missing → treated as empty store (created on first write).
- Data file not valid JSON or not matching the data-file schema → exit 3, file left untouched.
- Any failing command leaves the data file byte-identical.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a task with a title (1–200 characters after trimming leading and
  trailing whitespace), optional priority (`low` | `medium` | `high`, default `medium`) and zero
  or more tags; new tasks have status `todo`.
- **FR-002**: System MUST assign each new task the next integer id starting at 1; ids MUST NOT be
  reused after deletion.
- **FR-003**: System MUST normalise tags to lower case, de-duplicate them, store them sorted
  ascending, accept only `^[a-z0-9-]{1,30}$`, and allow at most 10 tags per task.
- **FR-004**: System MUST display a single task by id as JSON (2-space indent, keys sorted).
- **FR-005**: System MUST update a task's title, priority, and tags (add and remove) with the
  same validation as FR-001/FR-003, and set `updated_at` to the current time.
- **FR-006**: System MUST delete a task by id.
- **FR-007**: System MUST support statuses `todo`, `in_progress`, `done`, `cancelled` and permit only
  these transitions: `todo→in_progress`, `todo→cancelled`, `in_progress→todo`,
  `in_progress→done`, `in_progress→cancelled`, plus any allowed by FR-014. Every other transition,
  including to the same status, MUST be rejected with exit 2 and
  `error: invalid transition <from> -> <to>`.
- **FR-008**: System MUST list tasks, optionally filtered by `--status <status>`.
- **FR-009**: System MUST filter tasks by one or more `--tag` values; a task is included only if it
  has ALL given tags (tag values are normalised as in FR-003 before matching). `--tag` and
  `--status` filters combine with logical AND.
- **FR-010**: System MUST sort lists by id ascending by default, and with `--sort priority` by
  priority (high > medium > low), then `created_at` ascending, then id ascending.
- **FR-011**: Human list output MUST be one line per task with tab-separated fields
  `<id>\t<status>\t<priority>\t<title>\t<tags joined by ",">`; `--json` MUST output a JSON array
  (2-space indent, keys sorted); an empty result prints `No tasks found.` (human) or `[]` (JSON).
- **FR-012**: System MUST persist all tasks to a JSON data file, chosen by `--data <path>`, else
  environment variable `TASKFLOW_DATA`, else `./tasks.json`, and MUST write it atomically.
- **FR-013**: System MUST use exit codes 0 success, 1 task not found, 2 usage/validation error,
  3 data-file error; error messages go to stderr prefixed `error: `; nothing is written to stdout
  on error.
- **FR-014**: Tasks in status `done` or `cancelled` MAY be re-opened only to `todo`
  (`done→todo`, `cancelled→todo`); every other transition out of these states is rejected per FR-007.
- **FR-015**: Timestamps (`created_at`, `updated_at`) MUST be ISO-8601 UTC with second precision and
  a `Z` suffix, taken from the current time; if environment variable `TASKFLOW_NOW` is set to such a
  timestamp the system MUST use it instead (deterministic clock for tests and demos).
- **FR-016**: Success messages MUST be exactly: `Created task <id>`, `Updated task <id>`,
  `Deleted task <id>`, `Task <id>: <from> -> <to>`.

### Key Entities

- **Task**: `id` (int ≥ 1), `title` (str), `priority` (enum), `status` (enum), `tags` (sorted list
  of str), `created_at` (timestamp), `updated_at` (timestamp).
- **Task store (data file)**: `{"version": 1, "next_id": <int>, "tasks": [<Task>, ...]}`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of acceptance scenarios above pass as automated tests.
- **SC-002**: Any command on a store of 1,000 tasks completes in under 1 second.
- **SC-003**: Running the same command sequence twice against fresh stores with a fixed clock
  produces byte-identical outputs and data files.
- **SC-004**: No failing command ever modifies the data file (verified for every error class).

## Assumptions

- Single user, single process; concurrent writers are out of scope.
- Due dates, reminders, sub-tasks and multi-user sync are out of scope for v1.
- The terminal accepts UTF-8; titles may contain any Unicode except control characters, which are
  rejected (exit 2).
