# Step 1 of the software plan: the approval gate. The coordinator and
# the bridge are separate processes, so the request travels as a small
# JSON file and the outcome travels through the task note. These tests
# prove the three hard rules: no green, no run; red never runs; expiry
# never runs. No Pi, no key, no network.
"""Approval gate tests. Coordinator wait, bridge poll, timeout, restart."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import approval, bridge, config, coordinator, models
from si_console.guard import GuardState
from si_console.state_store import ClaimStore, StateStore
from si_console.vault import (
    TaskNote,
    create_task,
    new_task_body,
    read_note,
    update_status,
)

WRITE_ARGS = {"path": "vault/si-console/log/approval-test.md", "content": "# Draft\n\nWritten by the approval gate test."}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Temp vault, state, claims and bridge globals for every test."""
    root = tmp_path / "vault"
    (root / "tasks").mkdir(parents=True)
    monkeypatch.setattr(config, "VAULT_PATH", root)
    monkeypatch.setattr(config, "APPROVAL_TIMEOUT_SECONDS", 120)
    store = StateStore(tmp_path / "state.json")
    monkeypatch.setattr(coordinator, "state_store", store)
    monkeypatch.setattr(bridge, "state_store", store)
    monkeypatch.setattr(bridge, "claim_store", ClaimStore(tmp_path / "claims.json"))
    for name, value in (
        ("kill_active", False),
        ("resume_required", False),
        ("approval_pending", False),
        ("approval_task_id", ""),
    ):
        monkeypatch.setattr(bridge, name, value)
    return root


def _task(task_id="t-001", agent="coordinator", status="working", approved_by=""):
    note = TaskNote(
        id=task_id,
        agent=agent,
        status="queued",
        type="order",
        body=new_task_body("Test.", "None.", "Next.", []),
    )
    create_task(note)
    if status != "queued" or approved_by:
        update_status(task_id, status, approved_by=approved_by)
    return read_note(task_id)


def _call(name, args):
    return {"function": {"name": name, "arguments": json.dumps(args)}}


def _clock(monkeypatch, step=0.15, on_sleep=None):
    """Fake monotonic clock and sleep. on_sleep runs after each poll,
    so a test can simulate a green press, a red press or a kill."""
    now = [0.0]

    def fake_monotonic():
        return now[0]

    def fake_sleep(seconds):
        now[0] += step
        if on_sleep is not None:
            on_sleep()

    monkeypatch.setattr(coordinator, "_monotonic", fake_monotonic)
    monkeypatch.setattr(coordinator, "_sleep", fake_sleep)
    return now


# --- Coordinator side ----------------------------------------------------

def test_green_press_runs_tool_once(env, monkeypatch):
    _task()
    approved = [0]

    def on_sleep():
        if not approved[0]:
            approved[0] += 1
            update_status("t-001", "working", approved_by="human")

    _clock(monkeypatch, on_sleep=on_sleep)
    log: list = []
    coordinator._run_one_tool_call(
        _call("vault_write", WRITE_ARGS), read_note("t-001"), GuardState(), log
    )
    assert log.count("ran vault_write") == 1
    assert read_note("t-001").approved_by == "human"
    assert approval.read_request() == {}


def test_red_press_never_runs_tool(env, monkeypatch):
    _task()

    def on_sleep():
        update_status("t-001", "blocked", "HUMAN_REJECT")

    _clock(monkeypatch, on_sleep=on_sleep)
    log: list = []
    coordinator._run_one_tool_call(
        _call("vault_write", WRITE_ARGS), read_note("t-001"), GuardState(), log
    )
    assert not any(line.startswith("ran ") for line in log)
    assert any("approval rejected for vault_write" in line for line in log)
    assert read_note("t-001").status == "blocked"


def test_timeout_never_runs_tool(env, monkeypatch):
    _task()
    _clock(monkeypatch, step=60)
    log: list = []
    coordinator._run_one_tool_call(
        _call("vault_write", WRITE_ARGS), read_note("t-001"), GuardState(), log
    )
    assert not any(line.startswith("ran ") for line in log)
    assert any("approval timeout for vault_write" in line for line in log)
    note = read_note("t-001")
    assert note.status == "blocked"
    assert note.risk_reason == "HUMAN_TIMEOUT"
    assert approval.read_request() == {}


def test_kill_during_wait_aborts(env, monkeypatch):
    _task()
    killed = [0]

    def on_sleep():
        if not killed[0]:
            killed[0] += 1
            coordinator.state_store.update(kill_active=True)

    _clock(monkeypatch, on_sleep=on_sleep)
    log: list = []
    coordinator._run_one_tool_call(
        _call("vault_write", WRITE_ARGS), read_note("t-001"), GuardState(), log
    )
    assert not any(line.startswith("ran ") for line in log)
    assert any("approval killed for vault_write" in line for line in log)
    assert approval.read_request() == {}


