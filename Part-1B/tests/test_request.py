"""T007 – FR-001 request validation and GR-1 pre-check (no model call)."""

import pytest

from remindme.agent import RequestError, handle
from tests.conftest import KEYS, REMINDERS, FakeExtractor, ext, req, ts


@pytest.mark.parametrize(
    "bad",
    [
        {"now": "2026-11-23T09:00:00+05:30", "timezone": "Asia/Kolkata", "reminders": []},
        req(now="2026-11-23T09:00:00"),  # no offset
        req(now="not a date"),
        req(tz="Mars/Olympus_Mons"),
        {**req(), "reminders": "r1"},
        req(reminders=[{"id": "r1", "task": "x"}]),  # missing due_at
        req(reminders=[{"id": "r1", "task": "x", "due_at": "tomorrow"}]),
    ],
)
def test_fr001_invalid_request_raises_without_model_call(bad):
    fake = FakeExtractor(ext())
    with pytest.raises(RequestError):
        handle(bad, extractor=fake)
    assert fake.calls == 0


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("", "input is empty"),
        ("   \n\t ", "input is empty"),
        ("x" * 501, "input is longer than 500 characters"),
    ],
)
def test_gr1_reject_without_model_call(text, reason):
    fake = FakeExtractor(ext())
    out = handle(req(text), extractor=fake)
    assert fake.calls == 0
    assert set(out) == KEYS
    assert (out["intent"], out["reason"]) == ("reject", reason)
    assert out["due_at"] is None and out["target_id"] is None


def test_gr1_500_chars_is_allowed():
    fake = FakeExtractor(ext(task="read", time_spec=ts(offset_minutes=5), recurrence="none"))
    out = handle(req("y" * 500), extractor=fake)
    assert fake.calls == 1
    assert out["intent"] == "create"


def test_reminders_are_accepted():
    fake = FakeExtractor(ext("cancel", target_id="r1"))
    out = handle(req(reminders=REMINDERS), extractor=fake)
    assert out["target_id"] == "r1"
