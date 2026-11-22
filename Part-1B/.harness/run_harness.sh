#!/usr/bin/env bash
# RemindMe harness: 0 integrity -> 1 lint -> 2 offline tests (+coverage) -> 3 live evaluation.
# Usage: .harness/run_harness.sh [--label "description"]   (needs ANTHROPIC_API_KEY for gate 3)
# Reads ./.env if present (never printed or copied into evidence).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BIN="$ROOT/.venv/bin"
LABEL="${2:-}"
if [[ -f .env ]]; then set -a; source .env; set +a; fi

OUT="$ROOT/evidence/harness-results"; mkdir -p "$OUT"
N=$(find "$OUT" -maxdepth 1 -type d -name 'run-*' | wc -l | tr -d ' ')
RUN="$OUT/$(printf 'run-%03d' $((N + 1)))"; mkdir -p "$RUN"
OVERALL=0
gate() { local name="$1"; shift; echo "== gate: $name"
  "$@" >"$RUN/$name.stdout.txt" 2>"$RUN/$name.stderr.txt"; local rc=$?
  echo "$name $rc" >>"$RUN/gates.txt"
  if [[ $rc -eq 0 ]]; then echo "   PASS"; else echo "   FAIL (exit $rc)"; OVERALL=1; fi; }

gate integrity shasum -a 256 -c .harness/integrity.sha256
gate lint "$BIN/ruff" check --config .harness/ruff.toml src tests .harness
gate unit_tests "$BIN/python" -m pytest --cov=src/remindme --cov-report=term-missing \
  --cov-fail-under=85 -p no:cacheprovider
gate evaluation "$BIN/python" .harness/run_eval.py --label "$LABEL"
tail -12 "$RUN/evaluation.stdout.txt"
LATEST=$(ls -d evidence/eval-runs/run-* 2>/dev/null | tail -1)
[[ -n "$LATEST" ]] && echo "evaluation run dir: $LATEST" >>"$RUN/gates.txt"
echo "== overall: $([[ $OVERALL -eq 0 ]] && echo PASS || echo FAIL)  ($RUN)"
exit $OVERALL
