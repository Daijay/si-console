# Reads and writes the task notes. Writes are atomic: a temp file in the
# same folder, then os.replace, so a crash can never leave a half written
# note. When in doubt it refuses rather than guesses, with an error code.
# Ids pass a path guard. A status change edits the YAML frontmatter, so
# the whole note is rebuilt and written back. The file also parses
# status, depends_on, and wikilinks in the body.
# This file only reads and writes notes. It never watches the folder.
# The bridge does that.
# Two writers (coordinator and bridge) can race on the same note, so
# change the write path test first. See tests/test_vault_write.py.
"""Vault notes. Read, write, and list task notes by frontmatter.

The vault is the single source of truth for tasks. state.json is a
cache. If they disagree, the vault wins. The bridge rebuilds state
from the vault on every start. Free text never drives LEDs or screens.
Only frontmatter status drives them.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from si_console import config
from si_console.errors import VaultError

# Allowed frontmatter values.
# A value outside these lists is rejected, not silently accepted.
AGENTS = {"signal", "risk", "execution", "coordinator"}
STATUSES = {"queued", "working", "blocked", "done"}
TYPES = {"signal", "risk_check", "order", "narration", "research"}
MODES = {"home", "booth"}
RISK_CHECKS = {"pass", "fail", ""}

# Reason codes. A fixed list, so the screens can show each one.
REASON_CODES = {
    "MAX_SECTOR", "MAX_DRAWDOWN", "TOO_MUCH_TURNOVER", "CASH_LOW",
    "CRASH_STOP", "HUMAN_REJECT", "ROUND_LIMIT", "BAD_OUTPUT", "BAD_JSON",
    "BAD_ACTION", "BAD_SCHEMA", "BAD_TICKER", "BAD_AMOUNT",
    "BAD_DEPENDENCY", "DUPLICATE_TASK", "GUARD_BLOCK", "API_TIMEOUT",
    "API_ERROR", "TOOL_TIMEOUT", "VAULT_WRITE_FAIL", "STUCK",
    "POWER_LOSS", "ESCALATE", "KILL_SWITCH", "CLAIM_EXPIRED",
    "CLAIM_RELEASED",
}

TASK_DIR = "tasks"
RESEARCH_DIR = "research"
PORTFOLIO_DIR = "portfolio"
SLIDES_DIR = "slides"
LOG_DIR = "log"

# A task id is a file name without .md. ASCII only, so Chinese text
# never lands in a file name. Chinese goes in the body, never the name.
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_]{0,63}$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def utcnow_iso() -> str:
    """Current time in ISO form with timezone, for created and updated."""
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str:
    """Hash of a file, so the bridge can skip files that did not change."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vault_root() -> Path:
    """Resolve the vault root. Fail loudly if it is missing."""
    root = Path(config.VAULT_PATH)
    if not root.is_dir():
        raise VaultError(
            "no_vault",
            f"Vault path does not exist or is not a directory: {root}",
            remedy="Set SI_VAULT_PATH in .env to the vault folder.",
        )
    return root.resolve()


def _resolve_target(rel_path: str, root: Path) -> Path:
    """Resolve a vault relative path and confirm it stays inside the vault.

    The path can arrive from an external agent, so it is treated as
    untrusted. A crafted value must not let anyone edit files outside
    the vault.
    """
    target = Path(rel_path)
    if target.is_absolute():
        target = root / target.name
    target = (root / target).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise VaultError(
            "outside_vault",
            f"Refusing to write outside the vault: {rel_path}",
        ) from None
    if target.suffix.lower() != ".md":
        raise VaultError(
            "outside_vault",
            f"Refusing to write to a non-markdown file: {target.name}",
        )
    return target


@dataclass
class TaskNote:
    """One task note. Frontmatter fields plus the body text.

    depends_on holds plain ids in frontmatter, because YAML does not
    parse wikilinks cleanly. The body must list each dependency as
    [[id]] so Obsidian's graph shows the agent chain.
    """

    id: str
    agent: str
    status: str
    type: str
    mode: str = "booth"
    replay_date: str = ""
    created: str = ""
    updated: str = ""
    depends_on: list = field(default_factory=list)
    proposal: str = ""
    amount: float = 0
    ticker: str = ""
    price: float = 0
    risk_check: str = ""
    risk_reason: str = ""
    approved_by: str = ""
    approved_at: str = ""
    executed_at: str = ""
    lang: str = "en"
    priority: int = 2
    round: int = 0
    body: str = ""

    def to_frontmatter(self) -> dict:
        """Frontmatter dict, in a fixed order so notes stay easy to compare."""
        return {
            "id": self.id,
            "agent": self.agent,
            "status": self.status,
            "type": self.type,
            "mode": self.mode,
            "replay_date": self.replay_date,
            "created": self.created,
            "updated": self.updated,
            "depends_on": list(self.depends_on),
            "proposal": self.proposal,
            "amount": self.amount,
            "ticker": self.ticker,
            "price": self.price,
            "risk_check": self.risk_check,
            "risk_reason": self.risk_reason,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "executed_at": self.executed_at,
            "lang": self.lang,
            "priority": self.priority,
            "round": self.round,
        }

    def render(self) -> str:
        """Full file text: frontmatter, then body. UTF-8, LF endings."""
        text = yaml.safe_dump(
            self.to_frontmatter(), sort_keys=False, allow_unicode=True
        )
        return f"---\n{text}---\n{self.body}"


