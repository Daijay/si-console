# Builds the context the coordinator sends to the model. Everything is
# compressed before the model sees it. Tasks are the source of truth,
# so all of them in the chain go in. Snippets are clipped. Totals are
# stated honestly, so the model never implies it saw everything.
# Failures are visible to the model, so a failed source never produces
# a fake all clear. Compression matters because the coordinator calls
# the model in a loop, up to 3 rounds, and every extra token is paid
# for each time.
# The input is a task chain plus the portfolio note: the last 5 task
# notes, the portfolio, and the current task. The coordinator never
# reads the whole vault. That caps the prompt size and the cost.
"""Compress the task chain into a short prompt for the model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from si_console.vault import TaskNote

# Tuning knobs. Raising these raises cost per call roughly linearly.
MAX_CHAIN_NOTES = 5
SUMMARY_CHARS = 110
PROPOSAL_CHARS = 90


@dataclass
class TaskContext:
    """The compressed chain, plus stats so the cut is measurable."""

    text: str
    task_count: int = 0
    chain_count: int = 0
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tasks": self.task_count,
            "chain": self.chain_count,
            "errors": len(self.errors),
            "chars": len(self.text),
        }


def _clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def _summary_of(note: TaskNote) -> str:
    """First line of the Summary section, or the proposal text."""
    body = note.body or ""
    match = re.search(r"## Summary\s*\n+(.+)", body)
    if match:
        return _clip(match.group(1).strip(), SUMMARY_CHARS)
    return _clip(note.proposal, SUMMARY_CHARS)


def build_context(
    chain: list[TaskNote],
    current: TaskNote | None = None,
    portfolio_text: str = "",
    errors: list | None = None,
) -> TaskContext:
    """Build the compact briefing the coordinator sends to DeepSeek.

    Only the chain goes in, newest first, capped at 5 notes. The
    portfolio note goes in as numbers, not as a full file. Anything
    else the model needs, it must ask for with a tool call. That is
    the point of the fixed action menu: the model fetches, it does
    not get handed the whole vault.
    """
    shown = chain[:MAX_CHAIN_NOTES]
    lines: list[str] = []
    lines.append(f"TASKS IN CHAIN ({len(chain)} total, {len(shown)} shown):")
    if not shown:
        lines.append("  none")
    for note in shown:
        lines.append(
            f"  - [{note.id}] {note.agent} {note.status} "
            f"{note.type} round {note.round}: {_summary_of(note)}"
        )
        if note.proposal:
            lines.append(f"    proposal: {_clip(note.proposal, PROPOSAL_CHARS)}")
        if note.risk_reason:
            lines.append(f"    reason: {note.risk_reason}")
        if note.depends_on:
            deps = ", ".join(f"[[{d}]]" for d in note.depends_on)
            lines.append(f"    depends on: {deps}")
    lines.append("")
    if current is not None:
        lines.append(f"CURRENT TASK: [{current.id}] {current.agent} {current.type}")
        lines.append(f"  status: {current.status}, round: {current.round}")
        if current.proposal:
            lines.append(f"  proposal: {current.proposal}")
        lines.append("")
    if portfolio_text:
        lines.append("PORTFOLIO:")
        lines.append(_clip(portfolio_text, 600))
        lines.append("")
    if errors:
        lines.append("SOURCE FAILURES (data below may be incomplete):")
        for err in errors:
            lines.append(f"  - {err}")
    return TaskContext(
        text="\n".join(lines),
        task_count=len(chain),
        chain_count=len(shown),
        errors=list(errors or []),
    )
