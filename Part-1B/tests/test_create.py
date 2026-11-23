"""T011 – US1 create: R-1…R-7, R-11, FR-004, FR-007, FR-008, INV-1, INV-7, INV-8.

T033 (2026-11-23, GR-7): each request text now states what the fake extraction claims, because the
application only acts on information grounded in the user's text. Assertions are unchanged.
"""

import pytest

from tests.conftest import ext, req, run, ts


def create(time_spec, text, task="call mom", recurrence="none", **request_kw):
    return run(ext(task=task, time_spec=time_spec, recurrence=recurrence), req(text, **request_kw))


def test_us1_as1_tomorrow_at_6pm():
    out = create(ts(day_offset=1, time="18:00"), "remind me to call mom tomorrow at 6pm")
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
    out = create(ts(offset_minutes=45), "in 45 minutes remind me to call mom")
    assert out["due_at"] == "2026-11-23T09:45:00+05:30"


def test_r1_offset_keeps_seconds_of_now():
    out = create(
        ts(offset_minutes=10),
        "remind me to call mom in 10 minutes",
        now="2026-11-23T09:00:30+05:30",
    )
    assert out["due_at"] == "2026-11-23T09:10:30+05:30"


@pytest.mark.parametrize(
    ("weekday", "expected"),
    [("friday", "2026-11-27"), ("tuesday", "2026-11-24"), ("monday", "2026-11-30")],
)
def test_r2_weekday_strictly_after_today(weekday, expected):
    out = create(ts(weekday=weekday, time="10:00"), f"remind me to call mom on {weekday} at 10am")
    assert out["due_at"] == f"{expected}T10:00:00+05:30"


def test_r2_explicit_date():
    out = create(ts(date="2026-12-25", time="08:00"), "remind me to call mom on 25 December at 8am")
    assert out["due_at"] == "2026-12-25T08:00:00+05:30"


@pytest.mark.parametrize(
    ("time", "said", "expected"),
    [
        ("08:00", "8am", "2026-11-24T08:00:00+05:30"),
        ("10:00", "10am", "2026-11-23T10:00:00+05:30"),
    ],
)
def test_fr007_time_without_date_next_occurrence(time, said, expected):
    assert create(ts(time=time), f"remind me to call mom at {said}")["due_at"] == expected


def test_midnight_is_next_day():
    out = create(ts(time="00:00"), "remind me to call mom at midnight")
    assert out["due_at"] == "2026-11-24T00:00:00+05:30"


def test_inv8_dst_offset():
    out = create(
        ts(day_offset=1, time="09:00"),
        "remind me to call mom tomorrow at 9am",
        now="2027-03-13T20:00:00-05:00",
        tz="America/New_York",
    )
    assert out["due_at"] == "2027-03-14T09:00:00-04:00"


def test_fr008_weekdays_first_occurrence():
    out = create(
        ts(time="07:30"), "every weekday at 7:30am remind me to call mom", recurrence="weekdays"
    )
    assert (out["recurrence"], out["due_at"]) == ("weekdays", "2026-11-24T07:30:00+05:30")


def test_r7_weekdays_rolls_weekend_to_monday():
    out = create(
        ts(time="07:30"),
        "every weekday at 7:30am remind me to call mom",
        recurrence="weekdays",
        now="2026-11-27T20:00:00+05:30",  # Friday evening
    )
    assert out["due_at"] == "2026-11-30T07:30:00+05:30"


@pytest.mark.parametrize(
    ("recurrence", "said"),
    [("daily", "every day"), ("weekly", "every week"), ("monthly", "every month")],
)
def test_fr008_recurrence_values_pass_through(recurrence, said):
    text = f"starting tomorrow at 9am remind me to call mom {said}"
    out = create(ts(day_offset=1, time="09:00"), text, recurrence=recurrence)
    assert out["recurrence"] == recurrence


def test_r11_long_task_truncated_to_120():
    long_task = "word " * 60
    out = create(
        ts(day_offset=1, time="09:00"), f"remind me to {long_task}tomorrow at 9am", task=long_task
    )
    assert out["intent"] == "create" and 1 <= len(out["task"]) <= 120


@pytest.mark.parametrize(
    ("spec", "text"),
    [
        (ts(day_offset=1), "remind me to call mom tomorrow"),  # R-4 date without time
        (ts(weekday="friday"), "remind me to call mom on friday"),
        (None, "remind me to call mom"),  # no time information at all
        (ts(), "remind me to call mom"),
    ],
)
def test_gr4_no_time_means_clarify(spec, text):
    out = create(spec, text)
    assert (out["intent"], out["missing"], out["due_at"]) == ("clarify", ["time"], None)


@pytest.mark.parametrize(
    ("spec", "text"),
    [
        (ts(date="2026-11-22", time="15:00"), "remind me to call mom on 22 November 2026 at 3pm"),
        (ts(day_offset=0, time="08:00"), "remind me to call mom today at 8am"),
        (ts(date="2028-01-01", time="09:00"), "remind me to call mom on 1 January 2028 at 9am"),
        (ts(offset_minutes=0), "remind me to call mom in 0 minutes"),
    ],
)
def test_gr5_inv7_out_of_range_means_clarify(spec, text):
    out = create(spec, text)
    assert (out["intent"], out["missing"], out["due_at"]) == ("clarify", ["time"], None)


def test_r8_create_without_task_means_clarify_task():
    out = run(
        ext(task=None, time_spec=ts(day_offset=1, time="09:00"), recurrence="none"),
        req("remind me tomorrow at 9am"),
    )
    assert out["intent"] == "clarify" and "task" in out["missing"]
