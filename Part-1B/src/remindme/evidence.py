"""Deterministic evidence read directly from the user's text (constitution II, GR-4…GR-6).

The model's Extraction is untrusted. This module finds what the text itself says about clock
times, relative offsets, durations, days and recurrence, so that ``grounding`` can accept a model
value only when the text supports it (and degrade to ``clarify`` when it does not).
"""

import calendar
import re
from dataclasses import dataclass, field
from datetime import date, time

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4,
    "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9, "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}  # fmt: skip
NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
    "twenty": 20, "thirty": 30, "forty-five": 45, "forty five": 45, "forty": 40, "fifty": 50,
    "sixty": 60, "ninety": 90,
}  # fmt: skip
HOURS_PER_HALF_DAY = 12
MONTHS_AHEAD = 13

_NUM = r"\d+(?:\.\d+)?|" + "|".join(
    re.escape(word) for word in sorted(NUMBER_WORDS, key=len, reverse=True)
)
_MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))
_WEEKDAY = "|".join(WEEKDAYS)
_ORD = r"(?:st|nd|rd|th)"
_FLAGS = re.IGNORECASE

DURATION_RE = re.compile(
    rf"\b(?:(?P<prefix>in|after|within)\s+)?"
    rf"(?:(?P<frac>(?:a\s+)?(?:half|quarter)(?:\s+of)?\s+an?)|(?P<num>{_NUM}))\s*"
    r"(?P<unit>minutes?|mins?|hours?|hrs?)\b(?P<andhalf>\s+and\s+a\s+half)?",
    _FLAGS,
)
WEEKS_RE = re.compile(rf"\bin\s+(?P<num>{_NUM})\s+(?P<unit>days?|weeks?)\b", _FLAGS)
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
DAY_MONTH_RE = re.compile(
    rf"\b(?:the\s+)?(\d{{1,2}}){_ORD}?\s+(?:of\s+)?({_MONTH})\b\.?(?:,?\s+(\d{{4}})\b)?", _FLAGS
)
MONTH_DAY_RE = re.compile(
    rf"\b({_MONTH})\.?\s+(?:the\s+)?(\d{{1,2}}){_ORD}?\b(?:,?\s+(\d{{4}})\b)?", _FLAGS
)
ORDINAL_RE = re.compile(rf"\bthe\s+(\d{{1,2}}){_ORD}\b", _FLAGS)
RELATIVE_DAY_RE = re.compile(
    r"\b(?P<two>(?:the\s+)?day\s+after\s+tomorrow)\b|\b(?P<one>tomorrow|tmrw|tmr)\b"
    r"|\b(?P<zero>today|tonight|this\s+(?:morning|afternoon|evening))\b"
    r"|\b(?P<minus>yesterday)\b",
    _FLAGS,
)
WEEKDAY_RE = re.compile(rf"\b({_WEEKDAY})s?\b", _FLAGS)
VAGUE_DAY_RE = re.compile(
    r"\b(?:next|this|coming)\s+(?:week|month|year|weekend)\b|\bweekend\b"
    r"|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b",
    _FLAGS,
)
MERIDIEM_RE = re.compile(r"\b(\d{1,2})(?:[:.](\d{2}))?\s*([ap])\.?\s?m\b\.?", _FLAGS)
NAMED_CLOCK_RE = re.compile(r"\b(noon|midday|midnight)\b", _FLAGS)
HHMM_RE = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")
BARE_HOUR_RE = re.compile(
    rf"\b(?:at|around|by)\s+(\d{{1,2}})\b(?!\s*{_ORD}\b)(?:\s*o'?\s?clock\b)?"
    r"|\b(\d{1,2})\s*o'?\s?clock\b",
    _FLAGS,
)
EVENING_RE = re.compile(r"\b(tonight|evening|afternoon|night|dinner)\b", _FLAGS)
MORNING_RE = re.compile(r"\b(morning|breakfast|dawn|sunrise)\b", _FLAGS)

