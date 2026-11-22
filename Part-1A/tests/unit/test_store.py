"""T006 – persistence: FR-012 path resolution, data-model.md file format, exit 3 on invalid
files, SC-004 (failed commands do not modify the file), atomic write leaves no temp files."""

import json

import pytest

from taskflow.cli import main
from tests.conftest import T0


def test_data_file_exact_format(cli):
    cli("add", "Buy milk")
    expected = {
        "next_id": 2,
        "tasks": [
            {
                "created_at": T0,
                "id": 1,
                "priority": "medium",
                "status": "todo",
                "tags": [],
                "title": "Buy milk",
                "updated_at": T0,
            }
        ],
        "version": 1,
    }
    assert (
        cli.data.read_text(encoding="utf-8")
        == json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )


def test_non_ascii_stored_unescaped(cli):
    cli("add", "Café")
    assert "Café" in cli.data.read_text(encoding="utf-8")


def test_missing_file_is_empty_store(cli):
    r = cli("list")
    assert (r.code, r.out) == (0, "No tasks found.\n")


def test_no_temp_files_left_after_write(cli):
    cli("add", "a")
    cli("add", "b")
    assert sorted(p.name for p in cli.data.parent.iterdir()) == ["tasks.json"]


def test_fr012_env_var_fallback(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TASKFLOW_NOW", T0)
    target = tmp_path / "env.json"
    monkeypatch.setenv("TASKFLOW_DATA", str(target))
    assert main(["add", "a"]) == 0
    assert json.loads(target.read_text())["tasks"][0]["title"] == "a"


def test_fr012_flag_overrides_env(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TASKFLOW_NOW", T0)
    monkeypatch.setenv("TASKFLOW_DATA", str(tmp_path / "env.json"))
    flag = tmp_path / "flag.json"
    assert main(["--data", str(flag), "add", "a"]) == 0
    assert flag.exists() and not (tmp_path / "env.json").exists()


def test_fr012_default_path_in_cwd(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TASKFLOW_NOW", T0)
    monkeypatch.delenv("TASKFLOW_DATA", raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["add", "a"]) == 0
    assert (tmp_path / "tasks.json").exists()


def _task(i, **over):
    t = {
        "id": i,
        "title": "t",
        "priority": "low",
        "status": "todo",
        "tags": [],
        "created_at": T0,
        "updated_at": T0,
    }
    t.update(over)
    return t


INVALID_FILES = {
    "not_json": "{not json",
    "wrong_version": json.dumps({"version": 2, "next_id": 1, "tasks": []}),
    "missing_next_id": json.dumps({"version": 1, "tasks": []}),
    "duplicate_ids": json.dumps({"version": 1, "next_id": 3, "tasks": [_task(1), _task(1)]}),
    "id_not_below_next_id": json.dumps({"version": 1, "next_id": 2, "tasks": [_task(2)]}),
    "bad_status": json.dumps({"version": 1, "next_id": 2, "tasks": [_task(1, status="blocked")]}),
    "extra_field": json.dumps({"version": 1, "next_id": 2, "tasks": [_task(1, owner="x")]}),
    "title_wrong_type": json.dumps({"version": 1, "next_id": 2, "tasks": [_task(1, title=5)]}),
    "top_level_list": json.dumps([]),
}


@pytest.mark.parametrize("name", sorted(INVALID_FILES))
def test_invalid_data_file_exit_3_and_untouched(cli, name):
    cli.data.write_text(INVALID_FILES[name], encoding="utf-8")
    before = cli.raw()
    for args in (("list",), ("add", "x")):
        r = cli(*args)
        assert r.code == 3, (name, args)
        assert r.out == ""
        assert r.err.startswith("error: invalid data file: ")
    assert cli.raw() == before
