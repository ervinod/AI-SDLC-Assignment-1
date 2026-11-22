# Harness feedback — run-001 (FAIL)

Label: SELF-TEST mutant: shell_true

| Gate | Result | Exit |
|------|--------|------|
| integrity | PASS | 0 |
| lint | FAIL | 1 |
| security | FAIL | 1 |
| tests | PASS | 0 |

## Gate `lint` failed

```text
E402 Module level import not at top of file
  --> src/taskflow/formatting.py:48:1
   |
46 | def transition_message(task_id: int, from_status: str, to_status: str) -> str:
47 |     return f"Task {task_id}: {from_status} -> {to_status}"
48 | import subprocess
   | ^^^^^^^^^^^^^^^^^
help: Move module level imports to top of file

Found 1 error.

```

## Gate `security` failed

```text
Run started:2026-11-22 17:50:10.580555+00:00

Test results:
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue.
   Severity: High   Confidence: High
   CWE: CWE-78 (https://cwe.mitre.org/data/definitions/78.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b602_subprocess_popen_with_shell_equals_true.html
   Location: src/taskflow/formatting.py:52:11
51	def _x(c):
52	    return subprocess.run(c, shell=True, check=False)

--------------------------------------------------

Code scanned:
	Total lines of code: 578
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 1
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 2
Files skipped (0):
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	using config: .harness/bandit.yaml
[main]	INFO	running on Python 3.13.7
```

Instructions to the coding agent: repair `src/` only. Do not edit tests, the spec, or anything under `.harness/` (integrity gate).
