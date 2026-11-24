# SI Console — Software Architecture (writeup)

DRAFT. Authoritative: `docs/ARCHITECTURE.md`. Diagrams: `docs/ARCHITECTURE_DIAGRAMS.md`.

Two systemd services run on the Pi 5. The **bridge** (FastAPI :8001) is the only process touching GPIO: buttons, LEDs, vault watcher, and `state.json` cache for the dashboards. The **coordinator** picks a queued task, builds a short context, calls DeepSeek with a fixed JSON action menu, validates every reply, runs GUARD checks, and writes results back to the vault — never touching hardware.

The **vault** (markdown notes, strict YAML frontmatter, atomic writes, `[[wikilinks]]`) is the source of truth; `state.json` is a cache rebuilt on start. External agents use a token-protected, home-LAN-only API (off in booth) to claim research/narration work only — never approve, execute, or edit code.

Safety is code, not prompts: a normally-closed kill switch (GPIO22) freezes everything without auto-resume, and GUARD deterministically checks kill, role, human approval, and risk before any tool. One green press approves one action; red rejects. Sector ranking is a deterministic rules engine with a no-lookahead test; the LLM only explains. The router fails closed to DeepSeek (flash + pro), Bocha for research only.

The merged v1 spec is the target: explicit state machine, rules-only router, default-deny policy, injection guard, SQLite telemetry, offline replay. The skeleton implements vault, bridge, GUARD, coordinator and DeepSeek client (89 tests pass); the rest are documented gaps with owners.
