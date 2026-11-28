# Real tool bodies. Called by the coordinator only after validate_tool_call,
# GUARD and (for NEEDS APPROVAL) a green press. Every body returns a short
# dict that goes into the task log. Nothing here can skip a check: this
# module never imports GUARD and never writes an approval state.
#
# Safety rules kept here, not just in the registry:
#  - vault paths go through vault.resolve_note, so no escape and .md only;
#  - shell_run matches a fixed allow list, with no shell metacharacters;
#  - run_python calls functions in process, never exec of model text;
#  - speak and show only ids from strings.json, never free text.
"""Tool bodies. Real work, called only after validation and GUARD."""

from __future__ import annotations

import json
import shlex
from datetime import date
from pathlib import Path

from si_console import config, make_slides, models, outbox, websearch
from si_console.errors import ToolError, VaultError
from si_console.guard import check_shell_command
from si_console.rules_engine import rank_sectors
from si_console.strings import resolve
from si_console import strings as strings_module
from si_console import vault

def _clip(text: str, limit: int = 4000) -> str:
    return text if len(text) <= limit else text[:limit] + "\n... [clipped]"


def vault_read(args: dict) -> dict:
    """Read one note. A missing note is an honest empty result, not a
    tool failure: the model asked for a note that does not exist yet,
    and the loop must carry on to its round limit."""
    try:
        target = vault.resolve_note(args["path"])
    except VaultError as exc:
        # Outside the vault or a bad suffix is a real error: the path
        # guard must never be reported as a harmless missing note.
        raise ToolError("VAULT_ERROR", exc.message, exc.remedy) from None
    if not target.is_file():
        return {"status": "missing", "path": args["path"], "note": "No such note."}
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ToolError("VAULT_ERROR", f"Cannot read {args['path']}: {exc}") from None
    return {"status": "read", "path": args["path"], "text": _clip(text)}


def vault_write(args: dict, task) -> dict:
    """Write a full note atomically. A task note is written through the
    vault parser, so frontmatter can never be faked by raw text."""
    target = vault.resolve_note(args["path"])
    content = args["content"]
    if not isinstance(content, str) or not content.strip():
        raise ToolError("BAD_SCHEMA", "vault_write needs non-empty content.")
    if len(content) > 100_000:
        raise ToolError("BAD_SCHEMA", "Note is over 100000 characters.")
    root = vault._vault_root()
    rel = target.relative_to(root).as_posix()
    if rel.startswith(f"{vault.TASK_DIR}/"):
        note_id = Path(rel).stem
        try:
            parsed = vault.parse_note(content, task_id=note_id)
        except VaultError as exc:
            raise ToolError("BAD_SCHEMA", exc.message, exc.remedy) from None
        if parsed.id != note_id:
            raise ToolError("BAD_SCHEMA", "Note id does not match its file name.")
        result = vault.write_note(parsed)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        vault._write_atomic(target, content.rstrip() + "\n")
        result = {"path": rel}
    return {"status": "written", "path": result.get("path", rel)}


def vault_list(args: dict) -> dict:
    tasks = vault.list_tasks(status=args.get("status", ""), agent=args.get("agent", ""))
    return {
        "status": "listed",
        "count": len(tasks),
        "tasks": [{"id": t.id, "status": t.status, "agent": t.agent} for t in tasks[:20]],
    }


def shell_run(args: dict) -> dict:
    """One fixed command, no shell. The allow list lives in config and
    is enforced by GUARD; this body never keeps a second copy of it."""
    command = str(args["command"]).strip()
    # GUARD owns the control-character and allow-list policy. A block
    # raises GuardError; the coordinator turns it into a rejected round.
    check_shell_command(command)
    import subprocess

    try:
        done = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=min(int(args["timeout_seconds"]), 60),
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ToolError("TOOL_TIMEOUT", f"Command failed: {exc}") from None
    return {
        "status": "ran",
        "command": command,
        "returncode": done.returncode,
        "stdout": _clip(done.stdout.strip(), 2000),
        "stderr": _clip(done.stderr.strip(), 1000),
    }


def run_python(args: dict) -> dict:
    """Call a known script function. Never exec model-supplied code."""
    script = args["script"]
    params = args.get("args") or {}
    if not isinstance(params, dict):
        raise ToolError("BAD_SCHEMA", "run_python args must be an object.")
    if script == "rules_engine":
        replay = str(params.get("date", "")) or config.REPLAY_SCENARIO
        try:
            day = date.fromisoformat(replay)
        except ValueError:
            raise ToolError("BAD_SCHEMA", " rules_engine date must be YYYY-MM-DD.") from None
        return {"status": "ran", "script": script, "result": rank_sectors(day)}
    if script == "make_slides":
        return {"status": "ran", "script": script, "result": make_slides_call(params)}
    if script == "backtest":
        raise ToolError(
            "BAD_ACTION", "backtest is not implemented in this build.",
            remedy="Use rules_engine for the replay ranking.",
        )
    raise ToolError("BAD_ACTION", f"Unknown script: {script!r}.")


