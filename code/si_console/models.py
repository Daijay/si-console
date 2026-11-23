# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# This file is Autumn's autumn/models.py, rewired for DeepSeek.
# What changed: Groq and Anthropic are gone. DeepSeek is the only cloud
# provider. The narration tier is new, and it calls no model at all.
# It returns a prewritten sentence id from strings.json, so booth
# narration never loads a local LLM by accident. The premium tier is
# new too. It maps to the DeepSeek pro model, never to Claude, in the
# booth build. The router stub below is Christopher's tier idea on
# paper: tiers exist, a CLAUDE_ENABLED flag exists, but the router
# always fails closed to DeepSeek only. There is no Anthropic client
# in this codebase. Do not add one for the booth build. Claude Fable
# 5.2 is real but too expensive, and Anthropic policy does not support
# use by persons physically in mainland China. The booth is in
# Shenzhen. See config.py for the full note.
# What stayed: callers ask for a tier, never a model. The tier table
# lives in config. One ModelReply shape for every provider. Errors are
# provider agnostic, so a caller can show a failure without knowing
# which provider it came from. The anthropic tier in Autumn raised
# rather than silently returning prose where a schema was expected.
# This file keeps that rule for DeepSeek: a schema call that returns
# prose is an error, not an answer.
"""Model tiering and router stub. Callers ask for a tier, never a model."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from si_console import config
from si_console.deepseek_client import complete as deepseek_complete
from si_console.errors import ModelError

logger = logging.getLogger(__name__)

# Thinking per tier. The coordinator must run with thinking disabled,
# because tool calling needs a non-thinking reply. The worker may use
# thinking at low effort for research. Premium runs with thinking
# disabled, because it may do tool calls too. Narration makes no call.
_TIER_THINKING = {
    config.COORDINATOR: "disabled",
    config.WORKER: "low",
    config.PREMIUM: "disabled",
    config.LIGHT: "low",
}

# Tiers that already fell back to DeepSeek in this run. The fallback
# is logged once per tier per run, not once per call, so a busy loop
# does not flood the log. Tests reset this with reset_fallback_log().
_fallback_logged: set[str] = set()


def reset_fallback_log() -> None:
    """Clear the once-per-run fallback log. Tests only."""
    _fallback_logged.clear()


def tier_config(tier: str) -> dict:
    """Look up one tier in the config table. Unknown tier is an error."""
    try:
        return config.MODEL_TIERS[tier]
    except KeyError:
        known = ", ".join(sorted(config.MODEL_TIERS))
        raise ModelError(
            f"Unknown model tier {tier!r}.",
            remedy=f"Use one of: {known}.",
            status=500,
        ) from None


def resolve_tier(tier: str) -> dict:
    """Resolve a tier to a provider, model, budget, and thinking mode.

    This is the router stub. It supports Christopher's tier idea on
    paper and always fails closed to DeepSeek only in practice.
    Rules, in order:
    1. Unknown tier is a loud error, never a guess.
    2. The narration tier makes no model call. It passes through.
    3. A tier that names Claude falls back to DeepSeek flash when
       CLAUDE_ENABLED is false, or when no Anthropic key is set.
       The fallback is logged once per tier per run. It never raises
       an error that kills the coordinator loop. There is no
       Anthropic client in this codebase, so a Claude call is never
       made, even when the flag is true. The flag exists so the team
       can see the policy in one place.
    4. A DeepSeek tier with no model pinned is a loud error, not a
       silent downgrade. That includes the premium tier when
       DEEPSEEK_MODEL_PRO is empty.
    5. The coordinator tier always runs with thinking disabled.
    """
    spec = tier_config(tier)
    provider = spec["provider"]

    if provider == "prewritten":
        return {
            "provider": provider,
            "model": spec["model"],
            "max_tokens": spec["max_tokens"],
            "thinking": "disabled",
        }

    if provider == "claude":
        # Fail closed to DeepSeek flash. Log once per tier per run.
        if tier not in _fallback_logged:
            _fallback_logged.add(tier)
            logger.warning(
                "Tier %r asks for Claude, but the router falls back "
                "to DeepSeek flash. CLAUDE_ENABLED is %s. Claude is "
                "not called from this build.",
                tier,
                config.CLAUDE_ENABLED,
            )
        return {
            "provider": "deepseek",
            "model": config.DEEPSEEK_MODEL,
            "max_tokens": spec["max_tokens"],
            "thinking": "disabled",
        }

    if provider == "deepseek":
        model = spec["model"]
        if not model:
            raise ModelError(
                f"No DeepSeek model pinned for tier {tier!r}.",
                remedy=(
                    "Set DEEPSEEK_MODEL in .env. For the premium tier, "
                    "set DEEPSEEK_MODEL_PRO. Then restart."
                ),
                status=500,
            )
        return {
            "provider": provider,
            "model": model,
            "max_tokens": spec["max_tokens"],
            "thinking": _TIER_THINKING.get(tier, "disabled"),
        }

    raise ModelError(
        f"Tier {tier!r} names an unknown provider {provider!r}.",
        remedy="Teach si_console.models how to reach it, or fix the tier table.",
        status=500,
    )


@dataclass
class ModelReply:
    """One answer, in the same shape no matter which tier made it."""

    text: str
    tier: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    # Set only when the call passed a schema: the parsed JSON answer.
    data: Optional[dict] = None
    # Set only when the call passed tools: the raw tool calls from DeepSeek.
    # The coordinator validates each one before running it.
    tool_calls: Optional[list] = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "tier": self.tier,
            "provider": self.provider,
            "model": self.model,
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
            },
        }


def tier_config(tier: str) -> dict:
    """Look up one tier in the config table. Unknown tier is an error."""
    try:
        return config.MODEL_TIERS[tier]
    except KeyError:
        known = ", ".join(sorted(config.MODEL_TIERS))
        raise ModelError(
            f"Unknown model tier {tier!r}.",
            remedy=f"Use one of: {known}.",
            status=500,
        ) from None


def complete(
    tier: str,
    message: str,
    system: Optional[str] = None,
    *,
    max_tokens: Optional[int] = None,
    schema: Optional[dict] = None,
    tools: Optional[list] = None,
    thinking: Optional[str] = None,
) -> ModelReply:
    """Send one prompt to whichever provider backs `tier`.

    With `schema`, the answer is constrained JSON and the parsed result
    comes back on ModelReply.data. With `tools`, the answer may carry
    tool_calls, which come back on ModelReply.tool_calls for validation.
    The narration tier takes no model call. It returns the message as
    the sentence id, so the caller must pass a sentence id, not free
    text. Free LLM text is never spoken. See voice_intents.py.
    Thinking defaults to the tier rule: disabled for the coordinator
    and premium tiers, low for the worker tier. Pass `thinking` to
    override it. The router in resolve_tier() decides the provider
    and the model. A Claude tier falls back to DeepSeek flash.
    """
    resolved = resolve_tier(tier)
    provider = resolved["provider"]
    budget = max_tokens or resolved["max_tokens"]

    if provider == "prewritten":
        # No model call. The caller picks a sentence id from strings.json.
        # The bridge and Piper speak that sentence, not this text.
        return ModelReply(
            text=message,
            tier=tier,
            provider=provider,
            model=resolved["model"],
            input_tokens=0,
            output_tokens=0,
        )

    if provider == "deepseek":
        raw = deepseek_complete(
            message,
            system,
            model=resolved["model"],
            max_tokens=budget,
            tools=tools,
            schema=schema,
            thinking=thinking if thinking is not None else resolved["thinking"],
        )
        return ModelReply(
            text=raw["text"],
            tier=tier,
            provider=provider,
            model=raw["model"],
            input_tokens=raw["input_tokens"],
            output_tokens=raw["output_tokens"],
            data=raw.get("data"),
            tool_calls=raw.get("tool_calls") or None,
        )

    raise ModelError(
        f"Tier {tier!r} names an unknown provider {provider!r}.",
        remedy="Teach si_console.models how to reach it, or fix the tier table.",
        status=500,
    )


def key_configured(tier: str) -> bool:
    """Whether the provider behind a tier has a key. Never returns the key."""
    provider = tier_config(tier)["provider"]
    if provider == "prewritten":
        return True
    if provider == "deepseek":
        return bool(config.DEEPSEEK_API_KEY)
    if provider == "claude":
        # Claude is never called from this build. The router falls
        # back to DeepSeek. Report it as not configured, so callers
        # never treat a Claude tier as ready.
        return False
    return False