RECURRENCE_CUES = (
    (
        "weekdays",
        r"\bweek\s?days?\b|\bwork(?:ing)?\s?days?\b|\bbusiness\s+days?\b"
        r"|\bmonday\s*(?:to|through|thru|-|–)\s*friday\b",
    ),
    (
        "daily",
        r"\b(?:every|each)\s+(?:single\s+)?(?:day|morning|afternoon|evening|night)\b"
        r"|\beveryday\b|\bdaily\b|\bnightly\b",
    ),
    (
        "weekly",
        rf"\bweekly\b|\b(?:every|each)\s+(?:week|{_WEEKDAY})\b|\bon\s+(?:{_WEEKDAY})s\b",
    ),
    ("monthly", r"\bmonthly\b|\b(?:every|each)\s+month\b"),
)
UNSUPPORTED_RECURRENCE_RE = re.compile(
    r"\bevery\s+(?:other|second|\d+|two|three|four)\b|\b(?:bi-?weekly|fortnight\w*)\b"
    r"|\b(?:yearly|annually|hourly)\b|\bevery\s+(?:year|hour)\b",
    _FLAGS,
)


@dataclass
class Evidence:
    """What the text itself states. Each clock mention lists its plausible readings."""

    clocks: list[tuple[time, ...]] = field(default_factory=list)
    offsets: list[int] = field(default_factory=list)
    durations: list[int] = field(default_factory=list)
    days: list[dict | None] = field(default_factory=list)
    recurrences: set[str] = field(default_factory=set)
    unsupported_recurrence: bool = False


def _blank(text: str, match: re.Match) -> str:
    start, end = match.span()
    return text[:start] + " " * (end - start) + text[end:]


def _number(token: str) -> float:
    token = " ".join(token.lower().split())
    return float(NUMBER_WORDS[token]) if token in NUMBER_WORDS else float(token)


def _duration_minutes(match: re.Match) -> int | None:
    unit = 60 if match.group("unit").lower().startswith("h") else 1
    if match.group("frac"):
        value = 0.5 if "half" in match.group("frac").lower() else 0.25
        if unit == 1:
            return None
    else:
        value = _number(match.group("num"))
    if match.group("andhalf"):
        value += 0.5
    minutes = value * unit
    return int(minutes) if minutes == int(minutes) and minutes > 0 else None


def _durations(text: str, evidence: Evidence) -> str:
    for match in list(DURATION_RE.finditer(text)):
        minutes = _duration_minutes(match)
        if minutes is None:
            continue
        evidence.durations.append(minutes)
        if match.group("prefix"):
            evidence.offsets.append(minutes)
        text = _blank(text, match)
    return text


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _month_day(today: date, month: int, day: int, year: str | None) -> dict | None:
    if year:
        found = _safe_date(int(year), month, day)
    else:
        found = _safe_date(today.year, month, day)
        if found is not None and found < today:
            found = _safe_date(today.year + 1, month, day)
    return {"date": found.isoformat()} if found else None


def _next_day_of_month(today: date, day: int) -> dict | None:
    year, month = today.year, today.month
    for _ in range(MONTHS_AHEAD):
        if day <= calendar.monthrange(year, month)[1]:
            found = date(year, month, day)
            if found >= today:
                return {"date": found.isoformat()}
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)  # noqa: PLR2004
    return None


def _days(text: str, today: date, evidence: Evidence) -> str:
    found: list[tuple[int, dict | None]] = []
    for match in list(ISO_DATE_RE.finditer(text)):
        parsed = _safe_date(*(int(part) for part in match.groups()))
        found.append((match.start(), {"date": parsed.isoformat()} if parsed else None))
        text = _blank(text, match)
    for regex, order in ((DAY_MONTH_RE, (2, 1)), (MONTH_DAY_RE, (1, 2))):
        for match in list(regex.finditer(text)):
            month = MONTHS[match.group(order[0]).lower()]
            day = int(match.group(order[1]))
            found.append((match.start(), _month_day(today, month, day, match.group(3))))
            text = _blank(text, match)
    for match in list(ORDINAL_RE.finditer(text)):
        found.append((match.start(), _next_day_of_month(today, int(match.group(1)))))
        text = _blank(text, match)
    text = _relative_days(text, found)
    for match in list(VAGUE_DAY_RE.finditer(text)):
        found.append((match.start(), None))
        text = _blank(text, match)
    evidence.days = [part for _, part in sorted(found, key=lambda item: item[0])]
    return text


