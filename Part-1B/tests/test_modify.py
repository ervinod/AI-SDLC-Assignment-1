"""T016 – US2 reschedule / snooze / cancel: FR-005, R-9, INV-2…INV-4, INV-9, GR-6."""

import pytest

from tests.conftest import REMINDERS, ext, req, run, ts

R = req(reminders=REMINDERS)


def test_us2_as1_reschedule():
    out = run(ext("reschedule", target_id="r2", time_spec=ts(weekday="friday", time="16:00")), R)
    assert (out["intent"], out["target_id"], out["due_at"]) == (
        "reschedule",
        "r2",
        "2026-11-27T16:00:00+05:30",
    )
    assert out["snooze_minutes"] is None and out["missing"] == []


def test_us2_as2_snooze_from_reminder_due_time():
    out = run(ext("snooze", target_id="r1", snooze_minutes=15), R)
    assert (out["intent"], out["target_id"], out["snooze_minutes"], out["due_at"]) == (
        "snooze",
        "r1",
        15,
        "2026-11-23T09:45:00+05:30",
    )


def test_snooze_ignores_model_time_spec():
    out = run(ext("snooze", target_id="r3", snooze_minutes=30, time_spec=ts(time="23:00")), R)
    assert out["due_at"] == "2026-11-23T18:30:00+05:30"


@pytest.mark.parametrize("minutes", [0, -5, 1441, None])
def test_snooze_minutes_out_of_range_means_clarify(minutes):
    out = run(ext("snooze", target_id="r1", snooze_minutes=minutes), R)
    assert out["intent"] == "clarify" and out["missing"] == ["time"]


def test_us2_as3_cancel():
    out = run(ext("cancel", target_id="r3"), R)
    assert (out["intent"], out["target_id"], out["due_at"]) == ("cancel", "r3", None)


@pytest.mark.parametrize("intent", ["reschedule", "snooze", "cancel"])
@pytest.mark.parametrize("target", ["r99", None, ""])
def test_gr6_unknown_or_missing_target_means_clarify(intent, target):
    out = run(
        ext(intent, target_id=target, snooze_minutes=10, time_spec=ts(day_offset=1, time="10:00")),
        R,
    )
    assert (out["intent"], out["missing"], out["target_id"]) == ("clarify", ["target"], None)


def test_reschedule_without_time_means_clarify():
    out = run(ext("reschedule", target_id="r2", time_spec=None), R)
    assert (out["intent"], out["missing"]) == ("clarify", ["time"])


def test_reschedule_into_past_means_clarify():
    out = run(ext("reschedule", target_id="r2", time_spec=ts(day_offset=0, time="07:00")), R)
    assert (out["intent"], out["missing"]) == ("clarify", ["time"])
