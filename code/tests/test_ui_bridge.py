# Read-only UI bridge tests. The snapshot is built from real files,
# not fixtures; the tests prove that the approval command reaches the
# screen, that a bad source yields offline, and that no write route
# was added. No Pi, no key, no browser.
"""UI snapshot and endpoint tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import approval, bridge, config, ui_snapshot
from si_console.state_store import StateStore
from si_console.vault import TaskNote, create_task, new_task_body

MARKUP = Path(__file__).resolve().parent.parent / "dashboard" / "mockups"


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    (root / "tasks").mkdir(parents=True)
    monkeypatch.setattr(config, "VAULT_PATH", root)
    monkeypatch.setattr(config, "APPROVAL_PATH", tmp_path / "approval.json")
    monkeypatch.setattr(config, "APPROVAL_TIMEOUT_SECONDS", 120)
    store = StateStore(tmp_path / "state.json")
    monkeypatch.setattr(bridge, "state_store", store)
    note = TaskNote(
        id="t-001",
        agent="execution",
        status="working",
        type="order",
        ticker="XLK",
        amount=2000,
        risk_check="pass",
        body=new_task_body("S.", "N.", "N.", []),
    )
    create_task(note)
    from si_console.vault import update_status

    update_status("t-001", "working")
    return store


def test_ready_snapshot(env):
    env.update(current_task_id="t-001", current_status="working", mode="booth")
    snap = ui_snapshot.build(env)
    assert snap["console_state"] == "ui_w_working"
    assert snap["agents"]["a2"] == "working"
    assert snap["approval"] is None
    assert snap["cost"]["cap"] == config.DEEPSEEK_DAILY_CAP_USD


def test_approval_command_reaches_the_screen(env):
    env.update(current_task_id="t-001", approval_pending=True)
    request = approval.write_request("t-001", "shell_run", {"command": "ls -l"})
    snap = ui_snapshot.build(env, request)
    assert snap["approval"] is not None
    assert snap["approval"]["command"] == "ls -l"
    assert snap["approval"]["task_id"] == "t-001"
    assert snap["approval"]["secondsLeft"] <= 120
    assert snap["approval"]["verdict"] == "ui_guard_pass"
    assert snap["console_state"] == "ui_w_waiting"


def test_kill_overrides_approval(env):
    env.update(current_task_id="t-001", approval_pending=True, kill_active=True)
    request = approval.write_request("t-001", "shell_run", {"command": "ls"})
    snap = ui_snapshot.build(env, request)
    assert snap["console_state"] == "ui_w_frozen"
    assert snap["approval"] is None
    assert all(v == "off" for v in snap["agents"].values())


def test_vault_error_is_offline(env):
    env.update(last_error="VAULT ERROR")
    snap = ui_snapshot.build(env)
    assert snap["console_state"] == "ui_w_offline"
    assert snap["faults"]["vault"] is True


def test_bad_snapshot_is_offline(env):
    from si_console.vault import VaultError

    def bad(*args, **kwargs):
        raise VaultError("no_vault", "gone")

    import si_console.ui_snapshot as mod

    original = mod.list_tasks
    mod.list_tasks = bad
    try:
        assert ui_snapshot.build(env)["console_state"] == "offline"
    finally:
        mod.list_tasks = original


def test_ui_state_endpoint_is_loopback_and_read_only(monkeypatch):
    from fastapi.testclient import TestClient

    client = TestClient(bridge.app)
    res = client.get("/api/ui/state")
    assert res.status_code == 200
    assert "console_state" in res.json()
    for method in ("post", "put", "patch", "delete"):
        assert getattr(client, method)("/api/ui/state").status_code in (405, 404)


def test_static_pages_are_served():
    from fastapi.testclient import TestClient

    client = TestClient(bridge.app)
    assert client.get("/ui/mini.html").status_code == 200
    assert client.get("/ui/js/live.js").status_code == 200
    assert client.get("/api/ui/health").json()["status"] == "ok"


def test_live_pages_include_adapter():
    for name in ("mini.html", "monitor.html"):
        text = (MARKUP / name).read_text(encoding="utf-8")
        assert "js/live.js" in text