def _relative_days(text: str, found: list[tuple[int, dict | None]]) -> str:
    offsets = {"two": 2, "one": 1, "zero": 0, "minus": -1}
    for match in list(RELATIVE_DAY_RE.finditer(text)):
        found.append((match.start(), {"day_offset": offsets[match.lastgroup]}))
        text = _blank(text, match)
    for match in list(WEEKS_RE.finditer(text)):
        count = _number(match.group("num"))
        factor = 7 if match.group("unit").lower().startswith("w") else 1
        valid = count == int(count)
        found.append((match.start(), {"day_offset": int(count) * factor} if valid else None))
        text = _blank(text, match)
    for match in list(WEEKDAY_RE.finditer(text)):
        found.append((match.start(), {"weekday": match.group(1).lower()}))
        text = _blank(text, match)
    return text


def _readings(hour: int, minute: int, original: str) -> tuple[time, ...]:
    """Readings of a clock time written without am/pm (24-hour unless context says pm/am)."""
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:  # noqa: PLR2004
        return ()
    if hour == 0 or hour > HOURS_PER_HALF_DAY:
        return (time(hour, minute),)
    morning = time(hour % HOURS_PER_HALF_DAY, minute)
    evening = time(hour % HOURS_PER_HALF_DAY + HOURS_PER_HALF_DAY, minute)
    if EVENING_RE.search(original):
        return (evening,)
    if MORNING_RE.search(original):
        return (morning,)
    return (time(hour, minute),)


def _clocks(text: str, original: str, evidence: Evidence) -> None:
    found: list[tuple[int, tuple[time, ...]]] = []
    for match in list(MERIDIEM_RE.finditer(text)):
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        valid = 1 <= hour <= HOURS_PER_HALF_DAY and minute <= 59  # noqa: PLR2004
        shift = HOURS_PER_HALF_DAY if match.group(3).lower() == "p" else 0
        readings = (time(hour % HOURS_PER_HALF_DAY + shift, minute),) if valid else ()
        found.append((match.start(), readings))
        text = _blank(text, match)
    for match in list(NAMED_CLOCK_RE.finditer(text)):
        clock = time(0, 0) if "night" in match.group(1).lower() else time(12, 0)
        found.append((match.start(), (clock,)))
        text = _blank(text, match)
    for match in list(HHMM_RE.finditer(text)):
        found.append((match.start(), _readings(int(match.group(1)), int(match.group(2)), original)))
        text = _blank(text, match)
    for match in list(BARE_HOUR_RE.finditer(text)):
        found.append((match.start(), _bare_hour(int(match.group(1) or match.group(2)), original)))
    evidence.clocks = [readings for _, readings in sorted(found, key=lambda item: item[0])]


def _bare_hour(hour: int, original: str) -> tuple[time, ...]:
    """A bare hour ("at 5") is ambiguous between am and pm unless the context decides it."""
    decided = EVENING_RE.search(original) or MORNING_RE.search(original)
    if decided or hour == 0 or hour > HOURS_PER_HALF_DAY:
        return _readings(hour, 0, original)
    base = hour % HOURS_PER_HALF_DAY
    return (time(base, 0), time(base + HOURS_PER_HALF_DAY, 0))


def _recurrences(text: str, evidence: Evidence) -> None:
    evidence.recurrences = {
        name for name, pattern in RECURRENCE_CUES if re.search(pattern, text, _FLAGS)
    }
    evidence.unsupported_recurrence = bool(UNSUPPORTED_RECURRENCE_RE.search(text))


def read_evidence(text: str, today: date) -> Evidence:
    """Parse the user's text into Evidence (durations → dates/days → clock times)."""
    evidence = Evidence()
    _recurrences(text, evidence)
    rest = _durations(text, evidence)
    rest = _days(rest, today, evidence)
    _clocks(rest, text, evidence)
    return evidence

