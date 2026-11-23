"""Deterministic post-processing of a model Extraction into a Response (plan.md R-1…R-11).

The model only supplies a symbolic ``time_spec``; every date, timezone, snooze and target
decision is made here, after ``grounding`` has checked the extraction against the user's text.
Anything invalid degrades to a safe ``clarify`` (or keeps ``reject``).
"""

import calendar
import re
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta

from remindme.grounding import ground
from remindme.request import Reminder, Request
from remindme.response import (
    INTENTS,
    LIMITS,
    MAX_HORIZON,
    MAX_SNOOZE_MINUTES,
    RECURRENCES,
    clarify,
    contains_canary,
    format_due,
    make_response,
    order_missing,
    reject,
    truncate,
)
from remindme.safety import REFUSAL_REASON, harmful

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
CLOCK_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})(?::\d{2})?$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_OFFSET_MINUTES = 2 * 366 * 24 * 60
MAX_DAY_OFFSET = 2 * 366
MAX_ROLLS = 400
SATURDAY = 5
DECEMBER = 12


class _TimeError(Exception):
    """Internal: the time specification cannot be resolved to a valid future time."""


def postprocess(extraction: object, request: Request) -> dict:
    """Turn an (untrusted) Extraction into a response that satisfies SCH and INV."""
    if harmful(request.text):  # GR-2 enforced in code, whatever the model returned
        return reject(REFUSAL_REASON)
    if not isinstance(extraction, dict):
        return clarify(["task"])
    intent = extraction.get("intent")
    if intent not in INTENTS:
        return clarify(["task"])
    if contains_canary(extraction):
        return reject() if intent == "reject" else clarify(["task"])
    grounded = ground(extraction, request)  # constitution II: only text-supported values act
    return _HANDLERS[grounded["intent"]](grounded, request)


def fallback(extraction: object) -> dict:
    """R-8 last-resort response for an extraction that could not be processed."""
    if isinstance(extraction, dict) and extraction.get("intent") == "reject":
        return reject()
    return clarify(["task"])


# --- intent handlers -------------------------------------------------------------------------


def _handle_reject(extraction: dict, _request: Request) -> dict:
    return reject(extraction.get("reason"))


def _handle_clarify(extraction: dict, _request: Request) -> dict:
    task = truncate(extraction.get("task"), LIMITS["task"])
    missing = order_missing(extraction.get("missing"))
    if not missing:
        missing = ["time"] if task else ["task"]
    return clarify(missing, question=extraction.get("question"), task=task)


def _handle_create(extraction: dict, request: Request) -> dict:
    missing = []
    task = truncate(extraction.get("task"), LIMITS["task"])
    if task is None:
        missing.append("task")
    recurrence = _recurrence(extraction.get("recurrence"))
    due = None
    if recurrence is not None:
        due = resolve_due(extraction.get("time_spec"), request, recurrence)
    if due is None:
        missing.append("time")
    if missing:
        return clarify(missing, task=task)
    return make_response("create", task=task, due_at=format_due(due), recurrence=recurrence)


def _handle_reschedule(extraction: dict, request: Request) -> dict:
    target = _target(extraction, request)
    due = resolve_due(extraction.get("time_spec"), request, "none")
    missing = _missing_for(due is None, target is None)
    if missing:
        return clarify(missing)
    return make_response("reschedule", target_id=target.id, due_at=format_due(due))


def _handle_snooze(extraction: dict, request: Request) -> dict:
    target = _target(extraction, request)
    minutes = _snooze_minutes(extraction)
    due = None
    if target is not None and minutes is not None:
        due = snooze_due(target, minutes, request)
    missing = _missing_for(minutes is None or (target is not None and due is None), target is None)
    if missing:
        return clarify(missing)
    return make_response(
        "snooze", target_id=target.id, snooze_minutes=minutes, due_at=format_due(due)
    )


def _handle_cancel(extraction: dict, request: Request) -> dict:
    target = _target(extraction, request)
    if target is None:
        return clarify(["target"])
    return make_response("cancel", target_id=target.id)


_HANDLERS: dict[str, Callable[[dict, Request], dict]] = {
    "create": _handle_create,
    "reschedule": _handle_reschedule,
    "snooze": _handle_snooze,
    "cancel": _handle_cancel,
    "clarify": _handle_clarify,
    "reject": _handle_reject,
}


def _missing_for(time_missing: bool, target_missing: bool) -> list[str]:
    return [name for name, flag in (("time", time_missing), ("target", target_missing)) if flag]


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _recurrence(value: object) -> str | None:
    """None/absent → ``none``; a valid enum value → itself; anything else → None (invalid)."""
    if value is None:
        return "none"
    if isinstance(value, str) and value.strip().lower() in RECURRENCES:
        return value.strip().lower()
    return None


def _target(extraction: dict, request: Request) -> Reminder | None:
    """GR-6 / INV-9: the target must be the id of a supplied reminder."""
    target_id = extraction.get("target_id")
    if not isinstance(target_id, str):
        return None
    return request.reminder(target_id)


