# Telemetry to SQLite, per ARCHITECTURE.md "Memory and state" and
# MODEL_TIERS.md selection rule 5: every model selection is logged with
# route, pane, tier, slot, model, tokens, latency, cost and error code.
# The vault records what happened; this records how it ran.
# Never stored: prompt text, replies, keys, personal data.
# A telemetry failure never breaks a model call. It is swallowed.
"""SQLite telemetry for routing and model calls."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from si_console import config

# Upper-bound USD per 1M tokens (input, output), from the accepted
# roster in docs/MODEL_TIERS.md. Used for the cost column only. Update
# from the provider pricing pages; never used to make a decision.
PRICES_PER_M = {
    "deepseek-v4.1-flash": (0.30, 1.20),
    "hy4": (0.83, 2.50),
    "glm-5.3-flash": (0.15, 0.50),  # MODEL_TIERS.md culled table
    "qwen4-max": (1.50, 4.50),
    "mimo-2.6-flash": (0.14, 0.28),
    "jev": (0.042, 0.0),
    # Small Qwen judge backup on Bailian: ceiling estimate, not a quote.
    "qwen-judge": (0.30, 1.20),
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS model_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    pane TEXT,
    tier TEXT,
    slot TEXT,
    provider TEXT,
    model TEXT,
    route_reason TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    latency_ms INTEGER,
    cost_usd REAL,
    ok INTEGER NOT NULL,
    error_code TEXT
)
"""

_lock = threading.Lock()


def estimate_cost(slot: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES_PER_M.get(slot, (0.0, 0.0))
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 8)


def _connect() -> sqlite3.Connection:
    path = Path(config.TELEMETRY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=2)
    conn.execute(_SCHEMA)
    return conn


def record(
    *,
    kind: str,
    pane: str = "",
    tier: str = "",
    slot: str = "",
    provider: str = "",
    model: str = "",
    route_reason: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int = 0,
    ok: bool = True,
    error_code: str = "",
) -> None:
    """Write one row. kind is "chat", "judge" or "route"."""
    try:
        cost = estimate_cost(slot, input_tokens, output_tokens)
        with _lock:
            conn = _connect()
            try:
                conn.execute(
                    "INSERT INTO model_calls (ts, kind, pane, tier, slot, provider, model,"
                    " route_reason, input_tokens, output_tokens, latency_ms, cost_usd, ok,"
                    " error_code) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        kind,
                        pane,
                        tier,
                        slot,
                        provider,
                        model,
                        route_reason[:200],
                        int(input_tokens or 0),
                        int(output_tokens or 0),
                        int(latency_ms or 0),
                        cost,
                        1 if ok else 0,
                        error_code[:80],
                    ),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:  # noqa: BLE001 - telemetry must never break a call
        pass


def rows(limit: int = 100) -> list[dict]:
    """Newest rows first, for the dashboard and for tests."""
    try:
        conn = _connect()
    except Exception:  # noqa: BLE001
        return []
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM model_calls ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
