"""Layer 3 – semantic/quality score in [0, 1] against the case ground truth.

Score = mean of the applicable criteria (only keys present in `expected` apply):
intent / intent_in, due_at (exact instant), recurrence, target_id, snooze_minutes, missing (set),
task_keywords (recall in `task`), forbidden_keywords (absent from all text fields).
"""

from datetime import datetime

TEXT_FIELDS = ("task", "question", "reason")


def _same_instant(a, b) -> bool:
    if a is None or b is None:
        return a is b
    return a == b and datetime.fromisoformat(a) == datetime.fromisoformat(b)


def _keyword_recall(task, keywords) -> float:
    if not keywords:
        return 1.0
    text = (task or "").lower()
    return sum(1 for k in keywords if k.lower() in text) / len(keywords)


def _forbidden_absent(out, words) -> float:
    blob = " ".join((out.get(f) or "") for f in TEXT_FIELDS).lower()
    return 0.0 if any(w.lower() in blob for w in words) else 1.0


def score(out: dict, expected: dict) -> tuple[float, dict]:
    crit: dict[str, float] = {}
    if "intent" in expected:
        crit["intent"] = float(out["intent"] == expected["intent"])
    if "intent_in" in expected:
        crit["intent"] = float(out["intent"] in expected["intent_in"])
    if "due_at" in expected:
        crit["due_at"] = float(_same_instant(out["due_at"], expected["due_at"]))
    for key in ("recurrence", "target_id", "snooze_minutes"):
        if key in expected:
            crit[key] = float(out[key] == expected[key])
    if "missing" in expected:
        crit["missing"] = float(set(out["missing"]) == set(expected["missing"]))
    if "task_keywords" in expected:
        crit["task_keywords"] = _keyword_recall(out["task"], expected["task_keywords"])
    if "forbidden_keywords" in expected:
        crit["forbidden_keywords"] = _forbidden_absent(out, expected["forbidden_keywords"])
    value = sum(crit.values()) / len(crit) if crit else 1.0
    return round(value, 4), crit
