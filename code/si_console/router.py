# ROUTER, following docs/MODEL_TIERS.md. It is the only component that
# selects a model, so model choice and cost are decided in one place.
# It runs twice:
#   1. at intake: orchestrator_for(pane) -> the pane's T0 plan;
#   2. per task:  route(prompt, skill) -> worker tier T1, T2 or T3,
#      then dispatch() calls that tier through models.complete with
#      the pane's pin, allowlist and T1 rules.
# Routing is deterministic rules only: skill, keywords, length. When
# the rules disagree or find nothing, the Jev judge breaks the tie,
# but only between tiers this pane may use (MODEL_TIERS.md rule 4).
# If the judge is off or fails, the default is T2. No LLM decides a
# route on its own, and the coordinator never picks a model.
"""Rules-only router with a Jev tie-break and pane-aware dispatch."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional

from si_console import config, judge, models, telemetry
from si_console.errors import EscalationNeeded, ZeroPathNeeded

# Skill -> tier. Skills come from the coordinator's task type or the
# intake (voice intent, Ctrl+K command). Unknown skills use the rules.
SKILL_TIERS = {
    "summary": config.T3,
    "format": config.T3,
    "translate": config.T3,
    "voice_hint": config.T3,
    "search_query": config.T3,
    "narration": config.T3,
    "research": config.T2,
    "slides": config.T2,
    "synthesis": config.T2,
    "explain": config.T2,
    "signal": config.T2,
    "risk_check": config.T2,
    "code": config.T1,
    "debug": config.T1,
    "plan": config.T1,
    "escalation": config.T1,
}

HEAVY_WORDS = re.compile(
    r"\b(prove|debug|refactor|architect\w*|optimi[sz]e|root cause|design a|"
    r"multi-step|trade-?offs?|why does|implement)\b",
    re.I,
)
LIGHT_WORDS = re.compile(
    r"\b(summari[sz]e|tl;?dr|format|translate|rename|list|shorten|title for|"
    r"one line|keywords?)\b",
    re.I,
)
SHORT_CHARS = 200
LONG_CHARS = 4000

TIER_DESCRIPTIONS = {
    config.T1: "Hard reasoning, debugging, planning, or long multi-step work.",
    config.T2: "Normal synthesis: research, explanation, slide drafts, short chains.",
    config.T3: "Trivial small task: summary, formatting, translation, search query.",
}


@dataclass
class RouteDecision:
    tier: str
    reason: str
    judged: bool = False


@dataclass
class DispatchResult:
    route: RouteDecision
    reply: Optional[models.ModelReply] = None
    escalate: bool = False
    zero_path: bool = False
    detail: str = ""


def _votes(prompt: str, skill: str) -> list[tuple[str, str]]:
    votes: list[tuple[str, str]] = []
    if skill and skill in SKILL_TIERS:
        votes.append((SKILL_TIERS[skill], f"skill:{skill}"))
    if HEAVY_WORDS.search(prompt):
        votes.append((config.T1, "keyword:heavy"))
    if LIGHT_WORDS.search(prompt):
        votes.append((config.T3, "keyword:light"))
    if len(prompt) > LONG_CHARS:
        votes.append((config.T1, "length:long"))
    elif len(prompt) < SHORT_CHARS and not votes:
        votes.append((config.T3, "length:short"))
    return votes


def allowed_worker_tiers(pane: Optional[str]) -> list[str]:
    """Worker tiers this pane may route to. T1 drops out when it is off;
    T2 drops out when its allowlist is empty."""
    tiers = [config.T1, config.T2, config.T3]
    if not pane:
        return tiers
    cfg = config.PANE_CONFIG[pane.upper()]
    if cfg["t1"] == "off":
        tiers.remove(config.T1)
    if cfg["t2"] == "none":
        tiers.remove(config.T2)
    return tiers


def route(prompt: str, skill: str = "", pane: Optional[str] = None) -> RouteDecision:
    """Pick a worker tier. A skill vote wins outright. Otherwise one
    agreed tier wins; a conflict or no vote goes to the judge, then
    to the T2 default."""
    prompt = prompt or ""
    votes = _votes(prompt, skill)
    started = time.monotonic()
    decision = None
    skill_votes = [v for v in votes if v[1].startswith("skill:")]
    if skill_votes:
        decision = RouteDecision(skill_votes[0][0], skill_votes[0][1])
    else:
        tiers = {tier for tier, _ in votes}
        if len(tiers) == 1:
            decision = RouteDecision(votes[0][0], ",".join(r for _, r in votes))
    if decision is None:
        allowed = allowed_worker_tiers(pane)
        options = {t: TIER_DESCRIPTIONS[t] for t in allowed}
        reason = "conflict:" + ",".join(r for _, r in votes) if votes else "no_rule"
        try:
            picked = judge.decide_choice(
                "Which worker tier should handle `request`? Choose the cheapest "
                "tier that can do it well.",
                options,
                {"request": prompt[:4000], "skill": skill or "none"},
                pane=pane or "",
                purpose="route",
                min_confidence=0.5,
            )
            decision = RouteDecision(picked.choice, f"{reason}->judge", judged=True)
        except judge.JudgeError:
            decision = RouteDecision(config.T2, f"{reason}->default")
    telemetry.record(kind="route", pane=pane or "", tier=decision.tier,
                     route_reason=decision.reason,
                     latency_ms=int((time.monotonic() - started) * 1000), ok=True)
    return decision


def orchestrator_for(pane: str) -> list[str]:
    """Intake: the T0 slots this pane's orchestrator will try, in order."""
    return models.plan(config.T0, pane)[1]


def dispatch(
    prompt: str,
    *,
    pane: Optional[str] = None,
    skill: str = "",
    system: Optional[str] = None,
    schema: Optional[dict] = None,
) -> DispatchResult:
    """Route one worker task and run it. Escalation and the $0 path are
    results, not crashes: the caller shows ESCALATE TO HUMAN or uses
    voice_intents / a prewritten sentence."""
    decision = route(prompt, skill, pane)
    try:
        reply = models.complete(
            decision.tier, prompt, system, schema=schema, pane=pane,
            route_reason=decision.reason,
        )
    except EscalationNeeded as exc:
        return DispatchResult(decision, escalate=True, detail=exc.message)
    except ZeroPathNeeded as exc:
        return DispatchResult(decision, zero_path=True, detail=exc.message)
    return DispatchResult(decision, reply=reply)
