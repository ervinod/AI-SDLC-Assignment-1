"""T016 – US2 reschedule / snooze / cancel: FR-005, R-9, INV-2…INV-4, INV-9, GR-6.

T033 (2026-11-23, GR-7): each request text now states what the fake extraction claims.
Assertions are unchanged.
"""

import pytest

from tests.conftest import REMINDERS, ext, req, run, ts


def R(text):  # noqa: N802 - kept short; was a constant before T033
    return req(text, reminders=REMINDERS)


def test_us2_as1_reschedule():
    out = run(
        ext("reschedule", target_id="r2", time_spec=ts(weekday="friday", time="16:00")),
        R("move my dentist reminder to friday at 4pm"),
    )
    assert (out["intent"], out["target_id"], out["due_at"]) == (
        "reschedule",
        "r2",
        "2026-11-27T16:00:00+05:30",
    )
    assert out["snooze_minutes"] is None and out["missing"] == []


def test_us2_as2_snooze_from_reminder_due_time():
    out = run(
        ext("snooze", target_id="r1", snooze_minutes=15), R("snooze my medicine by 15 minutes")
    )
    assert (out["intent"], out["target_id"], out["snooze_minutes"], out["due_at"]) == (
        "snooze",
        "r1",
        15,
        "2026-11-23T09:45:00+05:30",
    )


def test_snooze_ignores_model_time_spec():
    out = run(
        ext("snooze", target_id="r3", snooze_minutes=30, time_spec=ts(time="23:00")),
        R("snooze the gym reminder for 30 minutes"),
    )
    assert out["due_at"] == "2026-11-23T18:30:00+05:30"


@pytest.mark.parametrize("minutes", [0, -5, 1441, None])
def test_snooze_minutes_out_of_range_means_clarify(minutes):
    said = "" if minutes is None else f" by {minutes} minutes"
    out = run(ext("snooze", target_id="r1", snooze_minutes=minutes), R(f"snooze my medicine{said}"))
    assert out["intent"] == "clarify" and out["missing"] == ["time"]


def test_us2_as3_cancel():
    out = run(ext("cancel", target_id="r3"), R("cancel the gym reminder"))
    assert (out["intent"], out["target_id"], out["due_at"]) == ("cancel", "r3", None)


@pytest.mark.parametrize("intent", ["reschedule", "snooze", "cancel"])
@pytest.mark.parametrize("target", ["r99", None, ""])
def test_gr6_unknown_or_missing_target_means_clarify(intent, target):
    out = run(
        ext(intent, target_id=target, snooze_minutes=10, time_spec=ts(day_offset=1, time="10:00")),
        R(f"{intent} reminder {target or 'for yoga'} by 10 minutes, tomorrow at 10am"),
    )
    assert (out["intent"], out["missing"], out["target_id"]) == ("clarify", ["target"], None)


def test_reschedule_without_time_means_clarify():
    out = run(
        ext("reschedule", target_id="r2", time_spec=None), R("reschedule my dentist reminder")
    )
    assert (out["intent"], out["missing"]) == ("clarify", ["time"])


def test_reschedule_into_past_means_clarify():
    out = run(
        ext("reschedule", target_id="r2", time_spec=ts(day_offset=0, time="07:00")),
        R("move my dentist reminder to today at 7am"),
    )
    assert (out["intent"], out["missing"]) == ("clarify", ["time"])
