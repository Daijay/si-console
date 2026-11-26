"""Keys must never appear in output, even partly masked by a provider."""

import pytest

from si_console.chat_client import redact

KEY = "sk-zSJXpAbCdEfGhIjKlMnOpQrStUvWxYzTbLdgcA"


@pytest.mark.parametrize("text", [
    f"Incorrect API key provided: {KEY}.",
    "Incorrect API key provided: sk-zSJXp************************************TbLdgcA. You can find it.",
    "bad key sk-zSJXp... (prefix only)",
    "key ends with ...TbLdgcA",
    "other key-shaped token sk-AAAAAAAAAAAA in the message",
])
def test_no_key_material_survives(text):
    out = redact(text, KEY)
    assert "zSJXp" not in out and "TbLdgcA" not in out and "sk-AAAA" not in out
    assert "[REDACTED]" in out


def test_plain_text_is_kept():
    message = "Rate limited by Hunyuan. Retry after 60s. Model hy4-flash not found."
    assert redact(message, KEY) == message


@pytest.mark.parametrize("status,body", [
    (429, {"error": {"code": "1113", "message": "余额不足或无可用资源包,请充值。"}}),
    (402, {"error": {"message": "Insufficient Balance"}}),
])
def test_out_of_credit_is_not_called_a_rate_limit(monkeypatch, status, body):
    import httpx
    from si_console import chat_client, config
    from si_console.errors import ModelError

    monkeypatch.setattr(config, "GLM_API_KEY", "k")
    monkeypatch.setattr(httpx, "post", lambda url, **kw: httpx.Response(
        status, json=body, request=httpx.Request("POST", url)))
    with pytest.raises(ModelError) as exc:
        chat_client.complete("glm", "hi", model="m", max_tokens=5)
    assert "out of credit" in exc.value.message and "Rate limited" not in exc.value.message
    assert exc.value.status == 402


def test_key_fragment_inside_a_url_is_not_redacted():
    # A key whose first 6 characters happen to occur inside a provider's link.
    key = "apikey_" + "Z" * 40 + "q9x8w7"
    url = "See: https://console.cloud.tencent.com/tokenhub/apikey"
    assert redact(url, key) == url
    assert "Z" * 10 not in redact(f"bad key {key[:10]}*****{key[-6:]}", key)
