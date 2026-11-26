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
