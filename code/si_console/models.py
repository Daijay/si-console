# Model tier router for the accepted roster in docs/MODEL_TIERS.md
# (2026-11-25). Callers ask for a tier, never a model. Each tier is an
# ordered chain of model slots; the router walks it, skips any slot
# with no key or no pinned model id, and falls back to the next slot
# on any ModelError. Every attempt is logged to SQLite telemetry.
#   T0 orchestrator : DeepSeek V4.1 Flash -> Hy4 -> GLM 5.4   (else error)
#   T1 heavy        : Qwen4 Max -> escalate_to_human          (EscalationNeeded)
#   T2 medium       : Hy4 -> DeepSeek V4.1 Flash -> GLM 5.4   (else error)
#   T3 small        : MiMo 2.6 Flash -> $0 code paths         (ZeroPathNeeded)
#   narration       : no model call, prewritten sentence id
# Arena panes (A, B, C) apply the operator's selection rules:
#   T0: pin to one T0 slot or "auto"; a pinned pane falls back down the
#       T0 chain from its pinned position only if FALLBACK is yes.
#   T2: per-pane allowlist. An empty allowlist ("none") sends T2 work
#       to T1, or to the $0 paths if T1 is off for that pane.
#   T1: "off" for a pane means escalate_to_human straight away.
# Claude is not in the roster and there is no Anthropic client.
# Old tier names (coordinator, worker, premium, light) are aliases.
"""Model tier router: roster chains, pane pinning, fallback, telemetry."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from si_console import chat_client, config, telemetry
from si_console.deepseek_client import complete as deepseek_complete
from si_console.errors import EscalationNeeded, ModelError, ZeroPathNeeded

logger = logging.getLogger(__name__)


def reset_fallback_log() -> None:
    """Kept for older tests. The router no longer keeps per-run state."""


def normalize_tier(tier: str) -> str:
    name = config.TIER_ALIASES.get(tier, tier)
    if name not in config.MODEL_TIERS:
        known = ", ".join(sorted(set(config.MODEL_TIERS) | set(config.TIER_ALIASES)))
        raise ModelError(f"Unknown model tier {tier!r}.", remedy=f"Use one of: {known}.", status=500)
    return name


def tier_config(tier: str) -> dict:
    """Look up one tier in the config table. Unknown tier is an error."""
    return config.MODEL_TIERS[normalize_tier(tier)]


def slot_info(slot: str) -> dict:
    """Provider and pinned model id for one slot. Unknown slot is loud."""
    try:
        spec = config.MODEL_SLOTS[slot]
    except KeyError:
        raise ModelError(
            f"Unknown model slot {slot!r}.",
            remedy=f"Use one of: {', '.join(sorted(config.MODEL_SLOTS))}.",
            status=500,
        ) from None
    return {
        "slot": slot,
        "provider": spec["provider"],
        "model": getattr(config, spec["model_attr"], "") or "",
        "model_attr": spec["model_attr"],
    }


def slot_configured(slot: str) -> bool:
    info = slot_info(slot)
    return bool(info["model"] and chat_client.provider_key(info["provider"]))


def _pane_config(pane: str) -> dict:
    key = (pane or "").upper()
    if key not in config.PANE_CONFIG:
        raise ModelError(
            f"Unknown arena pane {pane!r}.", remedy="Use A, B or C.", status=500
        )
    return config.PANE_CONFIG[key]


def plan(tier: str, pane: Optional[str] = None) -> tuple[str, list[str]]:
    """The tier actually used and its ordered slot list for one pane.

    Applies the MODEL_TIERS.md selection rules. Returns (tier, slots).
    An empty slot list means the tier is denied or empty for this pane;
    complete() then follows the tier's on_exhausted rule.
    """
    name = normalize_tier(tier)
    chain = list(config.MODEL_TIERS[name]["chain"])
    if not pane:
        return name, chain
    pane_cfg = _pane_config(pane)
    if name == config.T0:
        pin = pane_cfg["pin"]
        if pin == "auto":
            return name, chain
        if pin not in chain:
            raise ModelError(
                f"Pane {pane} is pinned to {pin!r}, which is not a T0 model.",
                remedy=f"Pin to auto or one of: {', '.join(chain)}.",
                status=500,
            )
        start = chain.index(pin)
        return name, chain[start:] if pane_cfg["fallback"] == "yes" else [pin]
    if name == config.T1:
        return name, [] if pane_cfg["t1"] == "off" else chain
    if name == config.T2:
        allow = pane_cfg["t2"]
        if allow == "all":
            return name, chain
        wanted = [] if allow == "none" else [s.strip() for s in allow.split(",") if s.strip()]
        unknown = [s for s in wanted if s not in chain]
        if unknown:
            raise ModelError(
                f"Pane {pane} T2 allowlist has non-T2 models: {', '.join(unknown)}.",
                remedy=f"Use all, none, or a comma list of: {', '.join(chain)}.",
                status=500,
            )
        allowed = [s for s in chain if s in wanted]
        if allowed:
            return name, allowed
        # Rule 3: no medium workers. T2 work goes to T1, or to the $0
        # paths when this pane is also denied T1.
        if pane_cfg["t1"] != "off":
            return config.T1, list(config.MODEL_TIERS[config.T1]["chain"])
        return config.T3, []
    return name, chain


def resolve_tier(tier: str, pane: Optional[str] = None) -> dict:
    """The first configured slot for a tier and pane, without calling it.

    Loud error when no slot in the chain has both a key and a pinned
    model id. The narration tier needs no model and always resolves.
    """
    name, slots = plan(tier, pane)
    spec = config.MODEL_TIERS[name]
    if name == config.NARRATION:
        return {"tier": name, "slot": "", "provider": "prewritten", "model": "strings.json",
                "max_tokens": 0, "thinking": "disabled"}
    for slot in slots:
        if slot_configured(slot):
            info = slot_info(slot)
            return {"tier": name, "slot": slot, "provider": info["provider"],
                    "model": info["model"], "max_tokens": spec["max_tokens"],
                    "thinking": spec["thinking"]}
    raise ModelError(
        f"No model configured for tier {name!r}"
        + (f" on pane {pane}" if pane else "")
        + f" (chain: {', '.join(slots) or 'empty'}).",
        remedy="Set the provider key and pin the model id in .env for at least one slot.",
        status=500,
    )


@dataclass
class ModelReply:
    """One answer, in the same shape no matter which slot made it."""

    text: str
    tier: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    # Parsed JSON when the caller passed a schema.
    data: Optional[dict] = None
    # Raw tool calls when the caller passed tools. The coordinator
    # validates every one before anything runs.
    tool_calls: Optional[list] = None
    slot: str = ""
    pane: str = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "tier": self.tier,
            "slot": self.slot,
            "pane": self.pane,
            "provider": self.provider,
            "model": self.model,
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
            },
        }


def _call_slot(info: dict, message, system, *, max_tokens, tools, schema, thinking) -> dict:
    if info["provider"] == "deepseek":
        # DeepSeek keeps its own wrapper with the fail-loud key checks.
        return deepseek_complete(
            message, system, model=info["model"], max_tokens=max_tokens,
            tools=tools, schema=schema, thinking=thinking,
        )
    return chat_client.complete(
        info["provider"], message, system, model=info["model"], max_tokens=max_tokens,
        tools=tools, schema=schema, thinking=thinking,
    )


def complete(
    tier: str,
    message: str,
    system: Optional[str] = None,
    *,
    max_tokens: Optional[int] = None,
    schema: Optional[dict] = None,
    tools: Optional[list] = None,
    thinking: Optional[str] = None,
    pane: Optional[str] = None,
    route_reason: str = "",
) -> ModelReply:
    """Send one prompt to the tier's chain for one pane, with fallback.

    The narration tier takes no model call: it returns the message as
    the sentence id. Free LLM text is never spoken. When the chain is
    exhausted: T1 raises EscalationNeeded, T3 raises ZeroPathNeeded,
    T0 and T2 raise ModelError naming every slot that failed.
    """
    name, slots = plan(tier, pane)
    spec = config.MODEL_TIERS[name]
    if name == config.NARRATION:
        return ModelReply(text=message, tier=name, provider="prewritten",
                          model="strings.json", input_tokens=0, output_tokens=0, pane=pane or "")

    budget = max_tokens or spec["max_tokens"]
    think = thinking if thinking is not None else spec["thinking"]
    failures: list[str] = []
    tried_any = False
    for slot in slots:
        info = slot_info(slot)
        if not (info["model"] and chat_client.provider_key(info["provider"])):
            failures.append(f"{slot}: not configured")
            continue
        tried_any = True
        started = time.monotonic()
        try:
            raw = _call_slot(info, message, system, max_tokens=budget,
                             tools=tools, schema=schema, thinking=think)
        except ModelError as exc:
            failures.append(f"{slot}: {exc.message}")
            telemetry.record(kind="chat", pane=pane or "", tier=name, slot=slot,
                             provider=info["provider"], model=info["model"],
                             route_reason=route_reason,
                             latency_ms=int((time.monotonic() - started) * 1000),
                             ok=False, error_code=f"HTTP_{exc.status}")
            logger.warning("tier %s slot %s failed (%s), falling back", name, slot, exc.status)
            continue
        telemetry.record(kind="chat", pane=pane or "", tier=name, slot=slot,
                         provider=info["provider"], model=raw.get("model", info["model"]),
                         route_reason=route_reason,
                         input_tokens=raw.get("input_tokens", 0),
                         output_tokens=raw.get("output_tokens", 0),
                         latency_ms=int((time.monotonic() - started) * 1000), ok=True)
        return ModelReply(
            text=raw["text"], tier=name, provider=info["provider"],
            model=raw.get("model", info["model"]),
            input_tokens=raw.get("input_tokens", 0), output_tokens=raw.get("output_tokens", 0),
            data=raw.get("data"), tool_calls=raw.get("tool_calls") or None,
            slot=slot, pane=pane or "",
        )

    detail = "; ".join(failures) or "no models in chain for this pane"
    rule = spec["on_exhausted"]
    if rule == "escalate_to_human":
        raise EscalationNeeded(f"Tier {name} exhausted: {detail}.")
    if rule == "zero_path":
        raise ZeroPathNeeded(f"Tier {name} exhausted: {detail}.")
    if not tried_any:
        raise ModelError(
            f"No model configured for tier {name!r}: {detail}.",
            remedy="Set the provider key and pin the model id in .env for at least one slot.",
            status=500,
        )
    raise ModelError(f"Every model in tier {name!r} failed: {detail}.",
                     remedy="Check provider status and keys. Retry once.", status=503)


def key_configured(tier: str, pane: Optional[str] = None) -> bool:
    """Whether at least one slot behind a tier is usable. Never returns a key."""
    name, slots = plan(tier, pane)
    if name == config.NARRATION:
        return True
    return any(slot_configured(slot) for slot in slots)


def roster_status() -> dict:
    """Which slots are usable, for a startup check and the dashboard.
    Names only, never keys."""
    return {
        slot: {
            "provider": slot_info(slot)["provider"],
            "model_pinned": bool(slot_info(slot)["model"]),
            "key_set": bool(chat_client.provider_key(slot_info(slot)["provider"])),
        }
        for slot in config.MODEL_SLOTS
    } | {"jev": {"provider": "openrouter", "model_pinned": bool(config.JEV_MODEL),
                 "key_set": bool(config.OPENROUTER_API_KEY)}}
