# The bridge is a small Python program that connects the vault to the
# hardware. It watches the vault, updates screens and LEDs, routes
# button events, and serves a local HTTP API. It does not trade. It
# does not call an LLM for decisions. It does not call DeepSeek or
# Bocha. Only the bridge touches GPIO, so no agent can touch hardware.
# It watches the vault continuously, so the screens follow a change
# without anyone asking. Watch method: watchdog with inotify first,
# poll every 1 second as fallback, because the booth must keep working
# if inotify fails. Handle created, modified, deleted, and moved
# events. Debounce 200 ms after the last event. Keep a hash map of file
# path to last parsed hash and skip a file when the hash did not
# change. Ignore .tmp files. A file must be stable for 200 ms before it
# is parsed, so a half written note is never read.
# Button rule: on a button press the bridge updates the task note,
# not state.json only. The note is the truth. state.json follows.
# API rules: token protected, Bearer token from .env, home LAN only,
# off in booth mode, rate limit 10 requests per minute per token, max
# 1 claim at a time per agent. External agents can claim research and
# narration tasks only. They can never approve, never execute, never
# propose trades, never edit code, never touch GPIO, never set a task
# to done for a trade task. Those actions belong to the person at the
# buttons. Kill cancels all claims at once. A write during kill returns
# 423. Ports: bridge API 8001, dashboard 8000. Do not expose the API to
# the internet. Do not port forward it.
"""Bridge. Vault watcher, LEDs, buttons, and the external agent API."""

from __future__ import annotations

import hashlib
import hmac
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException

from si_console import config
from si_console.errors import ConsoleError, VaultError
from si_console.state_store import ClaimStore, StateStore
from si_console.vault import (
    list_tasks,
    read_note,
    update_status,
    write_research_note,
    append_log,
    write_note,
)

# --- State ---------------------------------------------------------------
# The bridge owns kill state and approval state in memory. The vault
# owns task state. state.json is a cache for the screens. If state
# and the vault disagree, the vault wins on the next scan.
kill_active = False
# Set when the kill switch is pressed. Leaving the killed state takes a
# switch reset and then one green press, so releasing the switch alone
# never restarts work.
resume_required = False
approval_pending = False
approval_task_id = ""
rate_hits: list[float] = []

state_store = StateStore()
claim_store = ClaimStore()

# External agents may claim only these types. They cannot claim a
# signal task, a risk_check task, or an order task, because those lead
# to trades. The bridge enforces this by type. The list is a design
# choice that has not been tried with a real agent yet.
CLAIMABLE_TYPES = {"research", "narration"}

# Rate limit so one agent cannot flood the bridge: 10 requests per
# minute. The number is an estimate.
RATE_LIMIT_PER_MINUTE = 10


def _check_rate_limit() -> None:
    now = time.time()
    while rate_hits and rate_hits[0] < now - 60:
        rate_hits.pop(0)
    if len(rate_hits) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="RATE_LIMIT")
    rate_hits.append(now)


