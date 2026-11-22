# Harness feedback — run-001 (FAIL)

Label: SELF-TEST mutant: unused_import

| Gate | Result | Exit |
|------|--------|------|
| integrity | PASS | 0 |
| lint | FAIL | 1 |
| security | PASS | 0 |
| tests | PASS | 0 |

## Gate `lint` failed

```text
F401 [*] `os` imported but unused
 --> src/taskflow/formatting.py:4:8
  |
3 | import json
4 | import os
  |        ^^
5 | from collections.abc import Iterable
6 | from typing import Any
  |
help: Remove unused import: `os`
  |
3 | import json
  - import os
4 | from collections.abc import Iterable
  |

Found 1 error.
[*] 1 fixable with `--fix`.

```

Instructions to the coding agent: repair `src/` only. Do not edit tests, the spec, or anything under `.harness/` (integrity gate).
