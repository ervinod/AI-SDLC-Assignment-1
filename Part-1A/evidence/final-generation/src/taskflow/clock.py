"""Injectable clock honouring ``TASKFLOW_NOW`` (FR-015, research R3)."""

import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime

from taskflow.errors import ValidationError

ENV_VAR = "TASKFLOW_NOW"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def is_valid_timestamp(value: object) -> bool:
    """Return True if ``value`` is an ISO-8601 UTC timestamp ``YYYY-MM-DDTHH:MM:SSZ``."""
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        return False
    try:
        datetime.strptime(value, TIMESTAMP_FORMAT)
    except ValueError:
        return False
    return True


class Clock:
    """Single source of the current time.

    ``fixed`` (if given) wins; otherwise ``TASKFLOW_NOW`` from ``environ`` (default
    ``os.environ``, read at call time); otherwise wall-clock UTC truncated to seconds.
    """

    def __init__(self, environ: Mapping[str, str] | None = None, fixed: str | None = None):
        self._environ = environ
        self._fixed = fixed

    def now(self) -> str:
        if self._fixed is not None:
            return self._validated(self._fixed)
        env = os.environ if self._environ is None else self._environ
        raw = env.get(ENV_VAR)
        if raw is None:
            return datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
        return self._validated(raw)

    @staticmethod
    def _validated(value: str) -> str:
        if not is_valid_timestamp(value):
            raise ValidationError(f"invalid {ENV_VAR}")
        return value
