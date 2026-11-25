# These tests check the coordinator validation, the tool registry,
# the voice matcher, and the rules engine lookahead rule. None of
# them calls DeepSeek. None needs a Pi. None needs an API key.
# Run with: cd scratch && python3 -m pytest tests/test_coordinator_validation.py -v
"""Coordinator validation, tools, voice, and rules engine tests."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config
from si_console.coordinator import validate_action
from si_console.errors import ToolError
from si_console.rules_engine import _read_prices, rank_sectors
from si_console.tools import (
    TOOLS,
    tool_names_for_role,
    tools_for_role,
    validate_tool_call,
)
from si_console.vault import TaskNote
from si_console.voice_intents import match_intent


def _task():
    return TaskNote(
        id="2026-12-01-signal-001",
        agent="signal",
        status="queued",
        type="signal",
    )


def test_bad_action_is_rejected():
    with pytest.raises(ToolError) as exc:
        validate_action({"action": "delete_everything"}, _task())
    assert exc.value.code == "BAD_ACTION"


def test_bad_ticker_is_rejected():
    with pytest.raises(ToolError) as exc:
        validate_action(
            {"action": "create_task", "task_id": "x", "ticker": "GME", "amount": 100},
            _task(),
        )
    assert exc.value.code == "BAD_TICKER"


def test_bad_amount_is_rejected():
    with pytest.raises(ToolError) as exc:
        validate_action(
            {"action": "create_task", "task_id": "x", "ticker": "XLK", "amount": -5},
            _task(),
        )
    assert exc.value.code == "BAD_AMOUNT"


def test_tool_registry_has_all_arch_tools():
    # Tool names are copied exactly from ARCHITECTURE.md section 5.
    for name in (
        "vault_read", "vault_write", "vault_list", "shell_run", "run_python",
        "web_search", "fetch_url", "create_task_note", "update_task_status",
        "read_portfolio", "make_slides", "speak_sentence", "show_message",
    ):
        assert name in TOOLS, f"missing tool {name}"
    assert TOOLS["shell_run"].tag == "NEEDS APPROVAL"
    assert TOOLS["web_search"].tag == "SAFE"
    assert TOOLS["make_slides"].tag == "NEEDS APPROVAL"


def test_tool_names_for_role_returns_tool_names():
    # Regression test. The coordinator once passed Tool.roles to
    # GUARD, which holds role names, not tool names. Every tool call
    # was blocked. This helper must return tool names.
    names = tool_names_for_role("coordinator")
    assert "vault_read" in names
    assert "vault_write" in names
    assert "shell_run" not in names
    assert "make_slides" not in names
    assert "coordinator" not in names
    assert "signal" not in names


def test_coordinator_has_no_shell_tool():
    names = {t["function"]["name"] for t in tools_for_role("coordinator")}
    assert "shell_run" not in names
    assert "make_slides" not in names
    assert "vault_read" in names


def test_validate_tool_call_missing_field():
    with pytest.raises(ToolError) as exc:
        validate_tool_call("web_search", {"query": "2022 bear market"})
    assert exc.value.code == "BAD_SCHEMA"


def test_validate_tool_call_bad_ticker():
    with pytest.raises(ToolError) as exc:
        validate_tool_call(
            "create_task_note",
            {"task_id": "x", "agent": "signal", "type": "signal",
             "summary": "s", "ticker": "GME"},
        )
    assert exc.value.code == "BAD_TICKER"


def test_validate_tool_call_slide_path_outside_vault():
    with pytest.raises(ToolError):
        validate_tool_call(
            "make_slides",
            {"title": "t", "bullets": ["a"], "slide_count": 1,
             "lang": "en", "output_path": "/tmp/deck.pptx"},
        )


def test_voice_propose_english():
    result = match_intent("buy XLK")
    assert result["intent"] == "propose_sector_move"
    assert result["ticker"] == "XLK"
    assert result["direction"] == "buy"


def test_voice_propose_chinese():
    result = match_intent("买入 XLK")
    assert result["intent"] == "propose_sector_move"
    assert result["ticker"] == "XLK"


def test_voice_question_is_not_an_intent():
    result = match_intent("should I buy XLK?")
    assert result["intent"] == "unknown"


def test_voice_negation_is_not_an_intent():
    result = match_intent("do not buy XLK")
    assert result["intent"] == "unknown"


def test_voice_unknown_is_unknown():
    result = match_intent("tell me a joke about penguins")
    assert result["intent"] == "unknown"
    assert result["sentence_id"] == "did_not_understand"


def test_rules_engine_never_uses_future_data(tmp_path, monkeypatch):
    """The lookahead test. XLK jumps after the replay date. The
    engine must not see it. If it ever reads a future close, this
    test must fail."""
    data_dir = tmp_path / "market"
    data_dir.mkdir()
    monkeypatch.setattr(config, "DATA_DIR", data_dir)
    rows = "\n".join(
        ["date,close"]
        + [f"2022-01-{d:02d},100" for d in range(3, 28)]
        + ["2022-02-01,100", "2022-02-02,100"]
    )
    (data_dir / "SPY.csv").write_text(rows)
    # XLK is flat up to the replay date, then jumps to 200 after it.
    xlk = "\n".join(
        ["date,close"]
        + [f"2022-01-{d:02d},100" for d in range(3, 28)]
        + ["2022-02-01,100", "2022-02-02,200", "2022-02-03,200"]
    )
    (data_dir / "XLK.csv").write_text(xlk)
    for ticker in (
        "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLB", "XLU", "XLRE", "XLC",
    ):
        (data_dir / f"{ticker}.csv").write_text(rows)
    replay = date(2022, 2, 1)
    prices = _read_prices("XLK", replay)
    assert all(day <= replay for day, _ in prices)
    assert max(close for _, close in prices) == 100
    result = rank_sectors(replay)
    assert result["replay_date"] == "2022-02-01"
    assert result["rules"]["price_only"] is True
