"""Error hierarchy carrying process exit codes (FR-013)."""

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_USAGE = 2
EXIT_DATA_FILE = 3


class TaskFlowError(Exception):
    """Base error; ``message`` is printed after the ``error: `` prefix."""

    exit_code = EXIT_USAGE

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(TaskFlowError):
    """Invalid user input (exit 2)."""

    exit_code = EXIT_USAGE


class InvalidTransitionError(ValidationError):
    """Disallowed status transition (FR-007, exit 2)."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(f"invalid transition {from_status} -> {to_status}")
        self.from_status = from_status
        self.to_status = to_status


class NotFoundError(TaskFlowError):
    """Well-formed task id that does not exist (exit 1)."""

    exit_code = EXIT_NOT_FOUND

    def __init__(self, task_id: int) -> None:
        super().__init__(f"task {task_id} not found")
        self.task_id = task_id


class DataFileError(TaskFlowError):
    """Corrupt, schema-invalid or unreadable/unwritable data file (exit 3)."""

    exit_code = EXIT_DATA_FILE

    def __init__(self, reason: str) -> None:
        super().__init__(f"invalid data file: {reason}")
        self.reason = reason
