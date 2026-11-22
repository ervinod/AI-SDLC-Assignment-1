"""T011 – User Story 1 acceptance scenarios (AS1-1..AS1-6) and CRUD edge cases."""

import pytest

from tests.conftest import T0, dumps

T1 = "2026-11-22T11:30:00Z"


def test_as1_1_add_first_task(cli):
    r = cli("add", "Buy milk")
    assert (r.code, r.out, r.err) == (0, "Created task 1\n", "")
    t = cli.task(1)
    assert (t["id"], t["title"], t["priority"], t["status"], t["tags"]) == (
        1,
        "Buy milk",
        "medium",
        "todo",
        [],
    )


def test_as1_2_add_with_priority_and_tags(cli):
    cli("add", "Buy milk")
    r = cli("add", "Pay rent", "--priority", "high", "--tag", "Home", "--tag", "bills")
    assert r.out == "Created task 2\n"
    t = cli.task(2)
    assert (t["priority"], t["tags"]) == ("high", ["bills", "home"])


def test_as1_3_show_prints_canonical_json(cli):
    cli("add", "Buy milk", "--tag", "home")
    r = cli("show", "1")
    assert r.code == 0 and r.err == ""
    assert r.out == dumps(cli.task(1))


def test_as1_4_update_title_priority_sets_updated_at(cli):
    cli("add", "Buy milk")
    r = cli("update", "1", "--title", "Buy oat milk", "--priority", "low", now=T1)
    assert (r.code, r.out, r.err) == (0, "Updated task 1\n", "")
    t = cli.task(1)
    assert (t["title"], t["priority"], t["created_at"], t["updated_at"]) == (
        "Buy oat milk",
        "low",
        T0,
        T1,
    )


def test_fr005_update_add_and_remove_tags(cli):
    cli("add", "a", "--tag", "x", "--tag", "y")
    assert cli("update", "1", "--add-tag", "Z", "--remove-tag", "x").code == 0
    assert cli.task(1)["tags"] == ["y", "z"]


def test_fr005_remove_absent_tag_is_noop_success(cli):
    cli("add", "a", "--tag", "x")
    r = cli("update", "1", "--remove-tag", "nope")
    assert (r.code, r.out) == (0, "Updated task 1\n")
    assert cli.task(1)["tags"] == ["x"]


def test_fr005_update_validates_title(cli):
    cli("add", "a")
    r = cli("update", "1", "--title", "  ")
    assert (r.code, r.err) == (2, "error: title must be 1-200 characters\n")


def test_fr005_update_add_tag_limit(cli):
    cli("add", "a", *[x for i in range(10) for x in ("--tag", f"t{i}")])
    r = cli("update", "1", "--add-tag", "t10")
    assert (r.code, r.err) == (2, "error: a task may have at most 10 tags\n")


def test_fr005_update_invalid_tag(cli):
    cli("add", "a")
    r = cli("update", "1", "--add-tag", "no space")
    assert (r.code, r.err) == (2, "error: invalid tag 'no space'\n")


def test_update_nothing_to_update(cli):
    cli("add", "a")
    r = cli("update", "1")
    assert (r.code, r.out, r.err) == (2, "", "error: nothing to update\n")


def test_as1_5_delete_then_show_not_found(cli):
    cli("add", "a")
    r = cli("delete", "1")
    assert (r.code, r.out, r.err) == (0, "Deleted task 1\n", "")
    r = cli("show", "1")
    assert (r.code, r.out, r.err) == (1, "", "error: task 1 not found\n")


def test_as1_6_ids_never_reused(cli):
    cli("add", "a")
    cli("add", "b")
    cli("delete", "2")
    assert cli("add", "c").out == "Created task 3\n"
    assert cli.store()["next_id"] == 4


@pytest.mark.parametrize("cmd", [("show",), ("delete",), ("update", "--title", "x")])
def test_fr013_not_found_exit_1(cli, cmd):
    cli("add", "a")
    args = (cmd[0], "99", *cmd[1:])
    r = cli(*args)
    assert (r.code, r.out, r.err) == (1, "", "error: task 99 not found\n")


@pytest.mark.parametrize("raw", ["0", "-3", "abc", "1.5"])
def test_fr013_invalid_id_exit_2(cli, raw):
    cli("add", "a")
    r = cli("show", raw)
    assert (r.code, r.out, r.err) == (2, "", f"error: invalid task id '{raw}'\n")


def test_fr013_usage_error_returns_2(cli):
    r = cli("frobnicate")
    assert r.code == 2 and r.out == "" and r.err != ""
