"""Tests for code/deploy/sync_env.py: values kept, migrations, no secrets shown."""

import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent.parent / "deploy" / "sync_env.py"
_spec = importlib.util.spec_from_file_location("sync_env", _PATH)
sync_env = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_env)

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / ".env.example"

OLD_ENV = """﻿# old template\r
DEEPSEEK_API_KEY=sk-deep-SECRET\r
DEEPSEEK_MODEL=deepseek-flash\r
DEEPSEEK_MODEL_PRO=deepseek-v4-pro\r
GLM_API_KEY=glm-SECRET\r
GLM_MODEL=glm-5.4\r
OPENROUTER_API_KEY=ts-SECRET\r
JEV_MODEL=typesafe/jev-1.14\r
SI_ORCH_B=hy4\r
MY_EXTRA=1\r
"""


@pytest.fixture
def env(tmp_path):
    path = tmp_path / ".env"
    path.write_bytes(OLD_ENV.encode("utf-8"))
    return path


def _run(env, *extra):
    return sync_env.main(["--env", str(env), "--template", str(TEMPLATE_PATH), *extra])


def test_sync_keeps_values_and_migrates(env, capsys):
    assert _run(env) == 0
    new = sync_env.parse_env(env.read_text(encoding="utf-8"))
    assert new["DEEPSEEK_API_KEY"] == "sk-deep-SECRET"
    assert new["GLM_MODEL"] == "glm-5.4"
    assert "DEEPSEEK_MODEL_PRO" not in new
    assert new["TYPESAFE_API_KEY"] == "ts-SECRET"
    assert "OPENROUTER_API_KEY" not in new
    assert new["JEV_MODEL"] == "jev-1.14.0"
    assert new["MY_EXTRA"] == "1"
    # Every template variable is present.
    template = sync_env.parse_env(TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert set(template) <= set(new)
    out = capsys.readouterr().out
    assert "SECRET" not in out
    assert "TYPESAFE_API_KEY: set" in out
    backups = list(env.parent.glob(".env.bak-*"))
    assert len(backups) == 1 and "DEEPSEEK_MODEL_PRO" in backups[0].read_text(encoding="utf-8")
    assert b"\r\n" not in env.read_bytes()


def test_real_openrouter_key_stays(env):
    env.write_text("OPENROUTER_API_KEY=sk-or-v1-abc\nJEV_MODEL=typesafe/jev-1.14\n", encoding="utf-8")
    _run(env)
    new = sync_env.parse_env(env.read_text(encoding="utf-8"))
    assert new["OPENROUTER_API_KEY"] == "sk-or-v1-abc"
    assert new["JEV_MODEL"] == "typesafe/jev-1.14"
    assert not new.get("TYPESAFE_API_KEY")


def test_dry_run_writes_nothing(env):
    before = env.read_bytes()
    assert _run(env, "--dry-run") == 0
    assert env.read_bytes() == before
    assert not list(env.parent.glob(".env.bak-*"))


def test_second_run_is_a_no_op(env, capsys):
    _run(env)
    capsys.readouterr()
    _run(env)
    assert "Already up to date." in capsys.readouterr().out


def test_template_has_no_removed_or_stale_names():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    active = sync_env.parse_env(template)
    assert "DEEPSEEK_MODEL_PRO" not in active
    assert "OPENROUTER_API_KEY" not in active
    assert active["JEV_MODEL"] == "jev-1.14.0"
    assert "TYPESAFE_API_KEY" in active
