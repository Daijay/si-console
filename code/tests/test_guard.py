# GUARD is new code, so these tests are new too. They check the four
# rules in guard.py: kill blocks everything, a role cannot call a
# tool outside its list, a NEEDS APPROVAL tool needs a human approval,
# and an order that already filled never fills twice.
# Run with: cd scratch && python3 -m pytest tests/test_guard.py -v
# No Pi needed. No API key needed.
"""GUARD tests. Kill, role, approval, and double fill rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console.errors import GuardError
from si_console.guard import GuardState, check_order_execution, check_shell_command, check_tool
from si_console.vault import TaskNote


def _task(**overrides):
    fields = {
        "id": "2026-12-01-order-001",
        "agent": "execution",
        "status": "working",
        "type": "order",
        "risk_check": "pass",
        "approved_by": "human",
        "approved_at": "2026-12-01T10:00:00+00:00",
        "executed_at": "",
    }
    fields.update(overrides)
    return TaskNote(**fields)


def test_kill_blocks_every_tool():
    state = GuardState(kill_active=True)
    with pytest.raises(GuardError) as exc:
        check_tool("vault_read", "SAFE", "coordinator", {"vault_read"}, state)
    assert exc.value.code == "GUARD_BLOCK"


def test_role_cannot_call_outside_its_list():
    state = GuardState()
    with pytest.raises(GuardError):
        check_tool("shell_run", "NEEDS APPROVAL", "coordinator", {"vault_read"}, state)


def test_needs_approval_without_approval_is_blocked():
    state = GuardState(approval_pending=False, approved_by="")
    with pytest.raises(GuardError):
        check_tool("make_slides", "NEEDS APPROVAL", "execution", {"make_slides"}, state)


def test_needs_approval_with_human_approval_passes():
    state = GuardState(approval_pending=True, approved_by="human")
    check_tool("make_slides", "NEEDS APPROVAL", "execution", {"make_slides"}, state)


def test_approval_by_non_human_is_blocked():
    state = GuardState(approval_pending=True, approved_by="agent")
    with pytest.raises(GuardError):
        check_tool("make_slides", "NEEDS APPROVAL", "execution", {"make_slides"}, state)


def test_failed_risk_check_blocks_order_tool():
    state = GuardState(approval_pending=True, approved_by="human")
    task = _task(risk_check="fail", risk_reason="MAX_SECTOR")
    with pytest.raises(GuardError):
        check_tool("make_slides", "NEEDS APPROVAL", "execution", {"make_slides"}, state, task)


def test_order_execution_passes_when_approved():
    state = GuardState()
    check_order_execution(_task(), state)


def test_order_execution_blocked_without_approval():
    state = GuardState()
    with pytest.raises(GuardError):
        check_order_execution(_task(approved_by="", approved_at=""), state)


def test_order_execution_blocked_when_already_filled():
    state = GuardState()
    with pytest.raises(GuardError):
        check_order_execution(_task(executed_at="2026-12-01T10:05:00+00:00"), state)


def test_order_execution_blocked_on_kill():
    state = GuardState(kill_active=True)
    with pytest.raises(GuardError):
        check_order_execution(_task(), state)


def test_shell_allow_list():
    check_shell_command("vcgencmd get_throttled")
    check_shell_command("python3 rules_engine.py 2022-06-15")
    with pytest.raises(GuardError) as exc:
        check_shell_command("rm -rf /")
    assert exc.value.code == "SHELL_DENY"
    with pytest.raises(GuardError):
        check_shell_command("curl https://example.com")
    with pytest.raises(GuardError):
        check_shell_command("pip install requests")
