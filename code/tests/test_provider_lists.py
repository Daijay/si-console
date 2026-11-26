"""Free model-list checks per provider, and the TokenHub default."""

import httpx

from si_console import chat_client, config


def test_hunyuan_defaults_to_tokenhub_guangzhou():
    assert config.HUNYUAN_BASE_URL == "https://tokenhub.tencentcloudmaas.com/v1"


def test_bailian_uses_native_model_list(monkeypatch):
    monkeypatch.setattr(config, "DASHSCOPE_API_KEY", "k")
    monkeypatch.setattr(config, "DASHSCOPE_BASE_URL",
                        "https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1")
    seen = []

    def fake(url, headers=None, timeout=None):
        seen.append(url)
        return httpx.Response(200, json={"success": True, "output": {"total": 2, "models": [
            {"model": "qwen4-max", "name": "Qwen4-Max"},
            {"model": "qwen3.8-flash", "name": "Qwen3.8-Flash"}]}},
            request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake)
    result = chat_client.list_models("dashscope")
    assert seen == ["https://cn-hongkong.dashscope.aliyuncs.com/api/v1/models?page_size=200"]
    assert result["status"] == 200 and result["models"] == ["qwen4-max", "qwen3.8-flash"]


def test_openai_style_list_still_parsed(monkeypatch):
    monkeypatch.setattr(config, "DEEPSEEK_API_KEY", "k")
    monkeypatch.setattr(httpx, "get", lambda url, **kw: httpx.Response(
        200, json={"data": [{"id": "deepseek-flash"}]}, request=httpx.Request("GET", url)))
    assert chat_client.list_models("deepseek")["models"] == ["deepseek-flash"]
