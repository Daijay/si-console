# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton tests. Reference only. Not for Fallen submission.
# Tests for the accepted multi-provider roster (docs/MODEL_TIERS.md):
# tier chains and fallback, arena pane pinning and allowlists, T1
# escalation, the T3 $0 path, per-provider wire shapes, the Jev judge,
# rules-only routing and SQLite telemetry. No network, no keys: every
# HTTP call is a fake. Run with: cd code && python -m pytest tests -v
"""Roster router tests."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import pytest

from si_console import chat_client, config, judge, models, router, telemetry
from si_console.errors import EscalationNeeded, ModelError, ZeroPathNeeded

PROVIDER_ATTRS = {
    "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "deepseek-flash"),
    "hunyuan": ("HUNYUAN_API_KEY", "HY4_MODEL", "hy4-model"),
    "glm": ("GLM_API_KEY", "GLM_MODEL", "glm-5.4-model"),
    "dashscope": ("DASHSCOPE_API_KEY", "QWEN_MODEL", "qwen4-max-model"),
    "mimo": ("MIMO_API_KEY", "MIMO_MODEL", "mimo-flash-model"),
}


@pytest.fixture(autouse=True)
def _all_configured(monkeypatch):
    """Every provider has a fake key and a pinned model id, the way .env
    would at build time. Panes use the documented defaults."""
    for key_attr, model_attr, model in PROVIDER_ATTRS.values():
        monkeypatch.setattr(config, key_attr, "test-key")
        monkeypatch.setattr(config, model_attr, model)
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(config, "JEV_MODEL", "typesafe/jev-1.14")
    panes = {
        "A": {"pin": "auto", "t2": "all", "t1": "on", "fallback": "yes"},
        "B": {"pin": "hy4", "t2": "all", "t1": "on", "fallback": "yes"},
        "C": {"pin": "glm-5.4", "t2": "all", "t1": "on", "fallback": "yes"},
    }
    monkeypatch.setattr(config, "PANE_CONFIG", panes)


def _unconfigure(monkeypatch, provider):
    monkeypatch.setattr(config, PROVIDER_ATTRS[provider][0], "")


class FakeHTTP:
    """Fake httpx.post. Routes by URL host, records every request.
    `fail` is a set of hosts that answer HTTP 503."""

    def __init__(self, fail=(), tool_calls=None):
        self.calls = []
        self.fail = set(fail)
        self.tool_calls = tool_calls

    def host_for(self, url):
        return httpx.URL(url).host

    def __call__(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json})
        request = httpx.Request("POST", url)
        if self.host_for(url) in self.fail:
            return httpx.Response(503, json={"error": "down"}, request=request)
        message = {"content": "ok from " + self.host_for(url)}
        if self.tool_calls:
            message["tool_calls"] = self.tool_calls
        return httpx.Response(
            200,
            json={
                "model": json["model"],
                "choices": [{"message": message, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 20},
            },
            request=request,
        )


HOSTS = {
    "deepseek": "api.deepseek.com",
    "hunyuan": "api.hunyuan.cloud.tencent.com",
    "glm": "open.bigmodel.cn",
    "dashscope": "dashscope-intl.aliyuncs.com",
    "mimo": "api.xiaomimimo.com",
}


@pytest.fixture
def http(monkeypatch):
    fake = FakeHTTP()
    monkeypatch.setattr(httpx, "post", fake)
    return fake


# --- Chains and fallback ------------------------------------------------

def test_tier_chains_match_accepted_roster():
    assert config.MODEL_TIERS["t0"]["chain"] == ["deepseek-v4.1-flash", "hy4", "glm-5.4"]
    assert config.MODEL_TIERS["t1"]["chain"] == ["qwen4-max"]
    assert config.MODEL_TIERS["t2"]["chain"] == ["hy4", "deepseek-v4.1-flash", "glm-5.4"]
    assert config.MODEL_TIERS["t3"]["chain"] == ["mimo-2.6-flash"]


def test_four_different_primaries():
    primaries = {config.MODEL_SLOTS[config.MODEL_TIERS[t]["chain"][0]]["provider"]
                 for t in ("t0", "t1", "t2", "t3")}
    assert primaries == {"deepseek", "dashscope", "hunyuan", "mimo"}


@pytest.mark.parametrize(
    "tier,provider",
    [("t0", "deepseek"), ("coordinator", "deepseek"), ("t1", "dashscope"),
     ("premium", "dashscope"), ("t2", "hunyuan"), ("worker", "hunyuan"), ("t3", "mimo")],
)
def test_each_tier_calls_its_primary(http, tier, provider):
    reply = models.complete(tier, "hi")
    assert reply.provider == provider
    assert http.host_for(http.calls[0]["url"]) == HOSTS[provider]
    assert http.calls[0]["url"].endswith("/chat/completions")


def test_t0_falls_back_deepseek_to_hy4_to_glm(monkeypatch):
    fake = FakeHTTP(fail={HOSTS["deepseek"], HOSTS["hunyuan"]})
    monkeypatch.setattr(httpx, "post", fake)
    reply = models.complete("t0", "hi")
    assert reply.slot == "glm-5.4"
    assert [fake.host_for(c["url"]) for c in fake.calls] == [
        HOSTS["deepseek"], HOSTS["hunyuan"], HOSTS["glm"]]


def test_unconfigured_slot_is_skipped(http, monkeypatch):
    _unconfigure(monkeypatch, "deepseek")
    reply = models.complete("t0", "hi")
    assert reply.slot == "hy4"
    assert all(http.host_for(c["url"]) != HOSTS["deepseek"] for c in http.calls)


def test_whole_t0_down_is_a_model_error(monkeypatch):
    monkeypatch.setattr(httpx, "post", FakeHTTP(fail=set(HOSTS.values())))
    with pytest.raises(ModelError) as exc:
        models.complete("t0", "hi")
    assert "deepseek-v4.1-flash" in exc.value.message and "glm-5.4" in exc.value.message


def test_nothing_configured_is_a_loud_error(monkeypatch):
    for provider in ("deepseek", "hunyuan", "glm"):
        _unconfigure(monkeypatch, provider)
    with pytest.raises(ModelError) as exc:
        models.resolve_tier("t0")
    assert exc.value.status == 500


def test_t1_failure_escalates_to_human(monkeypatch):
    monkeypatch.setattr(httpx, "post", FakeHTTP(fail={HOSTS["dashscope"]}))
    with pytest.raises(EscalationNeeded) as exc:
        models.complete("t1", "hard task")
    assert exc.value.code == "ESCALATE"


def test_t3_failure_goes_to_zero_path(monkeypatch):
    monkeypatch.setattr(httpx, "post", FakeHTTP(fail={HOSTS["mimo"]}))
    with pytest.raises(ZeroPathNeeded):
        models.complete("t3", "summarize this")


def test_unknown_tier_is_a_loud_error():
    with pytest.raises(ModelError):
        models.resolve_tier("no_such_tier")


def test_narration_tier_makes_no_model_call(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("model called"))
    reply = models.complete("narration", "task_started")
    assert reply.text == "task_started"
    assert reply.provider == "prewritten"


def test_claude_is_disabled_and_not_in_roster():
    assert config.CLAUDE_ENABLED is False
    assert all("claude" not in s for s in config.MODEL_SLOTS)


# --- Wire shapes per provider -------------------------------------------

def test_deepseek_thinking_shape(http):
    models.complete("t0", "hi")
    assert http.calls[0]["json"]["thinking"] == {"type": "disabled"}


def test_glm_effort_is_capped_at_high(http, monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "C", {"pin": "glm-5.4", "t2": "all", "t1": "on", "fallback": "no"})
    models.complete("t0", "hi", pane="C", thinking="max")
    body = http.calls[0]["json"]
    assert http.host_for(http.calls[0]["url"]) == HOSTS["glm"]
    assert body["thinking"] == {"type": "enabled"}
    assert body["reasoning_effort"] == "high"


def test_dashscope_uses_enable_thinking(http):
    models.complete("t1", "hi")
    assert http.calls[0]["json"]["enable_thinking"] is False


def test_mimo_sends_api_key_header_and_no_thinking(http):
    models.complete("t3", "hi")
    call = http.calls[0]
    assert call["headers"]["api-key"] == "test-key"
    assert "thinking" not in call["json"] and "enable_thinking" not in call["json"]


def test_tools_reach_the_fallback_provider(monkeypatch):
    calls = [{"id": "1", "type": "function", "function": {"name": "vault_list", "arguments": "{}"}}]
    fake = FakeHTTP(fail={HOSTS["deepseek"]}, tool_calls=calls)
    monkeypatch.setattr(httpx, "post", fake)
    reply = models.complete("t0", "hi", tools=[{"type": "function"}])
    assert reply.tool_calls == calls
    assert fake.calls[1]["json"]["tools"] == [{"type": "function"}]


def test_key_never_in_reply(http):
    assert "test-key" not in json.dumps(models.complete("t2", "hi").to_dict())


def test_transport_error_falls_back(monkeypatch):
    seen = []

    def flaky(url, **kwargs):
        seen.append(url)
        if "deepseek" in url:
            raise httpx.RemoteProtocolError("peer closed")
        return FakeHTTP()(url, **kwargs)

    monkeypatch.setattr(httpx, "post", flaky)
    assert models.complete("t0", "hi").slot == "hy4"


# --- Arena panes --------------------------------------------------------

def test_pane_default_pins():
    assert router.orchestrator_for("A") == ["deepseek-v4.1-flash", "hy4", "glm-5.4"]
    assert router.orchestrator_for("B") == ["hy4", "glm-5.4"]
    assert router.orchestrator_for("C") == ["glm-5.4"]


def test_pinned_pane_without_fallback_stops(monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "B", {"pin": "hy4", "t2": "all", "t1": "on", "fallback": "no"})
    monkeypatch.setattr(httpx, "post", FakeHTTP(fail={HOSTS["hunyuan"]}))
    with pytest.raises(ModelError):
        models.complete("t0", "hi", pane="B")


def test_pin_must_be_a_t0_model(monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "qwen4-max", "t2": "all", "t1": "on", "fallback": "yes"})
    with pytest.raises(ModelError):
        models.plan("t0", "A")


def test_t2_allowlist_restricts_workers(http, monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "auto", "t2": "glm-5.4", "t1": "on", "fallback": "yes"})
    reply = models.complete("t2", "hi", pane="A")
    assert reply.slot == "glm-5.4"


def test_t2_allowlist_rejects_non_t2_model(monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "auto", "t2": "qwen4-max", "t1": "on", "fallback": "yes"})
    with pytest.raises(ModelError):
        models.plan("t2", "A")


def test_empty_t2_goes_to_t1_then_zero_path(monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "auto", "t2": "none", "t1": "on", "fallback": "yes"})
    assert models.plan("t2", "A") == ("t1", ["qwen4-max"])
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "auto", "t2": "none", "t1": "off", "fallback": "yes"})
    assert models.plan("t2", "A") == ("t3", [])


def test_t1_off_escalates_without_a_call(monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "auto", "t2": "all", "t1": "off", "fallback": "yes"})
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("model called"))
    with pytest.raises(EscalationNeeded):
        models.complete("t1", "hi", pane="A")


# --- Jev judge ----------------------------------------------------------

def _jev(monkeypatch, answer, status=200):
    seen = []

    def fake(url, headers=None, json=None, timeout=None):
        seen.append({"url": url, "json": json, "headers": headers})
        return httpx.Response(status, json={"answers": {"pick": answer},
                                            "usage": {"input_tokens": 500, "output_tokens": 3}},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake)
    return seen


def test_judge_request_shape(monkeypatch):
    seen = _jev(monkeypatch, {"type": "choice", "choice": "x", "confidence": 0.9})
    decision = judge.decide_choice("Pick one.", {"x": "first", "y": "second"}, {"a": 1})
    assert decision.choice == "x"
    body = seen[0]["json"]
    assert seen[0]["url"] == "https://openrouter.ai/api/alpha/decisions"
    assert body["model"] == "typesafe/jev-1.14"
    assert body["questions"]["pick"] == {"type": "choice", "instructions": "Pick one.",
                                         "criteria": {"x": "first", "y": "second"}}


def test_judge_cannot_pick_outside_options(monkeypatch):
    _jev(monkeypatch, {"type": "choice", "choice": "qwen4-max", "confidence": 1.0})
    with pytest.raises(judge.JudgeError):
        judge.decide_choice("Pick.", {"t2": "a", "t3": "b"}, "state")


def test_judge_refusal_and_low_confidence(monkeypatch):
    _jev(monkeypatch, {"type": "refusal"})
    with pytest.raises(judge.JudgeError):
        judge.decide_choice("Pick.", {"a": "a"}, "s")
    _jev(monkeypatch, {"type": "choice", "choice": "a", "confidence": 0.2})
    with pytest.raises(judge.JudgeError):
        judge.decide_choice("Pick.", {"a": "a"}, "s", min_confidence=0.5)


# --- Rules routing ------------------------------------------------------

def test_skill_wins(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("judge called"))
    assert router.route("anything at all", skill="research").tier == "t2"
    assert router.route("x", skill="debug").tier == "t1"


def test_keywords_and_length():
    assert router.route("Please summarize this paragraph.").tier == "t3"
    assert router.route("Debug why does the bridge drop the kill event " * 3).tier == "t1"


def test_conflict_uses_judge_within_allowlist(monkeypatch):
    monkeypatch.setitem(config.PANE_CONFIG, "A", {"pin": "auto", "t2": "all", "t1": "off", "fallback": "yes"})
    seen = _jev(monkeypatch, {"type": "choice", "choice": "t2", "confidence": 0.9})
    decision = router.route("Summarize and debug this " + "x" * 300, pane="A")
    assert decision.tier == "t2" and decision.judged
    assert set(seen[0]["json"]["questions"]["pick"]["criteria"]) == {"t2", "t3"}


def test_judge_failure_defaults_to_t2(monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "")
    decision = router.route("Summarize and debug this " + "x" * 300)
    assert decision.tier == "t2" and decision.reason.endswith("->default")


def test_dispatch_reports_escalation_not_crash(monkeypatch):
    monkeypatch.setattr(httpx, "post", FakeHTTP(fail={HOSTS["dashscope"]}))
    result = router.dispatch("x", skill="debug")
    assert result.escalate and result.reply is None


# --- Telemetry ----------------------------------------------------------

def test_every_attempt_is_logged(monkeypatch):
    monkeypatch.setattr(httpx, "post", FakeHTTP(fail={HOSTS["deepseek"]}))
    models.complete("t0", "secret prompt text", pane="A")
    logged = telemetry.rows()
    assert [(r["slot"], r["ok"]) for r in reversed(logged)] == [
        ("deepseek-v4.1-flash", 0), ("hy4", 1)]
    assert logged[0]["pane"] == "A" and logged[0]["cost_usd"] > 0
    assert "secret prompt text" not in json.dumps(logged)


def test_roster_status_has_no_keys():
    status = models.roster_status()
    assert set(status) == set(config.MODEL_SLOTS) | {"jev"}
    assert "test-key" not in json.dumps(status)
