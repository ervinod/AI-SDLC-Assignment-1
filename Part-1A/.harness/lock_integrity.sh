#!/usr/bin/env bash
# Re-generates .harness/integrity.sha256. Run ONLY by the human reviewer after a legitimate,
# documented change to the spec, tests or harness (never by the coding agent to obtain PASS).
set -euo pipefail
cd "$(dirname "$0")/.."
{
  echo .specify/memory/constitution.md
  echo pyproject.toml
  find specs -type f -name '*.md' ! -name tasks.md
  find tests -type f -name '*.py'
  echo .harness/ruff.toml; echo .harness/bandit.yaml; echo .harness/run_harness.sh
  echo .harness/make_feedback.py; echo .harness/lock_integrity.sh
} | LC_ALL=C sort | xargs shasum -a 256 > .harness/integrity.sha256
echo "locked $(wc -l < .harness/integrity.sha256 | tr -d ' ') files"
