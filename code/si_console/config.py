# Settings for SI Console. They come from .env with defaults. Keys come
# from .env only and are never logged. Model tiers live in one table, so
# a model changes in one place. Covers the cloud model providers, web
# search, the vault layout, the approval timeout, the round limit and
# the bridge port.
# Secrets live in .env in the project folder. Never in git. Never in
# the vault. Never on screen. The .env.example file shows the names only.
"""Settings for SI Console. Loaded from .env with sane defaults."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# SI_ENV_FILE points at another .env, e.g. to run the smoke check from
# a second checkout. Default: code/.env next to si_console/.
load_dotenv(os.getenv("SI_ENV_FILE", "").strip() or PROJECT_ROOT / ".env")

# --- Vault ---------------------------------------------------------------
# The vault is the single source of truth for tasks. It lives on the Pi.
# Set its location with SI_VAULT_PATH.
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
# No DeepSeek pro model: it is not in the accepted roster
# (docs/MODEL_TIERS.md). The heavy tier T1 is Qwen4 Max.

# Cost cap. The coordinator calls a paid API in a loop, so a daily cap
# in USD limits what a fault can spend. The value of 5 is an estimate.
# When the cap is hit, the coordinator stops calling DeepSeek, logs
# COST_CAP_HIT, and the bridge shows it on screen. No silent loop.
DEEPSEEK_DAILY_CAP_USD = float(os.getenv("SI_DEEPSEEK_DAILY_CAP_USD", "5.0"))
DEEPSEEK_MAX_TOKENS = int(os.getenv("SI_DEEPSEEK_MAX_TOKENS", "2000"))
DEEPSEEK_TIMEOUT_SECONDS = int(os.getenv("SI_DEEPSEEK_TIMEOUT_SECONDS", "30"))

# --- Web search: Zhipu (Z.ai) Web Search API -----------------------------
# Default research search, on the same key as GLM (GLM_API_KEY), so no
# extra account. POST {GLM_BASE_URL}/web_search. Engines on the mainland
# endpoint: search_std (basic, 0.01 CNY per call), search_pro (0.03),
# search_pro_sogou, search_pro_quark (0.05 each). The international
# Z.ai endpoint (api.z.ai) only has search-prime and is picked
# automatically when GLM_BASE_URL points there.
ZHIPU_SEARCH_ENGINE = os.getenv("ZHIPU_SEARCH_ENGINE", "").strip() or "search_std"
ZHIPU_SEARCH_TIMEOUT_SECONDS = int(os.getenv("SI_ZHIPU_SEARCH_TIMEOUT_SECONDS", "15"))

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

# --- Providers (accepted roster, docs/MODEL_TIERS.md 2026-11-25) -------
# Every provider below is reached with an OpenAI-compatible
# /chat/completions call, except Jev, which uses the OpenRouter
# Decisions API (see judge.py). Keys are secrets: .env only, never
# logged or returned. Model ids are NOT hard coded: pin each one in
# .env after checking the provider's own model list, same rule as
# DeepSeek. A provider with no key or no model id is skipped by the
# router, so a tier falls through to its next slot instead of failing.
# Base URLs below were checked against provider docs on 2026-11-24
# (LIKELY: docs read, no live call yet). Test one live call per
# provider from Shenzhen before the booth.

# Tencent Hunyuan (Hy4). T0 backup #1, T2 primary. Tencent moved Hunyuan
# API keys to TokenHub (console.cloud.tencent.com/tokenhub/apikey).
# TokenHub has two independent sites and a key only works on its own:
#   Guangzhou (mainland, default here for the Shenzhen booth):
#     https://tokenhub.tencentcloudmaas.com/v1
#   Singapore (global): https://tokenhub-intl.tencentcloudmaas.com/v1
# The old https://api.hunyuan.cloud.tencent.com/v1 rejects TokenHub keys.
# Model ids are TokenHub's (e.g. hy4-preview); check its model list.
HUNYUAN_API_KEY = os.getenv("HUNYUAN_API_KEY", "").strip()
HUNYUAN_BASE_URL = (
    os.getenv("HUNYUAN_BASE_URL", "").strip() or "https://tokenhub.tencentcloudmaas.com/v1"
)
HY4_MODEL = os.getenv("HY4_MODEL", "").strip()

# Zhipu GLM 5.3 Flash (temporary: the GLM 5.4 API is not out yet; MODEL_TIERS.md picks 5.4). T0 backup #3, T2 #3. Effort is capped at "high" in
# code (MODEL_TIERS.md: max effort burns ~1M reasoning tokens).
# Mainland endpoint by default; the international one is
# https://api.z.ai/api/paas/v4 with its own key.
GLM_API_KEY = os.getenv("GLM_API_KEY", "").strip()
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "").strip() or "https://open.bigmodel.cn/api/paas/v4"
GLM_MODEL = os.getenv("GLM_MODEL", "").strip()

# Alibaba Cloud Model Studio (Bailian / DashScope), Qwen4 Max. T1, the
# only heavy worker. Hong Kong endpoint by default, because the team's
# key is a Hong Kong region key. Keys are regional: a key from one
# region gets 401 on another region's URL. Other regions: Singapore
# https://dashscope-intl.aliyuncs.com/compatible-mode/v1, Beijing
# https://dashscope.aliyuncs.com/compatible-mode/v1. Set
# DASHSCOPE_BASE_URL in .env to change.
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
DASHSCOPE_BASE_URL = (
    os.getenv("DASHSCOPE_BASE_URL", "").strip()
    or "https://cn-hongkong.dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "").strip()
# Judge backup: a small, fast Qwen model on the same Bailian HK key,
# used when Jev does not respond within SI_JEV_TIMEOUT_SECONDS (see
# judge.py). Pin the id from Model Studio's Hong Kong model list.
QWEN_JUDGE_MODEL = os.getenv("QWEN_JUDGE_MODEL", "").strip()
QWEN_JUDGE_TIMEOUT_SECONDS = int(os.getenv("SI_QWEN_JUDGE_TIMEOUT_SECONDS", "5"))

# Xiaomi MiMo 2.6 Flash. T3, the only small model.
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "").strip()
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "").strip() or "https://api.xiaomimimo.com/v1"
MIMO_MODEL = os.getenv("MIMO_MODEL", "").strip()

# Jev 1.14 judge (TypeSafe), through OpenRouter's Decisions API.
# Typed decisions only: ambiguous routing, winner pick, tab promotion.
# Never a worker, never bypasses GUARD. The URL is configurable so the
# judge can be moved to another decisions endpoint without code edits.
# Direct TypeSafe key by default (POST https://api.typesafe.ai/v1/systemone,
# model ids like jev-1.14.0 or jev-latest, docs.typesafe.ai). An
# OpenRouter key also works: leave TYPESAFE_API_KEY empty and the judge
# uses OpenRouter's Decisions API with ids like typesafe/jev-1.14.
# Request and answer shapes are the same on both routes.
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
TYPESAFE_JEV_URL = "https://api.typesafe.ai/v1/systemone"
OPENROUTER_JEV_URL = "https://openrouter.ai/api/alpha/decisions"
_jev_url = os.getenv("JEV_URL", "").strip()
if TYPESAFE_API_KEY or not OPENROUTER_API_KEY:
    JEV_PROVIDER = "typesafe"
    JEV_API_KEY = TYPESAFE_API_KEY
    JEV_URL = _jev_url or TYPESAFE_JEV_URL
else:
    JEV_PROVIDER = "openrouter"
    JEV_API_KEY = OPENROUTER_API_KEY
    JEV_URL = _jev_url or OPENROUTER_JEV_URL
JEV_MODEL = os.getenv("JEV_MODEL", "").strip()
JEV_TIMEOUT_SECONDS = int(os.getenv("SI_JEV_TIMEOUT_SECONDS", "5"))

# One timeout for every chat provider. DeepSeek keeps its own setting.
PROVIDER_TIMEOUT_SECONDS = int(os.getenv("SI_PROVIDER_TIMEOUT_SECONDS", "30"))

# --- Model tiers ---------------------------------------------------------
# Callers ask for a tier, never a model. The router in models.py walks
# the tier's chain in order and falls back on any failure. The chains
# are the accepted roster in docs/MODEL_TIERS.md:
#   T0 orchestrator : DeepSeek V4.1 Flash -> Hy4 -> GLM 5.3 Flash
#   T1 heavy        : Qwen4 Max -> escalate_to_human
#   T2 medium       : Hy4 -> DeepSeek V4.1 Flash -> GLM 5.3 Flash
#   T3 small        : MiMo 2.6 Flash -> $0 code paths
# Claude is not in the roster and there is no Anthropic client. It is
# never called from the booth build (Anthropic does not support use
# from mainland China). CLAUDE_ENABLED stays as a policy flag only.
CLAUDE_ENABLED = os.getenv("SI_CLAUDE_ENABLED", "false").strip().lower() == "true"
CLAUDE_MODEL_PREMIUM = os.getenv("SI_CLAUDE_MODEL_PREMIUM", "").strip() or "claude-opus-5-5"

T0 = "t0"
T1 = "t1"
T2 = "t2"
T3 = "t3"
NARRATION = "narration"
# Older names, kept so existing callers keep working. They now point
# at the accepted tiers, not at DeepSeek only.
COORDINATOR = T0
WORKER = T2
PREMIUM = T1
LIGHT = T3
TIER_ALIASES = {
    "coordinator": T0,
    "orchestrator": T0,
    "worker": T2,
    "medium": T2,
    "premium": T1,
    "heavy": T1,
    "light": T3,
    "small": T3,
}

# Slot id -> provider and the config attribute that holds its model id.
# Slot ids are the pin values operators use (SI_ORCH_A=hy4 and so on).
MODEL_SLOTS = {
    "deepseek-v4.1-flash": {"provider": "deepseek", "model_attr": "DEEPSEEK_MODEL"},
    "hy4": {"provider": "hunyuan", "model_attr": "HY4_MODEL"},
    "glm-5.3-flash": {"provider": "glm", "model_attr": "GLM_MODEL"},
    "qwen4-max": {"provider": "dashscope", "model_attr": "QWEN_MODEL"},
    "mimo-2.6-flash": {"provider": "mimo", "model_attr": "MIMO_MODEL"},
}
# GLM runs 5.3 Flash until the GLM 5.4 API is out (team decision
# 2026-11-26; MODEL_TIERS.md picks 5.4). An old pin or allowlist entry
# that says glm-5.4 still means the GLM slot. When 5.4 ships: rename
# the slot back, swap the price in telemetry.py, re-pin GLM_MODEL.
SLOT_ALIASES = {"glm-5.4": "glm-5.3-flash"}

MODEL_TIERS = {
    # Tool calling needs thinking off, so the orchestrator never thinks.
    T0: {
        "chain": ["deepseek-v4.1-flash", "hy4", "glm-5.3-flash"],
        "max_tokens": DEEPSEEK_MAX_TOKENS,
        "thinking": "disabled",
        "on_exhausted": "error",
    },
    # Thinking off by default: DashScope documents that some models
    # reject enable_thinking=true on non-streaming calls, which would
    # turn every heavy task into an escalation. ASSUMED until one live
    # Qwen4 Max call with thinking on is tested; then flip to "high".
    T1: {
        "chain": ["qwen4-max"],
        "max_tokens": 4000,
        "thinking": "disabled",
        "on_exhausted": "escalate_to_human",
    },
    T2: {
        "chain": ["hy4", "deepseek-v4.1-flash", "glm-5.3-flash"],
        "max_tokens": 1500,
        "thinking": "low",
        "on_exhausted": "error",
    },
    T3: {
        "chain": ["mimo-2.6-flash"],
        "max_tokens": 600,
        "thinking": "disabled",
        "on_exhausted": "zero_path",
    },
    # No model call at all: prewritten EN/ZH sentences from strings.json.
    NARRATION: {
        "chain": [],
        "max_tokens": 0,
        "thinking": "disabled",
        "on_exhausted": "prewritten",
    },
}

# --- Arena panes (MODEL_TIERS.md "Configurable model selection") ------
# Three orchestrator panes, A, B and C. Each can be pinned to one T0
# slot or left on "auto" (T0 chain order). A pinned pane falls back
# down the T0 chain from its pinned position only when its FALLBACK
# setting is yes. Each pane has a T2 allowlist ("all", "none", or a
# comma list of T2 slot ids) and can be denied T1 (SI_ORCH_A_T1=off).
# Defaults follow the doc's table: A auto (DeepSeek), B Hy4, C GLM 5.3 Flash.
PANES = ("A", "B", "C")
_PANE_DEFAULT_PIN = {"A": "auto", "B": "hy4", "C": "glm-5.3-flash"}


def _pane_setting(pane: str, suffix: str, default: str) -> str:
    key = f"SI_ORCH_{pane}{suffix}"
    value = os.getenv(key, "").strip().lower() or default
    # Map aliases inside pins and comma lists (e.g. glm-5.4).
    return ",".join(SLOT_ALIASES.get(part.strip(), part.strip()) for part in value.split(","))


PANE_CONFIG = {
    pane: {
        "pin": _pane_setting(pane, "", _PANE_DEFAULT_PIN[pane]),
        "t2": _pane_setting(pane, "_T2", "all"),
        "t1": _pane_setting(pane, "_T1", "on"),
        "fallback": _pane_setting(pane, "_FALLBACK", "yes"),
    }
    for pane in PANES
}
# The pane a single coordinator process serves (one process per pane).
COORDINATOR_PANE = os.getenv("SI_COORDINATOR_PANE", "").strip().upper() or "A"

# --- Telemetry -----------------------------------------------------------
# SQLite: route, pane, tier, slot, model, tokens, latency, cost, error
# code. Never prompt text, never keys, never personal data.
TELEMETRY_PATH = Path(
    os.getenv("SI_TELEMETRY_PATH", "").strip() or PROJECT_ROOT / "telemetry.sqlite"
)

# --- Scheduler -----------------------------------------------------------
# APScheduler, one job per task. A job missed by less than 1 hour still
# runs, missed runs are merged into one, and a job never overlaps itself.
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
# with SHELL_DENY, so a model can only run commands on this list.
ALLOWED_SHELL_COMMANDS = {
    "python3 rules_engine.py",
    "python3 make_slides.py",
    "ls",
    "vcgencmd measure_temp",
    "vcgencmd get_throttled",
    "free",
    "df",
}
