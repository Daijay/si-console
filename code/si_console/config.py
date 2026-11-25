# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# This file is Autumn's autumn/config.py, rewired for SI Console.
# What changed: Gmail and OAuth are gone. Groq and Anthropic are gone.
# DeepSeek is the only cloud model. Bocha is the web search provider.
# New settings: vault layout, approval timeout, round limit, bridge port.
# What stayed: settings come from .env with defaults, keys come from
# .env only and are never logged, and model tiers live in one table.
# Secrets live in .env in the project folder. Never in git. Never in
# the vault. Never on screen. The .env.example file shows the names only.
"""Settings for SI Console. Loaded from .env with sane defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

# --- Vault ---------------------------------------------------------------
# The vault is the single source of truth for tasks. It lives on the Pi.
# Autumn used AUTUMN_VAULT_PATH. SI Console uses SI_VAULT_PATH.
# The .env.example file shows a Linux path, not a Windows path.
_vault = os.getenv("SI_VAULT_PATH")
VAULT_PATH = Path(_vault) if _vault else PROJECT_ROOT / "vault" / "si-console"

# Folders inside the vault that never hold real notes.
VAULT_IGNORE_DIRS = {".obsidian", ".trash", ".git", "node_modules", ".venv"}

# State file for the screens. Outside the vault. The dashboard reads it.
# The vault wins if state.json and the vault ever disagree.
# "or" and not a getenv default: an empty SI_STATE_PATH= line in .env
# must fall back to the default, not become Path("") (the cwd).
STATE_PATH = Path(os.getenv("SI_STATE_PATH", "").strip() or PROJECT_ROOT / "state.json")

# Claims file for external agents. Outside the vault. See bridge.py.
CLAIMS_PATH = Path(os.getenv("SI_CLAIMS_PATH", "").strip() or PROJECT_ROOT / "claims.json")

# Price data lives outside the vault, so the bridge never parses big files.
DATA_DIR = Path(os.getenv("SI_DATA_DIR", "").strip() or PROJECT_ROOT / "data" / "market")

# --- DeepSeek ------------------------------------------------------------
# Secret. From .env only. Never logged or returned.
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
).strip()

# The model name is NOT hard coded here. It is pinned in .env at build
# time, after checking the official DeepSeek platform page. VERIFIED
# on the official DeepSeek docs 2026-11-23: the current models are
# deepseek-flash (V4.1-Flash-1017) and deepseek-v4-pro (V4-Pro-0813).
# deepseek-chat and deepseek-reasoner are retired since July 24, 2026.
# deepseek-v4-flash is also retired. The name still routes to V4.1
# Flash for now, but do not pin it. Pin deepseek-flash instead.
# Never hard code deepseek-chat in code. If the pinned model is gone,
# the build must fail loudly at startup, not silently fall back.
# A thinking model must never be the coordinator model. The
# coordinator needs tool calling with thinking disabled. See the
# thinking flag in deepseek_client.py.
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "").strip()

# Optional higher tier model, also from .env, also never hard coded.
# VERIFIED 2026-11-23: deepseek-v4-pro is current. Empty means the
# premium tier is off. A caller that asks for the premium tier with
# this empty gets a loud error, not a silent downgrade. See models.py.
DEEPSEEK_MODEL_PRO = os.getenv("DEEPSEEK_MODEL_PRO", "").strip()

# Cost cap. ARCHITECTURE.md has no daily cap, and INTEGRATION.md flags
# that as a gap. This is the fix: a daily cap in USD, ASSUMED at 5.
# When the cap is hit, the coordinator stops calling DeepSeek, logs
# COST_CAP_HIT, and the bridge shows it on screen. No silent loop.
DEEPSEEK_DAILY_CAP_USD = float(os.getenv("SI_DEEPSEEK_DAILY_CAP_USD", "5.0"))
DEEPSEEK_MAX_TOKENS = int(os.getenv("SI_DEEPSEEK_MAX_TOKENS", "2000"))
DEEPSEEK_TIMEOUT_SECONDS = int(os.getenv("SI_DEEPSEEK_TIMEOUT_SECONDS", "30"))

# --- Bocha web search ----------------------------------------------------
# Secret. From .env only. Never logged or returned.
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY", "").strip()
# Two domains appear in sources: api.bochaai.com and api.bocha.cn.
# Put the base URL in config, test both from Canada before travel,
# test again in Shenzhen, use the one that answers. Do not hard code one.
BOCHA_BASE_URL = os.getenv(
    "BOCHA_BASE_URL", "https://api.bochaai.com/v1/web-search"
).strip()
BOCHA_TIMEOUT_SECONDS = int(os.getenv("SI_BOCHA_TIMEOUT_SECONDS", "15"))

# --- Bridge API ----------------------------------------------------------
# One token for external agents. A long random string, made at build time.
# Stored only in .env on the Pi and in Jayden's password manager.
# Never in a task note. Never on screen. Never logged.
BRIDGE_API_TOKEN = os.getenv("BRIDGE_API_TOKEN", "").strip()
BRIDGE_HOST = os.getenv("SI_BRIDGE_HOST", "127.0.0.1")
BRIDGE_PORT = int(os.getenv("SI_BRIDGE_PORT", "8001"))
DASHBOARD_PORT = int(os.getenv("SI_DASHBOARD_PORT", "8000"))

# --- Coordinator ---------------------------------------------------------
ROUND_LIMIT = int(os.getenv("SI_ROUND_LIMIT", "3"))
APPROVAL_TIMEOUT_SECONDS = int(os.getenv("SI_APPROVAL_TIMEOUT_SECONDS", "120"))
STUCK_SECONDS = int(os.getenv("SI_STUCK_SECONDS", "300"))
WATCHDOG_INTERVAL_SECONDS = int(os.getenv("SI_WATCHDOG_INTERVAL_SECONDS", "30"))

# --- Modes and replay ----------------------------------------------------
MODE = os.getenv("SI_MODE", "booth").strip()  # home or booth
REPLAY_SCENARIO = os.getenv("SI_REPLAY_SCENARIO", "2020").strip()  # 2020 or 2022
LANG = os.getenv("SI_LANG", "en").strip()  # en or zh

# --- Model tiers ---------------------------------------------------------
# Copied from Autumn config.MODEL_TIERS. Callers ask for a tier, never
# a model. Moving a feature between tiers is a one word edit.
#   coordinator: the agent loop. Needs tool calling. DeepSeek chat model.
#   worker:      research and explanation. Same model, smaller budget.
#   narration:   booth narration. No model call at all. Prewritten
#                bilingual sentences from strings.json. This tier exists
#                so code that asks for narration never reaches for a
#                local LLM by accident. ARCHITECTURE.md drops Qwen in v1.
#   premium:     optional higher tier. DeepSeek pro model only, never
#                a Claude model in the booth build. See CLAUDE_ENABLED.
# Claude is never called from this code. CLAUDE_ENABLED is a policy
# flag, default false. When false, the router in models.py maps every
# tier to a DeepSeek model and never touches Anthropic. This is on
# purpose. Claude Fable 5.2 is real, but it costs 8 USD input and 40
# USD output per 1M tokens, about 27 times DeepSeek flash input, and
# Anthropic policy does not support use by persons physically in
# mainland China, Hong Kong, or Macau, VERIFIED on Anthropic's own
# Supported Regions page 2026-11-23. The booth is in Shenzhen. The
# booth build ships with CLAUDE_ENABLED false and no Anthropic key
# in .env, so the code cannot call Claude even by accident. If the
# team later wants Claude for home use in Canada, the change is one
# flag and one key in .env. The coordinator loop does not change.
# There is no Anthropic client in this codebase. Do not add one for
# the booth build. The router stub is a table and a flag, not a
# second provider client.
CLAUDE_ENABLED = os.getenv("SI_CLAUDE_ENABLED", "false").strip().lower() == "true"
# The Claude model string a premium tier would name if Claude were
# ever enabled for home use. It is a name only. Nothing in this code
# calls it. claude-opus-5-5 is the daily driver, not Fable. Fable
# is too expensive for any tier here. VERIFIED on Anthropic docs
# 2026-11-23: claude-opus-5-5 is 4 USD input and 20 USD output per
# 1M tokens, claude-fable-5-2 is 8 and 40 USD.
CLAUDE_MODEL_PREMIUM = os.getenv("SI_CLAUDE_MODEL_PREMIUM", "").strip() or "claude-opus-5-5"
LIGHT = "light"
COORDINATOR = "coordinator"
WORKER = "worker"
NARRATION = "narration"
PREMIUM = "premium"

MODEL_TIERS = {
    COORDINATOR: {
        "provider": "deepseek",
        "model": DEEPSEEK_MODEL,
        "max_tokens": DEEPSEEK_MAX_TOKENS,
    },
    WORKER: {
        "provider": "deepseek",
        "model": DEEPSEEK_MODEL,
        "max_tokens": 1200,
    },
    NARRATION: {
        "provider": "prewritten",
        "model": "strings.json",
        "max_tokens": 0,
    },
    # Premium tier. DeepSeek pro model when DEEPSEEK_MODEL_PRO is set.
    # The router in models.py enforces this. If the pro model is not
    # set, asking for premium is a loud error, not a silent downgrade.
    PREMIUM: {
        "provider": "deepseek",
        "model": DEEPSEEK_MODEL_PRO,
        "max_tokens": DEEPSEEK_MAX_TOKENS,
    },
    # LIGHT is kept as an alias for WORKER, so Autumn callers that ask
    # for LIGHT still work. It is the same DeepSeek model, not Groq.
    LIGHT: {
        "provider": "deepseek",
        "model": DEEPSEEK_MODEL,
        "max_tokens": 1200,
    },
}

# --- Scheduler -----------------------------------------------------------
# Copied from Autumn server.py and briefing.py. APScheduler, one job
# per task, misfire grace 1 hour, coalesce true, max instances 1.
BRIEFING_HOUR = int(os.getenv("SI_BRIEFING_HOUR", "11"))
BRIEFING_MINUTE = int(os.getenv("SI_BRIEFING_MINUTE", "0"))
SCHEDULER_MISFIRE_GRACE_SECONDS = int(
    os.getenv("SI_SCHEDULER_MISFIRE_GRACE_SECONDS", "3600")
)

# --- Allow lists ---------------------------------------------------------
# Tickers the coordinator may use. Anything else is rejected with
# BAD_TICKER. Sector ETFs plus SPY, price only, no news tickers.
ALLOWED_TICKERS = {
    "SPY", "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLB", "XLU",
    "XLRE", "XLC",
}

# Shell commands the shell_run tool may run. Anything else is rejected
# with SHELL_DENY. Copied from ARCHITECTURE.md section 5.2.
ALLOWED_SHELL_COMMANDS = {
    "python3 rules_engine.py",
    "python3 make_slides.py",
    "ls",
    "vcgencmd measure_temp",
    "vcgencmd get_throttled",
    "free",
    "df",
}
