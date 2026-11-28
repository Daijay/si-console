# These tests run the coordinator loop with a mocked DeepSeek. No
# test calls the real DeepSeek API. No test needs a Pi or a key.
# The vault is a temp folder. The model is a fake function that
# returns fixed replies. The tests check the loop rules: kill stops
# everything, 3 rounds then escalate, bad output escalates, and a
# NEEDS APPROVAL tool pauses for the green button.
# Run with: cd scratch && python3 -m pytest tests/test_coordinator_loop.py -v
"""Coordinator loop tests. Mocked DeepSeek, temp vault."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config, coordinator, models
from si_console.coordinator import run_task
from si_console.errors import ModelError
from si_console.guard import GuardState
from si_console.vault import (
    TaskNote,
    create_task,
    new_task_body,
    read_note,
    update_status,
)


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """Point the vault at a temp folder. Returns the folder."""
    root = tmp_path / "vault"
    (root / "tasks").mkdir(parents=True)
    monkeypatch.setattr(config, "VAULT_PATH", root)
    return root


def _make_task(task_id="2026-12-01-signal-001"):
    note = TaskNote(
        id=task_id,
        agent="signal",
        status="queued",
        type="signal",
        body=new_task_body(
            summary="Test signal task.",
            numbers="No prices in this test.",
            next_step="Rank the sectors.",
            deps=[],
        ),
    )
    create_task(note)
    update_status(task_id, "working")
    return note


def _reply(tool_calls=None, data=None):
    return models.ModelReply(
        text="",
        tier="coordinator",
        provider="deepseek",
        model="deepseek-flash",
        input_tokens=10,
        output_tokens=5,
        data=data,
        tool_calls=tool_calls,
    )


def _tool_call(name, args):
    import json

    return {"function": {"name": name, "arguments": json.dumps(args)}}


def test_kill_active_stops_before_any_model_call(vault, monkeypatch):
    _make_task()
    calls = []

    def fake_complete(*args, **kwargs):
        calls.append(1)
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState(kill_active=True))
    assert result.done is False
    assert result.rounds_used == 0
    assert result.reason_code == "KILL_SWITCH"
    assert calls == []


def test_three_rounds_then_round_limit(vault, monkeypatch):
    _make_task()
    calls = []

    def fake_complete(*args, **kwargs):
        calls.append(1)
        return _reply(
            tool_calls=[
                _tool_call(
                    "vault_read", {"path": "vault/si-console/tasks/x.md"}
                )
            ]
        )

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState())
    assert result.rounds_used == 3
    assert result.reason_code == "ROUND_LIMIT"
    assert len(calls) == 3
    task = read_note("2026-12-01-signal-001")
    assert task.status == "blocked"
    assert task.risk_reason == "ROUND_LIMIT"


def test_no_tool_call_escalates_bad_output(vault, monkeypatch):
    _make_task()

    def fake_complete(*args, **kwargs):
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState())
    assert result.rounds_used == 1
    assert result.reason_code == "BAD_OUTPUT"
    task = read_note("2026-12-01-signal-001")
    assert task.status == "blocked"


def test_needs_approval_tool_waits_then_times_out(vault, monkeypatch):
    """A NEEDS APPROVAL tool no longer logs a pause and moves on. It
    waits for the note, and with no green press it blocks the task
    with HUMAN_TIMEOUT and never runs the tool."""
    _make_task()
    calls = [0]

    def fake_complete(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 1:
            return _reply(
                tool_calls=[
                    _tool_call(
                        "vault_write",
                        {
                            "path": "vault/si-console/tasks/x.md",
                            "content": "draft",
                        },
                    )
                ]
            )
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    # Fake clock: each poll advances a minute, so 120 s expires fast.
    clock = [0.0]
    monkeypatch.setattr(coordinator, "_monotonic", lambda: clock[0])
    monkeypatch.setattr(
        coordinator, "_sleep", lambda seconds: clock.__setitem__(0, clock[0] + 60)
    )
    result = run_task("2026-12-01-signal-001", GuardState())
    assert any("approval timeout for vault_write" in line for line in result.log_lines)
    assert not any("ran vault_write" in line for line in result.log_lines)
    assert result.reason_code == "HUMAN_TIMEOUT"
    task = read_note("2026-12-01-signal-001")
    assert task.status == "blocked"
    assert task.risk_reason == "HUMAN_TIMEOUT"


def test_model_error_retries_once_then_escalates(vault, monkeypatch):
    _make_task()
    monkeypatch.setattr(
        "si_console.coordinator.time.sleep", lambda seconds: None
    )
    calls = [0]

    def fake_complete(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 1:
            raise ModelError("DeepSeek timed out.", status=504)
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState())
    assert calls[0] == 2
    assert result.rounds_used == 2
    assert result.reason_code == "BAD_OUTPUT"


def test_bad_tool_call_is_rejected_and_round_continues(vault, monkeypatch):
    _make_task()
    calls = [0]

    def fake_complete(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 1:
            # Unknown tool. The whole reply is discarded, never partly run.
            return _reply(tool_calls=[_tool_call("delete_everything", {})])
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState())
    assert calls[0] == 2
    assert result.reason_code == "BAD_OUTPUT"


def test_guard_block_is_a_rejected_round_not_a_crash(vault, monkeypatch):
    # The signal role may not call shell_run, which belongs to
    # execution. GUARD blocks it before any approval request. The loop
    # must treat the block as a rejected round and continue, not crash.
    # This caught a real bug: the coordinator passed tool.roles to
    # GUARD, which blocked every tool call.
    _make_task()
    calls = [0]

    def fake_complete(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 1:
            return _reply(
                tool_calls=[
                    _tool_call(
                        "shell_run",
                        {"command": "vcgencmd get_throttled", "timeout_seconds": 10},
                    )
                ]
            )
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState())
    assert any("GUARD_BLOCK" in line for line in result.log_lines)
    assert result.reason_code == "BAD_OUTPUT"
    assert result.rounds_used == 2
