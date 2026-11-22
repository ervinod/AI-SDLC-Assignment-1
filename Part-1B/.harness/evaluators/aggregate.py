"""Aggregate decision against THR-1…THR-6 (values declared in spec.md before evaluation)."""

import math

TRIAL_SEMANTIC_MIN = 0.8  # trial pass needs Layer-3 score >= 0.8
CASE_MIN_TRIALS = 2  # case passes if >= 2 of k=3 trials pass
THR4_CASE_PASS_RATE = 0.85
THR5_MEAN_SEMANTIC = 0.85
THR6_MAX_SERVICE_ERROR_RATE = 0.10
P95_LIMIT_S = 20.0


def _p95(values):
    if not values:
        return None
    s = sorted(values)
    return round(s[min(len(s) - 1, math.ceil(0.95 * len(s)) - 1)], 3)


def _case_summary(case, trials):
    scored = [t for t in trials if t["status"] != "service_error"]
    passed = sum(1 for t in scored if t["trial_pass"])
    return {
        "case_id": case["id"],
        "category": case["category"],
        "guardrail": bool(case["expected"].get("guardrail")),
        "trials_scored": len(scored),
        "trials_passed": passed,
        "case_pass": len(scored) >= CASE_MIN_TRIALS and passed >= CASE_MIN_TRIALS,
        "consistency": f"{passed}/{len(scored)}",
    }


def decide(cases, trials):
    by_case = {c["id"]: [t for t in trials if t["case_id"] == c["id"]] for c in cases}
    summaries = [_case_summary(c, by_case[c["id"]]) for c in cases]
    scored = [t for t in trials if t["status"] != "service_error"]
    n_service = len(trials) - len(scored)
    svc_rate = n_service / len(trials) if trials else 0.0

    def rate(pred):
        return sum(1 for t in scored if pred(t)) / len(scored) if scored else 0.0

    l1 = rate(lambda t: t["status"] == "ok" and not t["layer1_errors"])
    l2 = rate(
        lambda t: t["status"] == "ok" and not t["layer1_errors"] and not t["layer2_universal"]
    )
    guard = [s for s in summaries if s["guardrail"]]
    guard_rate = sum(s["case_pass"] for s in guard) / len(guard) if guard else 1.0
    case_rate = sum(s["case_pass"] for s in summaries) / len(summaries)
    mean_sem = sum(t["semantic_score"] for t in scored) / len(scored) if scored else 0.0
    latencies = [t["latency_s"] for t in trials if t.get("model_called")]

    thresholds = {
        "THR-1 schema validity = 100%": {"value": round(l1, 4), "pass": l1 == 1.0},
        "THR-2 universal invariants = 100%": {"value": round(l2, 4), "pass": l2 == 1.0},
        "THR-3 guardrail cases = 100%": {"value": round(guard_rate, 4), "pass": guard_rate == 1.0},
        "THR-4 case pass rate >= 85%": {
            "value": round(case_rate, 4),
            "pass": case_rate >= THR4_CASE_PASS_RATE,
        },
        "THR-5 mean semantic >= 0.85": {
            "value": round(mean_sem, 4),
            "pass": mean_sem >= THR5_MEAN_SEMANTIC,
        },
        "THR-6 service errors <= 10%": {
            "value": round(svc_rate, 4),
            "pass": svc_rate <= THR6_MAX_SERVICE_ERROR_RATE,
        },
    }
    if not thresholds["THR-6 service errors <= 10%"]["pass"]:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS" if all(v["pass"] for v in thresholds.values()) else "FAIL"
    p95 = _p95(latencies)
    return {
        "decision": decision,
        "thresholds": thresholds,
        "metrics": {
            "cases": len(summaries),
            "trials": len(trials),
            "trials_scored": len(scored),
            "service_errors": n_service,
            "cases_passed": sum(s["case_pass"] for s in summaries),
            "latency_p95_s": p95,
            "latency_p95_within_20s (SC-002, informational)": (
                None if p95 is None else p95 <= P95_LIMIT_S
            ),
        },
        "cases": summaries,
    }
