# One time fetch of the replay price data. Not part of the running
# console: the booth must work offline, so the CSVs are committed and
# this script is only re-run to refresh them. It uses the public
# Yahoo chart endpoint, no key, no login.
#
# Output: data/market/TICKER.csv with two columns, date,close.
# close is the adjusted close, so splits and dividends do not fake a
# price jump. The rules engine reads only these two columns.
#
# Range: 2019-01-01 to 2023-12-31. The 2020 and 2022 scenarios need
# 60 trading days of history before the replay date, and 2019 gives
# that. No row after 2023 is fetched, so a stray later file can never
# leak into a replay.
#
# Usage: python -m tools.fetch_market_data  (from code/)
"""Fetch daily closes for the sector ETFs and SPY into data/market/."""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from si_console import config  # noqa: E402
from si_console.rules_engine import SECTOR_TICKERS  # noqa: E402

TICKERS = list(SECTOR_TICKERS) + ["SPY"]
START = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp())
END = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?period1={start}&period2={end}&interval=1d&events=div%7Csplit"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (si-console data fetch)"}


def fetch(ticker: str) -> list[tuple[str, float]]:
    """One ticker, as (date, adjusted close) rows. Raises on a bad reply."""
    url = URL.format(ticker=ticker, start=START, end=END)
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload["chart"]["result"][0]
    stamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    adj = (result["indicators"].get("adjclose") or [{}])[0].get("adjclose")
    closes = adj if adj else quote["close"]
    rows: list[tuple[str, float]] = []
    for stamp, close in zip(stamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat()
        rows.append((day, round(float(close), 4)))
    return rows


def main() -> None:
    target = Path(config.DATA_DIR)
    target.mkdir(parents=True, exist_ok=True)
    for index, ticker in enumerate(TICKERS):
        rows = fetch(ticker)
        if not rows:
            raise SystemExit(f"No rows for {ticker}. Nothing written.")
        path = target / f"{ticker}.csv"
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["date", "close"])
            writer.writerows(rows)
        print(f"{ticker}: {len(rows)} rows, {rows[0][0]} to {rows[-1][0]}")
        if index + 1 < len(TICKERS):
            time.sleep(1.5)  # be polite to a free endpoint


if __name__ == "__main__":
    main()
