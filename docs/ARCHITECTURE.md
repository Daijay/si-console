# SI CONSOLE AGENT ARCHITECTURE, MERGED v1 (Jayden + Christopher)

Status: AUTHORITATIVE. Single source of truth for agent runtime design.
Date: 2026-11-23. Owners: Jayden (vault, bridge, GPIO, offline fallback, integration),
Christopher (router, policy, injection guard, telemetry, state machine code).

The text in the sections below is the merged v1 spec as agreed by Jayden and
Christopher. Section "Implementation gaps" at the end is a provisional reconciliation
with the current `code/` skeleton, added by the code review on 2026-11-23. It
does not change the spec. It lists what the skeleton does not do yet.

## STATE MACHINE (from Christopher, authoritative)

IDLE -> RUNNING -> AWAITING_APPROVAL -> RUNNING|IDLE; any state -> KILLED on hardware kill (GPIO22 NC open). KILLED exits only via kill switch reset + one green press, then new coordinator task; never resume half-finished actions. AWAITING_APPROVAL exits on green (execute), red (reject, back to coordinator), or 120s timeout (treated as reject). LEDs and mini screen render state from this machine only.

## FLOW

user input (push-to-talk STT or Ctrl+K text) -> intake (rejects if KILLED or busy) -> ROUTER (rules-only in v1: skill, keywords, length -> tier) -> COORDINATOR (deepseek flash, fixed JSON action menu, max 3 rounds, then escalate_to_human) -> task prompt handed back to ROUTER (rules-only) -> WORKER selected by tier (see MODEL TIERS below) -> TOOL CALL -> POLICY CHECK (default deny; allowlisted read-only tools run immediately; everything else -> AWAITING_APPROVAL with the exact command shown on screen) -> EXECUTE (own process group, timeout) -> VERIFY RESULT (errors, empty output, step limit) -> back to coordinator.

The ROUTER is the only component that selects a model, and it runs twice: once
at intake to pick the orchestrator, and again per task to pick the worker tier
and model. The COORDINATOR never selects models — it decomposes the job, writes
worker prompts, picks from the fixed 12-action JSON menu, and synthesizes
results. The hard thinking is delegated to workers.

### MODEL TIERS (accepted 2026-11-25 — see `docs/MODEL_TIERS.md`)

The authoritative v1 flow above names two tiers (FAST|THINK). The four-tier
roster in `docs/MODEL_TIERS.md` is **ACCEPTED** as of 2026-11-25. It records
model selection for the runtime and the booth arena. Implemented in `code/` on 2026-11-24 (mocked tests only, no live call yet):
`config.py` tier chains and pane settings, `chat_client.py`, `models.py`,
`router.py`, `judge.py`, `telemetry.py`. The PROVIDERS text below still says
DeepSeek only; updating it is the owners' call.

| Tier | Job | Call volume | Quality need | Latency | Cost tolerance |
|---|---|---|---|---|---|
| T0 Orchestrator | plan, write worker prompts, 12-action menu | highest (up to 3 rounds/task) | tool-call discipline, JSON reliability | strict (human at button) | low — cheapest reliable model wins |
| T1 Heavy workers | hard reasoning, escalations | low | frontier | loose | high — rare calls justify $1.50–4.50/M |
| T2 Medium workers | synthesis, slide drafts, multi-step chains | medium | solid reasoning + tool use | moderate | mid — $0.09–2.50/M |
| T3 Small tasks | summaries, formatting, voice hints, search queries | high | minimal | fast | rock bottom, or $0 |

Accepted placement (fallback chains, in order) — all China-reachable:

```
T0 orchestrator : DeepSeek V4.1 Flash -> Hy4 -> GLM 5.4
T1 heavy        : Qwen4 Max -> escalate_to_human
T2 medium       : Hy4 -> DeepSeek V4.1 Flash -> GLM 5.4
T3 small        : MiMo 2.6 Flash -> $0 code paths (voice_intents.py + prewritten narration)
Judge           : Jev 1.14 (typed decisions; ~100ms; not a worker)
```

