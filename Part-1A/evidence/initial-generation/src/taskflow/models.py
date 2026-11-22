"""Task model, enums and input validation (FR-001, FR-003, FR-007, data-model.md)."""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from taskflow.errors import ValidationError

TITLE_MAX_LENGTH = 200
MAX_TAGS = 10
TAG_RE = re.compile(r"[a-z0-9-]{1,30}")
_TASK_ID_RE = re.compile(r"[0-9]+")

TASK_FIELDS = ("id", "title", "priority", "status", "tags", "created_at", "updated_at")


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


PRIORITY_RANK = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


@dataclass
class Task:
    id: int
    title: str
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "priority": str(self.priority),
            "status": str(self.status),
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            priority=Priority(data["priority"]),
            status=Status(data["status"]),
            tags=list(data["tags"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


def validate_title(title: str) -> str:
    """Trim and validate a title (FR-001, research R6)."""
    trimmed = title.strip()
    if not 1 <= len(trimmed) <= TITLE_MAX_LENGTH:
        raise ValidationError(f"title must be 1-{TITLE_MAX_LENGTH} characters")
    if any(unicodedata.category(ch) == "Cc" for ch in trimmed):
        raise ValidationError("title contains control characters")
    return trimmed


def normalize_tag(tag: str) -> str:
    """Lower-case and validate a single tag (FR-003)."""
    lowered = tag.lower()
    if not TAG_RE.fullmatch(lowered):
        raise ValidationError(f"invalid tag '{tag}'")
    return lowered


def normalize_tags(tags: Iterable[str]) -> list[str]:
    """Normalise, de-duplicate and sort tags, enforcing the 10-tag limit (FR-003)."""
    result = sorted({normalize_tag(tag) for tag in tags})
    check_tag_count(result)
    return result


def check_tag_count(tags: list[str]) -> None:
    if len(tags) > MAX_TAGS:
        raise ValidationError(f"a task may have at most {MAX_TAGS} tags")


def parse_priority(value: str) -> Priority:
    try:
        return Priority(value)
    except ValueError:
        raise ValidationError(f"invalid priority '{value}'") from None


def parse_status(value: str) -> Status:
    try:
        return Status(value)
    except ValueError:
        raise ValidationError(f"invalid status '{value}'") from None


def parse_task_id(raw: str) -> int:
    """Parse a positive integer task id; anything else is a usage error (exit 2)."""
    if not _TASK_ID_RE.fullmatch(raw) or int(raw) < 1:
        raise ValidationError(f"invalid task id '{raw}'")
    return int(raw)
