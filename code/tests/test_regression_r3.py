# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton tests. Reference only. Not for Fallen submission.
# Regression tests for five R3 bugs found in review:
# 1. The coordinator's __main__ block sat before pick_next_task and
#    stuck_watchdog, so python -m si_console.coordinator crashed in a
#    systemd restart loop.
# 2. stuck_watchdog used timezone.utc without importing timezone.
# 3. bridge.on_kill release wrote kill_active=True, so the screens
#    showed KILL ACTIVE forever after the switch came off.
# 4. _escalate created its note with status queued (create_task forced
#    it), so the queue re-ran escalation notes and burned API credit.
# 5. serve_forever never refreshed GuardState, so a kill never reached
#    the coordinator loop.
# No Pi, no keys, no network. Mocked model and temp folders only.
"""Regression tests for the R3 review bugs."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config, models
from si_console import coordinator
from si_console.coordinator import pick_next_task, run_task, stuck_watchdog
from si_console.guard import GuardState
from si_console.state_store import StateStore
from si_console.vault import (
    TaskNote,
    VaultError,
    create_task,
    new_task_body,
    read_note,
    update_status,
)

COORDINATOR_SRC = (
    Path(__file__).resolve().parent.parent / "si_console" / "coordinator.py"
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


# --- Bug 1: __main__ block position --------------------------------------

def test_main_block_is_after_the_functions_it_calls():
    """python -m si_console.coordinator must not NameError at import.

    serve_forever() calls pick_next_task and stuck_watchdog. If the
    __main__ block runs before those defs, the service crash-loops.
    """
    source = COORDINATOR_SRC.read_text(encoding="utf-8")
    main_at = source.find('if __name__ == "__main__":')
    assert main_at != -1, "coordinator has no __main__ block"
    assert source.count('if __name__ == "__main__":') == 1
    assert main_at > source.find("def pick_next_task(")
    assert main_at > source.find("def stuck_watchdog(")
    assert main_at > source.find("def serve_forever(")


# --- Bug 2: stuck_watchdog timezone import -------------------------------

def test_stuck_watchdog_blocks_stale_task(vault):
    """A task working for more than 300s becomes blocked with STUCK."""
    _make_task()
    update_status("2026-12-01-signal-001", "working")
    # Backdate updated. write_note stamps now, so render the note and
    # write the file directly to control the timestamp.
    stale = read_note("2026-12-01-signal-001")
    stale.updated = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat()
    target = vault / "tasks" / "2026-12-01-signal-001.md"
    target.write_text(stale.render(), encoding="utf-8")

    blocked = stuck_watchdog(GuardState())

    assert blocked == ["2026-12-01-signal-001"]
    assert read_note("2026-12-01-signal-001").status == "blocked"


def test_stuck_watchdog_leaves_fresh_task_alone(vault):
    """A task updated 10s ago is not stuck. No exception either."""
    _make_task()
    update_status("2026-12-01-signal-001", "working")

    blocked = stuck_watchdog(GuardState())

    assert blocked == []
    assert read_note("2026-12-01-signal-001").status == "working"


# --- Bug 3: kill release state -------------------------------------------

def test_kill_release_clears_state(vault, tmp_path, monkeypatch):
    """on_kill(False) must write kill_active False, not True."""
    from si_console import bridge
    from si_console.state_store import ClaimStore

    monkeypatch.setattr(
        bridge, "state_store", StateStore(tmp_path / "state.json")
    )
    monkeypatch.setattr(
        bridge, "claim_store", ClaimStore(tmp_path / "claims.json")
    )

    bridge.on_kill(True)
    assert bridge.state_store.read()["kill_active"] is True

    bridge.on_kill(False)
    assert bridge.state_store.read()["kill_active"] is False


# --- Bug 4: escalation notes must not be re-run --------------------------

def test_escalation_note_is_blocked(vault, monkeypatch):
    """_escalate writes its note as blocked, never queued."""
    _make_task()

    def fake_complete(*args, **kwargs):
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    result = run_task("2026-12-01-signal-001", GuardState())

    assert result.reason_code == "BAD_OUTPUT"
    escalation = read_note("2026-12-01-signal-001-escalate")
    assert escalation.status == "blocked"


def test_escalation_note_is_not_picked_up(vault, monkeypatch):
    """After an escalation the queue is empty. No escalation loop,
    no repeated DeepSeek calls, no burn of the daily cost cap."""
    _make_task()

    def fake_complete(*args, **kwargs):
        return _reply()

    monkeypatch.setattr(models, "complete", fake_complete)
    run_task("2026-12-01-signal-001", GuardState())

    assert pick_next_task() is None


def test_create_task_rejects_bad_initial_status(vault):
    """initial_status is validated against the frontmatter statuses."""
    note = TaskNote(
        id="2026-12-01-signal-002",
        agent="signal",
        status="queued",
        type="signal",
        body=new_task_body(
            summary="Bad status test.",
            numbers="None.",
            next_step="None.",
            deps=[],
        ),
    )
    with pytest.raises(VaultError):
        create_task(note, initial_status="escalated")


def test_create_task_default_is_still_queued(vault):
    """Normal proposals keep the old behaviour: queued on create."""
    _make_task()
    assert read_note("2026-12-01-signal-001").status == "queued"


# --- Bug 5: serve_forever must see a kill --------------------------------

def test_serve_forever_skips_when_killed(vault, tmp_path, monkeypatch):
    """With kill active in state.json the loop must not pick up or
    run a task. It waits instead, and fails closed if state.json
    cannot be read."""
    _make_task()
    calls = {"picked": 0, "ran": 0}

    monkeypatch.setattr(
        coordinator,
        "state_store",
        StateStore(tmp_path / "state.json"),
    )
    coordinator.state_store.write({"kill_active": True})

    def fake_pick():
        calls["picked"] += 1
        return None

    def fake_run(*args, **kwargs):
        calls["ran"] += 1

    monkeypatch.setattr(coordinator, "pick_next_task", fake_pick)
    monkeypatch.setattr(coordinator, "run_task", fake_run)

    class StopLoop(Exception):
        pass

    def fake_sleep(seconds):
        raise StopLoop

    monkeypatch.setattr(coordinator.time, "sleep", fake_sleep)

    with pytest.raises(StopLoop):
        coordinator.serve_forever()

    assert calls["picked"] == 0
    assert calls["ran"] == 0


def test_serve_forever_fails_closed_on_unreadable_state(vault, tmp_path, monkeypatch):
    """A state.json that raises on read counts as killed, not clear."""
    calls = {"picked": 0}

    class BrokenStore:
        def read(self):
            raise OSError("disk gone")

    monkeypatch.setattr(coordinator, "state_store", BrokenStore())

    def fake_pick():
        calls["picked"] += 1
        return None

    monkeypatch.setattr(coordinator, "pick_next_task", fake_pick)

    class StopLoop(Exception):
        pass

    def fake_sleep(seconds):
        raise StopLoop

    monkeypatch.setattr(coordinator.time, "sleep", fake_sleep)

    with pytest.raises(StopLoop):
        coordinator.serve_forever()

    assert calls["picked"] == 0
