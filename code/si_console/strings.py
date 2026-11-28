# Prewritten strings. The model picks an id; this file resolves it.
#
# Free LLM text is never spoken and never shown as a status line. A
# missing id is an error, not a fallback to the id itself: showing a
# raw id on a booth screen is worse than showing nothing.
"""Resolve prewritten message ids to EN/ZH text."""

from __future__ import annotations

import json
from pathlib import Path

from si_console import config
from si_console.errors import ToolError

_cache: dict[tuple[str, str], dict] = {}


def _load(lang: str) -> dict:
    key = (str(config.STRINGS_PATH), lang)
    if key in _cache:
        return _cache[key]
    path = Path(config.STRINGS_PATH)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError(
            "VAULT_ERROR", f"Cannot read strings file: {path}", str(exc)
        ) from None
    table = data.get(lang)
    if not isinstance(table, dict):
        raise ToolError("BAD_SCHEMA", f"No {lang!r} table in {path}.")
    _cache[key] = table
    return table


def resolve(message_id: str, lang: str) -> str:
    """The exact sentence for one id, or a ToolError. No free text."""
    table = _load(lang)
    text = table.get(message_id)
    if not isinstance(text, str) or not text.strip():
        raise ToolError(
            "BAD_SCHEMA",
            f"Unknown message id {message_id!r} for {lang}.",
            remedy="Use an id from dashboard/strings.json.",
        )
    return text


def has(message_id: str, lang: str) -> bool:
    return message_id in _load(lang)
