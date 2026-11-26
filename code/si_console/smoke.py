# Provider smoke check. Run it on the Pi after copying .env, and again
# at the booth in Shenzhen, before starting the services:
#   python -m si_console.smoke          free: config, DNS, clock, keys
#   python -m si_console.smoke --live   one tiny real call per model
# The free mode spends nothing: it reads each provider's /models list
# (and OpenRouter's /key info) to prove the key works and the pinned
# model id exists. The live mode sends each model exactly the request
# the router sends (same thinking fields; tool calling for T0 models),
# once, with no retries, and prints a cost ceiling first. Keys are
# never printed: every message is redacted. Exit code 0 means every
# tier has a working model; 1 means something must be fixed first.
"""Provider smoke check: free config/key checks, optional live calls."""

from __future__ import annotations

import argparse
import email.utils
import json
import socket
import sys
import time
from dataclasses import dataclass

import httpx

from si_console import chat_client, config, models, telemetry
from si_console.errors import ModelError

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"
CLOCK_SKEW_LIMIT_SECONDS = 300
# Free key checks for the judge. TypeSafe: GET /v1/models sends no text
# to the model. OpenRouter: GET /api/v1/key returns key info.
JEV_KEY_CHECK_URLS = {
    "typesafe": "https://api.typesafe.ai/v1/models",
    "openrouter": "https://openrouter.ai/api/v1/key",
}

