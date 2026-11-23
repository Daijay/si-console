# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton tests. Reference only. Not for Fallen submission.
# These tests check the router stub in models.py. No test calls
# DeepSeek. No test calls Anthropic. No test needs a Pi or a key.
# The router maps tiers to DeepSeek models and always fails closed
# to DeepSeek flash when a tier asks for Claude. The booth build
# ships with CLAUDE_ENABLED false and no Anthropic key.
# Run with: cd scratch && python3 -m pytest tests/test_router.py -v
"""Router stub tests. Tier resolution and Claude fallback."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config, models
from si_console.errors import ModelError


@pytest.fixture(autouse=True)
def _pinned_models(monkeypatch):
    """Pin the model names the way .env would at build time."""
    monkeypatch.setattr(config, "DEEPSEEK_MODEL", "deepseek-flash")
    monkeypatch.setattr(config, "DEEPSEEK_MODEL_PRO", "deepseek-v4-pro")
    monkeypatch.setattr(config, "CLAUDE_ENABLED", False)
    for tier, model in (
        ("coordinator", "deepseek-flash"),
        ("worker", "deepseek-flash"),
        ("premium", "deepseek-v4-pro"),
        ("light", "deepseek-flash"),
    ):
        monkeypatch.setitem(config.MODEL_TIERS[tier], "model", model)
    models.reset_fallback_log()
    yield
    models.reset_fallback_log()


def _fake_deepseek_reply(**overrides):
    """A fake raw reply in the shape deepseek_client.complete returns."""
    reply = {
        "text": "done",
        "data": None,
        "tool_calls": [],
        "model": "deepseek-flash",
        "finish_reason": "stop",
        "input_tokens": 10,
        "output_tokens": 5,
    }
    reply.update(overrides)
    return reply


def test_coordinator_resolves_to_flash_with_thinking_disabled():
    resolved = models.resolve_tier("coordinator")
    assert resolved["provider"] == "deepseek"
    assert resolved["model"] == "deepseek-flash"
    assert resolved["thinking"] == "disabled"


def test_worker_resolves_to_flash_with_thinking_low():
    resolved = models.resolve_tier("worker")
    assert resolved["provider"] == "deepseek"
    assert resolved["model"] == "deepseek-flash"
    assert resolved["thinking"] == "low"


def test_premium_resolves_to_pro_with_thinking_disabled():
    resolved = models.resolve_tier("premium")
    assert resolved["provider"] == "deepseek"
    assert resolved["model"] == "deepseek-v4-pro"
    assert resolved["thinking"] == "disabled"


def test_premium_without_pro_model_is_a_loud_error(monkeypatch):
    monkeypatch.setitem(config.MODEL_TIERS["premium"], "model", "")
    with pytest.raises(ModelError):
        models.resolve_tier("premium")


def test_coordinator_without_model_is_a_loud_error(monkeypatch):
    monkeypatch.setitem(config.MODEL_TIERS["coordinator"], "model", "")
    with pytest.raises(ModelError):
        models.resolve_tier("coordinator")


def test_unknown_tier_is_a_loud_error():
    with pytest.raises(ModelError):
        models.resolve_tier("no_such_tier")


def test_claude_tier_falls_back_to_deepseek_flash(monkeypatch):
    # A tier that names Claude. The table has none by default, so
    # the test adds one. The router must never call Claude.
    monkeypatch.setitem(
        config.MODEL_TIERS,
        "claude_premium",
        {"provider": "claude", "model": "claude-opus-5-5", "max_tokens": 2000},
    )
    resolved = models.resolve_tier("claude_premium")
    assert resolved["provider"] == "deepseek"
    assert resolved["model"] == "deepseek-flash"
    assert resolved["thinking"] == "disabled"


def test_claude_fallback_logs_once_per_run(monkeypatch, caplog):
    monkeypatch.setitem(
        config.MODEL_TIERS,
        "claude_premium",
        {"provider": "claude", "model": "claude-opus-5-5", "max_tokens": 2000},
    )
    with caplog.at_level(logging.WARNING, logger="si_console.models"):
        models.resolve_tier("claude_premium")
        models.resolve_tier("claude_premium")
    hits = [r for r in caplog.records if "falls back" in r.getMessage()]
    assert len(hits) == 1
    models.reset_fallback_log()
    with caplog.at_level(logging.WARNING, logger="si_console.models"):
        models.resolve_tier("claude_premium")
    hits = [r for r in caplog.records if "falls back" in r.getMessage()]
    assert len(hits) == 2


def test_complete_passes_thinking_per_tier(monkeypatch):
    seen = {}

    def fake_complete(message, system, *, model, max_tokens, tools, schema, thinking):
        seen["model"] = model
        seen["thinking"] = thinking
        return _fake_deepseek_reply(model=model)

    monkeypatch.setattr(models, "deepseek_complete", fake_complete)
    models.complete("coordinator", "hi")
    assert seen["model"] == "deepseek-flash"
    assert seen["thinking"] == "disabled"
    models.complete("worker", "hi")
    assert seen["thinking"] == "low"
    models.complete("premium", "hi")
    assert seen["model"] == "deepseek-v4-pro"
    assert seen["thinking"] == "disabled"


def test_complete_thinking_override(monkeypatch):
    seen = {}

    def fake_complete(message, system, *, model, max_tokens, tools, schema, thinking):
        seen["thinking"] = thinking
        return _fake_deepseek_reply(model=model)

    monkeypatch.setattr(models, "deepseek_complete", fake_complete)
    models.complete("coordinator", "hi", thinking="low")
    assert seen["thinking"] == "low"


def test_narration_tier_makes_no_model_call(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("narration must not call a model")

    monkeypatch.setattr(models, "deepseek_complete", fail_if_called)
    reply = models.complete("narration", "task_started")
    assert reply.provider == "prewritten"
    assert reply.text == "task_started"
    assert reply.model == "strings.json"


def test_key_configured(monkeypatch):
    assert models.key_configured("narration") is True
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "")
    assert models.key_configured("coordinator") is False
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "test-key")
    assert models.key_configured("coordinator") is True
    monkeypatch.setitem(
        config.MODEL_TIERS,
        "claude_premium",
        {"provider": "claude", "model": "claude-opus-5-5", "max_tokens": 2000},
    )
    # Claude is never treated as configured in this build. The
    # router falls back to DeepSeek, so callers must not wait on it.
    assert models.key_configured("claude_premium") is False


def test_claude_is_disabled_by_default():
    # The default lives in config.py: SI_CLAUDE_ENABLED defaults to
    # "false". The booth build ships with it off and no Anthropic key.
    assert config.CLAUDE_ENABLED is False
