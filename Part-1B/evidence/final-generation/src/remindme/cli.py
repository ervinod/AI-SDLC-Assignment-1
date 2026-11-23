"""Command line: ``remindme [--now ISO] [--tz ZONE] [--reminders FILE] TEXT`` (SCH-4).

Exit 0 with the response JSON on stdout; exit 2 on RequestError; exit 3 on ServiceError.
"""

import argparse
import json
import sys
from datetime import UTC, datetime

from remindme.agent import RequestError, ServiceError, handle

EXIT_REQUEST_ERROR = 2
EXIT_SERVICE_ERROR = 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remindme", description="Turn a natural-language reminder request into JSON."
    )
    parser.add_argument("--now", help="reference time, ISO-8601 with offset (default: now)")
    parser.add_argument("--tz", default="UTC", help="IANA timezone name (default: UTC)")
    parser.add_argument("--reminders", help="JSON file with a list of {id, task, due_at}")
    parser.add_argument("text", help="the reminder request")
    return parser


def _load_reminders(path: str | None) -> object:
    if path is None:
        return []
    try:
        with open(path, encoding="utf-8") as handle_:
            return json.load(handle_)
    except (OSError, ValueError) as exc:
        raise RequestError(f"cannot read reminders file {path!r}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    args = _parser().parse_args(argv)
    now = args.now or datetime.now(UTC).isoformat(timespec="seconds")
    try:
        request = {
            "text": args.text,
            "now": now,
            "timezone": args.tz,
            "reminders": _load_reminders(args.reminders),
        }
        response = handle(request)
    except RequestError as exc:
        print(f"remindme: invalid request: {exc}", file=sys.stderr)
        return EXIT_REQUEST_ERROR
    except ServiceError as exc:
        print(f"remindme: model/service error: {exc}", file=sys.stderr)
        return EXIT_SERVICE_ERROR
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(response, indent=2, sort_keys=True, ensure_ascii=False))
    return 0