PING_TOOL = {
    "type": "function",
    "function": {
        "name": "ping",
        "description": "Health check. Call it when asked to.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
}


@dataclass
class Check:
    status: str
    name: str
    detail: str
    ms: int = 0


def _secrets() -> list[str]:
    keys = [chat_client.provider_key(p) for p in chat_client.PROVIDERS]
    return [k for k in keys + [config.JEV_API_KEY] if k]


def _clean(text: str) -> str:
    return chat_client.redact(str(text), *_secrets())


def slot_usage() -> dict:
    """Every (thinking, tools) combination the router can send to each
    slot, taken from the tier table, so live mode tests the real thing."""
    usage: dict[str, set] = {}
    for tier, spec in config.MODEL_TIERS.items():
        for slot in spec["chain"]:
            usage.setdefault(slot, set()).add((spec["thinking"], tier == config.T0))
    return {slot: sorted(combos) for slot, combos in usage.items()}


def _host(url: str) -> str:
    return httpx.URL(url).host


# --- Free checks --------------------------------------------------------

def check_config() -> list[Check]:
    out = []
    for slot in config.MODEL_SLOTS:
        info = models.slot_info(slot)
        key_attr = chat_client.provider_spec(info["provider"])["key_attr"]
        missing = [n for n, ok in ((key_attr, chat_client.provider_key(info["provider"])),
                                   (info["model_attr"], info["model"])) if not ok]
        if missing:
            out.append(Check(SKIP, slot, "not configured: set " + ", ".join(missing) + " in .env"))
        else:
            out.append(Check(PASS, slot, f"key set, model {info['model']}"))
    if config.JEV_API_KEY and config.JEV_MODEL:
        out.append(Check(PASS, "jev", f"{config.JEV_PROVIDER} key set, model {config.JEV_MODEL}"))
        if config.JEV_PROVIDER == "typesafe" and config.JEV_MODEL.startswith("typesafe/"):
            out.append(Check(FAIL, "jev", "typesafe/... is an OpenRouter id; on TypeSafe "
                                          "use jev-1.14.0 or jev-latest"))
    else:
        out.append(Check(SKIP, "jev", "not configured"))
    if config.DASHSCOPE_API_KEY and config.QWEN_JUDGE_MODEL:
        out.append(Check(PASS, "judge backup", f"Qwen on Bailian, model {config.QWEN_JUDGE_MODEL}"))
    elif config.QWEN_JUDGE_MODEL:
        out.append(Check(SKIP, "judge backup", "QWEN_JUDGE_MODEL set but DASHSCOPE_API_KEY is empty"))
    else:
        out.append(Check(SKIP, "judge backup", "not configured: set QWEN_JUDGE_MODEL in .env"))
    from si_console import websearch

    if websearch.zhipu_configured():
        engine = "search-prime" if websearch._international() else config.ZHIPU_SEARCH_ENGINE
        out.append(Check(PASS, "web search", f"Zhipu on the GLM key, engine {engine}"
                         + (", Bocha fallback" if config.BOCHA_API_KEY else "")))
    elif config.BOCHA_API_KEY:
        out.append(Check(PASS, "web search", "Bocha only (no GLM key)"))
    else:
        out.append(Check(WARN, "web search", "none: set GLM_API_KEY (Zhipu search uses it)"))
    for pane in config.PANES:
        try:
            for tier in (config.T0, config.T1, config.T2, config.T3):
                models.plan(tier, pane)
            out.append(Check(PASS, f"pane {pane}", json.dumps(config.PANE_CONFIG[pane])))
        except ModelError as exc:
            out.append(Check(FAIL, f"pane {pane}", exc.message))
    return out


def _configured_providers() -> list[str]:
    seen = []
    for slot in config.MODEL_SLOTS:
        provider = models.slot_info(slot)["provider"]
        if models.slot_configured(slot) and provider not in seen:
            seen.append(provider)
    if config.DASHSCOPE_API_KEY and config.QWEN_JUDGE_MODEL and "dashscope" not in seen:
        seen.append("dashscope")
    return seen


def check_network() -> list[Check]:
    out = []
    hosts = {p: _host(chat_client.base_url(p)) for p in _configured_providers()}
    if config.JEV_API_KEY:
        hosts[config.JEV_PROVIDER] = _host(config.JEV_URL)
    for name, host in hosts.items():
        started = time.monotonic()
        try:
            socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
            out.append(Check(PASS, f"dns {name}", host, int((time.monotonic() - started) * 1000)))
        except OSError as exc:
            out.append(Check(FAIL, f"dns {name}", f"{host}: {type(exc).__name__}"))
    # HTTPS needs a correct clock. A Pi has no RTC battery by default.
    for name, host in hosts.items():
        try:
            response = httpx.head(f"https://{host}/", timeout=5)
        except httpx.HTTPError as exc:
            out.append(Check(FAIL, "clock", f"could not reach {host}: {type(exc).__name__}"))
            break
        date = response.headers.get("date")
        if not date:
            continue
        skew = abs(time.time() - email.utils.parsedate_to_datetime(date).timestamp())
        status = PASS if skew <= CLOCK_SKEW_LIMIT_SECONDS else FAIL
        detail = f"{skew:.0f}s off {host}"
        if status == FAIL:
            detail += " - run: sudo timedatectl set-ntp true"
        out.append(Check(status, "clock", detail))
        break
    return out


def check_keys() -> list[Check]:
    """Free key and model-id checks through each provider's /models."""
    out = []
    for provider in _configured_providers():
        label = chat_client.provider_spec(provider)["label"]
        started = time.monotonic()
        try:
            result = chat_client.list_models(provider)
        except ModelError as exc:
            out.append(Check(FAIL, f"key {provider}", _clean(exc.message)))
            continue
        ms = int((time.monotonic() - started) * 1000)
        status_code = result["status"]
        if status_code in (401, 403):
            out.append(Check(FAIL, f"key {provider}",
                             _clean(f"{label} rejected the key ({status_code}).{result['detail']}"), ms))
            continue
        if status_code != 200:
            out.append(Check(WARN, f"key {provider}",
                             _clean(f"no free /models check ({status_code}); verify with --live"), ms))
            continue
        out.append(Check(PASS, f"key {provider}", f"{label} accepted the key", ms))
        listed = result["models"]
        for slot in config.MODEL_SLOTS:
            info = models.slot_info(slot)
            if info["provider"] != provider or not info["model"]:
                continue
            if listed is None:
                out.append(Check(WARN, f"model {slot}", "provider list unreadable; verify with --live"))
            elif info["model"] in listed:
                out.append(Check(PASS, f"model {slot}", f"{info['model']} is listed"))
            else:
                near = [m for m in listed if m.split("-")[0] == info["model"].split("-")[0]][:5]
                out.append(Check(WARN, f"model {slot}",
                                 f"{info['model']} is not in {label}'s list"
                                 + (f"; listed: {', '.join(near)}" if near else "")))
        if provider == "dashscope" and config.QWEN_JUDGE_MODEL:
            if listed is None:
                out.append(Check(WARN, "model qwen-judge", "provider list unreadable; verify with --live"))
            elif config.QWEN_JUDGE_MODEL in listed:
                out.append(Check(PASS, "model qwen-judge", f"{config.QWEN_JUDGE_MODEL} is listed"))
            else:
                near = [m for m in listed if m.startswith("qwen")][:8]
                out.append(Check(WARN, "model qwen-judge",
                                 f"{config.QWEN_JUDGE_MODEL} is not in {label}'s list"
                                 + (f"; listed: {', '.join(near)}" if near else "")))
    if config.JEV_API_KEY:
        name = f"key {config.JEV_PROVIDER}"
        try:
            response = httpx.get(JEV_KEY_CHECK_URLS[config.JEV_PROVIDER], timeout=10,
                                 headers={"Authorization": f"Bearer {config.JEV_API_KEY}"})
            if response.status_code == 200:
                out.append(Check(PASS, name, f"{config.JEV_PROVIDER} accepted the Jev key"))
            else:
                out.append(Check(FAIL, name, _clean(
                    f"{config.JEV_PROVIDER} returned {response.status_code}."
                    f"{chat_client.error_detail(response, config.JEV_API_KEY)}")))
        except httpx.HTTPError as exc:
            out.append(Check(FAIL, name, f"not reachable: {type(exc).__name__}"))
    return out


# --- Live checks --------------------------------------------------------

def estimate_live_cost() -> float:
    total = 0.0
    for slot, combos in slot_usage().items():
        if models.slot_configured(slot):
            for thinking, _tools in combos:
                total += telemetry.estimate_cost(slot, 300, 400 if thinking != "disabled" else 40)
    if config.JEV_API_KEY and config.JEV_MODEL:
        total += telemetry.estimate_cost("jev", 300, 0)
    if config.DASHSCOPE_API_KEY and config.QWEN_JUDGE_MODEL:
        total += telemetry.estimate_cost("qwen-judge", 300, 60)
    return total


def _live_chat(slot: str, thinking: str, with_tools: bool) -> Check:
    info = models.slot_info(slot)
    name = f"live {slot} thinking={thinking}" + (" +tools" if with_tools else "")
    started = time.monotonic()
    try:
        raw = chat_client.complete(
            info["provider"],
            "Call the ping tool now." if with_tools else "Reply with the single word OK.",
            "You are a health check. Keep the answer minimal.",
            model=info["model"],
            max_tokens=400 if thinking != "disabled" else 40,
            tools=[PING_TOOL] if with_tools else None,
            thinking=thinking,
        )
    except ModelError as exc:
        return Check(FAIL, name, _clean(exc.message), int((time.monotonic() - started) * 1000))
    ms = int((time.monotonic() - started) * 1000)
    usage = f"{raw['input_tokens']}+{raw['output_tokens']} tok"
    if with_tools:
        called = [c.get("function", {}).get("name") for c in raw["tool_calls"]]
        if "ping" in called:
            return Check(PASS, name, f"tool call works, {usage}", ms)
        return Check(WARN, name, f"answered without calling the tool ({usage}); "
                                 "this model may be unreliable as an orchestrator", ms)
    return Check(PASS, name, f"replied {raw['text'][:20]!r}, {usage}", ms)


def _live_judge(backend: str) -> Check:
    """One decision from one judge backend on its own, so a working
    backup cannot hide a dead Jev (or the other way round)."""
    from si_console import judge

    name = "live jev" if backend == "jev" else "live judge backup (qwen)"
    started = time.monotonic()
    try:
        decision = judge.ask(
            backend,
            "Which option is a fruit?",
            {"apple": "A fruit.", "brick": "A building material."},
            {"health_check": True},
            purpose="smoke",
        )
    except judge.JudgeError as exc:
        return Check(FAIL, name, _clean(exc.message), int((time.monotonic() - started) * 1000))
    ms = int((time.monotonic() - started) * 1000)
    status = PASS if decision.choice == "apple" else WARN
    slow = ""
    limit = config.JEV_TIMEOUT_SECONDS if backend == "jev" else config.QWEN_JUDGE_TIMEOUT_SECONDS
    if ms > limit * 1000 * 0.8:
        status, slow = WARN, f"; close to the {limit}s timeout"
    return Check(status, name, f"chose {decision.choice} ({decision.confidence:.2f}){slow}", ms)


def check_live() -> list[Check]:
    out = []
    for slot, combos in slot_usage().items():
        if not models.slot_configured(slot):
            continue
        for thinking, with_tools in combos:
            out.append(_live_chat(slot, thinking, with_tools))
    from si_console import judge

    judged = [_live_judge(backend) for backend in judge.backends()]
    # One working judge is enough: a dead Jev with a working backup (or
    # the reverse) is a warning, not a failure. No judge at all only
    # means routing ties use the T2 default, so that is a warning too.
    if any(c.status == PASS for c in judged):
        for c in judged:
            if c.status == FAIL:
                c.status, c.detail = WARN, c.detail + " (the other judge covers it)"
    else:
        for c in judged:
            if c.status == FAIL:
                c.status, c.detail = WARN, c.detail + " (no judge works: routing ties use T2)"
    return out + judged + [_live_search()]


def _live_search() -> Check:
    """One real search (about 0.01 CNY on search_std). Search is research
    only, so a failure is a warning: tasks continue without results."""
    from si_console import websearch

    if not (websearch.zhipu_configured() or config.BOCHA_API_KEY):
        return Check(SKIP, "live web search", "no search configured")
    started = time.monotonic()
    result = websearch.web_search("Shenzhen weather today", count=2, freshness="oneWeek")
    ms = int((time.monotonic() - started) * 1000)
    if "results" in result:
        return Check(PASS, "live web search",
                     f"{result.get('provider', '?')}: {len(result['results'])} result(s)", ms)
    return Check(WARN, "live web search", _clean(result["error"]), ms)


# --- Summary ------------------------------------------------------------

def tier_summary(checks: list[Check], live: bool) -> list[Check]:
    """Each tier needs at least one slot that passed. T0 has no fallback
    beyond its chain, so an empty T0 is a FAIL; T1 empty means every
    heavy task escalates, T3 empty means the $0 paths: WARN."""
    failed = {c.name.split()[1] for c in checks
              if c.status == FAIL and c.name.split()[0] in ("live", "model")}
    bad_providers = {c.name.split()[1] for c in checks if c.status == FAIL and c.name.startswith("key ")}
    out = []
    for tier in (config.T0, config.T1, config.T2, config.T3):
        good = [s for s in config.MODEL_TIERS[tier]["chain"]
                if models.slot_configured(s) and s not in failed
                and models.slot_info(s)["provider"] not in bad_providers]
        if good:
            note = "" if live else " (keys checked; run --live to confirm calls)"
            out.append(Check(PASS, f"tier {tier}", f"usable: {', '.join(good)}{note}"))
        else:
            status = FAIL if tier in (config.T0, config.T2) else WARN
            effect = {config.T1: "heavy tasks escalate to the human",
                      config.T3: "small tasks use the $0 code paths"}.get(tier, "no model can run this tier")
            out.append(Check(status, f"tier {tier}", f"no working model: {effect}"))
    return out


def run(live: bool = False, assume_yes: bool = False, out=sys.stdout) -> int:
    checks = check_config() + check_network() + check_keys()
    if live:
        cost = estimate_live_cost()
        print(f"Live mode: one call per model and thinking setting, about ${cost:.4f} at most.",
              file=out)
        if not assume_yes:
            answer = input("Send live calls? [y/N] ").strip().lower()
            if answer != "y":
                print("Live calls skipped.", file=out)
                live = False
        if live:
            checks += check_live()
    checks += tier_summary(checks, live)
    width = max(len(c.name) for c in checks)
    for c in checks:
        ms = f" ({c.ms} ms)" if c.ms else ""
        print(f"{c.status:4}  {c.name:<{width}}  {_clean(c.detail)}{ms}", file=out)
    failures = [c for c in checks if c.status == FAIL]
    print(f"\n{len(failures)} failure(s)." if failures else "\nAll tiers usable.", file=out)
    return 1 if failures else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="send one tiny real call per model")
    parser.add_argument("--yes", action="store_true", help="do not ask before live calls")
    args = parser.parse_args(argv)
    return run(live=args.live, assume_yes=args.yes)


if __name__ == "__main__":
    raise SystemExit(main())
