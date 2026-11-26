# Tests for si_console.smoke. No network: httpx and DNS are faked.
"""Smoke check tests."""

import io
import socket
import sys
from email.utils import formatdate
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import pytest

from si_console import config, smoke

PROVIDERS = {
    "DEEPSEEK_API_KEY": ("DEEPSEEK_MODEL", "deepseek-flash"),
    "HUNYUAN_API_KEY": ("HY4_MODEL", "hy4-model"),
    "GLM_API_KEY": ("GLM_MODEL", "glm-5.4-model"),
    "DASHSCOPE_API_KEY": ("QWEN_MODEL", "qwen4-max-model"),
    "MIMO_API_KEY": ("MIMO_MODEL", "mimo-flash-model"),
}
SECRET = "sk-very-secret-123"


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    for key_attr, (model_attr, model) in PROVIDERS.items():
        monkeypatch.setattr(config, key_attr, SECRET)
        monkeypatch.setattr(config, model_attr, model)
    monkeypatch.setattr(config, "JEV_PROVIDER", "typesafe")
    monkeypatch.setattr(config, "JEV_API_KEY", SECRET)
    monkeypatch.setattr(config, "JEV_URL", config.TYPESAFE_JEV_URL)
    monkeypatch.setattr(config, "JEV_MODEL", "jev-1.14.0")
    monkeypatch.setattr(config, "PANE_CONFIG", {
        "A": {"pin": "auto", "t2": "all", "t1": "on", "fallback": "yes"},
        "B": {"pin": "hy4", "t2": "all", "t1": "on", "fallback": "yes"},
        "C": {"pin": "glm-5.3-flash", "t2": "all", "t1": "on", "fallback": "yes"},
    })
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda host, port, **k: [(2, 1, 6, "", ("93.184.216.34", port))])
    monkeypatch.setattr(httpx, "head", lambda url, **k: httpx.Response(
        200, headers={"date": formatdate(usegmt=True)}, request=httpx.Request("HEAD", url)))


def _fake_get(status_by_host=None, listed=None):
    status_by_host = status_by_host or {}

    def fake(url, headers=None, timeout=None):
        host = httpx.URL(url).host
        status = status_by_host.get(host, 200)
        req = httpx.Request("GET", url)
        if status != 200:
            return httpx.Response(status, json={"error": {"message": f"bad key {SECRET}"}}, request=req)
        ids = listed if listed is not None else [m for _, m in PROVIDERS.values()]
        return httpx.Response(200, json={"data": [{"id": i} for i in ids], "models": []}, request=req)

    return fake


def _run(**kwargs):
    buf = io.StringIO()
    code = smoke.run(out=buf, **kwargs)
    return code, buf.getvalue()


def test_free_mode_all_good(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("free mode spent money"))
    code, text = _run()
    assert code == 0, text
    assert "All tiers usable." in text
    assert SECRET not in text


def test_bad_key_fails_and_is_redacted(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get({"api.hunyuan.cloud.tencent.com": 401}))
    code, text = _run()
    assert "FAIL  key hunyuan" in text
    assert SECRET not in text
    # T0 and T2 still have other working models, so tiers stay usable.
    assert code == 1


def test_unlisted_model_is_a_warning(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get(listed=["deepseek-flash"]))
    code, text = _run()
    assert "WARN  model hy4" in text


def test_openrouter_style_jev_id_on_typesafe_fails(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())
    monkeypatch.setattr(config, "JEV_MODEL", "typesafe/jev-1.14")
    code, text = _run()
    assert code == 1 and "jev-1.14.0" in text


def test_no_t0_model_is_a_failure(monkeypatch):
    for attr in ("DEEPSEEK_API_KEY", "HUNYUAN_API_KEY", "GLM_API_KEY"):
        monkeypatch.setattr(config, attr, "")
    monkeypatch.setattr(httpx, "get", _fake_get())
    code, text = _run()
    assert code == 1 and "FAIL  tier t0" in text


def test_clock_skew_fails(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())
    monkeypatch.setattr(httpx, "head", lambda url, **k: httpx.Response(
        200, headers={"date": "Mon, 01 Jan 2024 00:00:00 GMT"}, request=httpx.Request("HEAD", url)))
    code, text = _run()
    assert code == 1 and "FAIL  clock" in text


def test_live_mode_sends_router_shapes(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())
    sent = []

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.append((url, json))
        req = httpx.Request("POST", url)
        if url.endswith("/web_search"):
            return httpx.Response(200, json=ZHIPU_SEARCH_OK, request=req)
        if url == config.TYPESAFE_JEV_URL:
            return httpx.Response(200, json={"answers": {"pick": {
                "type": "choice", "choice": "apple", "confidence": 0.99,
                "probabilities": {"apple": 0.99, "brick": 0.01}}}, "usage": {}}, request=req)
        message = {"content": "OK"}
        if json.get("tools"):
            message["tool_calls"] = [{"id": "1", "type": "function",
                                      "function": {"name": "ping", "arguments": "{}"}}]
        return httpx.Response(200, json={"model": json["model"], "choices": [
            {"message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 2}}, request=req)

    monkeypatch.setattr(httpx, "post", fake_post)
    code, text = _run(live=True, assume_yes=True)
    assert code == 0, text
    # T0 slots are tested with tools and thinking off, like the router.
    t0 = [j for u, j in sent if j.get("tools")]
    assert {j["model"] for j in t0} == {"deepseek-flash", "hy4-model", "glm-5.4-model"}
    assert any(u == config.TYPESAFE_JEV_URL for u, _ in sent)
    assert "PASS  live jev" in text
    assert "PASS  live web search" in text and "zhipu: 1 result" in text


ZHIPU_SEARCH_OK = {"search_result": [{"title": "t", "content": "c", "link": "https://e.cn",
                                      "media": "m", "publish_date": ""}]}


def test_live_mode_asks_first(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("sent without consent"))
    code, text = _run(live=True)
    assert "Live calls skipped." in text


def test_live_dead_jev_with_working_backup_is_a_warning(monkeypatch):
    monkeypatch.setattr(httpx, "get", _fake_get())
    monkeypatch.setattr(config, "QWEN_JUDGE_MODEL", "qwen-small-test")

    def fake_post(url, headers=None, json=None, timeout=None):
        req = httpx.Request("POST", url)
        if url.endswith("/web_search"):
            return httpx.Response(200, json=ZHIPU_SEARCH_OK, request=req)
        if url == config.TYPESAFE_JEV_URL:
            raise httpx.ConnectTimeout("blocked", request=req)
        content = '{"choice": "apple", "confidence": 0.9}' if json.get("response_format") else "OK"
        message = {"content": content}
        if json.get("tools"):
            message["tool_calls"] = [{"id": "1", "type": "function",
                                      "function": {"name": "ping", "arguments": "{}"}}]
        return httpx.Response(200, json={"model": json["model"], "choices": [
            {"message": message, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 2}}, request=req)

    monkeypatch.setattr(httpx, "post", fake_post)
    code, text = _run(live=True, assume_yes=True)
    assert "WARN  live jev" in text and "other judge covers it" in text
    assert "PASS  live judge backup (qwen)" in text
    assert code == 0, text
