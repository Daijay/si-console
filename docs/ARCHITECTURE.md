# SI CONSOLE AGENT ARCHITECTURE, MERGED v1 (Jayden + Christopher)

Status: AUTHORITATIVE. Single source of truth for agent runtime design.
Date: 2026-11-23. Owners: Jayden (vault, bridge, GPIO, offline fallback, integration),
Christopher (router, policy, injection guard, telemetry, state machine code).

The text in the sections below is the merged v1 spec as agreed by Jayden and
Christopher. Section "Implementation gaps" at the end is a DRAFT reconciliation
with the current `code/` skeleton, added by the code review on 2026-11-23. It
does not change the spec. It lists what the skeleton does not do yet.

## STATE MACHINE (from Christopher, authoritative)

IDLE -> RUNNING -> AWAITING_APPROVAL -> RUNNING|IDLE; any state -> KILLED on hardware kill (GPIO22 NC open). KILLED exits only via kill switch reset + one green press, then new coordinator task; never resume half-finished actions. AWAITING_APPROVAL exits on green (execute), red (reject, back to coordinator), or 120s timeout (treated as reject). LEDs and mini screen render state from this machine only.

## FLOW

user input (push-to-talk STT or Ctrl+K text) -> intake (rejects if KILLED or busy) -> ROUTER (rules-only in v1: skill, keywords, length -> tier FAST|THINK) -> COORDINATOR (deepseek flash, fixed JSON action menu, max 3 rounds, then escalate_to_human) -> WORKERS (model per routed tier: FAST=deepseek-v4-flash, THINK=deepseek-v4-pro; one escalation to pro on failure) -> TOOL CALL -> POLICY CHECK (default deny; allowlisted read-only tools run immediately; everything else -> AWAITING_APPROVAL with the exact command shown on screen) -> EXECUTE (own process group, timeout) -> VERIFY RESULT (errors, empty output, step limit) -> back to coordinator.

## SAFETY (merged)

default-deny policy (Christopher) replaces safe-list. Injection guard taints any web or file content and blocks tainted text from becoming tool arguments without approval (Christopher). GUARD is deterministic code, never an LLM. Hardware kill overrides everything at 100ms poll.

## MEMORY AND STATE (from Jayden)

Obsidian-compatible markdown vault is the source of truth for tasks (one note per task, strict YAML frontmatter, depends_on as [[wikilinks]]); state.json is a cache rebuilt from the vault on restart. Telemetry (Christopher) goes to SQLite: route decisions, model, tokens, latency, cost. Vault = what happened; SQLite = how it ran.

## PROVIDERS

v1 runtime is DeepSeek only (flash + pro) plus Bocha search. Claude, Qwen, GLM, Kimi and Jev are NOT on the critical path. Jev may run as an optional shadow advisor to the router at home only (0.8s limit, ignored on timeout, logged for comparison). Booth assumes no Claude access and possibly no internet.

## OFFLINE (from Jayden)

every live run is recorded to the vault. If DeepSeek or network fails, the console switches automatically to recorded runs for the demo scenarios. No feature may require internet at the booth without this fallback.

## EXTERNAL AGENTS (from Jayden)

token-protected bridge API, home LAN only, off in booth. External agents (Hermes first) may claim tasks and write reports or research notes only; they can never approve, execute, propose trades or edit code.

## OWNERSHIP

Christopher owns router, policy, injection guard, telemetry, state machine code. Jayden owns vault, bridge, GPIO, offline fallback, integration. Pin map is repo R2/R3 only.

---

## Implementation gaps (DRAFT, code review 2026-11-23)

The `code/` skeleton is DRAFT REFERENCE and does not yet implement all of the
above. This list is for planning. It does not change the authoritative spec.

| Spec requirement | Current skeleton | Gap |
|---|---|---|
| Explicit IDLE/RUNNING/AWAITING_APPROVAL/KILLED state machine | Implicit in `status` frontmatter (`queued`/`working`/`blocked`/`done`) plus `kill_active` in `state.json` | No state machine module; LEDs read `state.json` fields directly. Owner: Christopher. |
| 120 s approval timeout treated as reject | Approval pause in `coordinator._run_one_tool_call` only logs and waits; no timeout | Needs the wait loop reading note `approved_by`, green/red, and a 120 s clock. Owner: Jayden. |
| Hardware kill poll at 100 ms | Bridge GPIO debounce 0.05 s; coordinator reads `state.json` once per 1 s loop iteration | Tighten poll to 0.1 s at the GPIO layer. Pin map remains R2/R3 as stated. Owner: Jayden. |
| Ctrl+K text intake | Only `voice_intents.py` (fixed EN/ZH phrase matcher) | Text intake with its own fixed vocabulary not implemented. Owner: Jayden. |
| Rules-only ROUTER -> FAST/THINK tier | `models.py` tier router maps coordinator/worker/narration/premium tiers to models | No skill/keyword/length router; worker model is not selected per task tier. Owner: Christopher. |
| Default-deny policy, allowlisted read-only tools auto-run | `tools.py` tags each tool `SAFE` or `NEEDS APPROVAL`; SAFE runs immediately in `coordinator._run_one_tool_call` | Permissive tag list must be replaced with default-deny and a read-only allow list. Owner: Christopher. |
| Injection guard tainting web/file content | Bocha results clipped in `context.py`; vault search notes require citations | No taint tracking; no rule blocking tainted text from becoming tool arguments. Owner: Christopher. |
| Exact command shown on screen at approval time | `request_approval()` sets `approval_pending` and task id; screen shows proposal note | Command/args are not rendered verbatim from the tool call. Owner: Christopher. |
| EXECUTE in own process group with timeout, VERIFY RESULT | `guard.check_shell_command()` allow list; `shell_run` tool body is a skeleton | No process group, timeout, or empty-output/step-limit verification. Owner: Christopher. |
| `escalate_to_human` action name | `_escalate()` writes a `*-escalate` note with status `blocked`; reason code `ROUND_LIMIT` | Fixed menu has no `escalate_to_human` action; escalation is internal only. Owner: Christopher. |
| One escalation to pro on worker failure | `models.py` premium tier maps to `deepseek-v4-pro` if configured | No automatic one-time worker escalation path. Owner: Christopher. |
| Telemetry to SQLite (route, model, tokens, latency, cost) | No telemetry store; `LoopResult` and vault logs hold free-text lines | SQLite schema and writer not implemented. No secrets or personal data in telemetry. Owner: Christopher. |
| Every live run recorded; automatic offline replay | No recording mode; `deepseek_client.py` makes live calls only | Need a recorder in the client layer and a replay player feeding the same validation/GUARD path. Owner: Jayden. |
| External agents off in booth, claim research/narration only | Bridge API has `_check_home_mode()`, 10/min rate limit, `CLAIMABLE_TYPES = {research, narration}` | Already aligned. Claim TTL/heartbeat present in `state_store.py`. Owner: Jayden. |
| Pin map is repo R2/R3 only | `docs/GPIO_PIN_MAP.md` now has a dated R4.1 section (white AGENT 1 LED resistor, cable hole) | Spec says R2/R3 only; R4.1 doc section was added by the CAD work. Reconcile before implementation. Owners: Jayden + Christopher. |

Cross-reference: `AGENTS.md` (repo rules and sources of truth), `docs/decisions.md`
(open decisions), `llms.txt` (machine index). Missing integrations from older
comments in `code/` that cite `ARCHITECTURE.md` and `INTEGRATION.md`: this file
resolves `ARCHITECTURE.md`; `INTEGRATION.md` is still not in the repo.
