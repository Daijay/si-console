# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# The coordinator loop is new code. Autumn had no coordinator loop.
# Its chat orchestrator had handoff detection, and the audit says to
# reuse that idea, not that code. Handoff detection in Autumn was a
# deterministic matcher in dashboard/src/handoff.js. The same idea
# lives here as a fixed action menu: the model picks from a menu,
# code validates the pick, and plain text never executes anything.
# The loop is copied step by step from ARCHITECTURE.md section 4.1.
# A round is one DeepSeek call plus its tool executions. Max 3 rounds
# per task, then it escalates to the human. No fourth call for that
# task. The coordinator never retries a blocked task on its own.
# The coordinator does not touch GPIO. It does not touch state.json
# directly. It writes the vault, and the bridge follows. It does not
# make trading decisions. It does not rank sectors. The rules engine
# computes the numbers. The LLM writes the explanation.
"""Coordinator loop. Fixed menu, validation, 3 round limit."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from si_console import config, models
from si_console.context import build_context
from si_console.errors import GuardError, ModelError, ToolError
from si_console.guard import GuardState, check_tool
from si_console.state_store import StateStore
from si_console.tools import (
    FIXED_MENU,
    effective_tag,
    tool_names_for_role,
    tools_for_role,
    validate_tool_call,
)
from si_console.vault import (
    TaskNote,
    append_log,
    create_task,
    list_tasks,
    new_task_body,
    read_note,
    update_status,
    write_note,
)

# System prompt for the coordinator. Short on purpose. The model gets
# the task note, the chain, the portfolio, and the fixed menu. It does
# not get free text from other files. It does not get a way to bypass
# GUARD, because GUARD is code, not a prompt rule.
SYSTEM_PROMPT = (
    "You are the SI Console coordinator. Pick actions from the fixed "
    "menu only. Return tool calls, not plain text. Plain text never "
    "executes anything. You do not make trading decisions. You do not "
    "rank sectors. The rules engine computes the numbers. You route "
    "work: signal, then risk, then execution, then back to signal."
)

# The coordinator reads kill state from state.json, which the bridge
# writes. Module level so tests can swap it, same pattern as bridge.
state_store = StateStore()


@dataclass
class LoopResult:
    """What one task run did, so the caller can log it and show it."""

    task_id: str
    done: bool
    rounds_used: int
    reason_code: str = ""
    log_lines: list = field(default_factory=list)


def validate_action(action: dict, task: TaskNote) -> None:
    """Validate one coordinator action, in the order ARCHITECTURE.md
    section 4.4 lists. A rejected reply never runs a tool. A rejected
    reply never changes a task status, except to log the error."""
    if not isinstance(action, dict):
        raise ToolError("BAD_JSON", "Action is not a JSON object.")
    name = action.get("action")
    if name not in FIXED_MENU:
        raise ToolError("BAD_ACTION", f"Action is not in the fixed menu: {name!r}.")
    # Required fields per action. The full schema lives in tools.py.
    # This is the cheap check. The tool validator does the deep check.
    if name == "create_task" and not action.get("task_id"):
        raise ToolError("BAD_SCHEMA", "create_task needs task_id.")
    if name == "create_task" and action.get("ticker"):
        if action["ticker"] not in config.ALLOWED_TICKERS:
            raise ToolError("BAD_TICKER", f"Ticker not allowed: {action['ticker']}.")
    if name == "create_task" and action.get("amount") is not None:
        if not isinstance(action["amount"], (int, float)) or action["amount"] < 0:
            raise ToolError("BAD_AMOUNT", "Amount must be a number, zero or more.")
    if name == "create_task":
        for dep in action.get("depends_on") or []:
            try:
                read_note(dep)
            except Exception:
                raise ToolError(
                    "BAD_DEPENDENCY", f"depends_on id does not exist: {dep}."
                ) from None
    if name == "create_task":
        existing = [t.id for t in list_tasks()]
        if action["task_id"] in existing:
            raise ToolError(
                "DUPLICATE_TASK", f"Task id already exists: {action['task_id']}."
            )


def run_task(task_id: str, guard_state: GuardState, pane: str | None = None) -> LoopResult:
    """Run one task through the coordinator loop. Max 3 rounds.

    Step 1. Read the task. If kill is active, do not pick it up.
    Step 2. Build a prompt from the task note, the chain, and the
    portfolio only. Step 3. Call DeepSeek with the role tool list.
    Step 4. Validate each tool call. One bad call discards the whole
    reply. Step 5. Run each valid call through GUARD. SAFE tools run
    at once. NEEDS APPROVAL tools pause for the green or red button.
    Step 6. Write a log line. Step 7. Count one round. Done, or loop,
    or block at 3 rounds with ROUND_LIMIT and an escalation note.
    The model comes from the T0 chain for `pane` (arena pane A, B or
    C; default SI_COORDINATOR_PANE). The router falls back inside the
    chain, so a ModelError here means every T0 model failed.
    """
    pane = pane or config.COORDINATOR_PANE
    if guard_state.kill_active:
        return LoopResult(task_id, False, 0, "KILL_SWITCH")
    task = read_note(task_id)
    chain = list_tasks()[:5]
    context = build_context(chain, current=task)
    messages = context.text
    rounds = 0
    log_lines: list[str] = []

    while rounds < config.ROUND_LIMIT:
        # A round can take 30 s or more. Re-read kill state before
        # every round so a kill pressed mid-task stops the next model
        # call and the next tool call, not only the next task.
        if _killed_in_store():
            guard_state.kill_active = True
        if guard_state.kill_active:
            log_lines.append(f"round {rounds + 1} skipped: KILL_SWITCH")
            return LoopResult(task_id, False, rounds, "KILL_SWITCH", log_lines)
        rounds += 1
        task.round = rounds
        try:
            reply = models.complete(
                config.COORDINATOR,
                messages,
                system=SYSTEM_PROMPT,
                tools=tools_for_role(task.agent),
                pane=pane,
                route_reason=f"orchestrator task {task_id}",
            )
        except ModelError as exc:
            # One retry, then block. Do not retry forever. In booth
            # mode the recorded fallback takes over after this.
            log_lines.append(f"round {rounds} API error: {exc.code}")
            if rounds < config.ROUND_LIMIT:
                time.sleep(5)
                continue
            return _escalate(task, rounds, "API_TIMEOUT", log_lines)
        if reply.data is not None:
            # Structured JSON answer instead of tool calls. Validate
            # it against the fixed menu, the same way as a tool call.
            # A failed check discards the whole reply, never partly.
            try:
                validate_action(reply.data, task)
            except ToolError as exc:
                log_lines.append(f"round {rounds} rejected: {exc.code}")
                if rounds >= config.ROUND_LIMIT:
                    return _escalate(task, rounds, exc.code, log_lines)
                continue
            log_lines.append(f"round {rounds} action {reply.data.get('action')} valid")
            continue
        if not reply.tool_calls:
            # No tool call and no final answer is a failed round.
            # A plain text answer must become a menu action, or the
            # task is blocked with BAD_OUTPUT. Plain text never runs.
            log_lines.append(f"round {rounds} no tool call, BAD_OUTPUT")
            return _escalate(task, rounds, "BAD_OUTPUT", log_lines)
        try:
            for call in reply.tool_calls:
                _run_one_tool_call(call, task, guard_state, log_lines)
        except (ToolError, GuardError) as exc:
            # A GUARD block is a rejected reply, same as a bad tool
            # call. It must never crash the loop. A blocked tool
            # call discards the whole reply, logs the reason, and
            # the loop continues or escalates at the round limit.
            log_lines.append(f"round {rounds} rejected: {exc.code}")
            append_log(task, f"round {rounds} rejected {exc.code}")
            write_note(task)
            if rounds >= config.ROUND_LIMIT:
                return _escalate(task, rounds, exc.code, log_lines)
            continue
        # The tool results go back into the next prompt. This is a
        # skeleton, so the results are logged, not re-sent as full
        # DeepSeek message history. The real build must keep the
        # message list and append tool results to it, per section 4.1.
        messages += "\n" + "\n".join(log_lines[-3:])
        task = read_note(task_id)
        if task.status == "done":
            return LoopResult(task_id, True, rounds, "", log_lines)
        if task.status == "blocked":
            return LoopResult(task_id, False, rounds, task.risk_reason, log_lines)
    return _escalate(task, rounds, "ROUND_LIMIT", log_lines)


def _run_one_tool_call(call: dict, task: TaskNote, state: GuardState, log: list) -> None:
    """Validate one tool call, check it with GUARD, then run it.

    This is a skeleton dispatcher. Each branch is short on purpose.
    The real build fills in the tool bodies. The validation and the
    GUARD check are the parts that must not change shape.
    """
    func = call.get("function", {})
    name = func.get("name", "")
    try:
        args = json.loads(func.get("arguments", "{}"))
    except json.JSONDecodeError:
        raise ToolError("BAD_JSON", "Tool arguments are not valid JSON.") from None
    validate_tool_call(name, args)
    # The tag depends on the call, not only the tool: done on an order
    # task needs approval even though update_task_status is SAFE.
    tag = effective_tag(name, args)
    # GUARD checks the tool name against the tools this role may
    # call. tool_names_for_role returns tool names. Do not pass
    # tool.roles here: that set holds role names, and a tool name
    # is never in it, so every call would be blocked.
    check_tool(name, tag, task.agent, tool_names_for_role(task.agent), state, task)
    # SAFE tools run at once. NEEDS APPROVAL tools pause here in the
    # real build and wait for the bridge. This skeleton logs the pause
    # instead of wiring the full wait, so the team can see the gate.
    if tag == "NEEDS APPROVAL":
        log.append(f"approval needed for {name}, waiting for green or red")
        append_log(task, f"approval requested for {name}")
        write_note(task)
        return
    log.append(f"ran {name}")
    append_log(task, f"ran {name}")


def _escalate(task: TaskNote, rounds: int, reason: str, log_lines: list) -> LoopResult:
    """Mark a task blocked and write an escalation note.

    The escalation note says what was tried in each round and what is
    missing. The screens show ESCALATE TO HUMAN. The coordinator LED
    fast blinks, which means blocked. A human clears it by pressing
    red to reject and start a new proposal, or by writing a new task.
    """
    task = read_note(task.id)
    update_status(task.id, "blocked", reason)
    note = TaskNote(
        id=f"{task.id}-escalate",
        agent="coordinator",
        status="blocked",
        type="narration",
        mode=task.mode,
        depends_on=[task.id],
        risk_reason=reason,
        lang=task.lang,
        body=new_task_body(
            summary=f"Escalated after {rounds} rounds. Reason {reason}.",
            numbers="Rounds tried: " + str(rounds) + ".",
            next_step="Human: press red to reject, or write a new task note.",
            deps=[task.id],
        ),
    )
    try:
        create_task(note, initial_status="blocked")
    except Exception:
        # The escalation note is helpful, not required. If it cannot
        # be created, the blocked task is still the truth.
        pass
    return LoopResult(task.id, False, rounds, reason, log_lines)


def _killed_in_store() -> bool:
    """True when state.json says the console is frozen: the kill
    switch is on, or it was released but no green press resumed yet.
    An unreadable state.json counts as killed (fail closed)."""
    try:
        state = state_store.read()
    except Exception:
        return True
    return bool(state.get("kill_active", False) or state.get("resume_required", False))


def serve_forever() -> None:
    """Run the coordinator as a service. Pick up the next queued
    task, run it, wait 1 second, repeat. If kill is active, wait
    and do not pick up a task. This is the entry point the systemd
    unit runs. The loop never calls DeepSeek for a blocked task."""
    state = GuardState()
    while True:
        # The bridge owns kill state and writes it to state.json.
        # Refresh every iteration so a kill reaches this loop. The
        # vault and state.json are the source of truth, not a copy
        # held here since startup.
        # If state.json is unreadable, fail closed: treat it as killed
        # until the next scan can read it. A released kill switch still
        # counts as killed until a green press resumes (resume_required).
        state.kill_active = _killed_in_store()
        if state.kill_active:
            time.sleep(1)
            continue
        task = None
        try:
            task = pick_next_task()
        except Exception as exc:  # noqa: BLE001 - vault unreadable: wait, retry
            print(f"coordinator: could not list tasks: {getattr(exc, 'code', type(exc).__name__)}")
        if task is None:
            time.sleep(1)
            continue
        try:
            update_status(task.id, "working")
            run_task(task.id, state)
        except Exception as exc:  # noqa: BLE001 - the service must not die
            # One bad note, a vault hiccup, or an unexpected client error
            # must not crash the service into a systemd restart loop.
            # Block the task so the queue does not pick it up again.
            code = getattr(exc, "code", "") or type(exc).__name__
            try:
                update_status(task.id, "blocked", "ESCALATE")
            except Exception:
                pass
            print(f"coordinator: task {task.id} failed: {code}")
        time.sleep(1)


def pick_next_task() -> TaskNote | None:
    """The next queued task, oldest first. None when the queue is empty."""
    queued = list_tasks(status="queued")
    if not queued:
        return None
    return sorted(queued, key=lambda t: t.created or "")[0]


def stuck_watchdog(guard_state: GuardState) -> list[str]:
    """Find tasks stuck in working too long and block them.

    Runs every 30 seconds. Needs no LLM call. A task in working for
    more than 300 seconds becomes blocked with reason STUCK.
    """
    blocked: list[str] = []
    now = datetime.now(timezone.utc)
    for task in list_tasks(status="working"):
        try:
            updated = datetime.fromisoformat(task.updated)
        except ValueError:
            continue
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if (now - updated).total_seconds() > config.STUCK_SECONDS:
            update_status(task.id, "blocked", "STUCK")
            blocked.append(task.id)
    return blocked


if __name__ == "__main__":
    serve_forever()
