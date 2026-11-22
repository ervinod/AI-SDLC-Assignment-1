# Coding-agent context for the initial generation (`/speckit-implement`)

- **Agent**: a separate Claude Code sub-agent (Claude Opus 5.5) acting as the coding agent; it had no
  access to `tests/` or `.harness/`.
- **Date**: 2026-11-22
- **Spec context handed over**: constitution v1.0.0, `specs/001-task-cli/{spec,plan,research,data-model,quickstart}.md`,
  `contracts/cli.md`, `tasks.md`, the `speckit-implement` skill.
- **Tasks implemented**: T007–T010, T012–T014, T016–T017, T019–T021 (marked `[x]` in tasks.md).
- **Snapshot**: `evidence/initial-generation/src/` = commit "feat(1A): initial coding-agent generation".

## Prompt given to the coding agent (verbatim)

```text
You are the coding agent in a GitHub Spec Kit spec-driven-development workflow, executing
`/speckit-implement` for feature `001-task-cli` in the project at Part-1A.

Approved specification context (read ALL of these first; they are authoritative):
- .specify/memory/constitution.md
- specs/001-task-cli/spec.md (incl. Clarifications section)
- specs/001-task-cli/plan.md, research.md, data-model.md, contracts/cli.md
- specs/001-task-cli/tasks.md
- .claude/skills/speckit-implement/SKILL.md (follow its spirit, skip extension hooks and checklist prompts)
- pyproject.toml (already set up; do not edit)

Your job: implement the implementation tasks T007–T010, T012–T014, T016–T017, T019–T021 by creating
the package src/taskflow/ exactly per plan.md's structure. The public entry point is
taskflow.cli.main(argv: list[str] | None = None) -> int, which must RETURN the exit code (never let
SystemExit escape — see research.md R1). --data is a global option placed before the sub-command.
Follow the contract's exact output strings, exit codes and JSON formatting. Runtime: Python standard
library only. Then mark those task IDs as [x] in tasks.md.

Hard rules (enforced by an independent harness you cannot see):
- Do NOT read, create, or modify anything under tests/ or .harness/, and do not modify any
  spec/plan/contract/constitution file or pyproject.toml. Only write inside src/taskflow/ and the
  checkboxes of tasks.md.
- Do not write tests. Do not run any harness. Quick smoke runs only.
- Code style: ruff (mccabe ≤10, max-branches 12, max-args 6, line length 100, isort, bugbear,
  pyupgrade, pylint subset). Security gate: bandit MEDIUM+ (no eval/exec/pickle/shell, no assert
  for validation).
- Do not git commit.
```

## Interpretations the coding agent reported (summary of its hand-back)

1. `TASKFLOW_NOW` is validated for every command (FR-015 MUST), after argparse, before id lookup.
2. Invalid-tag error echoes the tag as typed by the user (not lower-cased).
3. `--remove-tag` values are validated too; adds are applied before removes, then the 10-tag limit.
4. Title length check runs before the control-character check.
5. Task id accepts only ASCII digits ≥ 1.
6. Data-file validation is strict on structure, tags and timestamps; titles are type-checked only.
7. Empty `TASKFLOW_DATA` = unset; empty `TASKFLOW_NOW` = invalid (exit 2).
8. OS read/write errors map to exit 3.
