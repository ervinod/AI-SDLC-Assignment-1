"""Layer 1 – structural validation against the harness-owned JSON Schema (SCH-1, SCH-2)."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

_SCHEMA = json.loads((Path(__file__).parent.parent / "schema" / "response.schema.json").read_text())
_VALIDATOR = Draft202012Validator(_SCHEMA)


def check(output) -> list[str]:
    """Return a list of schema violations (empty list = Layer 1 pass)."""
    errors = sorted(_VALIDATOR.iter_errors(output), key=lambda e: list(e.path))
    return [f"SCH: {'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors]
