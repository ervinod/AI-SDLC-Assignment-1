"""Ground the model's Extraction in the user's text (constitution II/III; GR-4, GR-6, SC-003).

The model is a non-deterministic extractor. Every value that drives an action is checked against
deterministic ``evidence`` read from the text: a time must be stated in the text, a target must be
the unique existing reminder the text refers to, recurrence must be named, and a task must contain
real words from the request. Unsupported values are dropped, which makes the post-processor
degrade to ``clarify``. Where the text is unambiguous, its reading replaces the model's (e.g. a
"4:15 pm" the model mis-converted).
"""

import re
from datetime import time

from remindme.evidence import Evidence, read_evidence
from remindme.request import Request
from remindme.response import RECURRENCES, order_missing

TARGET_INTENTS = ("reschedule", "snooze", "cancel")
INVALID = "invalid"
CLOCK_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::\d{2})?$")
WORD_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?|[☀-➿\U0001f000-\U0010ffff]")
MIN_STEM = 3
BULK_RE = re.compile(
    r"\b(?:all|every|each)\b(?:\s+(?:of|my|the|your|these|those|single|existing))*"
    r"\s+reminders?\b|\beverything\b|\ball\s+of\s+them\b",
    re.IGNORECASE,
)
ID_LIKE_RE = re.compile(r"(?<![\w-])(?:[a-z]{1,3}-?\d+|#\d+)(?![\w-])", re.IGNORECASE)
CREATE_CUE_RE = re.compile(
    r"\bremind\s+me\b|\bremember\s+to\b|\bset\s+(?:a\s+|an\s+)?(?:reminder|alarm)\b"
    r"|\bdon'?t\s+(?:let\s+me\s+)?forget\b",
    re.IGNORECASE,
)
MODIFY_CUE_RE = re.compile(
    r"\b(?:move|reschedul\w*|snooz\w*|cancel\w*|delet\w*|remove|postpon\w*|push|shift|"
    r"change|delay)\b",
    re.IGNORECASE,
)
HARM_RE = re.compile(
    r"\b(?:poison\w*|kill\w*|murder\w*|stab\w*|shoot\w*|hurt\w*|harm\w*|stalk\w*|drug\w*|"
    r"attack\w*|threat\w*|spik\w*|sleeping\s+pills?|beat\s+up)\b",
    re.IGNORECASE,
)

_FILLER_WORDS = """
a an the my me i you your it its this that these those to for at on in by of from with and or
but please can could would will just also then now up so as if is are be am pm o
remind reminder reminding reminded set create add make new schedule note alarm alert notify ping
tell let know about remember forget don't dont
today tomorrow tonight yesterday tmrw tmr morning afternoon evening night noon midday midnight
day week month year hour minute min mins hr hrs second sec oclock clock time
next last coming every each daily weekly monthly weekday weekend everyday nightly later soon
monday tuesday wednesday thursday friday saturday sunday
january february march april may june july august september october november december
jan feb mar apr jun jul aug sep sept oct nov dec
one two three four five six seven eight nine ten eleven twelve fifteen twenty thirty forty fifty
sixty ninety half quarter again
"""
_ACTION_WORDS = """
move moved reschedule rescheduled change changed push pushed postpone postponed delay delayed
snooze snoozed cancel cancelled canceled delete deleted remove removed stop drop clear shift bump
put get rid turn off one ones instead back forward while have has do does want need i'm you're
there all any some everything thanks thank yes no ok okay
"""


def _norm(token: str) -> str:
    token = token.lower()
    token = token[:-2] if token.endswith("'s") else token.replace("'", "")
    if len(token) > MIN_STEM and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    return token


def words(text: str) -> set[str]:
    """Normalised word (and emoji) tokens of a text."""
    return {_norm(token) for token in WORD_RE.findall(text)}


FILLER = frozenset(_norm(word) for word in _FILLER_WORDS.split())
TARGET_STOP = FILLER | frozenset(_norm(word) for word in _ACTION_WORDS.split())


def content_words(text: str, stop: frozenset[str]) -> set[str]:
    """Words that carry meaning (no scheduling / filler words, no single letters)."""
    return {word for word in words(text) if word and word not in stop and len(word) > 1}


class _Unresolved(Exception):
    """Internal: the text does not support exactly one reading."""


def _choose(options: list, model: object) -> object:
    """One distinct option → it; several → the model's value only if it is one of them."""
    distinct: list = []
    for option in options:
        if option not in distinct:
            distinct.append(option)
    if None in distinct:
        raise _Unresolved
    if len(distinct) == 1:
        return distinct[0]
    if model in distinct:
        return model
    raise _Unresolved


def _model_clock(spec: dict) -> time | None:
    value = spec.get("time")
    match = CLOCK_RE.match(value.strip()) if isinstance(value, str) else None
    if match is None:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    return time(hour, minute) if hour < 24 and minute < 60 else None  # noqa: PLR2004


def _model_day(spec: dict) -> dict:
    for key in ("date", "day_offset", "weekday"):
        value = spec.get(key)
        if value is not None:
            return {key: value.strip().lower() if isinstance(value, str) else value}
    return {}


