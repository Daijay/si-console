# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# This file is Autumn's autumn/chats.py, rewired for SI Console state.
# What stayed: one JSON file per record, atomic write with temp file
# then os.replace, path guard on ids, and the rule that a corrupt
# file can never take out the rest. ChatStore._write is the pattern.
# What changed: chats are gone. This store holds state.json for the
# screens and claims.json for external agent claims. The vault is
# still the truth for tasks. state.json is a cache. If they disagree,
# the vault wins. The bridge rebuilds state.json by scanning the
# vault on every start. Claims live outside the vault, in claims.json,
# because frontmatter has no claim field in ARCHITECTURE.md. Do not
# add a claim field to frontmatter without updating ARCHITECTURE.md.
# Claim rules, from INTEGRATION.md: one task, one claim, one agent.
# Claim TTL 300 seconds. Heartbeat every 60 seconds to renew. No
# heartbeat for 300 seconds, the claim expires and the task returns
# to queued. A heartbeat after expiry returns 410. A wrong claim
# token returns 403. Claims are lost on reboot. No claim survives
# a power loss. The bridge must check /api/health before every write.
"""State store. Atomic JSON for state.json and for claims."""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
import time
from pathlib import Path
from typing import Optional

from si_console import config
from si_console.errors import ConsoleError

# Claim rules, copied from INTEGRATION.md section 8.2. ASSUMED numbers.
CLAIM_TTL_SECONDS = 300
HEARTBEAT_INTERVAL_SECONDS = 60

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_]{0,63}$")


def _write_atomic_json(path: Path, data: dict) -> None:
    """Atomic JSON write. Copied from Autumn ChatStore._write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


class StateStore:
    """state.json. The dashboard reads it, never the vault directly.

    Fields, from ARCHITECTURE.md section 7: current_task_id,
    current_agent, current_status, kill_active, mode, replay_date,
    last_voice_text, last_error, approval_pending, lang, updated.
    """

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or config.STATE_PATH)

    def read(self) -> dict:
        return _read_json(self.path)

    def write(self, state: dict) -> dict:
        state["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _write_atomic_json(self.path, state)
        return state

    def update(self, **fields) -> dict:
        state = self.read()
        state.update(fields)
        return self.write(state)


class ClaimStore:
    """claims.json. One claim per task, one agent per claim.

    A claim is a dict: task_id, agent_id, claim_token, expires_at.
    The token is random per claim, never reused for a second task.
    """

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or config.CLAIMS_PATH)

    def _all(self) -> dict:
        return _read_json(self.path)

    def _save(self, claims: dict) -> None:
        _write_atomic_json(self.path, claims)

    def claim(self, task_id: str, agent_id: str) -> dict:
        """Claim one queued task. Second claim returns a conflict."""
        if not ID_RE.fullmatch(task_id):
            raise ConsoleError("TASK_NOT_FOUND", f"Invalid task id: {task_id!r}.", status=404)
        claims = self._all()
        now = time.time()
        # Drop expired claims first, so an expired claim never blocks.
        claims = {k: v for k, v in claims.items() if v.get("expires_at", 0) > now}
        if task_id in claims:
            raise ConsoleError(
                "CLAIM_CONFLICT",
                f"Task {task_id} is already claimed.",
                remedy="Wait, or try another task.",
                status=409,
            )
        token = secrets.token_urlsafe(24)
        claims[task_id] = {
            "task_id": task_id,
            "agent_id": agent_id,
            "claim_token": token,
            "expires_at": now + CLAIM_TTL_SECONDS,
        }
        self._save(claims)
        return claims[task_id]

    def heartbeat(self, task_id: str, agent_id: str, token: str) -> dict:
        """Renew a claim. A heartbeat after expiry returns 410."""
        claims = self._all()
        claim = claims.get(task_id)
        if claim is None:
            raise ConsoleError(
                "CLAIM_EXPIRED",
                f"No claim for task {task_id}. Claim again.",
                status=410,
            )
        if claim.get("claim_token") != token or claim.get("agent_id") != agent_id:
            raise ConsoleError(
                "CLAIM_TOKEN_BAD",
                "Claim token does not match.",
                status=403,
            )
        if claim.get("expires_at", 0) <= time.time():
            del claims[task_id]
            self._save(claims)
            raise ConsoleError(
                "CLAIM_EXPIRED",
                f"Claim for task {task_id} expired. Claim again.",
                status=410,
            )
        claim["expires_at"] = time.time() + CLAIM_TTL_SECONDS
        self._save(claims)
        return claim

    def release(self, task_id: str, agent_id: str, token: str) -> dict:
        """Release a claim before it expires. The task returns to queued."""
        claims = self._all()
        claim = claims.get(task_id)
        if claim is None:
            return {"task_id": task_id, "released": False}
        if claim.get("claim_token") != token or claim.get("agent_id") != agent_id:
            raise ConsoleError("CLAIM_TOKEN_BAD", "Claim token does not match.", status=403)
        del claims[task_id]
        self._save(claims)
        return {"task_id": task_id, "released": True}

    def release_all(self) -> list[str]:
        """Release every claim. The bridge calls this on kill and on
        power loss. On kill, all working tasks go to blocked with
        reason KILL_SWITCH, and all claims are released at once."""
        claims = self._all()
        released = list(claims.keys())
        self._save({})
        return released
