# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
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

import json
from typing import Optional

import httpx

from si_console import config
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

    With `tools`, the reply may contain tool_calls, which the coordinator
    validates before running. With `schema`, the answer is constrained
    to JSON and returned parsed under "data" as well as raw under "text".
    Do not pass both tools and schema in one call. The coordinator uses
    tools for actions and schema for structured answers, never both.
    Thinking mode: "disabled" means no thinking, "low", "high", or
    "max" means thinking on at that effort. The coordinator must pass
    "disabled". Tool calling needs a non-thinking reply. The worker
    may pass "low" for research. Thinking is on by default when the
    field is omitted, so this function always sends the field. The
    wire shape is {"type": "disabled"} or {"type": "enabled",
    "effort": "low"}. That shape is LIKELY from the DeepSeek thinking
    docs, not yet confirmed by a live call. Test one live call with
    thinking disabled before the booth build. If DeepSeek rejects
    the field, fix the shape here, not in the callers.
    Returns a plain dict so models.py can normalise it, the same way
    Autumn normalised Groq and Anthropic replies into one shape.
    """
    if not message.strip():
        raise ModelError("Message is empty.", status=400)
    if tools is not None and schema is not None:
        raise ModelError(
            "Pass tools or schema, not both.",
            remedy="Use tools for actions, schema for structured answers.",
            status=500,
        )
    if thinking not in ("disabled", "low", "high", "max"):
        raise ModelError(
            f"Bad thinking value {thinking!r}.",
            remedy='Use "disabled", "low", "high", or "max".',
            status=500,
        )

    key = _check_key()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    body: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if thinking == "disabled":
        body["thinking"] = {"type": "disabled"}
    else:
        body["thinking"] = {"type": "enabled", "effort": thinking}
    if tools is not None:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if schema is not None:
        # DeepSeek OpenAI compatible JSON mode. The schema itself is
        # enforced by our own validator after the call, not only by the
        # model. A model can still return JSON that fails our checks.
        body["response_format"] = {"type": "json_object"}

    url = config.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
    try:
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=config.DEEPSEEK_TIMEOUT_SECONDS,
        )
    except httpx.ConnectError:
        raise ModelError(
            "Could not reach the DeepSeek API.",
            remedy="Check the network connection. In booth mode, the "
            "recorded fallback should take over.",
            status=503,
        ) from None
    except httpx.TimeoutException:
        raise ModelError(
            "DeepSeek API timed out.",
            remedy="Retry once, then mark the task blocked with API_TIMEOUT.",
            status=504,
        ) from None

    if response.status_code == 401:
        raise ModelError(
            "DeepSeek rejected the API key.",
            remedy="Check DEEPSEEK_API_KEY in .env is current.",
            status=401,
        )
    if response.status_code == 429:
        retry = response.headers.get("retry-after", "60")
        raise ModelError(
            f"Rate limited by DeepSeek. Retry after {retry}s.",
            remedy="Wait and try again, or slow the request rate.",
            status=429,
        )
    if response.status_code >= 400:
        raise ModelError(
            f"DeepSeek API error {response.status_code}.",
            remedy="Log the status code, not the key. Retry once.",
            status=502,
        )

    try:
        payload = response.json()
    except ValueError:
        raise ModelError(
            "DeepSeek returned a reply that was not JSON.",
            remedy="Retry once, then mark the task blocked.",
            status=502,
        ) from None

    try:
        choice = payload["choices"][0]
        reply_message = choice["message"]
    except (KeyError, IndexError, TypeError):
        raise ModelError(
            "DeepSeek returned a reply with no choices.",
            remedy="Retry once, then mark the task blocked.",
            status=502,
        ) from None

    text = (reply_message.get("content") or "").strip()
    tool_calls = reply_message.get("tool_calls") or []
    finish = choice.get("finish_reason", "")

    if not text and not tool_calls:
        raise ModelError(
            f"DeepSeek returned no text (finish_reason: {finish}).",
            remedy="Try again, or raise SI_DEEPSEEK_MAX_TOKENS.",
            status=502,
        )

    data = None
    if schema is not None:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelError(
                f"DeepSeek returned malformed JSON: {exc}",
                remedy="Try again. The schema is enforced, so this is rare.",
                status=502,
            ) from None

    usage = payload.get("usage") or {}
    return {
        "text": text,
        "data": data,
        "tool_calls": tool_calls,
        "model": payload.get("model", model),
        "finish_reason": finish,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }
