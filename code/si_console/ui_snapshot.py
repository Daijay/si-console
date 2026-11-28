# Read-only UI snapshot. Turns the real state.json, the vault, the
# approval request and telemetry into the shape the mockup screens
# already render. No approve/reject/kill route is added: screens stay
# read only and the buttons remain on GPIO.
#
# Fail safe: a malformed or unreadable source yields an "offline"
# snapshot, never a stale or half drawn screen. The browser already
# treats an unknown console_state as offline.
"""Build the GET /api/ui/state snapshot from real sources."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from si_console import config, strings, telemetry
from si_console.errors import ConsoleError
from si_console.state_store import StateStore
from si_console.vault import VaultError, list_tasks, read_note

OFFLINE = {
    "console_state": "offline",
    "round": 0,
    "max_rounds": config.ROUND_LIMIT,
    "mode": config.MODE,
    "replay": config.REPLAY_SCENARIO,
    "lang": config.LANG,
    "agents": {"coord": "off", "a1": "off", "a2": "off", "guard": "off"},
    "kill_active": False,
    "resume_required": False,
    "software_freeze": False,
    "approval": None,
    "outcome": None,
    "cost": {"usd": 0.0, "cap": config.DEEPSEEK_DAILY_CAP_USD, "calls": 0},
    "judge": None,
    "faults": {"net": False, "mic": False, "models": False, "vault": True, "cost_cap": False},
    "said": "",
}

_ROLE_LED = {
    "coordinator": "coord",
    "signal": "a1",
    "risk": "guard",
    "execution": "a2",
}


def _age_seconds(iso: str) -> float:
    try:
        then = dt.datetime.fromisoformat(iso)
        if then.tzinfo is None:
            then = then.replace(tzinfo=dt.timezone.utc)
        return (dt.datetime.now(dt.timezone.utc) - then).total_seconds()
    except (TypeError, ValueError):
        return 0.0


def _agents(state: dict, task) -> dict:
    base = {"coord": "off", "a1": "off", "a2": "off", "guard": "off"}
    if task is not None:
        led = _ROLE_LED.get(task.agent)
        if led:
            base[led] = {
                "queued": "queued",
                "working": "working",
                "done": "done",
                "blocked": "blocked",
            }.get(task.status, "off")
    if state.get("kill_active") or state.get("resume_required"):
        return {k: "off" for k in base}
    return base


def _approval(request: dict, task, state: dict) -> dict | None:
    if not state.get("approval_pending") or not request:
        return None
    # Priority: frozen overrides an approval. A killed console never
    # offers a green button, even if the request file is still around.
    if state.get("kill_active") or state.get("resume_required"):
        return None
    if task is None:
        return None
    try:
        requested = float(request.get("requested_at", 0))
    except (TypeError, ValueError):
        return None
    expires = requested + config.APPROVAL_TIMEOUT_SECONDS
    seconds_left = max(0, int(expires - __import__("time").time()))
    risk = "high" if task.type == "order" else "medium"
    verdict = "ui_guard_pass" if task.risk_check == "pass" else "ui_guard_block"
    checks = [
        ["ui_chk_kill", not (state.get("kill_active") or state.get("resume_required"))],
        ["ui_chk_tool", True],
        ["ui_chk_risk_pass", task.risk_check != "fail"],
        ["ui_chk_human", True],
    ]
    return {
        "task_id": task.id,
        "agent": _ROLE_LED.get(task.agent, "coord"),
        "risk": risk,
        "action": {"id": "ui_act_buy" if task.type == "order" else "ui_act_slides",
                   "params": {"ticker": task.ticker, "amount": task.amount}},
        "command": str(request.get("command", "")),
        "why": {"id": "ui_why_rank", "params": {}},
        "checks": checks,
        "verdict": verdict,
        "expires_at": dt.datetime.fromtimestamp(expires, dt.timezone.utc).isoformat(),
        "secondsLeft": seconds_left,
        "timeout": config.APPROVAL_TIMEOUT_SECONDS,
        "reject_proposed": False,
    }


def _cost() -> dict:
    rows = telemetry.rows(limit=200)
    today = dt.date.today().isoformat()
    todays = [r for r in rows if str(r.get("ts", "")).startswith(today)]
    return {
        "usd": round(sum(float(r.get("cost_usd") or 0) for r in todays), 6),
        "cap": config.DEEPSEEK_DAILY_CAP_USD,
        "calls": len(todays),
    }


def build(store: StateStore | None = None, request: dict | None = None) -> dict:
    """One snapshot. Any source failure returns the offline snapshot."""
    from si_console import approval

    try:
        state = (store or StateStore()).read()
        if not state:
            return dict(OFFLINE)
        req = request if request is not None else approval.read_request()
        tasks = list_tasks()
        task = None
        task_id = state.get("current_task_id") or (req.get("task_id") if req else "")
        for candidate in tasks:
            if candidate.id == task_id:
                task = candidate
                break
        if task is None and tasks:
            task = tasks[0]
        last_error = str(state.get("last_error", "")).upper()
        word = "ui_w_ready"
        if state.get("kill_active"):
            word = "ui_w_frozen"
        elif state.get("resume_required"):
            word = "ui_w_still_frozen"
        elif "VAULT" in last_error:
            word = "ui_w_offline"
        elif state.get("approval_pending") and task is not None:
            word = "ui_w_waiting"
        elif task is not None:
            word = {
                "working": "ui_w_working",
                "blocked": "ui_w_blocked",
                "done": "ui_w_done",
            }.get(task.status, "ui_w_ready")
        cost = _cost()
        faults = {
            "net": False,       # no network check yet
            "mic": False,       # no mic check yet
            "models": "API" in last_error or "MODEL" in last_error,
            "vault": "VAULT" in last_error,
            "cost_cap": cost["usd"] >= cost["cap"],
        }
        snapshot = {
            "console_state": word,
            "round": int(task.round) if task else 0,
            "max_rounds": config.ROUND_LIMIT,
            "mode": str(state.get("mode", config.MODE)),
            "replay": config.REPLAY_SCENARIO,
            "lang": str(state.get("lang", config.LANG)),
            "agents": _agents(state, task),
            "kill_active": bool(state.get("kill_active")),
            "resume_required": bool(state.get("resume_required")),
            "software_freeze": bool(state.get("software_freeze")),
            "approval": _approval(req, task, state),
            "outcome": (
                {"id": f"ui_reason_{task.risk_reason}", "params": {}}
                if task is not None and task.risk_reason else None
            ),
            "cost": cost,
            "judge": None,   # confidence not stored in telemetry yet
            "faults": faults,
            "said": "",      # STT not wired yet
            "current_task_id": task.id if task else "",
            "current_status": task.status if task else "",
            "last_message_id": state.get("last_message_id", ""),
            "last_message_lang": state.get("last_message_lang", ""),
        }
        # The screen text must resolve: a broken id is a fault, not a
        # raw id painted on the kiosk.
        for key in ("last_message_id",):
            if snapshot[key] and not strings.has(snapshot[key], snapshot["lang"]):
                snapshot["faults"]["vault"] = True
        return snapshot
    except (ConsoleError, VaultError, OSError, ValueError, TypeError):
        return dict(OFFLINE)
