# Quickstart: TaskFlow CLI

```bash
cd Part-1A
uv venv && uv pip install -e ".[dev]"
export TASKFLOW_DATA=/tmp/demo-tasks.json
.venv/bin/taskflow add "Buy milk" --tag home
.venv/bin/taskflow add "Ship report" --priority high --tag work --tag urgent
.venv/bin/taskflow status 2 in_progress
.venv/bin/taskflow list --sort priority
.venv/bin/taskflow list --tag work --json
```

Run the harness (lint → security → tests):

```bash
.harness/run_harness.sh
```
