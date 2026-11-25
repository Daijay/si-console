# Jev 1.14 judge (TypeSafe), per docs/MODEL_TIERS.md. Default route is
# TypeSafe's own API with a TypeSafe key; OpenRouter is the alternate
# (config.JEV_PROVIDER). Both take the same body and answer shape. A decision model,
# not a worker: it returns typed, calibrated decisions in ~100 ms and
# cannot write code. Used for ambiguous routing, winner pick and tab
# promotion. GUARD stays the final authority for physical actions; the
# judge never approves, executes or bypasses anything.
# Wire contract, read from docs.typesafe.ai (System One reference,
# primitives/choice, models) and OpenRouter's Decisions API reference
# on 2026-11-24 (LIKELY, no live call yet):
#   POST https://api.typesafe.ai/v1/systemone   (TypeSafe key, model
#        jev-1.14.0 or jev-latest)
#   or POST https://openrouter.ai/api/alpha/decisions  (OpenRouter key,
#        model typesafe/jev-1.14)
#   Authorization: Bearer <key>
#   {"model": "<id>", "state": <string|object|array>,
#    "questions": {"<id>": {"type": "choice", "instructions": "...",
#                           "criteria": {"<option>": "<description>"}}}}
#   -> {"answers": {"<id>": {"type": "choice", "choice": "<option>",
#                            "probabilities": {...}, "confidence": 0..1}},
#       "usage": {"input_tokens": n, "output_tokens": n, "cost": usd}}
#   OpenRouter may answer {"type": "refusal"}; TypeSafe documents no
#   refusal type. Errors: {"detail": ...} on TypeSafe.
# The question id is not shown to the model, so the meaning lives in
# the instructions and criteria. Output tokens are free.
# Every answer is checked against the options this code offered. A
# choice outside them is an error, so Jev can never pick a model or
# tier outside the operator's allowlist (MODEL_TIERS.md rule 4).
"""Jev judge client: typed choice decisions through OpenRouter."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx

from si_console import config, telemetry
from si_console.errors import ConsoleError


class JudgeError(ConsoleError):
    """The judge could not give a usable decision. Callers must fall
    back to a deterministic default, never to a guess."""

    def __init__(self, message: str, remedy: str = "", status: int = 502):
        super().__init__("JUDGE_ERROR", message, remedy, status)


@dataclass
class Decision:
    choice: str
    confidence: float
    probabilities: dict = field(default_factory=dict)


def configured() -> bool:
    return bool(config.JEV_API_KEY and config.JEV_MODEL)


def decide_choice(
    instructions: str,
    options: dict,
    state,
    *,
    pane: str = "",
    purpose: str = "decision",
    min_confidence: float = 0.0,
) -> Decision:
    """Ask Jev to pick one of `options` ({name: description}).

    Raises JudgeError when the judge is not configured, the call fails,
    the question is refused, the choice is not one of the options, or
    the confidence is below `min_confidence`.
    """
    if not options:
        raise JudgeError("No options to choose from.", status=500)
    if not configured():
        raise JudgeError(
            "Jev judge is not configured.",
            remedy="Set TYPESAFE_API_KEY and JEV_MODEL (e.g. jev-1.14.0) in .env.",
            status=503,
        )
    body = {
        "model": config.JEV_MODEL,
        "state": state,
        "questions": {
            "pick": {
                "type": "choice",
                "instructions": instructions,
                "criteria": {str(k): str(v) for k, v in options.items()},
            }
        },
    }
    started = time.monotonic()
    error = ""
    usage: dict = {}
    try:
        try:
            response = httpx.post(
                config.JEV_URL,
                headers={
                    "Authorization": f"Bearer {config.JEV_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=config.JEV_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            error = type(exc).__name__
            raise JudgeError(f"Jev request failed: {error}.") from None
        if response.status_code != 200:
            error = f"HTTP_{response.status_code}"
            from si_console.chat_client import error_detail

            raise JudgeError(
                f"Jev returned HTTP {response.status_code}."
                f"{error_detail(response, config.JEV_API_KEY)}"
            )
        try:
            payload = response.json()
            usage = payload.get("usage") or {}
            answer = payload["answers"]["pick"]
        except (ValueError, KeyError, TypeError, AttributeError):
            error = "BAD_REPLY"
            raise JudgeError("Jev reply has no answer for the question.") from None
        if answer.get("type") == "refusal":
            error = "REFUSAL"
            raise JudgeError("Jev declined the question.")
        choice = answer.get("choice")
        if choice not in options:
            error = "OUT_OF_OPTIONS"
            raise JudgeError(f"Jev picked {choice!r}, which was not offered.")
        try:
            confidence = float(answer.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < min_confidence:
            error = "LOW_CONFIDENCE"
            raise JudgeError(f"Jev confidence {confidence:.2f} is below {min_confidence:.2f}.")
        return Decision(choice, confidence, dict(answer.get("probabilities") or {}))
    finally:
        telemetry.record(
            kind="judge",
            pane=pane,
            slot="jev",
            provider=config.JEV_PROVIDER,
            model=config.JEV_MODEL,
            route_reason=purpose,
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            latency_ms=int((time.monotonic() - started) * 1000),
            ok=not error,
            error_code=error,
        )


def pick_winner(task: str, candidates: dict, *, pane: str = "") -> Decision:
    """Arena winner pick: `candidates` is {candidate_id: short summary}.
    The summaries are data, not instructions."""
    return decide_choice(
        "Pick the candidate whose result best completes `task`. Judge only on "
        "correctness and completeness of the described result.",
        candidates,
        {"task": task},
        pane=pane,
        purpose="winner_pick",
    )
