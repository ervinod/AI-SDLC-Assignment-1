"""Human and JSON output rendering (FR-004, FR-011, FR-016)."""

import json
from collections.abc import Iterable
from typing import Any

from taskflow.models import Task

EMPTY_LIST_MESSAGE = "No tasks found."


def to_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)


def format_task_json(task: Task) -> str:
    return to_json(task.to_dict())


def format_task_line(task: Task) -> str:
    fields = [str(task.id), str(task.status), str(task.priority), task.title, ",".join(task.tags)]
    return "\t".join(fields)


def format_task_list(tasks: Iterable[Task]) -> str:
    lines = [format_task_line(task) for task in tasks]
    return "\n".join(lines) if lines else EMPTY_LIST_MESSAGE


def format_task_list_json(tasks: Iterable[Task]) -> str:
    return to_json([task.to_dict() for task in tasks])


def created_message(task_id: int) -> str:
    return f"Created task {task_id}"


def updated_message(task_id: int) -> str:
    return f"Updated task {task_id}"


def deleted_message(task_id: int) -> str:
    return f"Deleted task {task_id}"


def transition_message(task_id: int, from_status: str, to_status: str) -> str:
    return f"Task {task_id}: {from_status} -> {to_status}"
