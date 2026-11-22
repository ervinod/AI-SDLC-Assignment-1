"""T028 – FR-011 provider selection and the local Ollama extractor (plan.md › Amendment).

Offline: `urllib.request.urlopen` is stubbed; no server or download is needed.
"""

import io
import json
import urllib.error
import urllib.request

import pytest

from remindme.agent import ServiceError, handle
from tests.conftest import REMINDERS, req
from tests.test_extractor_cli import GOOD


class FakeHTTP:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def __call__(self, request, timeout=None, **kwargs):
        self.requests.append((request, timeout))
        if isinstance(self.result, Exception):
            raise self.result
        return io.BytesIO(self.result)


def body(content, done_reason="stop"):
    return json.dumps(
        {
            "message": {"role": "assistant", "content": content},
            "done": True,
            "done_reason": done_reason,
        }
    ).encode()


@pytest.fixture
def ollama(monkeypatch):
    monkeypatch.setenv("REMINDME_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("REMINDME_OLLAMA_MODEL", raising=False)

    def install(result):
        fake = FakeHTTP(result)
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        return fake

    return install


def test_fr011_ollama_end_to_end_request_shape(ollama):
    fake = ollama(body(json.dumps(GOOD)))
    out = handle(req("remind me to call mom tomorrow at 6pm", reminders=REMINDERS))
    assert (out["intent"], out["due_at"]) == ("create", "2026-11-24T18:00:00+05:30")
    request, timeout = fake.requests[0]
    assert request.full_url == "http://127.0.0.1:11434/api/chat"
    assert timeout == 120
    sent = json.loads(request.data)
    assert sent["model"] == "llama3.2:3b"
    assert sent["stream"] is False
    assert sent["format"]["properties"]["intent"]["enum"][0] == "create"
    roles = [m["role"] for m in sent["messages"]]
    assert roles == ["system", "user"]
    assert "RMD-CANARY-7731" in sent["messages"][0]["content"]
    assert "remind me to call mom tomorrow at 6pm" in sent["messages"][1]["content"]
    assert "options" not in sent or not {"temperature", "seed"} & set(sent["options"])


def test_fr011_host_and_model_overrides(ollama, monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:9999")
    monkeypatch.setenv("REMINDME_OLLAMA_MODEL", "qwen2.5:7b")
    fake = ollama(body(json.dumps(GOOD)))
    handle(req("remind me to call mom tomorrow at 6pm"))
    request, _ = fake.requests[0]
    assert request.full_url == "http://localhost:9999/api/chat"
    assert json.loads(request.data)["model"] == "qwen2.5:7b"


def test_done_reason_length_is_service_error(ollama):
    ollama(body(json.dumps(GOOD), done_reason="length"))
    with pytest.raises(ServiceError):
        handle(req("remind me to call mom tomorrow at 6pm"))


@pytest.mark.parametrize(
    "exc",
    [
        urllib.error.URLError("connection refused"),
        urllib.error.HTTPError("http://x", 500, "boom", {}, None),
        TimeoutError("slow"),
        ConnectionResetError("reset"),
    ],
)
def test_transport_errors_are_service_errors(ollama, exc):
    ollama(exc)
    with pytest.raises(ServiceError):
        handle(req("remind me to call mom tomorrow at 6pm"))


@pytest.mark.parametrize("raw", [b"<html>not json</html>", json.dumps({"done": True}).encode()])
def test_invalid_http_body_is_service_error(ollama, raw):
    ollama(raw)
    with pytest.raises(ServiceError):
        handle(req("remind me to call mom tomorrow at 6pm"))


def test_unparsable_model_content_becomes_clarify(ollama):
    ollama(body("Sure! Here is your reminder: call mom"))
    assert handle(req("remind me to call mom tomorrow at 6pm"))["intent"] == "clarify"


def test_unknown_provider_is_service_error(monkeypatch):
    monkeypatch.setenv("REMINDME_PROVIDER", "carrier-pigeon")
    with pytest.raises(ServiceError):
        handle(req("remind me to call mom tomorrow at 6pm"))


def test_gr1_still_needs_no_provider(ollama):
    fake = ollama(urllib.error.URLError("must not be called"))
    assert handle(req("   "))["intent"] == "reject"
    assert fake.requests == []
