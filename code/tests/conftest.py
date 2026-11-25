"""Shared test setup. Telemetry goes to a temp folder, never to code/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from si_console import config


@pytest.fixture(autouse=True)
def _telemetry_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TELEMETRY_PATH", tmp_path / "telemetry.sqlite")
