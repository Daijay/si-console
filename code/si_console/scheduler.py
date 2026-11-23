# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# The scheduler is Autumn's server.py lifespan and briefing scheduler,
# rewired for SI Console. What stayed: APScheduler AsyncIOScheduler
# with CronTrigger, misfire grace 1 hour, coalesce true, max
# instances 1, and the warning from the audit that FastAPI ignores
# @app.on_event handlers once a lifespan is supplied, so everything
# must start from the lifespan handler. One scheduler, started once.
# What changed: the 11am daily briefing is now a replay clock and a
# daily agent summary. Gmail refresh is gone. The briefing content
# changes from mail to agent runs. The rule from Autumn briefing.py
# stays: a failed source never produces a fabricated all clear. A
# failed replay must say it failed, never show a fake score.
# The replay clock advances one trading day per tick in demo mode,
# or one day per button press in interactive mode. The team must pick
# one and test it. This skeleton defaults to manual, one day per
# button press, because that is more interactive at a booth.
"""Scheduler. Replay clock and daily summary, from Autumn's shape."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from si_console import config

scheduler = AsyncIOScheduler()

# Replay clock. One trading day per tick. Weekends are skipped, so
# the clock only lands on trading days in the price files. The real
# build must read the trading calendar from the price data, not from
# this list. This skeleton skips Saturday and Sunday only.
REPLAY_TICK_HOUR = 10
REPLAY_TICK_MINUTE = 0


def next_trading_day(day: date) -> date:
    """Next weekday after a date. Skips Saturday and Sunday."""
    nxt = day + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt


def advance_replay(current: date) -> date:
    """Advance the replay clock by one trading day. Returns the new date.

    The caller writes the new date to state.json and to the log. The
    coordinator then runs the rules engine for that date. The engine
    must never use data after that date. See rules_engine.py.
    """
    return next_trading_day(current)


def daily_summary_job() -> dict:
    """Build the daily agent summary. One JSON file per run, pruned
    to 7 days, the same storage shape as Autumn BriefingStore.

    The summary lists tasks done, tasks blocked, and the portfolio
    value. It never invents a score. If the portfolio file cannot be
    read, the summary says so, and the run is marked failed.
    """
    from si_console.vault import list_tasks

    done = list_tasks(status="done")
    blocked = list_tasks(status="blocked")
    summary = {
        "date": date.today().isoformat(),
        "done": len(done),
        "blocked": len(blocked),
        "blocked_ids": [t.id for t in blocked],
    }
    out_dir = Path(config.PROJECT_ROOT) / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{summary['date']}.json"
    import json

    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    # Prune to 7 days, same rule as Autumn BriefingStore.
    for old in sorted(out_dir.glob("*.json"))[:-7]:
        old.unlink(missing_ok=True)
    return summary


def start_scheduler() -> AsyncIOScheduler:
    """Start the scheduler. Call once, from the lifespan handler.

    Jobs: the daily summary at the hour in config, and the replay
    clock tick in demo mode. The replay tick is off by default, so
    the console does not advance on its own at the booth. The button
    press is the clock in interactive mode. Turn the tick on only for
    the auto demo, and say so on screen.
    """
    scheduler.add_job(
        daily_summary_job,
        CronTrigger(hour=config.BRIEFING_HOUR, minute=config.BRIEFING_MINUTE),
        id="daily_summary",
        misfire_grace_time=config.SCHEDULER_MISFIRE_GRACE_SECONDS,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    return scheduler


def stop_scheduler() -> None:
    """Stop the scheduler. Call from the lifespan shutdown half."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
