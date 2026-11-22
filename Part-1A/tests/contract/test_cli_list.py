"""T018 – User Story 3: listing, filtering (AND) and priority sort (FR-008..FR-011)."""

import json

from tests.conftest import dumps


def line(t):
    return f"{t['id']}\t{t['status']}\t{t['priority']}\t{t['title']}\t{','.join(t['tags'])}"


def seed_priorities(cli):
    # created_at deliberately non-monotonic in id to exercise the created_at tie-breaker.
    cli("add", "one", "--priority", "low", now="2026-11-22T10:00:00Z")
    cli("add", "two", "--priority", "high", now="2026-11-22T10:05:00Z")
    cli("add", "three", "--priority", "medium", now="2026-11-22T10:02:00Z")
    cli("add", "four", "--priority", "high", now="2026-11-22T10:01:00Z")
    cli("add", "five", "--priority", "high", now="2026-11-22T10:01:00Z")


def ids(out):
    return [int(x.split("\t")[0]) for x in out.splitlines()]


def test_as3_1_default_order_by_id_and_exact_format(cli):
    seed_priorities(cli)
    cli("update", "3", "--add-tag", "b", "--add-tag", "a")
    r = cli("list")
    store = {t["id"]: t for t in cli.store()["tasks"]}
    assert r.code == 0 and r.err == ""
    assert r.out == "".join(line(store[i]) + "\n" for i in [1, 2, 3, 4, 5])
    assert "3\ttodo\tmedium\tthree\ta,b\n" in r.out
    assert "1\ttodo\tlow\tone\t\n" in r.out


def test_as3_2_priority_sort_with_tiebreakers(cli):
    seed_priorities(cli)
    r = cli("list", "--sort", "priority")
    # high: 4 (10:01, id4), 5 (10:01, id5), 2 (10:05); medium: 3; low: 1
    assert ids(r.out) == [4, 5, 2, 3, 1]


def test_sort_id_explicit(cli):
    seed_priorities(cli)
    assert ids(cli("list", "--sort", "id").out) == [1, 2, 3, 4, 5]


def seed_tags(cli):
    cli("add", "w", "--tag", "work")
    cli("add", "h", "--tag", "home")
    cli("add", "wu", "--tag", "work", "--tag", "urgent")


def test_as3_3_tag_filter_is_and(cli):
    seed_tags(cli)
    assert ids(cli("list", "--tag", "work", "--tag", "urgent").out) == [3]
    assert ids(cli("list", "--tag", "work").out) == [1, 3]


def test_fr009_tag_filter_normalised(cli):
    seed_tags(cli)
    assert ids(cli("list", "--tag", "WORK").out) == [1, 3]


def test_fr008_status_filter_and_combination(cli):
    seed_tags(cli)
    cli("status", "3", "in_progress")
    assert ids(cli("list", "--status", "in_progress").out) == [3]
    assert ids(cli("list", "--status", "todo", "--tag", "work").out) == [1]


def test_as3_4_no_match(cli):
    seed_tags(cli)
    r = cli("list", "--tag", "nothing")
    assert (r.code, r.out, r.err) == (0, "No tasks found.\n", "")


def test_as3_5_json_output(cli):
    seed_priorities(cli)
    r = cli("list", "--json", "--sort", "priority")
    data = json.loads(r.out)
    assert [t["id"] for t in data] == [4, 5, 2, 3, 1]
    assert r.out == dumps(data)


def test_fr011_json_empty(cli):
    r = cli("list", "--json")
    assert (r.code, r.out) == (0, "[]\n")


def test_invalid_sort_key_and_status(cli):
    assert cli("list", "--sort", "title").code == 2
    assert cli("list", "--status", "blocked").code == 2
