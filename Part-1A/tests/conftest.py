"""Shared fixtures. Tests drive the public contract only: ``taskflow.cli.main(argv) -> int``
(research.md R1, contracts/cli.md) plus the data-file format (data-model.md)."""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from taskflow.cli import main

T0 = "2026-11-22T10:00:00Z"


@dataclass
class Result:
    code: int
    out: str
    err: str


class Cli:
    def __init__(self, data: Path, monkeypatch, capsys):
        self.data = data
        self._mp = monkeypatch
        self._capsys = capsys

    def __call__(self, *args: str, now: str | None = None) -> Result:
        if now is not None:
            self._mp.setenv("TASKFLOW_NOW", now)
        code = main(["--data", str(self.data), *args])
        cap = self._capsys.readouterr()
        return Result(code, cap.out, cap.err)

    def store(self) -> dict:
        return json.loads(self.data.read_text(encoding="utf-8"))

    def task(self, task_id: int) -> dict:
        return next(t for t in self.store()["tasks"] if t["id"] == task_id)

    def raw(self) -> bytes:
        return self.data.read_bytes()


@pytest.fixture
def cli(tmp_path, monkeypatch, capsys) -> Cli:
    monkeypatch.setenv("TASKFLOW_NOW", T0)
    monkeypatch.delenv("TASKFLOW_DATA", raising=False)
    return Cli(tmp_path / "tasks.json", monkeypatch, capsys)


def dumps(obj) -> str:
    """Canonical JSON rendering required by FR-004 / FR-011 / data-model.md."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
