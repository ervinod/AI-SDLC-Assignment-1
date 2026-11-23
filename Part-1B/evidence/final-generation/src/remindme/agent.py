"""Public API: ``handle(request, extractor=None) -> response`` (plan.md / Public Contracts).

validate request → GR-1 precheck → extractor (model) → post-process → validate response.
"""

from collections.abc import Callable

from remindme.errors import RequestError, ServiceError
from remindme.llm import default_extractor
from remindme.postprocess import fallback, postprocess
from remindme.request import parse_request, precheck_text
from remindme.response import reject, validate_response

Extractor = Callable[[dict], object]

__all__ = ["RequestError", "ServiceError", "handle"]


def _extract(extractor: Extractor, request: dict) -> object:
    """Call the extractor; any failure there is a service failure, never a fabricated reply."""
    try:
        return extractor(request)
    except ServiceError:
        raise
    except Exception as exc:  # the extractor is an external component
        raise ServiceError(f"extractor failed: {type(exc).__name__}") from exc


def handle(request: dict, extractor: Extractor | None = None) -> dict:
    """Interpret one reminder request and return a schema-valid response.

    Raises RequestError for a malformed request (no model call) and ServiceError when the
    model/service fails (FR-010).
    """
    parsed = parse_request(request)
    reason = precheck_text(parsed.text)
    if reason is not None:
        return reject(reason)
    extraction = _extract(extractor or default_extractor(), request)
    try:
        response = postprocess(extraction, parsed)
    except (TypeError, ValueError, KeyError, AttributeError, ArithmeticError):
        # constitution II: degrade to a safe response, never crash
        response = fallback(extraction)
    if validate_response(response, parsed):
        response = fallback(extraction)
    return response
