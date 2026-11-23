# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton tests. Reference only. Not for Fallen submission.
# These tests check deepseek_client.py with a mocked httpx.post. No
# test calls the real DeepSeek API. No test needs a key. The fake
# reply is shaped like the real chat completions response.
# Run with: cd scratch && python3 -m pytest tests/test_deepseek_client.py -v
"""DeepSeek client tests. Mocked HTTP, thinking flag, error paths."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config, deepseek_client
from si_console.errors import ModelError


class FakeResponse:
    """Minimal stand-in for an httpx response."""

    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.headers = {}
        self._payload = payload or {}

    def json(self):
        return self._payload


def _ok_payload(text="hello", model="deepseek-flash", tool_calls=None):
    return {
        "choices": [
            {
                "message": {
                    "content": text,
                    "tool_calls": tool_calls or [],
                },
                "finish_reason": "stop",
            }
        ],
        "model": model,
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


@pytest.fixture(autouse=True)
def _key_and_model(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(config, "DEEPSEEK_MODEL", "deepseek-flash")


def _capture_post(monkeypatch, response):
    """Replace httpx.post. Returns the list of calls it saw."""
    seen = []

    def fake_post(url, headers, json, timeout):
        seen.append({"url": url, "headers": headers, "json": json})
        return response

    monkeypatch.setattr(deepseek_client.httpx, "post", fake_post)
    return seen


def test_complete_sends_thinking_disabled_by_default(monkeypatch):
    seen = _capture_post(monkeypatch, FakeResponse(200, _ok_payload()))
    result = deepseek_client.complete(
        "hi", model="deepseek-flash", max_tokens=100
    )
    assert result["text"] == "hello"
    assert result["model"] == "deepseek-flash"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5
    assert seen[0]["json"]["thinking"] == {"type": "disabled"}
    assert seen[0]["json"]["model"] == "deepseek-flash"
    # The key is sent, but it is never in the returned result.
    assert "test-key" not in str(result)


def test_complete_thinking_low_sends_enabled_effort(monkeypatch):
    seen = _capture_post(monkeypatch, FakeResponse(200, _ok_payload()))
    deepseek_client.complete(
        "hi", model="deepseek-flash", max_tokens=100, thinking="low"
    )
    assert seen[0]["json"]["thinking"] == {"type": "enabled", "effort": "low"}


def test_bad_thinking_value_is_rejected():
    with pytest.raises(ModelError):
        deepseek_client.complete(
            "hi", model="deepseek-flash", max_tokens=100, thinking="huge"
        )


def test_tools_and_schema_together_is_rejected():
    with pytest.raises(ModelError):
        deepseek_client.complete(
            "hi",
            model="deepseek-flash",
            max_tokens=100,
            tools=[{"type": "function"}],
            schema={"type": "object"},
        )


def test_empty_message_is_rejected():
    with pytest.raises(ModelError):
        deepseek_client.complete("   ", model="deepseek-flash", max_tokens=100)


def test_schema_path_returns_parsed_data(monkeypatch):
    payload = _ok_payload(text='{"action": "create_task", "task_id": "x"}')
    _capture_post(monkeypatch, FakeResponse(200, payload))
    result = deepseek_client.complete(
        "hi",
        model="deepseek-flash",
        max_tokens=100,
        schema={"type": "object"},
    )
    assert result["data"] == {"action": "create_task", "task_id": "x"}


def test_tool_calls_pass_through(monkeypatch):
    calls = [{"function": {"name": "vault_read", "arguments": "{}"}}]
    payload = _ok_payload(text="", tool_calls=calls)
    _capture_post(monkeypatch, FakeResponse(200, payload))
    result = deepseek_client.complete(
        "hi",
        model="deepseek-flash",
        max_tokens=100,
        tools=[{"type": "function"}],
    )
    assert result["tool_calls"] == calls


def test_missing_key_fails_loudly(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "")
    with pytest.raises(ModelError) as exc:
        deepseek_client.complete("hi", model="deepseek-flash", max_tokens=100)
    assert exc.value.status == 503


def test_missing_model_fails_loudly(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_MODEL", "")
    with pytest.raises(ModelError) as exc:
        deepseek_client.complete("hi", model="deepseek-flash", max_tokens=100)
    assert exc.value.status == 500


def test_401_is_an_error(monkeypatch):
    _capture_post(monkeypatch, FakeResponse(401, {}))
    with pytest.raises(ModelError) as exc:
        deepseek_client.complete("hi", model="deepseek-flash", max_tokens=100)
    assert exc.value.status == 401


def test_429_is_an_error(monkeypatch):
    _capture_post(monkeypatch, FakeResponse(429, {}))
    with pytest.raises(ModelError) as exc:
        deepseek_client.complete("hi", model="deepseek-flash", max_tokens=100)
    assert exc.value.status == 429


def test_non_json_reply_is_an_error(monkeypatch):
    bad = FakeResponse(200, {})
    bad.json = lambda: (_ for _ in ()).throw(ValueError("not json"))
    _capture_post(monkeypatch, bad)
    with pytest.raises(ModelError) as exc:
        deepseek_client.complete("hi", model="deepseek-flash", max_tokens=100)
    assert exc.value.status == 502


def test_reply_with_no_choices_is_an_error(monkeypatch):
    _capture_post(monkeypatch, FakeResponse(200, {"choices": []}))
    with pytest.raises(ModelError) as exc:
        deepseek_client.complete("hi", model="deepseek-flash", max_tokens=100)
    assert exc.value.status == 502
