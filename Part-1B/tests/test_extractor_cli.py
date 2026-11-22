"""T026/T027 (added after harness run-001, see evidence/harness-log.md) – default extractor and CLI.

Offline: `anthropic.Anthropic` is replaced by a fake client, so no network call or API key is used.
Covers FR-010 / research R6 (service-error mapping), R1 (structured output request), R4 (canary
in prompt, delimited user text), SCH-4 and the CLI exit codes in plan.md.
"""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from remindme import cli
from remindme.agent import ServiceError, handle
from tests.conftest import REMINDERS, req

GOOD = {
    "intent": "create",
    "task": "call mom",
    "time_spec": {
        "offset_minutes": None,
        "day_offset": 1,
        "weekday": None,
        "date": None,
        "time": "18:00",
    },
    "recurrence": "none",
    "target_id": None,
    "snooze_minutes": None,
    "missing": [],
    "question": None,
    "reason": None,
}


def message(text=None, stop_reason="end_turn"):
    content = [] if text is None else [SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(stop_reason=stop_reason, content=content)


class FakeClient:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture
def client(monkeypatch):
    holder = {}

    def install(result):
        holder["c"] = FakeClient(result)
        monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: holder["c"])
        return holder["c"]

    return install


def test_default_extractor_end_to_end(client):
    c = client(message(json.dumps(GOOD)))
    out = handle(req("remind me to call mom tomorrow at 6pm", reminders=REMINDERS))
    assert (out["intent"], out["due_at"]) == ("create", "2026-11-24T18:00:00+05:30")
    call = c.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in call and "top_p" not in call
    assert "RMD-CANARY-7731" in json.dumps(call["system"])
    user_text = json.dumps(call["messages"])
    assert "remind me to call mom tomorrow at 6pm" in user_text
    assert "r2" in user_text  # existing reminders are provided to the model


def test_model_and_effort_env_overrides(client, monkeypatch):
    monkeypatch.setenv("REMINDME_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("REMINDME_EFFORT", "medium")
    c = client(message(json.dumps(GOOD)))
    handle(req("remind me to call mom tomorrow at 6pm"))
    assert c.calls[0]["model"] == "claude-sonnet-5-5"
    assert c.calls[0]["output_config"]["effort"] == "medium"


@pytest.mark.parametrize("stop", ["refusal", "max_tokens"])
def test_r6_bad_stop_reason_is_service_error(client, stop):
    client(message(json.dumps(GOOD), stop_reason=stop))
    with pytest.raises(ServiceError):
        handle(req("remind me to call mom tomorrow at 6pm"))


def _status_error(code):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(code, request=request)
    return anthropic.APIStatusError("boom", response=response, body=None)


@pytest.mark.parametrize(
    "exc",
    [
        anthropic.APIConnectionError(
            request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
        ),
        _status_error(429),
        _status_error(500),
        _status_error(401),
    ],
)
def test_r6_api_errors_are_service_errors(client, exc):
    client(exc)
    with pytest.raises(ServiceError):
        handle(req("remind me to call mom tomorrow at 6pm"))


@pytest.mark.parametrize("raw", [message("not json {"), message(None)])
def test_r8_unparsable_model_reply_becomes_clarify(client, raw):
    client(raw)
    out = handle(req("remind me to call mom tomorrow at 6pm"))
    assert out["intent"] == "clarify"


# --- CLI (SCH-4, exit codes) ---------------------------------------------------------------------
NOW = ["--now", "2026-11-23T09:00:00+05:30", "--tz", "Asia/Kolkata"]


def test_cli_success_prints_json(client, capsys):
    client(message(json.dumps(GOOD)))
    code = cli.main([*NOW, "remind me to call mom tomorrow at 6pm"])
    out = capsys.readouterr().out
    assert code == 0
    assert json.loads(out)["due_at"] == "2026-11-24T18:00:00+05:30"


def test_cli_with_reminders_file(client, capsys, tmp_path):
    f = tmp_path / "rem.json"
    f.write_text(json.dumps(REMINDERS))
    client(message(json.dumps({**GOOD, "intent": "cancel", "target_id": "r3", "task": None})))
    assert cli.main([*NOW, "--reminders", str(f), "cancel the gym reminder"]) == 0
    assert json.loads(capsys.readouterr().out)["target_id"] == "r3"


def test_cli_request_error_exit_2(client, capsys):
    client(message(json.dumps(GOOD)))
    assert cli.main(["--now", "bad", "--tz", "Asia/Kolkata", "x"]) == 2
    assert capsys.readouterr().out == ""


def test_cli_missing_reminders_file_exit_2(client, capsys, tmp_path):
    client(message(json.dumps(GOOD)))
    assert cli.main([*NOW, "--reminders", str(tmp_path / "nope.json"), "x"]) == 2


def test_cli_service_error_exit_3(client, capsys):
    client(_status_error(503))
    assert cli.main([*NOW, "remind me to call mom tomorrow at 6pm"]) == 3
    assert capsys.readouterr().out == ""


def test_cli_default_now(client, capsys):
    client(message(json.dumps({**GOOD, "time_spec": {**GOOD["time_spec"], "day_offset": 1}})))
    assert cli.main(["--tz", "Asia/Kolkata", "remind me to call mom tomorrow at 6pm"]) == 0
