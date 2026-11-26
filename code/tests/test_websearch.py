"""Web search: Zhipu (Z.ai) on the GLM key first, Bocha fallback only if set."""

import json

import httpx
import pytest

from si_console import config, websearch

MAINLAND = "https://open.bigmodel.cn/api/paas/v4"
INTL = "https://api.z.ai/api/paas/v4"


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setattr(config, "GLM_API_KEY", "glm-key")
    monkeypatch.setattr(config, "GLM_BASE_URL", MAINLAND)
    monkeypatch.setattr(config, "ZHIPU_SEARCH_ENGINE", "search_std")
    monkeypatch.setattr(config, "BOCHA_API_KEY", "")


ZHIPU_OK = {
    "id": "t1", "created": 1, "request_id": "r1",
    "search_intent": [{"query": "q", "intent": "SEARCH_ALWAYS", "keywords": "q"}],
    "search_result": [
        {"title": "Shenzhen", "content": "Sunny.", "link": "https://example.cn/a",
         "media": "Example", "icon": "", "refer": "ref_1", "publish_date": "2026-11-25"},
        {"title": "Two", "content": "More.", "link": "https://example.cn/b",
         "media": "Ex", "icon": "", "refer": "ref_2", "publish_date": ""},
    ],
}


def _capture(monkeypatch, status=200, payload=ZHIPU_OK, raise_exc=None):
    seen = []

    def fake(url, headers=None, json=None, timeout=None):
        seen.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        if raise_exc:
            raise raise_exc
        return httpx.Response(status, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake)
    return seen


def test_mainland_request_and_mapping(monkeypatch):
    seen = _capture(monkeypatch)
    result = websearch.web_search("Shenzhen weather", count=2, freshness="oneWeek")
    assert result["provider"] == "zhipu"
    assert result["results"][0] == {"title": "Shenzhen", "url": "https://example.cn/a",
                                    "snippet": "Sunny.", "date": "2026-11-25", "source": "Example"}
    call = seen[0]
    assert call["url"] == MAINLAND + "/web_search"
    assert call["headers"]["Authorization"] == "Bearer glm-key"
    assert call["json"] == {"search_query": "Shenzhen weather", "search_engine": "search_std",
                            "count": 2, "search_recency_filter": "oneWeek",
                            "search_intent": False, "content_size": "medium"}


def test_international_zai_uses_search_prime(monkeypatch):
    monkeypatch.setattr(config, "GLM_BASE_URL", INTL)
    seen = _capture(monkeypatch)
    websearch.web_search("x" * 150, count=3)
    body = seen[0]["json"]
    assert seen[0]["url"] == INTL + "/web_search"
    assert body["search_engine"] == "search-prime"
    assert "search_intent" not in body and "content_size" not in body
    assert len(body["search_query"]) == 150  # no 70-char cap on Z.ai


def test_mainland_query_clipped_to_70_at_a_word(monkeypatch):
    seen = _capture(monkeypatch)
    query = "sector rotation energy stocks 2022 bear market inflation interest rates oil price shock"
    websearch.web_search(query)
    sent = seen[0]["json"]["search_query"]
    assert len(sent) <= 70 and query.startswith(sent) and not sent.endswith(" ")


def test_error_is_reported_not_empty_and_key_redacted(monkeypatch):
    _capture(monkeypatch, status=429,
             payload={"error": {"code": "1701", "message": "concurrency limit glm-key"}})
    result = websearch.web_search("q")
    assert "error" in result and "429" in result["error"] and "1701" not in result.get("results", [])
    assert "glm-key" not in json.dumps(result)


def test_network_error_retries_once_then_errors(monkeypatch):
    seen = _capture(monkeypatch, raise_exc=httpx.ConnectError("down"))
    result = websearch.web_search("q")
    assert len(seen) == 2 and "not reachable" in result["error"]


def test_bocha_fallback_only_when_its_key_is_set(monkeypatch):
    _capture(monkeypatch, status=503, payload={"error": {"code": "1702", "message": "no engine"}})
    called = []
    from si_console import bocha

    monkeypatch.setattr(bocha, "web_search", lambda *a, **k: called.append(1) or {"results": []})
    assert "error" in websearch.web_search("q")
    assert not called
    monkeypatch.setattr(config, "BOCHA_API_KEY", "b-key")
    assert websearch.web_search("q")["provider"] == "bocha"
    assert called


def test_no_search_configured(monkeypatch):
    monkeypatch.setattr(config, "GLM_API_KEY", "")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("called"))
    assert "GLM_API_KEY" in websearch.web_search("q")["error"]


@pytest.mark.parametrize("args", [("", 5, "noLimit"), ("q", 0, "noLimit"), ("q", 11, "noLimit"),
                                  ("q", True, "noLimit"), ("q", 5, "lastYear")])
def test_input_validation(monkeypatch, args):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("called"))
    assert "error" in websearch.web_search(*args)
