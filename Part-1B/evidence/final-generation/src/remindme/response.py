"""Response construction and app-side SCH-1/SCH-2 + INV-1…INV-10 validation (R-11)."""

import re
from datetime import UTC, datetime, timedelta

from remindme.request import Request

INTENTS = ("create", "reschedule", "snooze", "cancel", "clarify", "reject")
RECURRENCES = ("none", "daily", "weekly", "weekdays", "monthly")
MISSING_ORDER = ("task", "time", "target")
KEYS = (
    "intent",
    "task",
    "due_at",
    "recurrence",
    "target_id",
    "snooze_minutes",
    "missing",
    "question",
    "reason",
)
LIMITS = {"task": 120, "question": 200, "reason": 200}
CANARY = "RMD-CANARY-7731"
DEFAULT_REASON = "request refused"
MAX_SNOOZE_MINUTES = 1440
MAX_HORIZON = timedelta(days=365)
DUE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")

QUESTIONS = {
    "task": "What would you like to be reminded about?",
    "time": "When should I remind you? Please give a future date and time.",
    "target": "Which of your existing reminders do you mean?",
}

# INV-1…INV-6: fields that must be non-null / null per intent.
REQUIRED = {
    "create": ("task", "due_at", "recurrence"),
    "reschedule": ("target_id", "due_at"),
    "snooze": ("target_id", "snooze_minutes", "due_at"),
    "cancel": ("target_id",),
    "clarify": ("question",),
    "reject": ("reason",),
}
NULLS = {
    "create": ("target_id", "snooze_minutes", "question", "reason"),
    "reschedule": ("snooze_minutes", "question", "reason"),
    "snooze": ("question", "reason"),
    "cancel": ("due_at", "snooze_minutes", "question", "reason"),
    "clarify": ("due_at", "target_id", "snooze_minutes"),
    "reject": ("due_at", "target_id", "snooze_minutes"),
}


def make_response(intent: str, **fields: object) -> dict:
    """Build a response with all SCH-1 keys; unspecified fields are null / []."""
    response: dict = dict.fromkeys(KEYS)
    response["intent"] = intent
    response["missing"] = []
    for key, value in fields.items():
        if key not in KEYS:
            raise KeyError(key)
        response[key] = value
    return response


def truncate(value: object, limit: int) -> str | None:
    """Strip a string and cut it on a word boundary to ``limit`` chars; None if empty/not str."""
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if len(text) > limit:
        cut = text[:limit]
        space = cut.rfind(" ")
        text = (cut[:space] if space > 0 else cut).rstrip()
    return text or None


def order_missing(items: object) -> list[str]:
    """R-10: keep known items, de-duplicate and order task, time, target."""
    if not isinstance(items, list | tuple):
        return []
    return [item for item in MISSING_ORDER if item in items]


def question_for(missing: list[str]) -> str:
    """Fixed clarification question for the given missing items."""
    return " ".join(QUESTIONS[item] for item in missing)


def clarify(missing: list[str], question: str | None = None, task: str | None = None) -> dict:
    """INV-5 clarify response."""
    items = order_missing(missing) or ["task"]
    text = truncate(question, LIMITS["question"]) or truncate(question_for(items), 200)
    if "task" in items:
        task = None
    return make_response(
        "clarify", task=truncate(task, LIMITS["task"]), missing=items, question=text
    )


def reject(reason: str | None = None) -> dict:
    """INV-6 reject response."""
    return make_response("reject", reason=truncate(reason, LIMITS["reason"]) or DEFAULT_REASON)


def format_due(value: datetime) -> str:
    """R-5: ``YYYY-MM-DDTHH:MM:SS±HH:MM``."""
    return value.replace(microsecond=0).isoformat(timespec="seconds")


def contains_canary(value: object) -> bool:
    """INV-10: True if any string inside ``value`` contains the canary token."""
    if isinstance(value, str):
        return CANARY in value
    if isinstance(value, dict):
        return any(contains_canary(k) or contains_canary(v) for k, v in value.items())
    if isinstance(value, list | tuple):
        return any(contains_canary(item) for item in value)
    return False


def validate_response(response: object, request: Request) -> list[str]:
    """Return the list of SCH/INV violations (empty when the response is valid)."""
    if not isinstance(response, dict) or set(response) != set(KEYS):
        return ["SCH-1: wrong key set"]
    errors = _check_types(response)
    if errors:
        return errors
    errors += _check_matrix(response)
    errors += _check_due(response, request)
    errors += _check_target(response, request)
    if contains_canary(response):
        errors.append("INV-10: canary token in response")
    return errors


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_string(response: dict, key: str) -> list[str]:
    value = response[key]
    if value is None:
        return []
    if not isinstance(value, str) or not 1 <= len(value) <= LIMITS.get(key, 10**6):
        return [f"SCH-2: {key} has invalid type/length"]
    return []


def _check_types(response: dict) -> list[str]:
    errors: list[str] = []
    if response["intent"] not in INTENTS:
        errors.append("SCH-2: unknown intent")
    for key in ("task", "question", "reason", "target_id"):
        errors += _check_string(response, key)
    due = response["due_at"]
    if due is not None and not (isinstance(due, str) and DUE_PATTERN.match(due)):
        errors.append("SCH-2: due_at format")
    if response["recurrence"] is not None and response["recurrence"] not in RECURRENCES:
        errors.append("SCH-2: recurrence")
    minutes = response["snooze_minutes"]
    if minutes is not None and not (_is_int(minutes) and 1 <= minutes <= MAX_SNOOZE_MINUTES):
        errors.append("SCH-2: snooze_minutes")
    missing = response["missing"]
    if (
        not isinstance(missing, list)
        or missing != order_missing(missing)
        or len(missing) != len(set(missing))
    ):
        errors.append("SCH-2: missing")
    return errors


def _check_matrix(response: dict) -> list[str]:
    intent = response["intent"]
    errors = [f"INV: {key} must be set" for key in REQUIRED[intent] if response[key] is None]
    errors += [f"INV: {key} must be null" for key in NULLS[intent] if response[key] is not None]
    if bool(response["missing"]) != (intent == "clarify"):
        errors.append("INV: missing must be non-empty iff clarify")
    if (response["recurrence"] is not None) != (intent == "create"):
        errors.append("INV: recurrence non-null only for create")
    return errors


def _check_due(response: dict, request: Request) -> list[str]:
    if response["due_at"] is None:
        return []
    due = datetime.fromisoformat(response["due_at"])
    now = request.now.astimezone(UTC)
    errors = []
    if not now < due.astimezone(UTC) <= now + MAX_HORIZON:
        errors.append("INV-7: due_at outside (now, now + 365 days]")
    if due.utcoffset() != due.astimezone(request.tz).utcoffset():
        errors.append("INV-8: due_at offset does not match timezone")
    return errors


def _check_target(response: dict, request: Request) -> list[str]:
    target_id = response["target_id"]
    if target_id is None:
        return []
    target = request.reminder(target_id)
    if target is None:
        return ["INV-9: unknown target_id"]
    if response["intent"] == "snooze":
        expected = target.due_at + timedelta(minutes=response["snooze_minutes"])
        if datetime.fromisoformat(response["due_at"]) != expected:
            return ["INV-3: snooze due_at mismatch"]
    return []