def test_already_approved_task_skips_the_press(env):
    _task(approved_by="human")
    log: list = []
    coordinator._run_one_tool_call(
        _call("vault_write", WRITE_ARGS), read_note("t-001"), GuardState(), log
    )
    assert log.count("ran vault_write") == 1
    assert approval.read_request() == {}


def test_run_task_green_end_to_end(env, monkeypatch):
    _task()
    calls = [0]

    def fake_complete(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 1:
            return models.ModelReply(
                text="",
                tier="coordinator",
                provider="deepseek",
                model="test",
                input_tokens=1,
                output_tokens=1,
                tool_calls=[_call("vault_write", WRITE_ARGS)],
            )
        return models.ModelReply(
            text="",
            tier="coordinator",
            provider="deepseek",
            model="test",
            input_tokens=1,
            output_tokens=1,
        )

    monkeypatch.setattr(models, "complete", fake_complete)
    approved = [0]

    def on_sleep():
        if not approved[0]:
            approved[0] += 1
            update_status("t-001", "working", approved_by="human")

    _clock(monkeypatch, on_sleep=on_sleep)
    result = coordinator.run_task("t-001", GuardState())
    assert any("ran vault_write" in line for line in result.log_lines)
    assert approval.read_request() == {}


# --- Bridge side ---------------------------------------------------------

def test_bridge_expiry_blocks_task(env):
    _task()
    request = approval.write_request("t-001", "shell_run", {"command": "ls"}, "ls")
    result = bridge.poll_approval(now=request["requested_at"] + 121)
    assert result["status"] == "expired"
    note = read_note("t-001")
    assert note.status == "blocked"
    assert note.risk_reason == "HUMAN_TIMEOUT"
    assert approval.read_request() == {}
    # A late green press must not revive the timed out task.
    assert bridge.on_green_press()["status"] == "ignored"


def test_bridge_restart_restores_pending(env):
    _task()
    approval.write_request("t-001", "vault_write", WRITE_ARGS)
    bridge.approval_pending = False
    bridge.approval_task_id = ""
    bridge.VaultWatcher(env).rebuild_state()
    assert bridge.approval_pending is True
    assert bridge.approval_task_id == "t-001"
    assert bridge.state_store.read().get("approval_pending") is True


def test_green_press_approves_one_task_only(env):
    _task()
    approval.write_request("t-001", "vault_write", WRITE_ARGS)
    assert bridge.poll_approval()["status"] == "pending"
    assert bridge.on_green_press()["status"] == "approved"
    assert read_note("t-001").approved_by == "human"
    assert approval.read_request() == {}
    assert bridge.on_green_press()["status"] == "ignored"


def test_kill_clears_request_and_blocks_task(env):
    _task()
    approval.write_request("t-001", "vault_write", WRITE_ARGS)
    bridge.poll_approval()
    bridge.on_kill(True)
    assert approval.read_request() == {}
    note = read_note("t-001")
    assert note.status == "blocked"
    assert note.risk_reason == "KILL_SWITCH"
    assert bridge.on_green_press()["status"] == "ignored"


def test_request_for_blocked_task_is_discarded(env):
    _task(status="blocked")
    approval.write_request("t-001", "vault_write", WRITE_ARGS)
    assert bridge.poll_approval()["status"] == "ignored"
    assert approval.read_request() == {}
    assert bridge.approval_pending is False


def test_clear_request_is_task_scoped(env):
    approval.write_request("t-001", "vault_write", WRITE_ARGS)
    assert approval.clear_request("t-002") is False
    assert approval.read_request()["task_id"] == "t-001"


def test_corrupt_request_fails_closed(env):
    approval.request_path().write_text("{not json", encoding="utf-8")
    assert approval.read_request() == {}
    assert bridge.poll_approval()["status"] == "none"


def test_unreadable_task_never_runs(env, monkeypatch):
    _task()
    note = read_note("t-001")
    (env / "tasks" / "t-001.md").unlink()
    log: list = []
    coordinator._run_one_tool_call(
        _call("vault_write", WRITE_ARGS), note, GuardState(), log
    )
    assert not any(line.startswith("ran ") for line in log)
    assert any("task unreadable" in line for line in log)
    assert approval.read_request() == {}


def test_command_is_shown_verbatim():
    assert approval.command_for("shell_run", {"command": "vcgencmd get_throttled"}) == (
        "vcgencmd get_throttled"
    )
    assert approval.command_for("vault_write", {"path": "vault/si-console/tasks/x.md"}) == (
        "write vault/si-console/tasks/x.md"
    )
