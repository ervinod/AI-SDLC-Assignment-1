"""T015 – User Story 2: status state machine (FR-007, FR-014, FR-016)."""

import pytest

T1 = "2026-11-22T12:00:00Z"

STATUSES = ["todo", "in_progress", "done", "cancelled"]
ALLOWED = {
    ("todo", "in_progress"),
    ("todo", "cancelled"),
    ("in_progress", "todo"),
    ("in_progress", "done"),
    ("in_progress", "cancelled"),
    ("done", "todo"),
    ("cancelled", "todo"),
}
# Path of allowed transitions used to reach each starting state from `todo`.
PATH_TO = {
    "todo": [],
    "in_progress": ["in_progress"],
    "done": ["in_progress", "done"],
    "cancelled": ["cancelled"],
}


def _task_in(cli, state):
    cli("add", "a")
    for step in PATH_TO[state]:
        assert cli("status", "1", step).code == 0


@pytest.mark.parametrize(("src", "dst"), sorted(ALLOWED))
def test_fr007_allowed_transition(cli, src, dst):
    _task_in(cli, src)
    r = cli("status", "1", dst, now=T1)
    assert (r.code, r.out, r.err) == (0, f"Task 1: {src} -> {dst}\n", "")
    t = cli.task(1)
    assert (t["status"], t["updated_at"]) == (dst, T1)


FORBIDDEN = sorted((s, d) for s in STATUSES for d in STATUSES if (s, d) not in ALLOWED)


@pytest.mark.parametrize(("src", "dst"), FORBIDDEN)
def test_fr007_forbidden_transition_rejected_and_unchanged(cli, src, dst):
    _task_in(cli, src)
    before = cli.raw()
    r = cli("status", "1", dst, now=T1)
    assert (r.code, r.out, r.err) == (2, "", f"error: invalid transition {src} -> {dst}\n")
    assert cli.raw() == before


def test_as2_1_todo_to_in_progress(cli):
    cli("add", "a")
    assert cli("status", "1", "in_progress").out == "Task 1: todo -> in_progress\n"


def test_as2_4_reopen_done(cli):
    _task_in(cli, "done")
    assert cli("status", "1", "todo").out == "Task 1: done -> todo\n"


def test_unknown_status_value_is_usage_error(cli):
    cli("add", "a")
    r = cli("status", "1", "blocked")
    assert r.code == 2 and r.out == "" and r.err != ""
    assert cli.task(1)["status"] == "todo"


def test_status_on_missing_task(cli):
    r = cli("status", "5", "done")
    assert (r.code, r.err) == (1, "error: task 5 not found\n")
