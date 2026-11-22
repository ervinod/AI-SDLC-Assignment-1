"""T005 – validation rules for Task.title, Task.priority, Task.tags and the clock.
Exercised through the CLI boundary so tests depend only on the specified contract."""

import re

import pytest

from tests.conftest import T0


# --- FR-001 title -----------------------------------------------------------------------------
def test_fr001_title_is_trimmed(cli):
    assert cli("add", "  Buy milk  ").code == 0
    assert cli.task(1)["title"] == "Buy milk"


def test_fr001_title_200_chars_accepted(cli):
    assert cli("add", "x" * 200).code == 0


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
def test_fr001_title_length_rejected(cli, title):
    r = cli("add", title)
    assert (r.code, r.out, r.err) == (2, "", "error: title must be 1-200 characters\n")


def test_fr001_title_control_chars_rejected(cli):
    r = cli("add", "bell\x07")
    assert (r.code, r.out, r.err) == (2, "", "error: title contains control characters\n")


def test_fr001_unicode_title_accepted(cli):
    assert cli("add", "Café ☕ 日本").code == 0
    assert cli.task(1)["title"] == "Café ☕ 日本"


# --- FR-001 priority ----------------------------------------------------------------------------
def test_fr001_default_priority_medium_and_status_todo(cli):
    cli("add", "a")
    t = cli.task(1)
    assert (t["priority"], t["status"]) == ("medium", "todo")


def test_fr001_unknown_priority_rejected(cli):
    r = cli("add", "a", "--priority", "urgent")
    assert r.code == 2 and r.out == "" and r.err != ""


# --- FR-003 tags --------------------------------------------------------------------------------
def test_fr003_tags_lowercased_deduplicated_sorted(cli):
    cli("add", "a", "--tag", "Work", "--tag", "home", "--tag", "WORK", "--tag", "a-1")
    assert cli.task(1)["tags"] == ["a-1", "home", "work"]


@pytest.mark.parametrize("tag", ["bad_tag", "with space", "x" * 31, "", "dot.ted"])
def test_fr003_invalid_tag_rejected(cli, tag):
    r = cli("add", "a", "--tag", tag)
    assert (r.code, r.out, r.err) == (2, "", f"error: invalid tag '{tag}'\n")


def test_fr003_tag_30_chars_accepted(cli):
    assert cli("add", "a", "--tag", "x" * 30).code == 0


def test_fr003_ten_tags_accepted_eleven_rejected(cli):
    ten = [a for i in range(10) for a in ("--tag", f"t{i}")]
    assert cli("add", "a", *ten).code == 0
    r = cli("add", "b", *ten, "--tag", "t10")
    assert (r.code, r.err) == (2, "error: a task may have at most 10 tags\n")


# --- FR-015 clock -------------------------------------------------------------------------------
def test_fr015_fixed_clock_used_for_timestamps(cli):
    cli("add", "a")
    t = cli.task(1)
    assert t["created_at"] == T0 and t["updated_at"] == T0


def test_fr015_real_clock_format(cli, monkeypatch):
    monkeypatch.delenv("TASKFLOW_NOW")
    cli("add", "a")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", cli.task(1)["created_at"])


@pytest.mark.parametrize("bad", ["2026-11-22 10:00:00", "2026-11-22T10:00:00+00:00", "yesterday"])
def test_fr015_invalid_clock_rejected(cli, bad):
    r = cli("add", "a", now=bad)
    assert (r.code, r.out, r.err) == (2, "", "error: invalid TASKFLOW_NOW\n")