Each tier's primary is a different provider (DeepSeek / Qwen4 Max / Hy4 / MiMo),
so no single API outage kills two primaries. Dual-role models (Hy4 T0/T2,
DeepSeek T0/T2, GLM 5.4 T0/T2) appear only as backups or secondaries. GLM 5.4 is
benchmarked (KingBench 4: 33.2, 7/19, top open model); the earlier interim note
is CLOSED and GLM 5.3 Flash is permanently culled. Operators can pin any T0
model per orchestrator pane and restrict each pane's T2 worker pool — see
`docs/MODEL_TIERS.md` §"Configurable model selection". All placements are
implemented in `code/si_console/models.py` and `router.py` (2026-11-24).

## SAFETY (merged)

default-deny policy (Christopher) replaces safe-list. Injection guard taints any web or file content and blocks tainted text from becoming tool arguments without approval (Christopher). GUARD is deterministic code, never an LLM. Hardware kill overrides everything at 100ms poll.

## MEMORY AND STATE (from Jayden)

Obsidian-compatible markdown vault is the source of truth for tasks (one note per task, strict YAML frontmatter, depends_on as [[wikilinks]]); state.json is a cache rebuilt from the vault on restart. Telemetry (Christopher) goes to SQLite: route decisions, model, tokens, latency, cost. Vault = what happened; SQLite = how it ran.

## PROVIDERS

v1 runtime is DeepSeek only (flash + pro) plus web search. Claude is NOT on
the critical path and is never called from the booth build. Booth assumes no
Claude access and possibly no internet. The accepted 2026-11-25 roster adds
Qwen4 Max, GLM 5.4, Hy4, MiMo 2.6 Flash as planned workers and Jev 1.14 as a
judge (typed decisions, ~100ms — winner pick, tab promotion, ambiguous routing;
GUARD retains final authority over physical actions). Jev is not a worker and
never bypasses GUARD; the old optional home-only 0.8s shadow-advisor idea is
superseded. The booth has internet; offline replay is only the failure net.

The accepted multi-provider tier assignments (T0 orchestrator / T1 heavy /
T2 medium / T3 small), benchmark data, final culls, per-orchestrator model
pinning, T2 worker allowlists, and the booth arena cost model are recorded in
`docs/MODEL_TIERS.md`. That document is ACCEPTED as of 2026-11-25 for model
selection; it does not change this v1 spec's runtime.

## OFFLINE (from Jayden)

every live run is recorded to the vault. If DeepSeek or network fails, the console switches automatically to recorded runs for the demo scenarios. No feature may require internet at the booth without this fallback.

## EXTERNAL AGENTS (from Jayden)

token-protected bridge API, home LAN only, off in booth. External agents (Hermes first) may claim tasks and write reports or research notes only; they can never approve, execute, propose trades or edit code.

## OWNERSHIP

Christopher owns router, policy, injection guard, telemetry, state machine code. Jayden owns vault, bridge, GPIO, offline fallback, integration. Pin map is `docs/GPIO_PIN_MAP.md` only.

---

## Implementation gaps (provisional, code review 2026-11-23)

The code in `code/` does not yet implement all of the
above. This list is for planning. It does not change the authoritative spec.

