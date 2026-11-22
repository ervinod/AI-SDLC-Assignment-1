"""argparse command-line interface; ``main(argv) -> int`` (FR-012, FR-013, contracts/cli.md)."""

import argparse
import os
import sys
from collections.abc import Callable

from taskflow import formatting
from taskflow.clock import Clock
from taskflow.errors import EXIT_OK, EXIT_USAGE, TaskFlowError
from taskflow.models import Priority, Status, parse_task_id
from taskflow.service import SORT_KEYS, TaskService
from taskflow.store import JsonStore

DATA_ENV_VAR = "TASKFLOW_DATA"
DEFAULT_DATA_PATH = "tasks.json"

PRIORITIES = [p.value for p in Priority]
STATUSES = [s.value for s in Status]


def _add_parsers(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    add = sub.add_parser("add", help="create a task")
    add.add_argument("title")
    add.add_argument("--priority", choices=PRIORITIES, default=Priority.MEDIUM.value)
    add.add_argument("--tag", action="append", default=[], dest="tags")

    show = sub.add_parser("show", help="show a task as JSON")
    show.add_argument("id")

    update = sub.add_parser("update", help="update a task")
    update.add_argument("id")
    update.add_argument("--title")
    update.add_argument("--priority", choices=PRIORITIES)
    update.add_argument("--add-tag", action="append", default=[], dest="add_tags")
    update.add_argument("--remove-tag", action="append", default=[], dest="remove_tags")

    delete = sub.add_parser("delete", help="delete a task")
    delete.add_argument("id")

    status = sub.add_parser("status", help="change a task's status")
    status.add_argument("id")
    status.add_argument("new_status", choices=STATUSES)

    listing = sub.add_parser("list", help="list tasks")
    listing.add_argument("--tag", action="append", default=[], dest="tags")
    listing.add_argument("--status", choices=STATUSES)
    listing.add_argument("--sort", choices=list(SORT_KEYS), default="id")
    listing.add_argument("--json", action="store_true", dest="as_json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskflow", description="TaskFlow task manager")
    parser.add_argument("--data", help="path to the JSON data file")
    _add_parsers(parser)
    return parser


def resolve_data_path(cli_value: str | None) -> str:
    """``--data`` > ``TASKFLOW_DATA`` > ``./tasks.json`` (FR-012)."""
    if cli_value:
        return cli_value
    return os.environ.get(DATA_ENV_VAR) or DEFAULT_DATA_PATH


def _cmd_add(args: argparse.Namespace, service: TaskService) -> str:
    task = service.add(args.title, args.priority, args.tags)
    return formatting.created_message(task.id)


def _cmd_show(args: argparse.Namespace, service: TaskService) -> str:
    return formatting.format_task_json(service.get(parse_task_id(args.id)))


def _cmd_update(args: argparse.Namespace, service: TaskService) -> str:
    task_id = parse_task_id(args.id)
    service.update(task_id, args.title, args.priority, args.add_tags, args.remove_tags)
    return formatting.updated_message(task_id)


def _cmd_delete(args: argparse.Namespace, service: TaskService) -> str:
    task_id = parse_task_id(args.id)
    service.delete(task_id)
    return formatting.deleted_message(task_id)


def _cmd_status(args: argparse.Namespace, service: TaskService) -> str:
    task_id = parse_task_id(args.id)
    old, new = service.transition(task_id, args.new_status)
    return formatting.transition_message(task_id, old.value, new.value)


def _cmd_list(args: argparse.Namespace, service: TaskService) -> str:
    tasks = service.list(args.tags, args.status, args.sort)
    if args.as_json:
        return formatting.format_task_list_json(tasks)
    return formatting.format_task_list(tasks)


HANDLERS: dict[str, Callable[[argparse.Namespace, TaskService], str]] = {
    "add": _cmd_add,
    "show": _cmd_show,
    "update": _cmd_update,
    "delete": _cmd_delete,
    "status": _cmd_status,
    "list": _cmd_list,
}


def _parse(argv: list[str] | None) -> argparse.Namespace | int:
    try:
        return build_parser().parse_args(argv)
    except SystemExit as exc:
        return _exit_code(exc.code)


def _exit_code(code: object) -> int:
    if code is None:
        return EXIT_OK
    if isinstance(code, int):
        return code
    return EXIT_USAGE


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code (never raises SystemExit)."""
    parsed = _parse(argv)
    if isinstance(parsed, int):
        return parsed
    clock = Clock()
    service = TaskService(JsonStore(resolve_data_path(parsed.data)), clock)
    try:
        clock.now()
        output = HANDLERS[parsed.command](parsed, service)
    except TaskFlowError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return exc.exit_code
    print(output)
    return EXIT_OK
