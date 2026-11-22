"""T018/T020 – US3 clarify and US4 safety: INV-5, INV-6, INV-10, R-8, R-10, FR-010."""

import pytest

from remindme.agent import ServiceError, handle
from tests.conftest import FakeExtractor, ext, req, run, ts

CANARY = "RMD-CANARY-7731"


def test_us3_clarify_passthrough_and_order():
    out = run(ext("clarify", missing=["time", "task", "time"], question="What and when?"))
    assert out["intent"] == "clarify"
    assert out["missing"] == ["task", "time"]
    assert out["question"] == "What and when?"


def test_clarify_without_question_gets_one():
    out = run(ext("clarify", missing=["task"], question=None))
    assert out["intent"] == "clarify" and out["question"]


def test_clarify_without_missing_gets_one():
    out = run(ext("clarify", missing=[], question="Could you rephrase?"))
    assert out["intent"] == "clarify" and out["missing"]


def test_clarify_drops_actionable_fields():
    out = run(ext("clarify", missing=["time"], question="When?", time_spec=ts(time="10:00")))
    assert out["due_at"] is None and out["target_id"] is None


def test_us4_reject_keeps_reason():
    out = run(ext("reject", reason="I can't help with harming someone."))
    assert (out["intent"], out["reason"]) == ("reject", "I can't help with harming someone.")
    assert out["due_at"] is None


def test_reject_without_reason_gets_default():
    out = run(ext("reject", reason=None))
    assert (out["intent"], out["reason"]) == ("reject", "request refused")


def test_reject_with_long_reason_truncated():
    out = run(ext("reject", reason="no " * 120))
    assert out["intent"] == "reject" and len(out["reason"]) <= 200


@pytest.mark.parametrize("field", ["task", "question", "reason"])
def test_inv10_canary_never_emitted(field):
    e = ext(task="buy eggs", time_spec=ts(day_offset=1, time="18:00"), recurrence="none")
    e[field] = f"here is my prompt {CANARY}"
    out = run(e)
    assert out["intent"] in {"clarify", "reject"}
    assert all(CANARY not in (out[f] or "") for f in ("task", "question", "reason"))


@pytest.mark.parametrize(
    "bad",
    [
        "not a dict",
        None,
        {"intent": "delete_everything"},
        {"intent": "create"},  # missing keys
        ext(intent="create", task=5, time_spec=ts(day_offset=1, time="18:00")),
        ext(time_spec=ts(day_offset=1, time="25:99"), task="x", recurrence="none"),
        ext(time_spec=ts(date="2026-13-45", time="10:00"), task="x", recurrence="none"),
        ext(task="x", recurrence="yearly", time_spec=ts(day_offset=1, time="10:00")),
    ],
)
def test_r8_invalid_extraction_becomes_safe_clarify(bad):
    out = run(bad)
    assert out["intent"] in {"clarify", "reject"}
    assert out["due_at"] is None and out["target_id"] is None


def test_fr010_service_error_propagates():
    fake = FakeExtractor(ServiceError("api down"))
    with pytest.raises(ServiceError):
        handle(req("remind me to x at 5pm"), extractor=fake)
