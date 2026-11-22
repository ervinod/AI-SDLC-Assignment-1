"""Task operations: CRUD, status transitions, filtering and sorting.

FR-001..FR-010, FR-014; data-model.md "Status state machine".
"""

from collections.abc import Iterable
from dataclasses import dataclass

from taskflow.clock import Clock
from taskflow.errors import InvalidTransitionError, NotFoundError, ValidationError
from taskflow.models import (
    PRIORITY_RANK,
    Priority,
    Status,
    Task,
    check_tag_count,
    normalize_tag,
    normalize_tags,
    parse_priority,
    parse_status,
    validate_title,
)
from taskflow.store import JsonStore, StoreData

ALLOWED_TRANSITIONS: frozenset[tuple[Status, Status]] = frozenset(
    {
        (Status.TODO, Status.IN_PROGRESS),
        (Status.TODO, Status.CANCELLED),
        (Status.IN_PROGRESS, Status.TODO),
        (Status.IN_PROGRESS, Status.DONE),
        (Status.IN_PROGRESS, Status.CANCELLED),
        (Status.DONE, Status.TODO),
        (Status.CANCELLED, Status.TODO),
    }
)

SORT_KEYS = ("id", "priority")


def is_allowed_transition(from_status: Status | str, to_status: Status | str) -> bool:
    return (Status(from_status), Status(to_status)) in ALLOWED_TRANSITIONS


def _id_key(task: Task) -> tuple[int]:
    return (task.id,)


def _priority_key(task: Task) -> tuple[int, str, int]:
    return (PRIORITY_RANK[task.priority], task.created_at, task.id)


def sort_tasks(tasks: Iterable[Task], sort: str = "id") -> list[Task]:
    """Total order (FR-010, research R4)."""
    if sort not in SORT_KEYS:
        raise ValidationError(f"invalid sort key '{sort}'")
    key = _priority_key if sort == "priority" else _id_key
    return sorted(tasks, key=key)


def filter_tasks(
    tasks: Iterable[Task], tags: Iterable[str] = (), status: Status | str | None = None
) -> list[Task]:
    """AND semantics across all tags and the status (FR-008, FR-009)."""
    wanted = {normalize_tag(tag) for tag in tags}
    wanted_status = parse_status(status) if status is not None else None
    return [
        task
        for task in tasks
        if wanted.issubset(task.tags) and (wanted_status is None or task.status == wanted_status)
    ]


@dataclass(frozen=True)
class TaskUpdate:
    """Validated change set for ``TaskService.update`` (FR-005)."""

    title: str | None = None
    priority: Priority | None = None
    add_tags: tuple[str, ...] = ()
    remove_tags: tuple[str, ...] = ()

    def is_empty(self) -> bool:
        return (
            self.title is None
            and self.priority is None
            and not self.add_tags
            and not self.remove_tags
        )


class TaskService:
    """Application service operating on a ``JsonStore`` with an injected ``Clock``."""

    def __init__(self, store: JsonStore, clock: Clock | None = None) -> None:
        self.store = store
        self.clock = clock if clock is not None else Clock()

    def add(self, title: str, priority: str = "medium", tags: Iterable[str] = ()) -> Task:
        clean_title = validate_title(title)
        clean_priority = parse_priority(priority)
        clean_tags = normalize_tags(tags)
        now = self.clock.now()
        data = self.store.load()
        task = Task(
            id=data.next_id,
            title=clean_title,
            priority=clean_priority,
            status=Status.TODO,
            tags=clean_tags,
            created_at=now,
            updated_at=now,
        )
        data.tasks.append(task)
        data.next_id += 1
        self.store.save(data)
        return task

    def get(self, task_id: int) -> Task:
        return _find(self.store.load(), task_id)

    def update(
        self,
        task_id: int,
        title: str | None = None,
        priority: str | None = None,
        add_tags: Iterable[str] = (),
        remove_tags: Iterable[str] = (),
    ) -> Task:
        change = TaskUpdate(
            title=validate_title(title) if title is not None else None,
            priority=parse_priority(priority) if priority is not None else None,
            add_tags=tuple(normalize_tag(tag) for tag in add_tags),
            remove_tags=tuple(normalize_tag(tag) for tag in remove_tags),
        )
        if change.is_empty():
            raise ValidationError("nothing to update")
        now = self.clock.now()
        data = self.store.load()
        task = _find(data, task_id)
        _apply_update(task, change)
        task.updated_at = now
        self.store.save(data)
        return task

    def delete(self, task_id: int) -> Task:
        data = self.store.load()
        task = _find(data, task_id)
        data.tasks.remove(task)
        self.store.save(data)
        return task

    def transition(self, task_id: int, new_status: str) -> tuple[Status, Status]:
        target = parse_status(new_status)
        now = self.clock.now()
        data = self.store.load()
        task = _find(data, task_id)
        current = task.status
        if not is_allowed_transition(current, target):
            raise InvalidTransitionError(current.value, target.value)
        task.status = target
        task.updated_at = now
        self.store.save(data)
        return current, target

    def list(
        self, tags: Iterable[str] = (), status: str | None = None, sort: str = "id"
    ) -> list[Task]:
        if sort not in SORT_KEYS:
            raise ValidationError(f"invalid sort key '{sort}'")
        selected = filter_tasks(self.store.load().tasks, tags, status)
        return sort_tasks(selected, sort)


def _find(data: StoreData, task_id: int) -> Task:
    for task in data.tasks:
        if task.id == task_id:
            return task
    raise NotFoundError(task_id)


def _apply_update(task: Task, change: TaskUpdate) -> None:
    if change.title is not None:
        task.title = change.title
    if change.priority is not None:
        task.priority = change.priority
    tags = (set(task.tags) | set(change.add_tags)) - set(change.remove_tags)
    new_tags = sorted(tags)
    check_tag_count(new_tags)
    task.tags = new_tags
