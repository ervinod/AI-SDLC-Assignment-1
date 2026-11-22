# Harness feedback — run-001 (FAIL)

Label: SELF-TEST mutant: weakened_test

| Gate | Result | Exit |
|------|--------|------|
| integrity | FAIL | 1 |
| lint | PASS | 0 |
| security | PASS | 0 |
| tests | PASS | 0 |

## Gate `integrity` failed

```text
.harness/bandit.yaml: OK
.harness/lock_integrity.sh: OK
.harness/make_feedback.py: OK
.harness/ruff.toml: OK
.harness/run_harness.sh: OK
.specify/memory/constitution.md: OK
pyproject.toml: OK
specs/001-task-cli/analysis-report.md: OK
specs/001-task-cli/checklists/requirements.md: OK
specs/001-task-cli/contracts/cli.md: OK
specs/001-task-cli/data-model.md: OK
specs/001-task-cli/plan.md: OK
specs/001-task-cli/quickstart.md: OK
specs/001-task-cli/research.md: OK
specs/001-task-cli/spec.md: OK
tests/__init__.py: OK
tests/conftest.py: OK
tests/contract/__init__.py: OK
tests/contract/test_cli_crud.py: OK
tests/contract/test_cli_list.py: FAILED
tests/contract/test_cli_nonfunctional.py: OK
tests/contract/test_cli_status.py: OK
tests/unit/__init__.py: OK
tests/unit/test_models.py: OK
tests/unit/test_store.py: OK
shasum: WARNING: 1 computed checksum did NOT match
```

Instructions to the coding agent: repair `src/` only. Do not edit tests, the spec, or anything under `.harness/` (integrity gate).
