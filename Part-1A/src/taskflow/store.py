"""JSON data-file persistence with schema validation and atomic writes.

FR-012, constitution IV, research R2/R5, data-model.md "Task store".
"""

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from taskflow.clock import is_valid_timestamp
from taskflow.errors import DataFileError
from taskflow.models import TAG_RE, TASK_FIELDS, Priority, Status, Task

SCHEMA_VERSION = 1
_TOP_LEVEL_KEYS = {"version", "next_id", "tasks"}


@dataclass
class StoreData:
    next_id: int = 1
    tasks: list[Task] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        ordered = sorted(self.tasks, key=lambda task: task.id)
        return {
            "version": SCHEMA_VERSION,
            "next_id": self.next_id,
            "tasks": [task.to_dict() for task in ordered],
        }


def dumps_data(data: StoreData) -> str:
    return json.dumps(data.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_tag_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(isinstance(tag, str) and TAG_RE.fullmatch(tag) for tag in value)


def _check_task_fields(index: int, raw: dict[str, Any]) -> None:
    checks = {
        "id": _is_int(raw["id"]) and raw["id"] >= 1,
        "title": isinstance(raw["title"], str),
        "priority": raw["priority"] in {p.value for p in Priority},
        "status": raw["status"] in {s.value for s in Status},
        "tags": _is_tag_list(raw["tags"]),
        "created_at": is_valid_timestamp(raw["created_at"]),
        "updated_at": is_valid_timestamp(raw["updated_at"]),
    }
    for name, ok in checks.items():
        if not ok:
            raise DataFileError(f"task at index {index} has invalid field '{name}'")


def _parse_task(index: int, raw: object) -> Task:
    if not isinstance(raw, dict):
        raise DataFileError(f"task at index {index} is not an object")
    if set(raw) != set(TASK_FIELDS):
        raise DataFileError(f"task at index {index} has missing or extra fields")
    _check_task_fields(index, raw)
    return Task.from_dict(raw)


def _check_top_level(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise DataFileError("top level is not an object")
    if set(raw) != _TOP_LEVEL_KEYS:
        raise DataFileError("top level must have exactly 'version', 'next_id' and 'tasks'")
    if not _is_int(raw["version"]) or raw["version"] != SCHEMA_VERSION:
        raise DataFileError(f"unsupported version (expected {SCHEMA_VERSION})")
    if not _is_int(raw["next_id"]) or raw["next_id"] < 1:
        raise DataFileError("'next_id' must be an integer >= 1")
    if not isinstance(raw["tasks"], list):
        raise DataFileError("'tasks' must be a list")
    return raw


def parse_data(raw: object) -> StoreData:
    """Validate a decoded JSON document against the data-file schema."""
    top = _check_top_level(raw)
    next_id = top["next_id"]
    tasks: list[Task] = []
    seen: set[int] = set()
    for index, item in enumerate(top["tasks"]):
        task = _parse_task(index, item)
        if task.id in seen:
            raise DataFileError(f"duplicate task id {task.id}")
        if task.id >= next_id:
            raise DataFileError(f"task id {task.id} is not below 'next_id' {next_id}")
        seen.add(task.id)
        tasks.append(task)
    return StoreData(next_id=next_id, tasks=tasks)


class JsonStore:
    """Loads and atomically saves the task data file."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def load(self) -> StoreData:
        try:
            raw_bytes = self.path.read_bytes()
        except FileNotFoundError:
            return StoreData()
        except OSError as exc:
            raise DataFileError(f"cannot read {self.path}: {exc.strerror}") from exc
        try:
            document = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise DataFileError(f"not valid UTF-8 JSON ({exc})") from exc
        return parse_data(document)

    def save(self, data: StoreData) -> None:
        payload = dumps_data(data).encode("utf-8")
        directory = self.path.parent
        tmp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=directory, prefix=f".{self.path.name}.", suffix=".tmp", delete=False
            ) as handle:
                tmp_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        except OSError as exc:
            _discard(tmp_name)
            raise DataFileError(f"cannot write {self.path}: {exc.strerror}") from exc


def _discard(tmp_name: str | None) -> None:
    if tmp_name is None:
        return
    try:
        os.unlink(tmp_name)
    except FileNotFoundError:
        return