def ground_time_spec(spec: object, evidence: Evidence, prefer_last: bool) -> dict | None:
    """A time_spec built only from what the text states (None when there is no usable time).

    ``prefer_last``: for a reschedule the new time is the last one mentioned.
    """
    model = spec if isinstance(spec, dict) else {}
    clocks = evidence.clocks[-1:] if prefer_last else evidence.clocks
    days = evidence.days[-1:] if prefer_last else evidence.days
    try:
        if evidence.offsets:
            if clocks or days:
                return None
            return {"offset_minutes": _choose(evidence.offsets, model.get("offset_minutes"))}
        clock = None
        if clocks:
            readings = [reading for mention in clocks for reading in mention or (None,)]
            clock = _choose(readings, _model_clock(model))
        day = _choose(days, _model_day(model)) if days else {}
    except _Unresolved:
        return None
    if clock is None and not day:
        return None
    return {"time": clock.strftime("%H:%M") if clock else None, **day}


def ground_recurrence(evidence: Evidence, model: object) -> str:
    """Recurrence named in the text; ``none`` when the text names none (never the model's guess)."""
    if evidence.unsupported_recurrence:
        return INVALID
    found = set(evidence.recurrences)
    if "weekdays" in found:
        found -= {"daily", "weekly"}
    if not found:
        return "none"
    if len(found) == 1:
        return found.pop()
    return model if model in found else INVALID


def ground_task(task: object, text: str) -> str | None:
    """Keep the task only if it has real (non-scheduling) words that occur in the request."""
    if not isinstance(task, str):
        return None
    meaningful = content_words(task, FILLER)
    if not meaningful or not meaningful & words(text):
        return None
    return task


def _mentions(text: str, reminder_id: str) -> bool:
    pattern = rf"(?<![\w-]){re.escape(reminder_id)}(?![\w-])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def ground_target(request: Request) -> str | None:
    """GR-6: the id of the ONE reminder the text refers to, else None (never a guess)."""
    text = request.text
    if BULK_RE.search(text):
        return None
    known = {item.id.lower() for item in request.reminders}
    if any(token.lower() not in known for token in ID_LIKE_RE.findall(text)):
        return None
    named = [item for item in request.reminders if _mentions(text, item.id)]
    if named:
        return named[0].id if len(named) == 1 else None
    wanted = content_words(text, TARGET_STOP)
    scores = [
        (len(content_words(item.task, TARGET_STOP) & wanted), item) for item in request.reminders
    ]
    best = max((score for score, _ in scores), default=0)
    winners = [item for score, item in scores if score == best]
    if best == 0 or len(winners) != 1:
        return None
    return winners[0].id


def _snooze_minutes(evidence: Evidence, model: object) -> int | None:
    if not evidence.durations:
        return None
    try:
        return _choose(evidence.durations, model)
    except _Unresolved:
        return None


def _has_time(spec: object) -> bool:
    if not isinstance(spec, dict):
        return False
    return spec.get("time") is not None or spec.get("offset_minutes") is not None


def _can_promote(grounded: dict, missing: list[str], text: str) -> bool:
    """A clarify that only asked for a time the text actually states becomes a create."""
    return (
        missing in ([], ["time"])
        and grounded["task"] is not None
        and _has_time(grounded["time_spec"])
        and grounded["recurrence"] in RECURRENCES
        and CREATE_CUE_RE.search(text) is not None
        and MODIFY_CUE_RE.search(text) is None
        and HARM_RE.search(text) is None
    )


def _ground_clarify(grounded: dict, model_task: object, text: str) -> dict:
    missing = order_missing(grounded.get("missing"))
    if _can_promote(grounded, missing, text):
        return {**grounded, "intent": "create", "missing": [], "question": None}
    fixed = list(missing)
    if model_task is not None and grounded["task"] is None and "task" not in fixed:
        fixed.insert(0, "task")
    if _has_time(grounded["time_spec"]) and "time" in fixed and len(fixed) > 1:
        fixed.remove("time")
    if fixed != missing:
        grounded = {**grounded, "missing": fixed, "question": None}
    return grounded


def ground(extraction: dict, request: Request) -> dict:
    """Return a copy of ``extraction`` whose action-driving fields are supported by the text."""
    intent = extraction.get("intent")
    if intent == "reject":
        return extraction
    evidence = read_evidence(request.text, request.now.date())
    grounded = dict(extraction)
    grounded["task"] = ground_task(extraction.get("task"), request.text)
    grounded["recurrence"] = ground_recurrence(evidence, extraction.get("recurrence"))
    if grounded["recurrence"] == "weekdays":
        evidence.days = [day for day in evidence.days if not (day and "weekday" in day)]
    grounded["time_spec"] = ground_time_spec(
        extraction.get("time_spec"), evidence, prefer_last=intent == "reschedule"
    )
    grounded["snooze_minutes"] = _snooze_minutes(evidence, extraction.get("snooze_minutes"))
    grounded["target_id"] = ground_target(request) if intent in TARGET_INTENTS else None
    if intent == "clarify":
        return _ground_clarify(grounded, extraction.get("task"), request.text)
    return grounded