def parse_note(text: str, task_id: str = "") -> TaskNote:
    """Parse one note. Bad frontmatter is an error, never a guess."""
    # A UTF-8 BOM (Notepad and some editors add one), or CRLF text
    # passed in directly, fails the frontmatter regex, and list_tasks
    # then drops the note without a word.
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise VaultError(
            "bad_frontmatter",
            "Note has no YAML frontmatter block.",
            remedy="Add a --- block at the top with the fields in ARCHITECTURE.md 8.2.",
        )
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise VaultError(
            "bad_frontmatter", f"Frontmatter is not valid YAML: {exc}"
        ) from None
    if not isinstance(front, dict):
        raise VaultError("bad_frontmatter", "Frontmatter is not a mapping.")
    if front.get("status") not in STATUSES:
        raise VaultError(
            "bad_status",
            f"Unknown status: {front.get('status')!r}.",
            remedy=f"Use one of: {sorted(STATUSES)}.",
        )
    if front.get("agent") not in AGENTS:
        raise VaultError("bad_status", f"Unknown agent: {front.get('agent')!r}.")
    if front.get("risk_reason") and front["risk_reason"] not in REASON_CODES:
        raise VaultError(
            "bad_status", f"Unknown reason code: {front['risk_reason']!r}."
        )
    return TaskNote(
        id=front.get("id", task_id),
        agent=front.get("agent", ""),
        status=front.get("status", ""),
        type=front.get("type", ""),
        mode=front.get("mode", "booth"),
        replay_date=front.get("replay_date") or "",
        created=front.get("created") or "",
        updated=front.get("updated") or "",
        depends_on=list(front.get("depends_on") or []),
        proposal=front.get("proposal") or "",
        amount=float(front.get("amount") or 0),
        ticker=front.get("ticker") or "",
        price=float(front.get("price") or 0),
        risk_check=front.get("risk_check") or "",
        risk_reason=front.get("risk_reason") or "",
        approved_by=front.get("approved_by") or "",
        approved_at=front.get("approved_at") or "",
        executed_at=front.get("executed_at") or "",
        lang=front.get("lang") or "en",
        priority=int(front.get("priority") or 2),
        round=int(front.get("round") or 0),
        body=match.group(2),
    )


def _write_atomic(target: Path, text: str) -> None:
    """Replace the note in one step.

    Write the full new file to a temp file in the same folder, flush,
    fsync, rename to the live name, fsync the folder if the OS allows
    it. A crash mid-write leaves the original note intact. The bridge
    must ignore .tmp files. Never write directly to the live file.
    """
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_note(note: TaskNote, retry_once: bool = True) -> dict:
    """Write a task note by atomic write. Retry once after 200 ms.

    On conflict, the caller must read the current file first, merge
    its log lines, then write. Never overwrite a newer file with an
    older copy. The updated timestamp detects the conflict. On a
    conflict, log VAULT_CONFLICT and keep the newer file.
    """
    import time

    root = _vault_root()
    target = _resolve_target(f"{TASK_DIR}/{note.id}.md", root)
    note.updated = utcnow_iso()
    text = note.render()
    try:
        _write_atomic(target, text)
    except OSError:
        if not retry_once:
            raise VaultError(
                "vault_write_fail",
                f"Could not write {note.id}.md.",
                remedy="Retry once after 200 ms, then mark the task blocked.",
            ) from None
        time.sleep(0.2)
        try:
            _write_atomic(target, text)
        except OSError:
            raise VaultError(
                "vault_write_fail",
                f"Could not write {note.id}.md after one retry.",
                remedy="Keep the old file. Mark the task blocked.",
            ) from None
    return {"status": "written", "id": note.id, "path": str(target)}


def read_note(task_id: str) -> TaskNote:
    """Read one task note by id. Refuses bad ids and missing files."""
    if not TASK_ID_RE.fullmatch(task_id):
        raise VaultError("not_found", f"Invalid task id: {task_id!r}.")
    root = _vault_root()
    target = _resolve_target(f"{TASK_DIR}/{task_id}.md", root)
    if not target.is_file():
        raise VaultError(
            "missing_file",
            f"That note no longer exists: {task_id}.md",
            remedy="List tasks to rescan the vault, then try again.",
        )
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise VaultError(
            "unreadable", f"Could not read {task_id}.md: {exc}"
        ) from None
    return parse_note(text, task_id)