def _check_token(authorization: Optional[str]) -> None:
    """Check the Bearer token. No token, no access. Wrong token, 401.
    The token is never logged. The token is never returned."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token.")
    token = authorization[len("Bearer ") :]
    expected = config.BRIDGE_API_TOKEN
    if not expected or not hmac.compare_digest(token.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Bad token.")


def _check_not_killed() -> None:
    if kill_active or resume_required:
        raise HTTPException(status_code=423, detail="KILL_ACTIVE_WRITE_DENY")


def _check_home_mode() -> None:
    if config.MODE == "booth":
        raise HTTPException(status_code=403, detail="API is off in booth mode.")


# --- Vault watcher -------------------------------------------------------
# The watcher keeps a hash map. If the hash did not change, skip the
# file. If the file is a .tmp file, skip it. If the file changed less
# than 200 ms ago, wait. This debounce and settle step stops a half
# written note from being parsed. The real build runs this with watchdog
# inotify. This skeleton shows the poll fallback, which is the same
# logic, one second at a time, so the team can test it without
# installing watchdog first.
class VaultWatcher:
    """Poll fallback watcher. 1 second poll, 200 ms settle, hash map."""

    def __init__(self, vault_root: Path):
        self.root = vault_root
        self.hashes: dict[str, str] = {}
        self.last_seen: dict[str, float] = {}

    def scan_once(self) -> list[str]:
        """Scan the vault once. Returns the ids of changed task notes."""
        changed: list[str] = []
        tasks_dir = self.root / "tasks"
        if not tasks_dir.is_dir():
            return changed
        for path in sorted(tasks_dir.glob("*.md")):
            if path.suffix == ".tmp":
                continue
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                continue
            key = str(path)
            if self.hashes.get(key) == digest:
                continue
            # Settle: the file must be stable for 200 ms before parsing.
            now = time.time()
            if self.last_seen.get(key, 0) > now - 0.2 and key not in self.hashes:
                self.last_seen[key] = now
                continue
            self.last_seen[key] = now
            self.hashes[key] = digest
            changed.append(path.stem)
        return changed

    def rebuild_state(self) -> dict:
        """Rebuild state.json by scanning the vault. Called on start
        and after a crash. If the vault is unreadable, show VAULT
        ERROR and set all LEDs off, except the kill pattern."""
        try:
            tasks = list_tasks()
        except VaultError:
            return state_store.update(last_error="VAULT ERROR")
        current = tasks[0] if tasks else None
        return state_store.update(
            current_task_id=current.id if current else "",
            current_agent=current.agent if current else "",
            current_status=current.status if current else "",
            kill_active=kill_active,
            resume_required=resume_required,
            mode=config.MODE,
            approval_pending=approval_pending,
            lang=config.LANG,
        )


# --- Button handling -----------------------------------------------------
# These functions are called by the GPIO layer, not by the API.
# One press approves one task only. It never approves all queued tasks.
# If no proposal is pending, a green press does nothing, and the
# screen shows NO PROPOSAL READY. If kill is active, a green press
# does nothing. If risk_check is fail, a green press does nothing.
def on_green_press() -> dict:
    """Green button. Approve one pending proposal, or pick the 2020
    scenario on the start screen, or resume after a kill.

    The start screen rule: green picks 2020 only before any task
    exists, and only when the screen says CHOOSE SCENARIO. Once a
    task exists, green means approve. The screen must label the
    buttons in both states, so a visitor knows what a press will do.
    """
    global approval_pending, approval_task_id, resume_required
    if kill_active:
        # The kill switch is still latched on. Green does nothing.
        # Turn the switch off first, then press green once.
        return {"status": "ignored", "note": "KILL ACTIVE"}
    if resume_required:
        # Resume path: the switch is already off (on_kill(False) ran).
        # Never auto resume. Old blocked tasks stay blocked, and no
        # proposal from before the kill can be approved by this press.
        resume_required = False
        approval_pending = False
        approval_task_id = ""
        state_store.update(
            kill_active=False, resume_required=False, approval_pending=False, last_error=""
        )
        return {"status": "resumed", "note": "New signal task will be created."}
    if not approval_pending or not approval_task_id:
        return {"status": "ignored", "note": "NO PROPOSAL READY"}
    try:
        task = read_note(approval_task_id)
    except VaultError:
        approval_pending = False
        return {"status": "ignored", "note": "Task is gone."}
    if task.risk_check == "fail":
        return {"status": "ignored", "note": f"RISK BLOCKED {task.risk_reason}"}
    if task.status in ("blocked", "done"):
        # A task blocked by kill, timeout or watchdog, or already done,
        # is no longer a live proposal. Never revive it with green.
        approval_pending = False
        approval_task_id = ""
        state_store.update(approval_pending=False)
        return {"status": "ignored", "note": f"TASK {task.status.upper()}"}
    update_status(task.id, "working", approved_by="human")
    approval_pending = False
    state_store.update(approval_pending=False)
    return {"status": "approved", "task_id": task.id}


def on_red_press() -> dict:
    """Red button. Reject one pending proposal, or pick the 2022
    scenario on the start screen. It does not execute anything. It
    does not change the portfolio. The coordinator routes work back
    to signal for a new proposal."""
    global approval_pending, approval_task_id
    if not approval_pending or not approval_task_id:
        return {"status": "ignored", "note": "NO PROPOSAL READY"}
    task_id = approval_task_id
    approval_pending = False
    approval_task_id = ""
    state_store.update(approval_pending=False)
    try:
        update_status(task_id, "blocked", "HUMAN_REJECT")
    except VaultError:
        return {"status": "ignored", "note": "Task is gone."}
    return {"status": "rejected", "task_id": task_id}


def on_kill(active: bool) -> dict:
    """Kill switch changed. Active means frozen. Within 200 ms the
    bridge must: set kill active, block all working tasks with
    KILL_SWITCH, stop execution, stop voice, set the kill LED
    pattern, show KILL ACTIVE, and log it. Claims are cancelled."""
    global kill_active, resume_required, approval_pending, approval_task_id
    kill_active = active
    if active:
        # Drop the pending proposal in memory too, not only in
        # state.json, or green could approve it after a resume.
        approval_pending = False
        approval_task_id = ""
        resume_required = True
        claim_store.release_all()
        for task in list_tasks(status="working"):
            try:
                update_status(task.id, "blocked", "KILL_SWITCH")
            except VaultError:
                continue
        state_store.update(kill_active=True, resume_required=True, approval_pending=False)
        return {"status": "killed"}
    # Switch released. Still frozen until one green press resumes.
    state_store.update(kill_active=False, resume_required=resume_required)
    return {"status": "kill released, press green to resume"}


def request_approval(task_id: str) -> dict:
    """Mark a task as waiting for the green button. The bridge lights
    the green button LED solid and shows the proposal on screen."""
    global approval_pending, approval_task_id
    if kill_active or resume_required:
        # Fail closed: no proposal is offered while frozen.
        return {"status": "ignored", "note": "KILL ACTIVE"}
    task = read_note(task_id)
    if task.status in ("blocked", "done"):
        return {"status": "ignored", "note": f"TASK {task.status.upper()}"}
    approval_pending = True
    approval_task_id = task.id
    state_store.update(approval_pending=True, current_task_id=task.id)
    return {"status": "approval_pending", "task_id": task.id}


# --- FastAPI app ---------------------------------------------------------
app = FastAPI(title="SI Console Bridge", version="0.1.0")


@app.get("/api/health")
def health() -> dict:
    """No auth. Check the bridge is up before claiming. If kill is
    active, do not claim. If mode is booth, do not claim."""
    state = state_store.read()
    return {
        "status": "ok",
        "mode": config.MODE,
        "kill_active": kill_active,
        "updated": state.get("updated", ""),
    }


@app.get("/api/tasks")
def list_api_tasks(
    status: str = "queued",
    agent: str = "",
    authorization: Optional[str] = Header(None),
) -> dict:
    """List task notes by status. Returns ids and titles only, not
    full bodies. External agents use this to find work. They must
    not scan the vault folder directly."""
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    if status not in ("queued", "working", "blocked", "done"):
        raise HTTPException(status_code=400, detail="Bad status.")
    tasks = list_tasks(status=status, agent=agent)
    return {
        "tasks": [
            {"id": t.id, "agent": t.agent, "status": t.status, "type": t.type}
            for t in tasks
        ]
    }


@app.get("/api/tasks/{task_id}")
def get_api_task(task_id: str, authorization: Optional[str] = Header(None)) -> dict:
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    try:
        task = read_note(task_id)
    except VaultError:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND") from None
    return {"task": task.to_frontmatter(), "body": task.body}


@app.post("/api/tasks/{task_id}/claim")
def claim_api_task(
    task_id: str,
    body: dict,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Claim one queued task for one external agent. One task, one
    claim, one agent. A task already claimed returns 409. A task
    that is not research or narration returns 403."""
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    _check_not_killed()
    try:
        task = read_note(task_id)
    except VaultError:
        raise HTTPException(status_code=404, detail="TASK_NOT_FOUND") from None
    if task.type not in CLAIMABLE_TYPES:
        raise HTTPException(status_code=403, detail="CLAIM_TYPE_DENY")
    if task.status != "queued":
        raise HTTPException(status_code=409, detail="CLAIM_CONFLICT")
    agent_id = body.get("agent_id", "")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required.")
    try:
        claim = claim_store.claim(task_id, agent_id)
    except ConsoleError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.code) from None
    update_status(task_id, "working")
    note = read_note(task_id)
    append_log(note, f"CLAIMED BY {agent_id}")
    write_note(note)
    return {"task_id": task_id, "claim_token": claim["claim_token"], "expires_at": claim["expires_at"]}


