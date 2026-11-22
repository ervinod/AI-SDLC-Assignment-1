"""Offline test helpers. Tests use only the public contract from plan.md:
``remindme.agent.handle(request, extractor)`` and ``remindme.errors``/``agent`` exceptions,
with a fake extractor returning `Extraction` objects (contracts/extraction.schema.json)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".harness"))

from evaluators import properties, structural  # noqa: E402
from remindme.agent import handle  # noqa: E402

NOW = "2026-11-23T09:00:00+05:30"  # Monday
TZ = "Asia/Kolkata"
REMINDERS = [
    {"id": "r1", "task": "Take medicine", "due_at": "2026-11-23T09:30:00+05:30"},
    {"id": "r2", "task": "Dentist appointment", "due_at": "2026-11-25T11:00:00+05:30"},
    {"id": "r3", "task": "Gym session", "due_at": "2026-11-23T18:00:00+05:30"},
]
KEYS = {
    "intent",
    "task",
    "due_at",
    "recurrence",
    "target_id",
    "snooze_minutes",
    "missing",
    "question",
    "reason",
}


def req(text="remind me", now=NOW, tz=TZ, reminders=None):
    return {"text": text, "now": now, "timezone": tz, "reminders": reminders or []}


def ts(offset_minutes=None, day_offset=None, weekday=None, date=None, time=None):
    return {
        "offset_minutes": offset_minutes,
        "day_offset": day_offset,
        "weekday": weekday,
        "date": date,
        "time": time,
    }


def ext(intent="create", **kw):
    base = {
        "intent": intent,
        "task": None,
        "time_spec": None,
        "recurrence": None,
        "target_id": None,
        "snooze_minutes": None,
        "missing": [],
        "question": None,
        "reason": None,
    }
    base.update(kw)
    return base


class FakeExtractor:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def run(extraction, request=None):
    """Run handle() with a fake extractor and assert the output satisfies SCH and INV-1…INV-10."""
    request = request or req()
    fake = FakeExtractor(extraction)
    out = handle(request, extractor=fake)
    assert set(out) == KEYS
    assert structural.check(out) == [], structural.check(out)
    assert properties.universal(out, request) == [], properties.universal(out, request)
    return out


@pytest.fixture
def fake():
    return FakeExtractor


PROVIDER_ENV = (
    "REMINDME_PROVIDER",
    "REMINDME_MODEL",
    "REMINDME_EFFORT",
    "REMINDME_OLLAMA_MODEL",
    "OLLAMA_HOST",
    "ANTHROPIC_API_KEY",
)


@pytest.fixture(autouse=True)
def _isolated_provider_env(monkeypatch):
    """Tests must not depend on the caller's environment (found by harness run-003)."""
    for name in PROVIDER_ENV:
        monkeypatch.delenv(name, raising=False)
