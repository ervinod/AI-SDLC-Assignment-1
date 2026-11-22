# Research: TaskFlow CLI

## R1 – CLI parsing library
- **Decision**: `argparse` (stdlib).
- **Rationale**: constitution V forbids runtime dependencies; argparse supports sub-commands and
  repeated options (`--tag` with `action="append"`).
- **Alternatives**: click / typer — rejected (third-party).
- **Note**: argparse exits with code 2 on usage errors and prints to stderr, matching FR-013.
  `main()` must catch `SystemExit` from argparse so the function returns an int.

## R2 – Atomic persistence
- **Decision**: write JSON to `tempfile.NamedTemporaryFile(dir=<target dir>, delete=False)`, flush +
  `os.fsync`, then `os.replace(tmp, target)`.
- **Rationale**: `os.replace` is atomic on POSIX when source and target are on the same filesystem.
- **Alternatives**: write in place — rejected (partial file on crash).

## R3 – Deterministic clock
- **Decision**: `Clock.now()` returns `TASKFLOW_NOW` if set (validated against
  `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`) else `datetime.now(UTC)` truncated to seconds.
- **Rationale**: FR-015; lets contract tests and demos be byte-reproducible (SC-003).
- Invalid `TASKFLOW_NOW` → exit 2 (`error: invalid TASKFLOW_NOW`).

## R4 – Sorting
- **Decision**: key = `(PRIORITY_RANK[p], created_at, id)` with `high=0, medium=1, low=2`.
  ISO-8601 Z strings sort lexicographically in time order, so no parsing is needed.

## R5 – Data-file schema validation
- **Decision**: hand-written validator in `store.py` (stdlib only) checking `version == 1`,
  `next_id` int ≥ 1, every task has exactly the 7 fields with correct types/enums, ids unique and
  `< next_id`. Any violation → `DataFileError` (exit 3).

## R6 – Control characters in titles
- **Decision**: reject any character with Unicode category `Cc` (spec Assumptions).
