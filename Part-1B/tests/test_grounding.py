"""T034 – GR-7 evidence grounding (spec revision 2026-11-23). The fake extraction plays the role of
an unreliable model; the application must only act on what the user's text supports."""

import pytest

from tests.conftest import REMINDERS, ext, req, run, ts

TWO_CALLS = [
    *REMINDERS,
    {"id": "r4", "task": "Call the bank", "due_at": "2026-11-24T10:00:00+05:30"},
    {"id": "r5", "task": "Call grandma", "due_at": "2026-11-26T19:00:00+05:30"},
]


def create(text, time_spec, task="pay rent", recurrence="none"):
    return run(ext(task=task, time_spec=time_spec, recurrence=recurrence), req(text))


# (a) time must come from the text -------------------------------------------------------------
def test_gr7a_invented_time_is_not_acted_on():
    out = create("remind me to pay rent", ts(day_offset=1, time="09:00"))
    assert (out["intent"], out["missing"], out["due_at"]) == ("clarify", ["time"], None)


def test_gr7a_day_without_clock_time_in_text():
    out = create("remind me tomorrow to pay rent", ts(day_offset=1, time="09:00"))
    assert (out["intent"], out["missing"]) == ("clarify", ["time"])


@pytest.mark.parametrize(
    ("text", "model_time", "expected"),
    [
        ("remind me to pay rent on friday at 4:15 pm", "14:15", "2026-11-27T16:15:00+05:30"),
        ("remind me to pay rent tomorrow at 6pm", "06:00", "2026-11-24T18:00:00+05:30"),
        ("remind me to pay rent tomorrow at noon", "00:00", "2026-11-24T12:00:00+05:30"),
        ("remind me to pay rent tomorrow at 21:30", "09:30", "2026-11-24T21:30:00+05:30"),
    ],
)
def test_gr7a_text_clock_overrides_model_misconversion(text, model_time, expected):
    day = "friday" if "friday" in text else None
    spec = ts(weekday=day, day_offset=None if day else 1, time=model_time)
    assert create(text, spec)["due_at"] == expected


def test_gr7a_text_day_overrides_wrong_model_day():
    out = create("remind me to pay rent on friday at 10am", ts(day_offset=0, time="10:00"))
    assert out["due_at"] == "2026-11-27T10:00:00+05:30"


def test_gr7a_relative_offset_from_text():
    out = create("in 2 hours remind me to pay rent", ts(offset_minutes=20))
    assert out["due_at"] == "2026-11-23T11:00:00+05:30"


# (b) recurrence only when stated -----------------------------------------------------------------
def test_gr7b_unstated_recurrence_becomes_none():
    out = create(
        "remind me to pay rent tomorrow at 6pm",
        ts(day_offset=1, time="18:00"),
        "pay rent",
        recurrence="weekly",
    )
    assert out["recurrence"] == "none"


@pytest.mark.parametrize(
    ("said", "expected"),
    [("every day", "daily"), ("every weekday", "weekdays"), ("daily", "daily")],
)
def test_gr7b_stated_recurrence_is_used(said, expected):
    out = create(f"{said} at 7am remind me to pay rent", ts(time="07:00"), recurrence="none")
    assert out["recurrence"] == expected


# (c) task must contain words from the text -------------------------------------------------------
def test_gr7c_scheduling_words_are_not_a_task():
    out = create("remind me at 5pm", ts(time="17:00"), task="at 5pm")
    assert out["intent"] == "clarify" and "task" in out["missing"]


def test_gr7c_hallucinated_task_is_rejected():
    out = create("remind me at 5pm", ts(time="17:00"), task="water the plants")
    assert out["intent"] == "clarify" and "task" in out["missing"]


# (d) target must be the unique reminder the text refers to --------------------------------------
def modify(intent, target, text, reminders=TWO_CALLS, **kw):
    return run(ext(intent, target_id=target, **kw), req(text, reminders=reminders))


def test_gr7d_ambiguous_reference_is_clarified():
    out = modify("snooze", "r5", "snooze the call reminder for 10 minutes", snooze_minutes=10)
    assert (out["intent"], out["missing"], out["target_id"]) == ("clarify", ["target"], None)


def test_gr7d_model_target_not_mentioned_is_clarified():
    out = modify("reschedule", "r3", "move my yoga reminder to 7pm", time_spec=ts(time="19:00"))
    assert (out["intent"], out["missing"]) == ("clarify", ["target"])


def test_gr7d_model_wrong_target_replaced_by_unique_text_match():
    out = modify("cancel", "r1", "cancel the dentist reminder")
    assert (out["intent"], out["target_id"]) == ("cancel", "r2")


def test_gr7d_named_id_is_used():
    out = modify("cancel", None, "please cancel r4")
    assert (out["intent"], out["target_id"]) == ("cancel", "r4")


@pytest.mark.parametrize(
    "text", ["delete all my reminders", "cancel every reminder", "cancel reminder r99 and r4"]
)
def test_gr7d_bulk_or_unknown_ids_are_clarified(text):
    out = modify("cancel", "r4", text)
    assert out["intent"] == "clarify" and out["target_id"] is None


# (e) snooze minutes from the text ----------------------------------------------------------------
def test_gr7e_snooze_minutes_from_text():
    out = modify("snooze", "r1", "snooze my medicine for half an hour", snooze_minutes=5)
    assert (out["snooze_minutes"], out["due_at"]) == (30, "2026-11-23T10:00:00+05:30")


def test_gr7e_snooze_hours_from_text():
    out = modify("snooze", "r1", "snooze my medicine by 2 hours", snooze_minutes=2)
    assert out["snooze_minutes"] == 120


# (f) clarify promotion ---------------------------------------------------------------------------
def test_gr7f_clarify_promoted_when_text_has_task_and_time():
    e = ext("clarify", task="pay rent", missing=["time"], question="When?")
    out = run(e, req("remind me to pay rent tomorrow at 6pm"))
    assert (out["intent"], out["due_at"]) == ("create", "2026-11-24T18:00:00+05:30")


@pytest.mark.parametrize(
    "text",
    [
        "remind me to pay rent",  # no time in text
        "move my rent reminder to tomorrow at 6pm",  # modify cue
        "remind me at 3pm to poison the neighbour's dog",  # harm words
    ],
)
def test_gr7f_clarify_not_promoted(text):
    # GR-7(f) requires "not promoted to an action". Since the GR-2 revision a harmful text may be
    # rejected outright, which is stricter, so the assertion is "clarify or reject" (2026-11-23).
    e = ext("clarify", task="pay rent", missing=["time"], question="When?")
    assert run(e, req(text))["intent"] in {"clarify", "reject"}


def test_gr7_reject_is_never_promoted():
    e = ext("reject", reason="harmful")
    assert run(e, req("remind me at 3pm to hurt someone"))["intent"] == "reject"
