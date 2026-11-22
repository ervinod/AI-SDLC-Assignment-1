"""Error types of the public API (plan.md / Public Contracts)."""


class RequestError(ValueError):
    """The request itself is malformed (usage error); no model call was made."""


class ServiceError(RuntimeError):
    """The model/service failed (network, HTTP 4xx/5xx, refusal, max_tokens) (FR-010)."""
