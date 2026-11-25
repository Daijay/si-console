# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# GUARD is new code. Nothing in Autumn does this. Autumn had no tool
# calling, no approval gate, and no kill switch, so there was nothing
# to guard. GUARD is a role, not a separate agent process. GUARD is
# code, not an LLM call. GUARD runs before every NEEDS APPROVAL tool
# call and before every state change that touches the portfolio.
# GUARD checks the fixed action menu, the tool tag, the kill state,
# the approval state, and the risk check. If any check fails, GUARD
# blocks the call and writes a log line. GUARD has no LLM. GUARD
# cannot be talked out of a block. The LLM never sees a way to bypass
# GUARD. There is no tool that disables GUARD. If you add one, the
# whole safety story is broken. Do not add one.
"""GUARD. Code checks that run before any risky tool call."""

from __future__ import annotations

from dataclasses import dataclass

from si_console import config
from si_console.errors import GuardError
from si_console.vault import TaskNote

# Characters that let one shell command chain, pipe, redirect, or
# substitute another. None of them is needed by an allowed command.
_SHELL_META = (";", "&", "|", "<", ">", "`", "$", "\n", "\r", "(", ")")


@dataclass
class GuardState:
    """The facts GUARD needs. The bridge owns kill state. The vault
    owns approval state. GUARD reads both, writes neither."""

    kill_active: bool = False
    approval_pending: bool = False
    approved_by: str = ""
    risk_check: str = ""


def check_tool(
    tool_name: str,
    tag: str,
    role: str,
    allowed_tools: set,
    state: GuardState,
    task: TaskNote | None = None,
) -> None:
    """Check one tool call. Raises GuardError on the first failure.

    Checks run in this order, so the log line names the first problem:
    1. Kill active. Nothing runs while kill is active, except the
       resume path, which is a button press, not a tool call.
    2. Role permission. The tool must be in the role's allowed list
       from ARCHITECTURE.md section 5.8.
    3. Approval. A NEEDS APPROVAL tool needs a pending approval that
       the green button already granted. A proposal that is only
       queued is not approved. approved_by must be human.
    4. Risk. An order tool needs risk_check pass. A failed risk check
       blocks the order, even if the green button was pressed. The
       bridge also checks this, so a bug in one place is caught by
       the other. Two checks, same rule.
    """
    if state.kill_active:
        raise GuardError(
            "GUARD_BLOCK",
            "Kill switch is active. No tool runs.",
            remedy="Turn the kill switch off, then press green once to resume.",
        )
    if tool_name not in allowed_tools:
        raise GuardError(
            "GUARD_BLOCK",
            f"Role {role} may not call tool {tool_name}.",
            remedy="Use a tool from the role's allowed list in ARCHITECTURE.md 5.8.",
        )
    if tag == "NEEDS APPROVAL":
        if not state.approval_pending and not state.approved_by:
            raise GuardError(
                "GUARD_BLOCK",
                f"Tool {tool_name} needs approval. No approval is pending.",
                remedy="Call request_approval first, then wait for green.",
            )
        if state.approved_by != "human":
            raise GuardError(
                "GUARD_BLOCK",
                "Approval was not given by a human pressing green.",
                remedy="Only the green button sets approved_by to human.",
            )
    if tool_name in ("make_slides", "run_python") and task is not None:
        if task.type == "order" and task.risk_check == "fail":
            raise GuardError(
                "GUARD_BLOCK",
                "Risk check failed. The order is blocked.",
                remedy=f"Reason code: {task.risk_reason or 'none'}.",
            )


def check_order_execution(task: TaskNote, state: GuardState) -> None:
    """Check an execution order before it fills. Three hard rules.

    1. The task must be in approved state, with approved_by human.
    2. Kill must not be active.
    3. executed_at must be blank. An order that already filled must
       never fill twice. Power loss must not cause a double fill.
    This is the check that stops a bug from spending paper money twice.
    """
    if state.kill_active:
        raise GuardError(
            "GUARD_BLOCK",
            "Kill switch is active. No order executes.",
        )
    if task.approved_by != "human" or not task.approved_at:
        raise GuardError(
            "GUARD_BLOCK",
            "Order was not approved by a human pressing green.",
            remedy="Wait for the green button, then try again.",
        )
    if task.executed_at:
        raise GuardError(
            "GUARD_BLOCK",
            f"Order already executed at {task.executed_at}.",
            remedy="Do not execute the same order twice.",
        )
    if task.risk_check == "fail":
        raise GuardError(
            "GUARD_BLOCK",
            "Risk check failed. The order is blocked.",
            remedy=f"Reason code: {task.risk_reason or 'none'}.",
        )


def check_shell_command(command: str) -> None:
    """Check a shell command against the allow list in config.

    No pipes to curl, no wget, no pip install, no rm, no sudo, no
    network calls from shell. The shell runs as a non root user.
    The working directory is fixed to the project folder.
    """
    first = command.strip().split(" ", 1)[0] if command.strip() else ""
    # A prefix match alone is not enough: "ls; rm -rf ~" starts with
    # "ls ". Refuse every shell control character before matching, so
    # an allowed command can never chain, pipe, redirect or substitute.
    if any(ch in command for ch in _SHELL_META):
        raise GuardError(
            "SHELL_DENY",
            "Shell command contains a control character (; & | < > ` $ or newline).",
            remedy="Run one allow listed command with plain arguments only.",
        )
    # The allow list holds full command starts, not single words, so
    # "python3 make_slides.py" is allowed but "python3" alone is not.
    for allowed in config.ALLOWED_SHELL_COMMANDS:
        if command.strip() == allowed or command.strip().startswith(allowed + " "):
            return
    raise GuardError(
        "SHELL_DENY",
        f"Shell command is not on the allow list: {first}.",
        remedy="Use a command from ALLOWED_SHELL_COMMANDS in config.py.",
    )
