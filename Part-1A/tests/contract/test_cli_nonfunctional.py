"""T022 – SC-002 performance, SC-003 determinism, SC-004 no mutation on failure."""

import json
import time

import pytest

from taskflow.cli import main
from tests.conftest import T0

SEQUENCE = [
    ("add", "Buy milk", "--tag", "home"),
    ("add", "Ship report", "--priority", "high", "--tag", "work", "--tag", "Urgent"),
    ("status", "2", "in_progress"),
    ("update", "1", "--add-tag", "shopping"),
    ("list", "--sort", "priority"),
    ("list", "--tag", "work", "--json"),
    ("show", "2"),
    ("delete", "1"),
    ("status", "2", "done"),
    ("list",),
]


def run_sequence(path, capsys):
    outs = []
    for args in SEQUENCE:
        code = main(["--data", str(path), *args])
        cap = capsys.readouterr()
        outs.append((code, cap.out, cap.err))
    return outs, path.read_bytes()


def test_sc003_deterministic_replay(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TASKFLOW_NOW", T0)
    a = run_sequence(tmp_path / "a.json", capsys)
    b = run_sequence(tmp_path / "b.json", capsys)
    assert a == b
    assert all(code == 0 for code, _, _ in a[0])


FAILING = [
    ("add", ""),
    ("add", "x", "--tag", "bad tag"),
    ("update", "1"),
    ("update", "99", "--title", "x"),
    ("show", "abc"),
    ("delete", "99"),
    ("status", "1", "done"),
    ("status", "1", "nope"),
    ("list", "--sort", "nope"),
]


@pytest.mark.parametrize("args", FAILING, ids=lambda a: " ".join(a) or "empty")
def test_sc004_failed_command_leaves_file_identical(cli, args):
    cli("add", "seed", "--tag", "x")
    before = cli.raw()
    r = cli(*args)
    assert r.code != 0
    assert r.out == ""
    assert cli.raw() == before


def _big_store(path, n=1000):
    prios = ["low", "medium", "high"]
    tasks = [
        {
            "id": i,
            "title": f"task {i}",
            "priority": prios[i % 3],
            "status": "todo",
            "tags": ["bulk", f"g{i % 7}"],
            "created_at": T0,
            "updated_at": T0,
        }
        for i in range(1, n + 1)
    ]
    path.write_text(json.dumps({"version": 1, "next_id": n + 1, "tasks": tasks}), encoding="utf-8")


@pytest.mark.parametrize(
    "args",
    [
        ("list", "--sort", "priority"),
        ("list", "--tag", "g3", "--json"),
        ("add", "new"),
        ("status", "500", "in_progress"),
    ],
)
def test_sc002_under_one_second_for_1000_tasks(cli, args):
    _big_store(cli.data)
    start = time.perf_counter()
    r = cli(*args)
    elapsed = time.perf_counter() - start
    assert r.code == 0
    assert elapsed < 1.0, f"{args} took {elapsed:.3f}s"
