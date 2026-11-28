# Approval handoff between two processes. The coordinator writes one
# small JSON file; the bridge polls it, lights the green button and
# waits for the physical press. The outcome comes back through the
# task note, because the vault is the truth. The file is deleted as
# soon as either side resolves it, so a stale request can never be
# approved. No agent tool can write this file: it lives outside the
# vault and only the coordinator calls this module.
#
# Why a file and not an HTTP call: the bridge is the only process that
# may touch GPIO, and the coordinator must keep running if the bridge
# is restarted. A file survives a restart; an in-memory call does not.
# The file is written atomically (temp file, then os.replace), so the
# bridge never reads half a request.
"""Approval request file shared by the coordinator and the bridge."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from si_console import config

# How often the coordinator checks the note while it waits. The bridge
# polls the request file at the same rate. 150 ms is well under the
# 100 ms kill poll budget plus one scan, and still invisible to a
# person at the button.
POLL_SECONDS = 0.15


def request_path() -> Path:
    """The current request file. Read at call time so tests can point
    config.APPROVAL_PATH at a temp folder."""
    return Path(config.APPROVAL_PATH)


def command_for(tool: str, args: dict) -> str:
    """A short, human readable line for the screen. Never a secret.

    The screen must show exactly what will run, not a paraphrase. For
    shell_run that is the command itself. For other tools it is the
    tool name plus the arguments that matter.
    """
    if tool == "shell_run":
        return str(args.get("command", ""))
    if tool == "vault_write":
        return f"write {args.get('path', '')}"
    if tool == "make_slides":
        return f"make slides: {args.get('title', '')}"
    if tool == "update_task_status":
        return f"set {args.get('task_id', '')} to {args.get('status', '')}"
    try:
        rendered = json.dumps(args, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        rendered = "{}"
    return f"{tool} {rendered}"


def _write_atomic(data: dict) -> None:
    target = request_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_request(task_id: str, tool: str, args: dict, command: str = "") -> dict:
    """Write one pending approval request. Overwrites an older one, so
    one task can never have two live proposals."""
    request = {
        "task_id": task_id,
        "tool": tool,
        "args": args,
        "command": command or command_for(tool, args),
        "requested_at": time.time(),
        "requested_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _write_atomic(request)
    return request


def read_request() -> dict:
    """The pending request, or {} when there is none. A corrupt file is
    treated as no request, so it can never be approved by accident."""
    try:
        data = json.loads(request_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or not data.get("task_id"):
        return {}
    return data


def clear_request(task_id: str = "") -> bool:
    """Delete the request. With a task id, only delete a request that
    belongs to that task, so one task cannot clear another's request.
    Missing or already deleted is not an error."""
    target = request_path()
    if not target.exists():
        return False
    if task_id:
        current = read_request()
        if current and current.get("task_id") != task_id:
            return False
    try:
        target.unlink()
    except OSError:
        return False
    return True


def is_expired(request: dict, now: float | None = None, timeout: int | None = None) -> bool:
    """True when the request is older than the approval timeout. A
    request with no usable timestamp counts as expired (fail closed)."""
    try:
        requested = float(request.get("requested_at", 0))
    except (TypeError, ValueError):
        return True
    limit = config.APPROVAL_TIMEOUT_SECONDS if timeout is None else timeout
    current = time.time() if now is None else now
    return current - requested >= limit
