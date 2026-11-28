# Tool bodies and replay data. The bodies run only after the gate, so
# these tests check the work itself: a vault path cannot escape, shell
# is a fixed command with no metacharacters, scripts are called not
# exec'd, and a screen/speech id must exist in strings.json.
# No Pi, no key, no network, no real DeepSeek.
"""Tool runtime tests. Real bodies against temp vault and price files."""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import bridge, config, models, outbox, rules_engine, strings, tool_runtime
from si_console.errors import ToolError, VaultError
from si_console.guard import GuardState
from si_console.vault import TaskNote, create_task, new_task_body

DATA = Path(__file__).resolve().parent.parent / "data" / "market"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    (root / "tasks").mkdir(parents=True)
    monkeypatch.setattr(config, "VAULT_PATH", root)
    note = TaskNote(
        id="t-001",
        agent="execution",
        status="working",
        type="order",
        body=new_task_body("S.", "N.", "N.", []),
    )
    create_task(note)
    return root


# --- Vault paths ---------------------------------------------------------

def test_vault_read_accepts_both_spellings(vault):
    target = vault / "log" / "x.md"
    target.parent.mkdir()
    target.write_text("# x\n", encoding="utf-8")
    assert tool_runtime.vault_read({"path": "log/x.md"})["status"] == "read"
    assert tool_runtime.vault_read(
        {"path": "vault/si-console/log/x.md"}
    )["status"] == "read"


def test_vault_read_missing_is_not_an_error(vault):
    assert tool_runtime.vault_read({"path": "log/nope.md"})["status"] == "missing"


def test_vault_path_cannot_escape(vault):
    with pytest.raises(ToolError):
        tool_runtime.vault_read({"path": "../secret.md"})


def test_vault_write_rejects_invalid_task_note(vault):
    from si_console.vault import read_note

    with pytest.raises(ToolError):
        tool_runtime.vault_write(
            {"path": "tasks/t-001.md", "content": "not yaml"}, read_note("t-001")
        )
    assert "not yaml" not in (vault / "tasks" / "t-001.md").read_text(encoding="utf-8")


# --- Shell and scripts ---------------------------------------------------

def test_shell_run_allow_list(vault, monkeypatch):
    """Test the policy, not the Pi: stub the subprocess so the exact
    allow-listed command is verified on Windows too."""
    import subprocess

    seen = {}

    class Done:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["shell"] = kwargs["shell"]
        return Done()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = tool_runtime.shell_run(
        {"command": "vcgencmd get_throttled", "timeout_seconds": 10}
    )
    assert result["status"] == "ran"
    assert seen["argv"] == ["vcgencmd", "get_throttled"]
    assert seen["shell"] is False


def test_shell_run_rejects_unlisted(vault):
    from si_console.errors import GuardError

    with pytest.raises(GuardError):
        tool_runtime.shell_run({"command": "rm -rf /", "timeout_seconds": 10})


def test_shell_run_rejects_metacharacters(vault):
    from si_console.errors import GuardError

    with pytest.raises(GuardError):
        tool_runtime.shell_run(
            {"command": "vcgencmd get_throttled; echo x", "timeout_seconds": 10}
        )


def test_run_python_calls_rules_engine(vault):
    result = tool_runtime.run_python(
        {"script": "rules_engine", "args": {"date": "2022-06-15"}}
    )
    assert result["result"]["replay_date"] == "2022-06-15"
    assert len(result["result"]["proposed"]) <= config.REPLAY_MAX_SECTORS


def test_run_python_backtest_is_honest(vault):
    with pytest.raises(ToolError):
        tool_runtime.run_python({"script": "backtest", "args": {}})


# --- Replay rules come from config --------------------------------------

def test_rules_follow_config(monkeypatch):
    from datetime import date

    monkeypatch.setattr(config, "REPLAY_MAX_SECTORS", 1)
    monkeypatch.setattr(config, "REPLAY_CASH_RESERVE", 0.5)
    result = rules_engine.rank_sectors(date(2022, 6, 15))
    assert len(result["proposed"]) == 1
    assert result["proposed"][0]["weight"] == 0.5
    assert result["rules"]["cash_reserve"] == 0.5
    assert result["rules"]["rebalance"] == config.REPLAY_REBALANCE


def test_committed_market_data_is_sane():
    assert (DATA / "SPY.csv").is_file()
    assert (DATA / "XLK.csv").is_file()
    spy = rules_engine._read_prices("SPY", date(2023, 12, 31))
    assert len(spy) > 1000
    assert all(close > 0 for _, close in spy)
    assert [d for d, _ in spy] == sorted(d for d, _ in spy)


def test_no_lookahead_with_real_data(monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", DATA)
    replay = date(2020, 3, 16)
    result = rules_engine.rank_sectors(replay)
    assert result["replay_date"] == "2020-03-16"
    assert result["rules"]["price_only"] is True


# --- Prewritten screen and speech ----------------------------------------

def test_show_message_publishes_an_existing_id(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_PATH", tmp_path / "outbox.json")
    result = tool_runtime.show_message({"message_id": "status_ready", "lang": "en"})
    assert result["status"] == "shown"
    assert result["text"] == strings.resolve("status_ready", "en")
    assert outbox.drain()[0]["id"] == "status_ready"


def test_unknown_id_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTBOX_PATH", tmp_path / "outbox.json")
    with pytest.raises(ToolError):
        tool_runtime.speak_sentence({"sentence_id": "make_up_a_sentence", "lang": "en"})


def test_bridge_folds_outbox_into_state(tmp_path, monkeypatch):
    from si_console.state_store import StateStore

    monkeypatch.setattr(config, "OUTBOX_PATH", tmp_path / "outbox.json")
    store = StateStore(tmp_path / "state.json")
    monkeypatch.setattr(bridge, "state_store", store)
    outbox.publish("message", "status_ready", "zh")
    assert bridge.drain_outbox()[0]["id"] == "status_ready"
    assert store.read()["last_message_id"] == "status_ready"
    assert store.read()["last_message_lang"] == "zh"
    assert bridge.drain_outbox() == []
