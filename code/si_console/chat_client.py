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
import re
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
        "label": "Hunyuan (TokenHub)",
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


_KEY_LIKE = re.compile(r"\b(?:sk|ak|pk|key)[-_][A-Za-z0-9*._\-]{6,}", re.I)
_MASKED = re.compile(r"[A-Za-z0-9_\-]*\*{3,}[A-Za-z0-9_\-*]*")


def redact(text: str, *secrets: str) -> str:
    """Remove every secret from a string before it is shown or logged.

    Besides each full key, this removes partly masked echoes such as
    "sk-zSJXp*****TbLdgcA" (providers often print the key's first and
    last characters in a 401 message): any word that starts with a known
    key's first 6 characters or ends with its last 6, plus key-shaped
    tokens like sk-.... A fragment in the middle of a word (for example
    inside a URL) is left alone."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
            if len(secret) >= 12:
                head, tail = re.escape(secret[:6]), re.escape(secret[-6:])
                text = re.sub(r"(?<!\S)" + head + r"\S*", "[REDACTED]", text)
                text = re.sub(r"(?<!\S)\S*" + tail + r"(?=[.,;:)\]]*(?:\s|$))", "[REDACTED]", text)
    text = _MASKED.sub("[REDACTED]", text)
    return _KEY_LIKE.sub("[REDACTED]", text)


def error_detail(response, *secrets: str, limit: int = 240) -> str:
    """The provider's own error message, short and with keys removed.
    Returns "" when the body has nothing useful."""
    try:
        payload = response.json()
    except ValueError:
        payload = None
    message = ""
    if isinstance(payload, dict):
        err = payload.get("error", payload)
        if isinstance(err, dict):
            message = str(err.get("message") or err.get("msg") or err.get("detail")
                          or err.get("code") or "")
        elif err:
            message = str(err)
        if not message:
            message = str(payload.get("message") or payload.get("msg") or "")
    if not message:
        message = (getattr(response, "text", "") or "").strip()
    message = " ".join(redact(message, *secrets).split())[:limit]
    return f" Provider says: {message}" if message else ""


_CREDIT_WORDS = ("insufficient balance", "insufficient account balance", "insufficient_quota",
                 "余额不足", "无可用资源包", "欠费", "请充值")


def _out_of_credit(detail: str) -> bool:
    """True when a provider's error text says the account has no money."""
    text = (detail or "").lower()
    return any(word in text for word in _CREDIT_WORDS)


def base_url(provider: str) -> str:
    return str(getattr(config, provider_spec(provider)["url_attr"])).rstrip("/")


def auth_headers(provider: str) -> dict:
    """Request headers for one provider. Holds the key: never log it."""
    spec = provider_spec(provider)
    key = provider_key(provider)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if spec.get("key_header"):
        headers[spec["key_header"]] = key
    return headers


def list_models(provider: str, timeout: float = 10) -> dict:
    """GET {base}/models. Free on every OpenAI-compatible API that has
    it, so it checks the key and the pinned model id without spending.
    Returns {"status": int, "models": [ids] or None, "detail": str}.
    Never raises for HTTP errors; raises ModelError for transport."""
    url = base_url(provider) + "/models"
    if provider == "dashscope":
        # Bailian's OpenAI-compatible /models answers 400; its native
        # list (/api/v1/models) works and is free. Being listed does not
        # prove the workspace site serves the model (some listed models
        # answer "not supported in current workspace service site"), so
        # --live is still the final check.
        url = base_url(provider).replace("/compatible-mode/v1", "/api/v1") + "/models?page_size=200"
    try:
        response = httpx.get(url, headers=auth_headers(provider), timeout=timeout)
    except httpx.HTTPError as exc:
        raise ModelError(
            f"{provider_spec(provider)['label']} not reachable: {type(exc).__name__}.",
            status=503,
        ) from None
    models = None
    if response.status_code == 200:
        try:
            payload = response.json()
            data = payload.get("data")
            if data is None and isinstance(payload.get("output"), dict):
                data = payload["output"].get("models")  # Bailian native shape
            if isinstance(data, list):
                models = [str(m.get("id") or m.get("model")) for m in data
                          if isinstance(m, dict) and (m.get("id") or m.get("model"))]
        except (ValueError, AttributeError):
            models = None
    detail = "" if response.status_code == 200 else error_detail(response, provider_key(provider))
    return {"status": response.status_code, "models": models, "detail": detail}


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
    timeout: Optional[float] = None,
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

    headers = auth_headers(provider)
    url = base_url(provider) + "/chat/completions"
    timeout = timeout or getattr(config, spec["timeout_attr"], 30)
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
            f"{label} rejected the API key.{error_detail(response, key)}",
            remedy=f"Check {spec['key_attr']} in .env is current.",
            status=401,
        )
    detail = error_detail(response, key)
    if response.status_code == 402 or _out_of_credit(detail):
        # DeepSeek and MiMo answer 402; Zhipu answers 429 with
        # "余额不足" (insufficient balance). Either way it is billing,
        # not a rate limit, and waiting will not fix it.
        raise ModelError(
            f"{label} account is out of credit ({response.status_code}).{detail}",
            remedy=f"Top up the {label} account, then run the smoke check again.",
            status=402,
        )
    if response.status_code == 429:
        retry = response.headers.get("retry-after", "60")
        raise ModelError(
            f"Rate limited by {label}. Retry after {retry}s.{detail}",
            remedy="Wait and try again, or slow the request rate.",
            status=429,
        )
    if response.status_code >= 400:
        # 400 usually means a field this provider does not accept (a
        # thinking shape, a model id). The provider's own message says
        # which, so keep it, with the key redacted.
        raise ModelError(
            f"{label} API error {response.status_code}.{error_detail(response, key)}",
            remedy="Read the provider message. Check the model id and the thinking fields.",
            status=400 if response.status_code == 400 else 502,
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
