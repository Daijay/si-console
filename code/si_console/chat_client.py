# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# One client for every chat provider in the accepted roster
# (docs/MODEL_TIERS.md): DeepSeek, Tencent Hunyuan (Hy4), Zhipu GLM,
# Alibaba Bailian/DashScope (Qwen4 Max) and Xiaomi MiMo. All five speak
# the OpenAI-compatible /chat/completions shape, so one function does
# the HTTP, the error mapping and the reply parsing. Only two things
# differ per provider: where the key and base URL live in config, and
# how "thinking" is switched on or off. Those are in PROVIDERS below.
# The router in models.py picks the provider. Callers never do.
# Thinking wire shapes, read from provider docs 2026-11-24 (LIKELY, not
# yet confirmed by a live call):
#   deepseek  : {"thinking": {"type": "disabled"}} or
#               {"thinking": {"type": "enabled", "effort": "low"}}
#   glm       : {"thinking": {"type": "enabled"|"disabled"}} plus
#               "reasoning_effort". Effort is capped at "high", never
#               "max" (MODEL_TIERS.md: max burns ~1M reasoning tokens).
#   dashscope : "enable_thinking": true|false (top-level in raw HTTP).
#   hunyuan, mimo : no thinking field is sent; provider default applies.
# If a provider rejects a field, fix the shape here, not in callers.
"""OpenAI-compatible chat client shared by every roster provider."""

from __future__ import annotations

import json
from typing import Optional

import httpx

from si_console import config
from si_console.errors import ModelError

THINKING_VALUES = ("disabled", "low", "high", "max")

PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek",
        "key_attr": "DEEPSEEK_API_KEY",
        "url_attr": "DEEPSEEK_BASE_URL",
        "timeout_attr": "DEEPSEEK_TIMEOUT_SECONDS",
        "thinking": "deepseek",
    },
    "hunyuan": {
        "label": "Hunyuan",
        "key_attr": "HUNYUAN_API_KEY",
        "url_attr": "HUNYUAN_BASE_URL",
        "timeout_attr": "PROVIDER_TIMEOUT_SECONDS",
        "thinking": "none",
    },
    "glm": {
        "label": "GLM",
        "key_attr": "GLM_API_KEY",
        "url_attr": "GLM_BASE_URL",
        "timeout_attr": "PROVIDER_TIMEOUT_SECONDS",
        "thinking": "glm",
    },
    "dashscope": {
        "label": "Qwen (Bailian)",
        "key_attr": "DASHSCOPE_API_KEY",
        "url_attr": "DASHSCOPE_BASE_URL",
        "timeout_attr": "PROVIDER_TIMEOUT_SECONDS",
        "thinking": "dashscope",
    },
    "mimo": {
        "label": "MiMo",
        "key_attr": "MIMO_API_KEY",
        "url_attr": "MIMO_BASE_URL",
        "timeout_attr": "PROVIDER_TIMEOUT_SECONDS",
        "thinking": "none",
        # MiMo's curl examples use an api-key header; its OpenAI SDK
        # examples use Bearer. Send both so either form is accepted.
        "key_header": "api-key",
    },
}


def provider_spec(provider: str) -> dict:
    try:
        return PROVIDERS[provider]
    except KeyError:
        raise ModelError(
            f"Unknown provider {provider!r}.",
            remedy=f"Use one of: {', '.join(sorted(PROVIDERS))}.",
            status=500,
        ) from None


def provider_key(provider: str) -> str:
    """The key for one provider, from config. Never logged or returned."""
    return getattr(config, provider_spec(provider)["key_attr"], "") or ""


def _thinking_fields(style: str, thinking: str) -> dict:
    if style == "deepseek":
        if thinking == "disabled":
            return {"thinking": {"type": "disabled"}}
        return {"thinking": {"type": "enabled", "effort": thinking}}
    if style == "glm":
        if thinking == "disabled":
            return {"thinking": {"type": "disabled"}}
        effort = "high" if thinking == "max" else thinking
        return {"thinking": {"type": "enabled"}, "reasoning_effort": effort}
    if style == "dashscope":
        return {"enable_thinking": thinking != "disabled"}
    return {}