| Spec requirement | Current skeleton | Gap |
|---|---|---|
| Explicit IDLE/RUNNING/AWAITING_APPROVAL/KILLED state machine | Implicit in `status` frontmatter (`queued`/`working`/`blocked`/`done`) plus `kill_active` in `state.json` | No state machine module; LEDs read `state.json` fields directly. Owner: Christopher. |
| 120 s approval timeout treated as reject | Approval pause in `coordinator._run_one_tool_call` only logs and waits; no timeout | Needs the wait loop reading note `approved_by`, green/red, and a 120 s clock. Owner: Jayden. |
| Hardware kill poll at 100 ms | Bridge GPIO debounce 0.05 s; coordinator reads `state.json` once per 1 s loop iteration | Tighten poll to 0.1 s at the GPIO layer. Pin map is `docs/GPIO_PIN_MAP.md`. Owner: Jayden. |
| Ctrl+K text intake | Only `voice_intents.py` (fixed EN/ZH phrase matcher) | Text intake with its own fixed vocabulary not implemented. Owner: Jayden. |
| Rules-only ROUTER -> tier (v1 FAST/THINK; accepted T0/T1/T2/T3 2026-11-25) | 2026-11-24: `router.py` rules (skill, keywords, length) with Jev tie-break; `models.py` T0-T3 chains across DeepSeek, Hunyuan, GLM, Bailian/Qwen, MiMo with fallback, pane pins, T2 allowlists, T1 off | Coordinator has no worker-dispatch action in the fixed menu yet, so `router.dispatch` is not called from the loop; arena contest runner and UI not built. Owner: Christopher. |
| Default-deny policy, allowlisted read-only tools auto-run | `tools.py` tags each tool `SAFE` or `NEEDS APPROVAL`; SAFE runs immediately in `coordinator._run_one_tool_call` | Permissive tag list must be replaced with default-deny and a read-only allow list. Owner: Christopher. |
| Injection guard tainting web/file content | Web search results (Zhipu on the GLM key; `websearch.py`) clipped in `context.py`; vault search notes require citations | No taint tracking; no rule blocking tainted text from becoming tool arguments. Owner: Christopher. |
| Exact command shown on screen at approval time | `request_approval()` sets `approval_pending` and task id; screen shows proposal note | Command/args are not rendered verbatim from the tool call. Owner: Christopher. |
| EXECUTE in own process group with timeout, VERIFY RESULT | `guard.check_shell_command()` allow list; `shell_run` tool body is a skeleton | No process group, timeout, or empty-output/step-limit verification. Owner: Christopher. |
| `escalate_to_human` action name | `_escalate()` writes a `*-escalate` note with status `blocked`; reason code `ROUND_LIMIT` | Fixed menu has no `escalate_to_human` action; escalation is internal only. Owner: Christopher. |
| One escalation on worker failure (v1: pro; accepted: T1 Qwen4 Max -> escalate_to_human) | 2026-11-24: T1 = Qwen4 Max; exhausted or denied T1 raises `EscalationNeeded`, `router.dispatch` returns `escalate=True` | Screen and vault note for ESCALATE TO HUMAN from a worker not wired. Owner: Christopher. |
| Telemetry to SQLite (route, model, tokens, latency, cost) | 2026-11-24: `telemetry.py` writes every chat attempt, judge call and route to SQLite (no prompt text, no keys) | Dashboard view of telemetry not built. Owner: Christopher. |
| Every live run recorded; automatic offline replay | No recording mode; `deepseek_client.py` makes live calls only | Need a recorder in the client layer and a replay player feeding the same validation/GUARD path. Owner: Jayden. |
| External agents off in booth, claim research/narration only | Bridge API has `_check_home_mode()`, 10/min rate limit, `CLAIMABLE_TYPES = {research, narration}` | Already aligned. Claim TTL/heartbeat present in `state_store.py`. Owner: Jayden. |
| Pin map has one source | Reconciled 2026-11-24: `docs/GPIO_PIN_MAP.md`, `code/si_console/gpio_map.py` and the R5 wiring diagram agree (AGENT 1 white, 100 ohm; grounds on the perfboard bus). | None. Owner decision: Jayden. |

Cross-reference: `CONTRIBUTING.md` (repo rules and sources of truth) and
`docs/decisions.md` (open decisions). `INTEGRATION.md`, which some documents
mention, is not in the repo.
