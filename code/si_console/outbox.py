# Screen and speech events from the coordinator to the bridge.
#
# The coordinator must not write state.json: the bridge owns it and a
# read-modify-write from two processes would lose updates. So the
# coordinator appends one small JSON file here, the bridge polls it,
# folds each event into state.json, and truncates it. The vault is
# still the truth for tasks; this file only carries what the screens
# and the speaker need right now.
#
# Every id in an event is a key in dashboard/strings.json. The model
# never sends free text to a screen or a speaker. That rule is the
# whole reason this file is ids, not sentences.
"""One-file event handoff for screen and speech messages."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

from si_console import config

ALLOWED_KINDS = ("message", "speech")


def outbox_path() -> Path:
    """Read at call time so tests can point it at a temp folder."""
    return Path(config.OUTBOX_PATH)


def _read() -> list[dict]:
    try:
        data = json.loads(outbox_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _write(events: list[dict]) -> None:
    target = outbox_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(events, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def publish(kind: str, message_id: str, lang: str, dedupe_key: str = "") -> dict:
    """Append one event. Replacing the same dedupe key stops a retried
    round from showing the same message over and over."""
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"Unknown event kind: {kind!r}.")
    event = {
        "id": message_id,
        "kind": kind,
        "lang": lang,
        "dedupe_key": dedupe_key or f"{kind}:{message_id}:{lang}",
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    events = [e for e in _read() if e.get("dedupe_key") != event["dedupe_key"]]
    events.append(event)
    _write(events[:20])  # bounded: a stuck bridge cannot grow this forever
    return event


def drain() -> list[dict]:
    """Take all pending events and clear the file. One reader only:
    the bridge calls this from its poll loop."""
    events = _read()
    if events:
        _write([])
    return events


def clear() -> None:
    _write([])
