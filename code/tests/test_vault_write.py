# These tests are Autumn's test_vault_write.py, adapted for frontmatter.
# Autumn's test used a scratch note and a hash check of every other
# note. This test does the same shape: create a note, change its
# status, check every other note is byte identical, check no .tmp
# file is left behind, and check every refusal path. Run with:
# cd scratch && python3 -m pytest tests/test_vault_write.py -v
# No Pi needed. No API key needed. The vault is a temp folder.
"""Vault write tests. Frontmatter edits, atomic writes, refusals."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config
from si_console.errors import VaultError
from si_console.vault import (
    TaskNote,
    append_log,
    create_task,
    list_tasks,
    new_task_body,
    read_note,
    update_status,
    write_research_note,
)


@pytest.fixture
def vault(tmp_path, monkeypatch):
    """A throwaway vault with a tasks folder and a .obsidian folder."""
    root = tmp_path / "vault" / "si-console"
    (root / "tasks").mkdir(parents=True)
    (root / "research").mkdir(parents=True)
    (root / ".obsidian").mkdir(parents=True)
    monkeypatch.setattr(config, "VAULT_PATH", root)
    return root


def _note(task_id="2026-12-01-signal-001"):
    return TaskNote(
        id=task_id,
        agent="signal",
        status="queued",
        type="signal",
        mode="booth",
        replay_date="2022-06-15",
        proposal="buy XLK 20 percent",
        ticker="XLK",
        amount=20000,
        lang="en",
        priority=2,
        body=new_task_body("Test summary.", "XLK momentum 0.12.", "Risk checks next.", []),
    )


def test_create_and_read(vault):
    create_task(_note())
    note = read_note("2026-12-01-signal-001")
    assert note.status == "queued"
    assert note.agent == "signal"
    assert note.proposal == "buy XLK 20 percent"
    assert note.ticker == "XLK"


def test_duplicate_is_refused(vault):
    create_task(_note())
    with pytest.raises(VaultError) as exc:
        create_task(_note())
    assert exc.value.code == "duplicate_task"


def test_bad_dependency_is_refused(vault):
    note = _note()
    note.depends_on = ["2026-12-01-no-such-task"]
    with pytest.raises(VaultError) as exc:
        create_task(note)
    assert exc.value.code == "bad_dependency"


def test_update_status_writes_log(vault):
    create_task(_note())
    updated = update_status("2026-12-01-signal-001", "working")
    assert updated.status == "working"
    assert "## Log" in updated.body


def test_bad_status_is_refused(vault):
    create_task(_note())
    with pytest.raises(VaultError) as exc:
        update_status("2026-12-01-signal-001", "flying")
    assert exc.value.code == "bad_status"


def test_bad_task_id_is_refused(vault):
    with pytest.raises(VaultError):
        read_note("../escape")
    with pytest.raises(VaultError):
        read_note("bad id with spaces!")


def test_missing_file_is_refused(vault):
    with pytest.raises(VaultError) as exc:
        read_note("2026-12-01-no-such-task")
    assert exc.value.code == "missing_file"


def test_other_notes_unchanged(vault):
    create_task(_note("2026-12-01-signal-001"))
    create_task(_note("2026-12-01-signal-002"))
    other = vault / "tasks" / "2026-12-01-signal-002.md"
    before = other.read_bytes()
    update_status("2026-12-01-signal-001", "blocked", "HUMAN_REJECT")
    assert other.read_bytes() == before


def test_no_tmp_file_left(vault):
    create_task(_note())
    update_status("2026-12-01-signal-001", "done")
    leftovers = list((vault / "tasks").glob("*.tmp"))
    assert leftovers == []


def test_append_log_only_changes_memory(vault):
    note = _note()
    append_log(note, "test line")
    assert "test line" in note.body
    # The file on disk is unchanged until the caller writes the note.
    assert not (vault / "tasks" / "2026-12-01-signal-001.md").exists()


def test_research_note_is_named_by_bridge(vault):
    name = write_research_note("2022 bear market", "# 2022 bear market\n\nNotes.")
    assert name.startswith("20")
    assert name.endswith(".md")
    assert (vault / "research" / name).is_file()


def test_list_filters_by_status(vault):
    create_task(_note("2026-12-01-signal-001"))
    create_task(_note("2026-12-01-signal-002"))
    update_status("2026-12-01-signal-001", "blocked", "HUMAN_REJECT")
    assert len(list_tasks(status="queued")) == 1
    assert len(list_tasks(status="blocked")) == 1
    assert len(list_tasks()) == 2