def _snooze_minutes(extraction: dict) -> int | None:
    value = extraction.get("snooze_minutes")
    spec = extraction.get("time_spec")
    if value is None and isinstance(spec, dict):
        value = spec.get("offset_minutes")
    if _is_int(value) and 1 <= value <= MAX_SNOOZE_MINUTES:
        return value
    return None


def snooze_due(target: Reminder, minutes: int, request: Request) -> datetime | None:
    """R-9: target.due_at + minutes, in the request timezone; None if outside the window."""
    due = (target.due_at.astimezone(UTC) + timedelta(minutes=minutes)).astimezone(request.tz)
    return due if _in_window(due, request.now) else None


# --- time resolution (R-1…R-7) ---------------------------------------------------------------


def resolve_due(spec: object, request: Request, recurrence: str) -> datetime | None:
    """Resolve a symbolic time_spec to an aware datetime in the request timezone, or None."""
    if not isinstance(spec, dict):
        return None
    try:
        if spec.get("offset_minutes") is not None:
            due = _resolve_offset(spec["offset_minutes"], request)
        else:
            due = _resolve_clock(spec, request, recurrence)
    except (_TimeError, OverflowError, ValueError):
        return None
    return due if _in_window(due, request.now) else None


def _in_window(due: datetime, now: datetime) -> bool:
    """R-6 / INV-7: strictly after now and at most 365 days after now."""
    now_utc = now.astimezone(UTC)
    return now_utc < due.astimezone(UTC) <= now_utc + MAX_HORIZON


def _resolve_offset(value: object, request: Request) -> datetime:
    """R-1: now + offset (absolute arithmetic); keeps now's seconds (R-5)."""
    if not _is_int(value) or abs(value) > MAX_OFFSET_MINUTES:
        raise _TimeError
    due = request.now.astimezone(UTC) + timedelta(minutes=value)
    return due.astimezone(request.tz).replace(microsecond=0)


def _resolve_clock(spec: dict, request: Request, recurrence: str) -> datetime:
    clock = _parse_clock(spec.get("time"))
    day = _date_part(spec, request.now.date())
    if day is None:
        due = _localize(request.now.date(), clock, request)
        if not _after(due, request.now):
            due = _localize(request.now.date() + timedelta(days=1), clock, request)
        day = due.date()
    if recurrence == "none":
        return _localize(day, clock, request)
    return _first_occurrence(day, clock, request, recurrence)


def _parse_clock(value: object) -> time:
    """24-hour ``HH:MM``; a missing or invalid time is a time problem (R-4, GR-4)."""
    if not isinstance(value, str):
        raise _TimeError
    match = CLOCK_PATTERN.match(value.strip())
    if match is None:
        raise _TimeError
    try:
        return time(int(match.group(1)), int(match.group(2)))
    except ValueError as exc:
        raise _TimeError from exc


def _date_part(spec: dict, today: date) -> date | None:
    """R-2: explicit date > day_offset > weekday; None when no date part is given."""
    explicit = spec.get("date")
    if explicit is not None:
        if not isinstance(explicit, str) or not DATE_PATTERN.match(explicit.strip()):
            raise _TimeError
        return date.fromisoformat(explicit.strip())
    offset = spec.get("day_offset")
    if offset is not None:
        if not _is_int(offset) or abs(offset) > MAX_DAY_OFFSET:
            raise _TimeError
        return today + timedelta(days=offset)
    weekday = spec.get("weekday")
    if weekday is not None:
        if not isinstance(weekday, str) or weekday.strip().lower() not in WEEKDAYS:
            raise _TimeError
        index = WEEKDAYS.index(weekday.strip().lower())
        return today + timedelta(days=(index - today.weekday()) % 7 or 7)
    return None


def _first_occurrence(day: date, clock: time, request: Request, recurrence: str) -> datetime:
    """R-7: first future occurrence of a recurring reminder (weekdays skip Sat/Sun)."""
    anchor = day.day
    for _ in range(MAX_ROLLS):
        if recurrence == "weekdays" and day.weekday() >= SATURDAY:
            day += timedelta(days=7 - day.weekday())
        due = _localize(day, clock, request)
        if _after(due, request.now):
            return due
        day = _advance(day, recurrence, anchor)
    raise _TimeError


def _advance(day: date, recurrence: str, anchor: int) -> date:
    if recurrence == "weekly":
        return day + timedelta(days=7)
    if recurrence == "monthly":
        year, month = (day.year + 1, 1) if day.month == DECEMBER else (day.year, day.month + 1)
        return date(year, month, min(anchor, calendar.monthrange(year, month)[1]))
    return day + timedelta(days=1)


def _localize(day: date, clock: time, request: Request) -> datetime:
    """R-5: attach the zone (DST-aware) and normalise via UTC so the offset is always valid."""
    naive = datetime.combine(day, clock)
    return naive.replace(tzinfo=request.tz).astimezone(UTC).astimezone(request.tz)


def _after(left: datetime, right: datetime) -> bool:
    return left.astimezone(UTC) > right.astimezone(UTC)