def complete(
    provider: str,
    message: str,
    system: Optional[str] = None,
    *,
    model: str,
    max_tokens: int,
    tools: Optional[list] = None,
    schema: Optional[dict] = None,
    thinking: str = "disabled",
) -> dict:
    """Send one prompt to one provider and return a plain dict.

    Same contract as the original DeepSeek client: with `tools`, the
    reply may carry tool_calls for the coordinator to validate; with
    `schema`, the answer is JSON and comes back parsed under "data".
    Tools and schema are never sent together. Every failure is a
    ModelError, so the router can fall back to the next slot.
    """
    spec = provider_spec(provider)
    label = spec["label"]
    if not message.strip():
        raise ModelError("Message is empty.", status=400)
    if tools is not None and schema is not None:
        raise ModelError(
            "Pass tools or schema, not both.",
            remedy="Use tools for actions, schema for structured answers.",
            status=500,
        )
    if thinking not in THINKING_VALUES:
        raise ModelError(
            f"Bad thinking value {thinking!r}.",
            remedy='Use "disabled", "low", "high", or "max".',
            status=500,
        )
    key = provider_key(provider)
    if not key:
        raise ModelError(
            f"No {label} API key configured.",
            remedy=f"Set {spec['key_attr']} in .env, then restart.",
            status=503,
        )
    if not model:
        raise ModelError(
            f"No {label} model pinned.",
            remedy="Pin the model id in .env after checking the provider's model list.",
            status=500,
        )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})
    body: dict = {"model": model, "messages": messages, "max_tokens": max_tokens}
    body.update(_thinking_fields(spec["thinking"], thinking))
    if tools is not None:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if schema is not None:
        # The OpenAI-compatible json_object mode. The schema itself is
        # described in the prompt; validation happens in the caller.
        body["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if spec.get("key_header"):
        headers[spec["key_header"]] = key
    url = str(getattr(config, spec["url_attr"])).rstrip("/") + "/chat/completions"
    timeout = getattr(config, spec["timeout_attr"], 30)
    try:
        response = httpx.post(url, headers=headers, json=body, timeout=timeout)
    except httpx.ConnectError:
        raise ModelError(
            f"Could not reach the {label} API.",
            remedy="Check the network. The router falls back to the next model.",
            status=503,
        ) from None
    except httpx.TimeoutException:
        raise ModelError(
            f"{label} API timed out.",
            remedy="The router falls back to the next model in the tier.",
            status=504,
        ) from None
    except httpx.HTTPError as exc:
        # Protocol, read, write or proxy errors. Without this they leave
        # as raw httpx errors, miss the ModelError handlers, and crash
        # the loop instead of falling back or blocking one task.
        raise ModelError(
            f"{label} request failed: {type(exc).__name__}.",
            remedy="The router falls back to the next model in the tier.",
            status=502,
        ) from None

    if response.status_code == 401:
        raise ModelError(
            f"{label} rejected the API key.",
            remedy=f"Check {spec['key_attr']} in .env is current.",
            status=401,
        )
    if response.status_code == 429:
        retry = response.headers.get("retry-after", "60")
        raise ModelError(
            f"Rate limited by {label}. Retry after {retry}s.",
            remedy="Wait and try again, or slow the request rate.",
            status=429,
        )
    if response.status_code >= 400:
        raise ModelError(
            f"{label} API error {response.status_code}.",
            remedy="Log the status code, not the key. Retry once.",
            status=502,
        )
    try:
        payload = response.json()
    except ValueError:
        raise ModelError(
            f"{label} returned a reply that was not JSON.",
            remedy="Retry once, then mark the task blocked.",
            status=502,
        ) from None
    try:
        choice = payload["choices"][0]
        reply_message = choice["message"]
    except (KeyError, IndexError, TypeError):
        raise ModelError(
            f"{label} returned a reply with no choices.",
            remedy="Retry once, then mark the task blocked.",
            status=502,
        ) from None

    text = (reply_message.get("content") or "").strip()
    tool_calls = reply_message.get("tool_calls") or []
    finish = choice.get("finish_reason", "")
    if not text and not tool_calls:
        raise ModelError(
            f"{label} returned no text (finish_reason: {finish}).",
            remedy="Try again, or raise the tier's max_tokens.",
            status=502,
        )
    data = None
    if schema is not None:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelError(
                f"{label} returned malformed JSON: {exc}",
                remedy="Try again. The schema is enforced, so this is rare.",
                status=502,
            ) from None
    usage = payload.get("usage") or {}
    return {
        "text": text,
        "data": data,
        "tool_calls": tool_calls,
        "provider": provider,
        "model": payload.get("model", model),
        "finish_reason": finish,
        "input_tokens": usage.get("prompt_tokens", 0) or 0,
        "output_tokens": usage.get("completion_tokens", 0) or 0,
    }
