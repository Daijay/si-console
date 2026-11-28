"""Shared test setup. Telemetry goes to a temp folder, never to code/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config


@pytest.fixture(autouse=True)
def _telemetry_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TELEMETRY_PATH", tmp_path / "telemetry.sqlite")


@pytest.fixture(autouse=True)
def _state_paths_in_tmp(tmp_path, monkeypatch):
    """No test may write state.json, claims.json or an approval request
    into the repo. Every test gets its own files."""
    monkeypatch.setattr(config, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(config, "CLAIMS_PATH", tmp_path / "claims.json")
    monkeypatch.setattr(config, "APPROVAL_PATH", tmp_path / "approval_request.json")
    monkeypatch.setattr(config, "OUTBOX_PATH", tmp_path / "outbox.json")
    monkeypatch.setattr(
        config, "STRINGS_PATH", Path(__file__).resolve().parent.parent / "dashboard" / "strings.json"
    )
