"""Request parsing/validation (FR-001, data-model.md / Request) and the GR-1 precheck."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from remindme.errors import RequestError

MAX_TEXT_LENGTH = 500
REASON_EMPTY = "input is empty"
REASON_TOO_LONG = "input is longer than 500 characters"
REQUIRED_KEYS = ("text", "now", "timezone", "reminders")


@dataclass(frozen=True)
class Reminder:
    """An existing reminder supplied by the caller."""

    id: str
    task: str
    due_at: datetime


@dataclass(frozen=True)
class Request:
    """A validated request. ``now`` is expressed in the request's timezone."""

    text: str
    now: datetime
    timezone: str
    tz: ZoneInfo
    reminders: tuple[Reminder, ...]

    def reminder(self, reminder_id: object) -> Reminder | None:
        """Return the reminder with this id, or None."""
        for item in self.reminders:
            if item.id == reminder_id:
                return item
        return None


def parse_request(raw: object) -> Request:
    """Validate a raw request dict; raise RequestError on any problem."""
    if not isinstance(raw, Mapping):
        raise RequestError("request must be a JSON object")
    absent = [key for key in REQUIRED_KEYS if key not in raw]
    if absent:
        raise RequestError(f"request is missing keys: {', '.join(absent)}")
    text = raw["text"]
    if not isinstance(text, str):
        raise RequestError("text must be a string")
    tz = parse_timezone(raw["timezone"])
    now = parse_timestamp(raw["now"], "now").astimezone(tz)
    reminders = _parse_reminders(raw["reminders"])
    return Request(text=text, now=now, timezone=raw["timezone"], tz=tz, reminders=reminders)


def parse_timestamp(value: object, field: str) -> datetime:
    """Parse an ISO-8601 timestamp that carries a UTC offset."""
    if not isinstance(value, str) or not value.strip():
        raise RequestError(f"{field} must be an ISO-8601 timestamp string")
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise RequestError(f"{field} is not a valid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RequestError(f"{field} must include a UTC offset: {value!r}")
    return parsed


def parse_timezone(value: object) -> ZoneInfo:
    """Return the ZoneInfo for a valid IANA zone name."""
    if not isinstance(value, str) or not value.strip():
        raise RequestError("timezone must be a non-empty IANA zone name")
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise RequestError(f"unknown timezone: {value!r}") from exc


def _parse_reminders(value: object) -> tuple[Reminder, ...]:
    if not isinstance(value, list):
        raise RequestError("reminders must be a list")
    parsed = tuple(_parse_reminder(item, index) for index, item in enumerate(value))
    ids = [item.id for item in parsed]
    if len(set(ids)) != len(ids):
        raise RequestError("reminder ids must be unique")
    return parsed


def _parse_reminder(item: object, index: int) -> Reminder:
    if not isinstance(item, Mapping):
        raise RequestError(f"reminders[{index}] must be an object")
    for key in ("id", "task"):
        field = item.get(key)
        if not isinstance(field, str) or not field.strip():
            raise RequestError(f"reminders[{index}].{key} must be a non-empty string")
    due_at = parse_timestamp(item.get("due_at"), f"reminders[{index}].due_at")
    return Reminder(id=item["id"], task=item["task"], due_at=due_at)


def precheck_text(text: str) -> str | None:
    """GR-1: return the reject reason for empty/overlong input, else None."""
    trimmed = text.strip()
    if not trimmed:
        return REASON_EMPTY
    if len(trimmed) > MAX_TEXT_LENGTH:
        return REASON_TOO_LONG
    return None