def make_slides_call(args: dict) -> dict:
    title = args.get("title", "")
    bullets = args.get("bullets", [])
    if not isinstance(title, str) or not title.strip():
        raise ToolError("BAD_SCHEMA", "make_slides needs a title.")
    if not isinstance(bullets, list) or not all(isinstance(b, str) for b in bullets):
        raise ToolError("BAD_SCHEMA", "make_slides bullets must be a list of strings.")
    return make_slides.make_slides(
        title=title,
        bullets=bullets,
        slide_count=int(args.get("slide_count", 3)),
        lang=args.get("lang", config.LANG),
        output_path=args.get(
            "output_path", "vault/si-console/slides/deck.pptx"
        ),
        source_line=str(args.get("source_line", "SI Console replay")),
    )


def update_task_status(args: dict) -> dict:
    task_id = args["task_id"]
    status = args["status"]
    reason = args.get("reason_code", "")
    try:
        result = vault.update_status(task_id, status, reason_code=reason)
    except VaultError as exc:
        raise ToolError(exc.code, exc.message, exc.remedy) from None
    return {"status": "updated", "task_id": task_id, "new_status": status, "result": result}


def create_task_note(args: dict) -> dict:
    note = vault.TaskNote(
        id=args["task_id"],
        agent=args["agent"],
        status="queued",
        type=args["type"],
        mode=args.get("mode", config.MODE),
        summary=args.get("summary", ""),
        proposal=args.get("proposal", ""),
        depends_on=args.get("depends_on", []),
        ticker=args.get("ticker", ""),
        amount=float(args.get("amount", 0) or 0),
        lang=args.get("lang", config.LANG),
        priority=int(args.get("priority", 2)),
    )
    try:
        result = vault.create_task(note)
    except VaultError as exc:
        raise ToolError(exc.code, exc.message, exc.remedy) from None
    return {"status": "created", "task_id": args["task_id"], "result": result}


def read_portfolio(args: dict) -> dict:
    """The portfolio note is a real note in the vault. A missing
    portfolio is an honest 'no data', never an invented number."""
    mode = args["mode"]
    path = f"portfolio/{mode}.md"
    try:
        note = vault.resolve_note(path)
        text = note.read_text(encoding="utf-8")
    except (VaultError, OSError) as exc:
        return {"status": "no_data", "mode": mode, "note": str(exc)}
    return {"status": "read", "mode": mode, "text": _clip(text)}


def web_search(args: dict) -> dict:
    try:
        return websearch.web_search(
            query=args["query"],
            count=int(args.get("count", 5)),
            freshness=args.get("freshness", "noLimit"),
            lang=args.get("lang", config.LANG),
        )
    except Exception as exc:
        raise ToolError("SOURCE_ERROR", f"Web search failed: {exc}") from None


def fetch_url(args: dict) -> dict:
    try:
        return websearch.fetch_url(args["url"])
    except Exception as exc:
        raise ToolError("SOURCE_ERROR", f"Fetch failed: {exc}") from None


def speak_sentence(args: dict) -> dict:
    """Publish a prewritten speech id. TTS is not wired yet: the
    bridge will render the id when the voice model is chosen."""
    sentence_id = args["sentence_id"]
    lang = args["lang"]
    text = resolve(sentence_id, lang)  # raises on an unknown id
    outbox.publish("speech", sentence_id, lang, dedupe_key=f"speech:{sentence_id}:{lang}")
    return {"status": "queued", "sentence_id": sentence_id, "text": text}


def show_message(args: dict) -> dict:
    message_id = args["message_id"]
    lang = args["lang"]
    text = resolve(message_id, lang)
    outbox.publish(
        "message", message_id, lang, dedupe_key=f"message:{message_id}:{lang}"
    )
    return {"status": "shown", "message_id": message_id, "text": text}


HANDLERS = {
    "vault_read": vault_read,
    "vault_write": vault_write,
    "vault_list": vault_list,
    "shell_run": shell_run,
    "run_python": run_python,
    "web_search": web_search,
    "fetch_url": fetch_url,
    "create_task_note": create_task_note,
    "update_task_status": update_task_status,
    "read_portfolio": read_portfolio,
    "make_slides": make_slides_call,
    "speak_sentence": speak_sentence,
    "show_message": show_message,
}


def run(name: str, args: dict, task) -> dict:
    handler = HANDLERS.get(name)
    if handler is None:
        raise ToolError("BAD_ACTION", f"No body for tool: {name!r}.")
    if name == "vault_write":
        return handler(args, task)
    return handler(args)