@app.post("/api/tasks/{task_id}/release")
def release_api_task(
    task_id: str,
    body: dict,
    authorization: Optional[str] = Header(None),
) -> dict:
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    try:
        result = claim_store.release(
            task_id, body.get("agent_id", ""), body.get("claim_token", "")
        )
    except ConsoleError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.code) from None
    if result.get("released"):
        note = read_note(task_id)
        append_log(note, "CLAIM_RELEASED")
        write_note(note)
        update_status(task_id, "queued")
    return result


@app.post("/api/tasks/{task_id}/heartbeat")
def heartbeat_api_task(
    task_id: str,
    body: dict,
    authorization: Optional[str] = Header(None),
) -> dict:
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    try:
        claim = claim_store.heartbeat(
            task_id, body.get("agent_id", ""), body.get("claim_token", "")
        )
    except ConsoleError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.code) from None
    return {"task_id": task_id, "expires_at": claim["expires_at"]}


@app.post("/api/research")
def research_api_task(
    body: dict,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Write a research note. The bridge sets the file name, never
    the caller. Max 20000 characters. The note must not contain a
    shell command, a secret, or a file path outside the vault."""
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    _check_not_killed()
    content = body.get("content", "")
    if len(content) > 20000:
        raise HTTPException(status_code=400, detail="RESEARCH_REJECT")
    if any(bad in content for bad in ("rm -rf", "curl ", "wget ", "sudo ")):
        raise HTTPException(status_code=400, detail="RESEARCH_REJECT")
    name = write_research_note(
        body.get("title", "research"), content, body.get("task_id", "")
    )
    return {"file": name, "task_id": body.get("task_id", "")}


@app.post("/api/tasks/{task_id}/report")
def report_api_task(
    task_id: str,
    body: dict,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Append a report to the Log section of a claimed task only.
    It does not change status. It does not change the proposal,
    amount, ticker, or price. It does not set risk_check. It does
    not set approved_by. Max 5000 characters. No HTML, no scripts."""
    _check_token(authorization)
    _check_rate_limit()
    _check_home_mode()
    _check_not_killed()
    content = body.get("content", "")
    if len(content) > 5000 or "<script" in content.lower():
        raise HTTPException(status_code=400, detail="Bad report.")
    try:
        claim_store.heartbeat(
            task_id, body.get("agent_id", ""), body.get("claim_token", "")
        )
    except ConsoleError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.code) from None
    note = read_note(task_id)
    append_log(note, f"REPORT by {body.get('agent_id', '')}: {content}")
    write_note(note)
    return {"task_id": task_id, "reported": True}


@app.get("/api/state")
def state_api(authorization: Optional[str] = Header(None)) -> dict:
    """state.json, read only. Do not poll faster than once per second."""
    _check_token(authorization)
    _check_rate_limit()
    return state_store.read()


def main() -> None:
    """Run the bridge API on port 8001. The dashboard is on 8000,
    so a dashboard crash does not take the API down. Run with:
    uvicorn si_console.bridge:app --host 127.0.0.1 --port 8001
    In home mode, bind to the LAN address for Hermes on the laptop.
    Never expose this API to the internet. Never port forward it.
    """
    import uvicorn

    uvicorn.run(app, host=config.BRIDGE_HOST, port=config.BRIDGE_PORT)
