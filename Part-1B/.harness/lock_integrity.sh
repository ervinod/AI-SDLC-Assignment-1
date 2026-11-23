#!/usr/bin/env bash
# Re-generates .harness/integrity.sha256. Run ONLY by the human reviewer after a legitimate,
# documented change to the spec, tests, dataset or harness (never by the coding agent).
set -euo pipefail
cd "$(dirname "$0")/.."
{
  echo .specify/memory/constitution.md
  echo pyproject.toml
  find specs -type f \( -name '*.md' -o -name '*.json' \) ! -name tasks.md
  find tests -type f -name '*.py'
  echo evals/dataset.json
  echo evals/holdout.json
  find .harness -type f \( -name '*.py' -o -name '*.json' -o -name '*.sh' -o -name '*.toml' \) ! -path '*/__pycache__/*'
} | LC_ALL=C sort | xargs shasum -a 256 > .harness/integrity.sha256
echo "locked $(wc -l < .harness/integrity.sha256 | tr -d ' ') files"