def create_task(note: TaskNote, initial_status: str = "queued") -> dict:
    """Create a new task note. Refuses duplicates.

    Defaults to queued, which is what the coordinator wants for a
    normal proposal. Escalation notes pass initial_status="blocked"
    so the queue never picks them up and re-runs them. The status is
    validated against the same set the frontmatter parser uses.
    """
    if initial_status not in STATUSES:
        raise VaultError(
            "bad_status",
            f"Invalid initial status: {initial_status!r}.",
            remedy=f"Use one of: {sorted(STATUSES)}.",
        )
    if not TASK_ID_RE.fullmatch(note.id):
        raise VaultError("not_found", f"Invalid task id: {note.id!r}.")
    root = _vault_root()
    target = _resolve_target(f"{TASK_DIR}/{note.id}.md", root)
    if target.exists():
        raise VaultError(
            "duplicate_task",
            f"A task with id {note.id} already exists.",
            remedy="Pick a new id, or update the existing task.",
        )
    for dep in note.depends_on:
        # Same id rule as the task itself, so a dependency can never
        # point outside tasks/ ("../../x") or probe other files.
        if not isinstance(dep, str) or not TASK_ID_RE.fullmatch(dep):
            raise VaultError("bad_dependency", f"Invalid depends_on id: {dep!r}.")
        dep_path = root / TASK_DIR / f"{dep}.md"
        if not dep_path.is_file():
            raise VaultError(
                "bad_dependency",
                f"depends_on id does not exist: {dep}.",
                remedy="Create the dependency first, or drop it from the list.",
            )
    now = utcnow_iso()
    note.created = now
    note.updated = now
    note.status = initial_status
    return write_note(note)


def list_tasks(status: str = "", agent: str = "") -> list[TaskNote]:
    """List task notes, newest first. Filter by status or agent.

    The bridge uses this on start to rebuild state.json. The
    coordinator uses it to find the next queued task. This reads the
    vault on demand. This file has no watcher. Watching is the
    bridge's job.
    """
    root = _vault_root()
    folder = root / TASK_DIR
    notes = []
    if not folder.is_dir():
        return notes
    for path in sorted(folder.glob("*.md"), reverse=True):
        try:
            note = parse_note(path.read_text(encoding="utf-8"), path.stem)
        except (VaultError, OSError, UnicodeDecodeError):
            continue
        if status and note.status != status:
            continue
        if agent and note.agent != agent:
            continue
        notes.append(note)
    return notes


def update_status(
    task_id: str,
    status: str,
    reason_code: str = "",
    approved_by: str = "",
) -> TaskNote:
    """Change one task status, by atomic write, with a log line.

    Only the bridge may set approved_by, and only the green button
    sets it to human. This function accepts approved_by so the bridge
    can pass it, but the coordinator and external agents must never
    call it with approved_by set. GUARD enforces that in tools.py.
    """
    if status not in STATUSES:
        raise VaultError("bad_status", f"Unknown status: {status!r}.")
    if reason_code and reason_code not in REASON_CODES:
        raise VaultError("bad_status", f"Unknown reason code: {reason_code!r}.")
    note = read_note(task_id)
    note.status = status
    if reason_code:
        note.risk_reason = reason_code
    if approved_by:
        note.approved_by = approved_by
        note.approved_at = utcnow_iso()
    append_log(note, f"{status} by bridge, reason {reason_code or 'none'}")
    write_note(note)
    return note


def append_log(note: TaskNote, line: str) -> None:
    """Append one time stamped line to the Log section of a note.

    The Log section is append only, newest at the bottom. This edits
    the in memory note only. The caller must write the note after.
    """
    stamp = utcnow_iso()
    entry = f"{stamp} {line}"
    if "## Log" not in note.body:
        note.body = note.body.rstrip() + "\n\n## Log\n"
    note.body = note.body.rstrip() + f"\n{entry}\n"


def new_task_body(summary: str, numbers: str, next_step: str, deps: list) -> str:
    """Build the body of a new task note, with sections in this order:
    Summary, Numbers, Next, Log. Each dependency
    is a [[wikilink]] so Obsidian's graph shows the agent chain."""
    links = "\n".join(f"- [[{dep}]]" for dep in deps)
    parts = [
        "## Summary",
        "",
        summary,
        "",
        "## Numbers",
        "",
        numbers,
        "",
        "## Next",
        "",
        next_step,
        "",
    ]
    if links:
        parts += ["## Depends on", "", links, ""]
    parts += ["## Log", ""]
    return "\n".join(parts)


def write_research_note(title: str, content: str, task_id: str = "") -> str:
    """Write a research note. The bridge sets the file name, never the
    caller. Max 20000 characters. Research notes never change a task
    status and never drive LEDs. This is the path external agents use
    through POST /api/research in bridge.py."""
    if len(content) > 20000:
        raise VaultError(
            "bad_schema",
            "Research note is over 20000 characters.",
            remedy="Split it into two notes.",
        )
    root = _vault_root()
    folder = root / RESEARCH_DIR
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\s-]", "", title).strip()
    slug = re.sub(r"[\s_]+", "-", slug)[:60] or "research"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = folder / f"{stamp}-{slug}.md"
    counter = 2
    while path.exists():
        path = folder / f"{stamp}-{slug}-{counter}.md"
        counter += 1
    if task_id:
        if not TASK_ID_RE.fullmatch(str(task_id)):
            raise VaultError("not_found", f"Invalid task id: {task_id!r}.")
        content = content.rstrip() + f"\n\nRelated task: [[{task_id}]]\n"
    _write_atomic(path, content)
    return path.name
