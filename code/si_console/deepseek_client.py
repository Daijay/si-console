# This file is Autumn's autumn/groq_client.py, rewired for DeepSeek.
# What changed: the provider is DeepSeek, reached through its OpenAI
# compatible API at the base URL in config. The Groq SDK is gone.
# This file uses plain httpx, not the OpenAI SDK, so the team can see
# every request and every error. No new SDK to learn.
# What stayed: the same error shape as groq_client.py, the same rule
# that the key comes from .env and is never logged, echoed, or returned,
# and the same schema constrained JSON path, which the coordinator loop
# depends on. DeepSeek supports response_format json_object for JSON.
# If DeepSeek ever drops json_object, this file must fail loudly, not
# silently return prose where the caller expected an object.
# No API keys are in this file. The key comes from config only.
"""DeepSeek API layer. One prompt in, one text answer out."""

from __future__ import annotations

from typing import Optional

import httpx  # noqa: F401 - tests patch deepseek_client.httpx.post

from si_console import chat_client, config
from si_console.errors import ModelError


def _check_key() -> str:
    """Get the key from config. Fail loudly if it is missing."""
    if not config.DEEPSEEK_API_KEY:
        raise ModelError(
            "No DeepSeek API key configured.",
            remedy="Set DEEPSEEK_API_KEY in .env, then restart.",
            status=503,
        )
    if not config.DEEPSEEK_MODEL:
        raise ModelError(
            "No DeepSeek model pinned.",
            remedy=(
                "Set DEEPSEEK_MODEL in .env to the pinned model name, "
                "checked against the official DeepSeek platform page."
            ),
            status=500,
        )
    return config.DEEPSEEK_API_KEY


def complete(
    message: str,
    system: Optional[str] = None,
    *,
    model: str,
    max_tokens: int,
    tools: Optional[list] = None,
    schema: Optional[dict] = None,
    thinking: str = "disabled",
) -> dict:
    """Send one prompt to DeepSeek and return a plain dict.

    Thin wrapper over chat_client.complete, which every roster provider
    shares. DeepSeek keeps its own fail-loud checks first: no key is a
    503, no pinned DEEPSEEK_MODEL is a 500, before any network call.
    """
    if not message.strip():
        raise ModelError("Message is empty.", status=400)
    _check_key()
    return chat_client.complete(
        "deepseek",
        message,
        system,
        model=model,
        max_tokens=max_tokens,
        tools=tools,
        schema=schema,
        thinking=thinking,
    )
