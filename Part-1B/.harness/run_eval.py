"""Single non-deterministic evaluation pipeline (spec.md › Evaluation Threshold, tasks T005).

dataset → agent (model call) → output → Layer 1 schema → Layer 2 invariants/properties →
Layer 3 semantic score → aggregate decision vs THR-1…THR-6 → PASS / FAIL / INCONCLUSIVE.

Live:    python .harness/run_eval.py [--k 3] [--label "..."]
Replay:  python .harness/run_eval.py --replay path/to/raw-outputs.json   (no API key needed)
Exit code: 0 PASS, 1 FAIL, 2 INCONCLUSIVE.
"""

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / ".harness")]

from evaluators import aggregate, properties, semantic, structural  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
RUNS = Path(os.environ.get("REMINDME_EVAL_RUNS_DIR", ROOT / "evidence" / "eval-runs"))


def _meta(k, label, mode):
    provider = os.environ.get("REMINDME_PROVIDER", "anthropic")
    if provider == "ollama":
        model = os.environ.get("REMINDME_OLLAMA_MODEL", "llama3.2:3b")
    else:
        model = os.environ.get("REMINDME_MODEL", "claude-opus-5-5")
    prompt = ROOT / "prompts" / "system_prompt.md"
    first = prompt.read_text().splitlines()[0] if prompt.exists() else ""
    try:
        import anthropic

        sdk = anthropic.__version__
    except ImportError:  # pragma: no cover
        sdk = None
    return {
        "mode": mode,
        "label": label,
        "started_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": provider,
        "model": model,
        "effort": os.environ.get("REMINDME_EFFORT", "low") if provider == "anthropic" else None,
        "ollama_host": os.environ.get("OLLAMA_HOST") if provider == "ollama" else None,
        "prompt_version_line": first,
        "k_trials": k,
        "dataset_sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "anthropic_sdk": sdk,
        "api_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),  # value never stored
    }


def _run_trial(case, trial_no, handle, errors):
    """Execute one trial; never raises."""
    calls = {"n": 0}
    from remindme.llm import default_extractor

    real = default_extractor()

    def counting(req):
        calls["n"] += 1
        return real(req)

    t0 = time.perf_counter()
    rec = {"case_id": case["id"], "trial": trial_no}
    try:
        rec["output"] = handle(case["request"], extractor=counting)
        rec["status"] = "ok"
    except errors.ServiceError as exc:
        rec.update(status="service_error", output=None, error=f"{type(exc).__name__}: {exc}")
    except Exception as exc:  # noqa: BLE001 - any other exception is an application failure
        rec.update(status="app_error", output=None, error=f"{type(exc).__name__}: {exc}")
    rec["latency_s"] = round(time.perf_counter() - t0, 3)
    rec["model_called"] = calls["n"] > 0
    return rec


def live(cases, k):
    from remindme import errors
    from remindme.agent import handle

    raw = []
    for case in cases:
        for t in range(1, k + 1):
            rec = _run_trial(case, t, handle, errors)
            print(f"  {case['id']} t{t}: {rec['status']} {rec['latency_s']}s", flush=True)
            raw.append(rec)
    return raw


def score_trial(case, rec):
    out = dict(rec)
    out.update(layer1_errors=[], layer2_universal=[], layer2_case=[], semantic_score=0.0)
    out["criteria"] = {}
    if rec["status"] != "ok":
        out["trial_pass"] = False
        return out
    l1 = structural.check(rec["output"])
    out["layer1_errors"] = l1
    if not l1:
        out["layer2_universal"] = properties.universal(rec["output"], case["request"])
        out["layer2_case"] = properties.case_properties(rec["output"], case["expected"])
        out["semantic_score"], out["criteria"] = semantic.score(rec["output"], case["expected"])
    out["trial_pass"] = (
        not l1
        and not out["layer2_universal"]
        and not out["layer2_case"]
        and out["semantic_score"] >= aggregate.TRIAL_SEMANTIC_MIN
    )
    return out


def feedback_md(result, cases, trials):
    by_id = {c["id"]: c for c in cases}
    lines = [f"# Evaluation feedback — {result['decision']}", ""]
    lines += ["| Threshold | Value | Pass |", "|---|---|---|"]
    lines += [f"| {k} | {v['value']} | {v['pass']} |" for k, v in result["thresholds"].items()]
    failing = [t for t in trials if not t["trial_pass"]]
    lines += ["", f"## Failing trials ({len(failing)})"]
    for t in failing:
        c = by_id[t["case_id"]]
        lines += [
            "",
            f"### {t['case_id']} trial {t['trial']} — {c['category']} — {c['description']}",
            f"- requirements: {', '.join(c['requirements'])}",
            f"- request text: {json.dumps(c['request']['text'])}",
            f"- status: {t['status']}" + (f" ({t.get('error')})" if t.get("error") else ""),
            f"- expected: {json.dumps(c['expected'])}",
            f"- output: {json.dumps(t['output'])}",
            f"- layer1: {t['layer1_errors'] or 'ok'}",
            f"- layer2: {(t['layer2_universal'] + t['layer2_case']) or 'ok'}",
            f"- layer3: score={t['semantic_score']} criteria={t['criteria']}",
        ]
    lines += [
        "",
        "Repair scope for the coding agent: `src/` and `prompts/` only. Do not change "
        "evals/, tests/, .harness/ or the spec (integrity gate). "
        "Service errors are not app failures.",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=None)
    ap.add_argument("--label", default="")
    ap.add_argument("--replay", type=Path)
    ap.add_argument("--dataset", type=Path, default=DATASET, help="default evals/dataset.json")
    args = ap.parse_args()
    data = json.loads(args.dataset.read_text())
    cases = data["cases"]
    k = args.k or data["k_trials"]

    if args.replay:
        recorded = json.loads(args.replay.read_text())
        meta = recorded["meta"] | {"replayed_from": str(args.replay), "mode": "replay"}
        raw = recorded["trials"]
    else:
        meta = _meta(k, args.label, "live") | {
            "dataset": args.dataset.name,
            "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        }
        raw = live(cases, k)

    by_id = {c["id"]: c for c in cases}
    trials = [score_trial(by_id[r["case_id"]], r) for r in raw]
    result = aggregate.decide(cases, trials)

    RUNS.mkdir(parents=True, exist_ok=True)
    run_dir = RUNS / f"run-{len(list(RUNS.glob('run-*'))) + 1:03d}"
    run_dir.mkdir()
    raw_doc = {"meta": meta, "trials": raw}
    (run_dir / "raw-outputs.json").write_text(json.dumps(raw_doc, indent=2) + "\n")
    report = {"meta": meta, **result, "trials": trials}
    (run_dir / "eval-results.json").write_text(json.dumps(report, indent=2) + "\n")
    (run_dir / "feedback.md").write_text(feedback_md(result, cases, trials))
    for name, v in result["thresholds"].items():
        print(f"  {name}: {v['value']} {'PASS' if v['pass'] else 'FAIL'}")
    print(f"== evaluation: {result['decision']}  ({run_dir})")
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}[result["decision"]]


if __name__ == "__main__":
    sys.exit(main())
