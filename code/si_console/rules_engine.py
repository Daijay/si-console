# The rules engine is deterministic code, not an LLM. The LLM writes the
# explanation. This file computes the numbers. That split is the
# whole point: a rules engine is fast, testable, and repeatable. A
# booth demo needs the same result every time. A local LLM must never
# make a trade. In v1 there is no local LLM in the loop at all.
# The engine must never use data after the replay date. That is the
# lookahead rule. It is tested by a unit test in tests/. The test
# checks the max date used. If the engine ever reads a future close,
# the test must fail. Price only. No news, no earnings, no
# fundamentals in the ranking. Web search is for background research
# notes only, never for the ranking itself.
# Replay rules: weekly rebalance, max 3 sectors, equal weight, 10
# percent cash, cost 0. Confirmed 2026-11-28. The numbers live in
# config.py and this file reads them at call time, so the engine and
# the screen text cannot drift. A change is one edit in config, and
# the output below changes with it. Do not copy a number into this
# file.
"""Rules engine. Price only sector ranking, deterministic, no LLM."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from si_console import config

SECTOR_TICKERS = [
    "XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLB", "XLU",
    "XLRE", "XLC",
]


@dataclass
class SectorScore:
    """One sector, with its numbers. The LLM explains, it does not rank."""

    ticker: str
    momentum: float
    relative_strength_vs_spy: float
    weight: float = 0.0
    has_data: bool = True


def _read_prices(ticker: str, replay_date: date) -> list[tuple[date, float]]:
    """Read one price CSV, up to the replay date only. Never after.

    Price files live in data/market/, outside the vault. Each file is
    named TICKER.csv with date and close columns. A row after the
    replay date is dropped, not used. The unit test checks this.
    """
    path = Path(config.DATA_DIR) / f"{ticker}.csv"
    rows: list[tuple[date, float]] = []
    if not path.is_file():
        return rows
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                day = date.fromisoformat(row["date"])
                close = float(row["close"])
            except (KeyError, ValueError):
                continue
            if day <= replay_date:
                rows.append((day, close))
    rows.sort()
    return rows


def _has_history(rows: list[tuple[date, float]]) -> bool:
    """Enough rows for a momentum number, with a usable start price."""
    lookback = config.REPLAY_LOOKBACK_DAYS
    return len(rows) >= lookback + 1 and rows[-lookback - 1][1] != 0


def _momentum(rows: list[tuple[date, float]]) -> float:
    """Simple momentum: close now divided by close N trading days ago.

    Returns 0 when there is not enough history. No history, no signal.
    The engine never invents a price. It says it has no data.
    """
    lookback = config.REPLAY_LOOKBACK_DAYS
    if len(rows) < lookback + 1:
        return 0.0
    now = rows[-1][1]
    then = rows[-lookback - 1][1]
    if then == 0:
        return 0.0
    return now / then - 1.0


def rank_sectors(replay_date: date) -> dict:
    """Rank sectors from price only, up to the replay date.

    Returns ranked sectors, the SPY momentum for comparison, the
    proposed equal weight allocation, and the rules used, so the
    screen can show them. The ranking is deterministic: the same
    date and the same files always give the same answer.
    """
    spy_rows = _read_prices("SPY", replay_date)
    spy_momentum = _momentum(spy_rows)
    spy_has_data = _has_history(spy_rows)
    scored: list[SectorScore] = []
    for ticker in SECTOR_TICKERS:
        rows = _read_prices(ticker, replay_date)
        mom = _momentum(rows)
        scored.append(
            SectorScore(
                ticker=ticker,
                momentum=mom,
                relative_strength_vs_spy=mom - spy_momentum,
                has_data=_has_history(rows),
            )
        )
    # A sector with no price history has momentum 0, which would beat
    # SPY in any falling market and get bought on no data at all. No
    # history, no signal: rank it last and never propose it. With no
    # SPY history there is no benchmark, so hold cash.
    scored.sort(key=lambda s: (s.has_data, s.relative_strength_vs_spy), reverse=True)
    top = [
        s
        for s in scored[: config.REPLAY_MAX_SECTORS]
        if spy_has_data and s.has_data and s.relative_strength_vs_spy > 0
    ]
    investable = 1.0 - config.REPLAY_CASH_RESERVE
    weight = investable / len(top) if top else 0.0
    for sector in top:
        sector.weight = weight
    return {
        "replay_date": replay_date.isoformat(),
        "spy_momentum": round(spy_momentum, 4),
        "spy_has_data": spy_has_data,
        "ranked": [
            {
                "ticker": s.ticker,
                "momentum": round(s.momentum, 4),
                "relative_strength_vs_spy": round(s.relative_strength_vs_spy, 4),
                "weight": round(s.weight, 4),
                "has_data": s.has_data,
            }
            for s in scored
        ],
        "proposed": [
            {"ticker": s.ticker, "weight": round(s.weight, 4)} for s in top
        ],
        "rules": {
            "rebalance": config.REPLAY_REBALANCE,
            "max_sectors": config.REPLAY_MAX_SECTORS,
            "cash_reserve": config.REPLAY_CASH_RESERVE,
            "cost_per_trade": config.REPLAY_COST_PER_TRADE,
            "lookback_days": config.REPLAY_LOOKBACK_DAYS,
            "price_only": True,
            "dividends_ignored": True,
        },
        "proposal_text": (
            "Buy " + ", ".join(
                f"{s.ticker} {round(s.weight * 100)} percent" for s in top
            )
            if top
            else "Hold cash. No sector beats SPY."
        ),
    }


def main() -> None:
    """Command line entry, so shell_run can call it. Usage:
    python3 rules_engine.py 2022-06-15
    Prints the ranking as JSON. No LLM is involved.
    """
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 rules_engine.py YYYY-MM-DD")
        raise SystemExit(2)
    try:
        replay_date = date.fromisoformat(sys.argv[1])
    except ValueError:
        print("Bad date. Usage: python3 rules_engine.py YYYY-MM-DD")
        raise SystemExit(2) from None
    print(json.dumps(rank_sectors(replay_date), indent=2))


if __name__ == "__main__":
    main()
