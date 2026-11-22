#!/usr/bin/env bash
# TaskFlow deterministic harness (tasks T003/T004).
# Gates: 0 integrity -> 1 lint -> 2 security -> 3 tests. All gates always run so the feedback is
# complete; the overall result is PASS only if every gate passes.
# Usage: .harness/run_harness.sh [--label "short description of this run"]
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PY:-$ROOT/.venv/bin/python}"
BIN="$(dirname "$PY")"
LABEL=""
if [[ "${1:-}" == "--label" ]]; then LABEL="${2:-}"; fi

RESULTS="$ROOT/evidence/harness-results"
mkdir -p "$RESULTS"
N=$(find "$RESULTS" -maxdepth 1 -type d -name 'run-*' | wc -l | tr -d ' ')
RUN_ID=$(printf "run-%03d" $((N + 1)))
OUT="$RESULTS/$RUN_ID"
mkdir -p "$OUT"
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)

declare -a NAMES CODES
gate() { # gate <name> <command...>
  local name="$1"; shift
  echo "== gate: $name"
  "$@" >"$OUT/$name.stdout.txt" 2>"$OUT/$name.stderr.txt"
  local rc=$?
  NAMES+=("$name"); CODES+=("$rc")
  if [[ $rc -eq 0 ]]; then echo "   PASS"; else echo "   FAIL (exit $rc)"; fi
}

gate integrity shasum -a 256 -c .harness/integrity.sha256
gate lint bash -c "'$BIN/ruff' check --config .harness/ruff.toml src tests && '$BIN/ruff' format --check --config .harness/ruff.toml src tests"
gate security "$BIN/bandit" -c .harness/bandit.yaml -r src -ll
gate tests "$PY" -m pytest --cov=src/taskflow --cov-report=term-missing --cov-fail-under=90 \
  --junitxml="$OUT/junit.xml" -p no:cacheprovider

"$PY" .harness/make_feedback.py "$OUT" "$RUN_ID" "$START" "$LABEL" "${NAMES[*]}" "${CODES[*]}"
RC=$?
echo "== overall: $(python3 -c "import json;print(json.load(open('$OUT/summary.json'))['overall'])")  ($OUT)"
exit $RC
