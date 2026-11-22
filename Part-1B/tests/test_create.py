"""T011 – US1 create: R-1…R-7, R-11, FR-004, FR-007, FR-008, INV-1, INV-7, INV-8."""

import pytest

from tests.conftest import ext, req, run, ts


def create(time_spec, task="call mom", recurrence="none", request=None):
    return run(ext(task=task, time_spec=time_spec, recurrence=recurrence), request)


def test_us1_as1_tomorrow_at_6pm():
    out = create(ts(day_offset=1, time="18:00"))
    assert out == {
        "intent": "create",
        "task": "call mom",
        "due_at": "2026-11-24T18:00:00+05:30",
        "recurrence": "none",
        "target_id": None,
        "snooze_minutes": None,
        "missing": [],
        "question": None,
        "reason": None,
    }


def test_r1_offset_minutes():
    assert create(ts(offset_minutes=45))["due_at"] == "2026-11-23T09:45:00+05:30"


def test_r1_offset_keeps_seconds_of_now():
    out = create(ts(offset_minutes=10), request=req(now="2026-11-23T09:00:30+05:30"))
    assert out["due_at"] == "2026-11-23T09:10:30+05:30"


@pytest.mark.parametrize(
    ("weekday", "expected"),
    [("friday", "2026-11-27"), ("tuesday", "2026-11-24"), ("monday", "2026-11-30")],
)
def test_r2_weekday_strictly_after_today(weekday, expected):
    out = create(ts(weekday=weekday, time="10:00"))
    assert out["due_at"] == f"{expected}T10:00:00+05:30"


def test_r2_explicit_date():
    assert create(ts(date="2026-12-25", time="08:00"))["due_at"] == "2026-12-25T08:00:00+05:30"


@pytest.mark.parametrize(
    ("time", "expected"),
    [("08:00", "2026-11-24T08:00:00+05:30"), ("10:00", "2026-11-23T10:00:00+05:30")],
)
def test_fr007_time_without_date_next_occurrence(time, expected):
    assert create(ts(time=time))["due_at"] == expected


def test_midnight_is_next_day():
    assert create(ts(time="00:00"))["due_at"] == "2026-11-24T00:00:00+05:30"


def test_inv8_dst_offset():
    request = req(now="2027-03-13T20:00:00-05:00", tz="America/New_York")
    assert create(ts(day_offset=1, time="09:00"), request=request)["due_at"] == (
        "2027-03-14T09:00:00-04:00"
    )


def test_fr008_weekdays_first_occurrence():
    out = create(ts(time="07:30"), recurrence="weekdays")
    assert (out["recurrence"], out["due_at"]) == ("weekdays", "2026-11-24T07:30:00+05:30")


def test_r7_weekdays_rolls_weekend_to_monday():
    request = req(now="2026-11-27T20:00:00+05:30")  # Friday evening
    out = create(ts(time="07:30"), recurrence="weekdays", request=request)
    assert out["due_at"] == "2026-11-30T07:30:00+05:30"


@pytest.mark.parametrize("recurrence", ["daily", "weekly", "monthly"])
def test_fr008_recurrence_values_pass_through(recurrence):
    assert create(ts(day_offset=1, time="09:00"), recurrence=recurrence)["recurrence"] == recurrence


def test_r11_long_task_truncated_to_120():
    out = create(ts(day_offset=1, time="09:00"), task="word " * 60)
    assert out["intent"] == "create" and 1 <= len(out["task"]) <= 120


@pytest.mark.parametrize(
    "spec",
    [
        ts(day_offset=1),  # R-4 date without time
        ts(weekday="friday"),
        None,  # no time information at all
        ts(),
    ],
)
def test_gr4_no_time_means_clarify(spec):
    out = create(spec)
    assert (out["intent"], out["missing"], out["due_at"]) == ("clarify", ["time"], None)


@pytest.mark.parametrize(
    "spec",
    [
        ts(date="2026-11-22", time="15:00"),  # yesterday (GR-5)
        ts(day_offset=0, time="08:00"),  # earlier today (GR-5)
        ts(date="2028-01-01", time="09:00"),  # > 365 days (INV-7)
        ts(offset_minutes=0),
    ],
)
def test_gr5_inv7_out_of_range_means_clarify(spec):
    out = create(spec)
    assert (out["intent"], out["missing"], out["due_at"]) == ("clarify", ["time"], None)


def test_r8_create_without_task_means_clarify_task():
    out = run(ext(task=None, time_spec=ts(day_offset=1, time="09:00"), recurrence="none"))
    assert out["intent"] == "clarify" and "task" in out["missing"]
