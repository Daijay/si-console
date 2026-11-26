# SI Console — Architecture Visualizations

Companion to `docs/ARCHITECTURE.md` (the authoritative v1 spec).
Date 2026-11-23, tier diagrams updated 2026-11-25. This document only
visualizes; it does not change the spec. The four-tier roster shown in diagrams
1, 3 and 6 is ACCEPTED (2026-11-25) in `docs/MODEL_TIERS.md`, but is not yet
implemented in the v1 skeleton.

Each diagram is Mermaid, so it renders on GitHub and in most Markdown viewers.
A legend after each diagram maps the parts to the spec section and to the
current `code/` skeleton: **DONE** (already implemented and tested),
**PARTIAL** (some of it exists), **GAP** (not implemented yet). Read
`docs/ARCHITECTURE.md` → "Implementation gaps" for the authoritative list.

---

## 1. Big picture — the whole system

```mermaid
flowchart TB
    subgraph H["HARDWARE (Pi 5, GPIO_PIN_MAP.md)"]
        PTT["Push-to-talk + Mic"]
        BTN["Green / Red buttons<br/>Kill switch (GPIO22 NC)<br/>EN/ZH toggle"]
        LED["4 agent LEDs + 2 button LEDs<br/>via ULN2003"]
        SCREEN["Main screen (HDMI0)<br/>Mini screen (HDMI1)"]
    end

    subgraph C["CONTROL (bridge, Jayden)"]
        BR["BRIDGE / state.json cache<br/>100 ms kill poll (GAP: 1 s today)"]
        FSM["STATE MACHINE<br/>IDLE / RUNNING / AWAITING_APPROVAL / KILLED"]
    end

    subgraph A["AGENT RUNTIME ( Christopher + Jayden )"]
        IN["Intake<br/>(reject if KILLED or busy)"]
        ROUTER["ROUTER (rules only)<br/>skill / keywords / length<br/>v1: FAST | THINK<br/>accepted 2026-11-25: T0 | T1 | T2 | T3"]
        COORD["COORDINATOR / T0<br/>DeepSeek flash, fixed JSON menu<br/>max 3 rounds, writes worker prompts"]
        WORK["WORKERS (accepted, implemented in code)<br/>T1 heavy / T2 medium / T3 small"]
        POLICY["POLICY CHECK<br/>default deny"]
        GUARD["GUARD<br/>deterministic code"]
        EXEC["EXECUTE<br/>own process group + timeout"]
        VERIFY["VERIFY RESULT<br/>errors / empty / step limit"]
        IG["INJECTION GUARD<br/>taint web + file content"]
    end

    subgraph M["MEMORY"]
        VAULT[("VAULT<br/>markdown notes<br/>what happened")]
        JSON[("state.json<br/>cache")]
        SQLITE[("SQLite<br/>how it ran")]
    end

    subgraph P["PROVIDERS + OFFLINE (accepted tiers, implemented in code)"]
        DS["T0: DeepSeek / Hy4 / GLM 5.4<br/>T1: Qwen4 Max<br/>T2: Hy4 / DeepSeek / GLM 5.4<br/>T3: MiMo 2.6 Flash + $0 paths<br/>Judge: Jev 1.14 (ACCEPTED 2026-11-25)"]
        BOCHA["Web search<br/>Zhipu on GLM key, Bocha fallback"]
        REC[("Recorded runs<br/>in the vault")]
    end

    subgraph E["EXTERNAL AGENTS"]
        API["Bridge API<br/>token, home LAN only, off in booth"]
        HERMES["Hermes: claim + report/research notes only"]
    end

    PTT --> IN
    BTN --> BR
    BR --> FSM
    FSM --> LED
    FSM --> SCREEN
    FSM --> IN
    IN --> ROUTER --> COORD --> WORK --> POLICY
    POLICY -- "allowlisted read-only" --> EXEC
    POLICY -- "everything else" --> FSM
    IG -.-> POLICY
    GUARD -.-> POLICY
    EXEC --> VERIFY --> COORD
    COORD <--> VAULT
    VAULT --> JSON --> SCREEN
    COORD --> SQLITE
    WORK --> DS
    WORK --> BOCHA
    ROUTER -.->|"per-task routing"| WORK
    DS & BOCHA -.-> IG
    DS --> REC
    REC -. "booth fallback on failure" .-> WORK
    API <--> BR
    HERMES --> API
```

**Legend:** hardware and bridge are **PARTIAL** (real GPIO, buttons, LEDs, bridge
API exist; the 100 ms poll and explicit FSM do not). Intake/router/policy/
injection guard/execute/verify are **GAP**. Coordinator is **PARTIAL** (menu,
3-round limit, GUARD exist; no `escalate_to_human` action). Vault is **DONE** as
truth with `state.json` rebuilt from it; SQLite telemetry is **GAP**. DeepSeek +
web search (Zhipu on the GLM key, Bocha fallback) are **DONE**; offline recording/replay is **GAP**. External-agent API is
**DONE / aligned** (home-mode, rate limit, claim types).

The four-tier worker roster is **ACCEPTED 2026-11-25** (see
`docs/MODEL_TIERS.md`) and the chains, pane pins, Jev tie-break and SQLite
telemetry are **implemented in `code/` (2026-11-24, mocked tests only)**;
the coordinator's worker-dispatch action and the arena runner/UI are still
GAP. The v1 spec text still names FAST/THINK and DeepSeek-only — updating it
is the owners' call. Spec sections: STATE MACHINE, FLOW, SAFETY, MEMORY AND
STATE, PROVIDERS, OFFLINE, EXTERNAL AGENTS.

---

## 2. State machine (Christopher, authoritative)

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> RUNNING: task picked
    RUNNING --> AWAITING_APPROVAL: tool needs approval
    AWAITING_APPROVAL --> RUNNING: green press (execute)
    AWAITING_APPROVAL --> IDLE: red press (reject → coordinator)
    AWAITING_APPROVAL --> IDLE: 120 s timeout (treated as reject)
    RUNNING --> IDLE: task done

    IDLE --> KILLED: GPIO22 NC open (hardware kill)
    RUNNING --> KILLED: GPIO22 NC open
    AWAITING_APPROVAL --> KILLED: GPIO22 NC open

    KILLED --> IDLE: switch reset + ONE green press<br/>→ NEW coordinator task only
    note right of KILLED
      Never resume half-finished actions.
      LEDs and mini screen render ONLY
      from this machine.
    end note
```

**Legend:** the explicit machine is a **GAP**. Today the skeleton uses tasks with
frontmatter status `queued → working → blocked/done`, an `approval_pending` flag,
and a `kill_active` flag in `state.json` — LEDs read those fields directly. The
kill-reset path is **PARTIAL**: the bridge clears `kill_active` on reset + green
press (I fixed the release-state bug), but there is no explicit `KILLED` state or
"new task only" enforcement. Spec section: STATE MACHINE.

---

## 3. End-to-end flow (the main loop)

```mermaid
flowchart TD
    START(["User input<br/>PTT STT  or  Ctrl+K text"]) --> INTAKE{"Intake<br/>KILLED or busy?"}
    INTAKE -- yes --> REJECT["REJECT input"]
    INTAKE -- no --> ROUTER["ROUTER (rules only, v1)<br/>skill + keywords + length"]

    ROUTER --> O["COORDINATOR / T0<br/>DeepSeek flash<br/>plan + write worker prompts"]
    O --> MENU["Fixed JSON action menu<br/>max 3 rounds"]
    MENU -->|3 rounds used| ESC["escalate_to_human"]
    MENU -->|task prompt| R2{{"ROUTER (rules only)<br/>per-task tier pick"}}
    R2 -->|T3 small| W3["MiMo 2.6 Flash → $0 paths"]
    R2 -->|T2 medium| W2["Hy4 → DeepSeek V4.1 Flash → GLM 5.4"]
    R2 -->|T1 heavy| W1["Qwen4 Max → escalate_to_human"]
    W1 & W2 & W3 -->|result| O
    W1 -->|failure| PRO["escalate_to_human"]
    PRO --> TOOL["TOOL CALL"]

    TOOL --> POLICY{"POLICY CHECK<br/>default deny"}
    POLICY -- "allowlisted read-only" --> EXEC["EXECUTE<br/>own process group<br/>+ timeout"]
    POLICY -- "everything else" --> WAIT["AWAITING_APPROVAL<br/>exact command on screen"]
    WAIT -->|green| EXEC
    WAIT -->|red / 120 s| BACK["back to COORDINATOR"]

    EXEC --> VERIFY{"VERIFY RESULT<br/>errors · empty output<br/>step limit"}
    VERIFY -- ok --> BACK
    VERIFY -- fail --> MENU
    BACK --> MENU
```

**Legend:** the coordinator skeleton has the **PARTIAL** pieces (fixed
12-action menu, 3-round limit → escalation note, validation, GUARD check, an
approval *pause* that only logs). Router, tiered workers (the T1/T2/T3 chains
shown are **ACCEPTED 2026-11-25** — see `docs/MODEL_TIERS.md` — but not
implemented), one-escalation, default-deny policy, exact-command display,
process-group execution and result verification are **GAP**. Spec sections:
FLOW, SAFETY, STATE MACHINE.

---

## 4. Safety stack (the five layers)

```mermaid
flowchart TB
    L1["1. HARDWARE KILL — GPIO22 NC open<br/>overrides everything, 100 ms poll<br/><i>PARTIAL: debounce 0.05 s, poll 1 s</i>"]
    L2["2. DEFAULT-DENY POLICY<br/>allowlisted read-only tools auto-run<br/>everything else → AWAITING_APPROVAL<br/><i>GAP: tools.py still uses SAFE tag</i>"]
    L3["3. INJECTION GUARD<br/>taint web + file content<br/>block tainted text as tool arguments<br/><i>GAP: no taint tracking</i>"]
    L4["4. GUARD — deterministic code, never an LLM<br/>kill · role · approval · risk checks<br/><i>DONE: guard.py (code, not LLM)</i>"]
    L5["5. PHYSICAL GATE — green executes, red rejects<br/>120 s timeout = reject<br/><i>PARTIAL: 120 s timeout missing</i>"]
    L1 --> L2 --> L3 --> L4 --> L5
    L5 --> OK["Tool may run"]
```

**Legend:** GUARD is **DONE** — it is code, has no LLM, cannot be talked out of a
block, and I recently synced kill state into it so a kill reaches the coordinator.
The hardware kill *circuit* is real (normally closed, fail-safe) but the **100 ms
poll is a GAP**. Default-deny and the injection taint guard are **GAPs**. The
physical gate is **PARTIAL**. Spec section: SAFETY.

---

## 5. Memory and state — three stores, three jobs

```mermaid
flowchart LR
    subgraph VAULT_S["VAULT (source of truth — what happened)"]
        N1["task note 1<br/>YAML frontmatter"]
        N2["task note 2<br/>depends_on: [[wikilinks]]"]
        N3["run recording<br/>(offline replay)"]
    end
    subgraph JSON_S["state.json (cache)"]
        SJ["current task · agent · status<br/>kill_active · approval_pending · lang"]
    end
    subgraph SQL_S["SQLite (how it ran — GAP)"]
        T1["route decisions"]
        T2["model · tokens · latency · cost"]
    end

    W(["Bridge / Coordinator"]) -->|"atomic .tmp + rename writes"| VAULT_S
    VAULT_S -->|"rebuilt on every restart"| JSON_S
    JSON_S --> S(["Screens + LEDs<br/>(render from FSM)"])
    W -.->|"telemetry (not built yet)"| SQL_S
    N3 -.->|"replay on failure"| W
```

**Legend:** vault + atomic note writes + `state.json` rebuild on start are
**DONE** (`vault.py`, `state_store.py`, 89 passing tests). `[[wikilinks]]` in the
body is **PARTIAL** (parser reads them; creation from the model is skeleton).
Run recordings and SQLite telemetry are **GAP**. Spec sections: MEMORY AND
STATE, OFFLINE.

---

## 6. Providers and routing (who calls whom)

```mermaid
flowchart TB
    R{"ROUTER (rules only) — runs TWICE<br/>1. intake → T0 orchestrator<br/>2. per task → worker tier + model<br/>Slots may be PINNED per pane (see MODEL_TIERS.md)"}

    R -->|intake| T0["T0 ORCHESTRATOR<br/>DeepSeek V4.1 Flash → Hy4 → GLM 5.4<br/>(per-pane pin: any of the 3, or auto)"]

    R -->|T3 small| T3["MiMo 2.6 Flash → $0 paths"]
    R -->|T2 medium| T2["Hy4 → DeepSeek V4.1 Flash → GLM 5.4<br/>(per-pane worker allowlist)"]
    R -->|T1 heavy| T1["Qwen4 Max → escalate_to_human"]

    T1 & T2 & T3 -->|result| T0
    T0 --> B["Web search: Zhipu (GLM key)<br/>Bocha fallback · best-effort, never blocks"]
    J{{"JEV 1.14 — JUDGE<br/>$0.042/M in, output free, ~100ms<br/>winner pick · tab promotion · ambiguous routing<br/>GUARD keeps final authority"}}
    T0 -.-> J
    T1 & T2 & T3 -.-> J
    CULL["Culled (2026-11-25): Kimi K3.1 Pro · GLM 5.3 Flash<br/>· Agnes 2.5 Pro Theta · Gemini 4 Neon (GFW)<br/>· Qwen 3.8 27B · Inkling 2 Small"]
```

**Legend:** all four tier chains are **ACCEPTED 2026-11-25** (recorded in
`docs/MODEL_TIERS.md`) and are **implemented in `code/` (2026-11-24)**:
`config.py` chains + pane pins, `chat_client.py` (one OpenAI-compatible client
for DeepSeek, Hunyuan/Hy4, GLM, Bailian/Qwen, MiMo), `models.py` chain walk with
fallback and T1 `EscalationNeeded`, `router.py` rules with Jev tie-break,
`judge.py` (Jev direct from TypeSafe, Qwen on Bailian HK as backup) and `telemetry.py` (SQLite). **213 mocked
tests pass; no live provider call has been made** — wire shapes are unconfirmed, taken from
docs and model ids go in `code/.env`. Still GAP: a worker-dispatch action in the
coordinator's fixed menu and live verification per provider. No Anthropic
client, deliberately, because the booth is in Shenzhen. Web search (Zhipu on the GLM key since 2026-11-26, Bocha as fallback) is **DONE** as a
best-effort search that never blocks and never changes a ranking. Jev 1.14 is
the accepted **judge** — typed decisions in ~100ms, output free — not the old
optional home-only shadow advisor (Inkling was culled). GLM 5.4 is benchmarked
(KingBench 4) and the
5.3 Flash interim note is CLOSED. Spec section: PROVIDERS.

---

## 7. Offline fallback (booth must work without internet)

```mermaid
flowchart TD
    LIVE["Live run<br/>Coordinator → DeepSeek → tools"] --> REC[("Record every request, reply,<br/>tool call + result to the vault")]
    REC --> DEMO["Demo scenarios:<br/>2020 replay · 2022 replay"]

    NET{"Network / DeepSeek OK?"}
    LIVE --> NET
    NET -- yes --> LIVE
    NET -- no --> FALL["Automatic switch to recorded runs<br/>for the current scenario"]
    FALL --> REPLAY["Replay player feeds recorded replies<br/>through the SAME validation → GUARD → tool path"]
    REPLAY --> RECORD["Numbers recomputed live from price CSVs<br/>(rules engine stays deterministic)"]
    RECORD --> OUT["Booth demo continues<br/>green/red press stays real"]
    RECORD -.->|"no-lookahead unit test still applies"| TEST["tests/test_coordinator_validation.py"]
```

**Legend:** everything here is **GAP** except the deterministic rules engine
(**DONE**, with a no-lookahead test). There is no recording mode in
`deepseek_client.py` yet and no replay player. The design principle — replay
through the *same* validation and GUARD path so approval never gets skipped — is
documented in the architecture gaps table. Spec section: OFFLINE.

---

## 8. External agents (home only)

```mermaid
flowchart TB
    subgraph BOOTH["BOOTH MODE"]
        OFF["External API: OFF<br/>_check_home_mode() returns 423/403"]
    end
    subgraph HOME["HOME MODE"]
        API["Bridge API :8001<br/>Bearer token from .env<br/>LAN only · 10 req/min · never port-forwarded"]
        H["Hermes (first external agent)"]
        H -->|"1. /api/health"| API
        API --> CLAIM["2. claim task by id<br/>(research | narration only)"]
        CLAIM --> HB["3. heartbeat every 60 s<br/>TTL 300 s; expiry → 410"]
        HB --> WRITE["4. write report / research note<br/>(atomic, path-guarded, ≤20k / ≤5k chars)"]
        WRITE --> REL["5. release claim"]
        K["Hardware kill"] -->|"cancels ALL claims at once"| CLAIM
    end
    OFF --- HOME
    DENY["NEVER allowed:<br/>approve · execute · propose trades · edit code · touch GPIO"]
    API --- DENY
```

**Legend:** **DONE / aligned** — `bridge.py` already has home-mode gating, the
rate limit, `CLAIMABLE_TYPES = {research, narration}`, token checks, and
`state_store.py` implements claim TTL/heartbeat/release-all-on-kill. The API is
documented as off in booth mode; no further work needed for this section. Spec
section: EXTERNAL AGENTS.

---

## 9. Ownership map

```mermaid
flowchart TB
    subgraph CHRIS["Christopher — runtime design & safety"]
        C1["state machine"]
        C2["router"]
        C3["policy (default deny)"]
        C4["injection guard"]
        C5["telemetry (SQLite)"]
    end
    subgraph JAY["Jayden — hardware & integration"]
        J1["vault"]
        J2["bridge"]
        J3["GPIO"]
        J4["offline fallback"]
        J5["integration"]
    end
    subgraph HASAN["Hasan — CAD"]
        H1["Fusion model / DXF review<br/>(R4.2 candidate waits for caliper checks)"]
    end
    CHRIS -->|"hands off spec to"| JAY
    JAY -->|"hardware + pin map"| CHRIS
    HASAN -->|"laser-ready geometry"| JAY
```

**Legend:** ownership matches the spec. The pin map has one source,
`docs/GPIO_PIN_MAP.md`; the code and the R5 wiring diagram agree with it
(reconciled 2026-11-24).

---

## 10. Booth arena demo (ACCEPTED 2026-11-25, runner/UI not built)

```mermaid
flowchart TB
    subgraph MON["LARGE MONITOR — 3 orchestrator columns"]
        direction LR
        subgraph A["A — DeepSeek Flash (pinnable)"]
            A1["sub 1<br/>product + launch/test"]
            A2["sub 2<br/>product + launch/test"]
            AT["tabs: [3][4][5] +"]
        end
        subgraph B["B — Hy4 (pinnable)"]
            B1["sub 1<br/>product + launch/test"]
            B2["sub 2<br/>product + launch/test"]
            BT["tabs: [3][4] +"]
        end
        subgraph C["C — GLM 5.4 (pinnable)"]
            C1["sub 1<br/>product + launch/test"]
            C2["sub 2<br/>product + launch/test"]
            CT["tabs: [3][4][5] +"]
        end
    end
    TP["Small touchpad<br/>by the Pi: select pane + chip"] --> MON
    BTN["Green / red buttons + kill switch<br/>physical gate, unchanged"] --> MON
    MON --> SAND["Isolated sandbox<br/>generated code runs here<br/>never on GPIO / bridge / keys"]
    SAND --> J{{"Jev 1.14 judge<br/>winner pick · tab promotion"}}
    J --> MON
    MON --> TEL[("SQLite telemetry<br/>pane · model · tokens · latency · cost")]
    PI["Pi 5: console state machine,<br/>dashboard render, API calls"] --> MON
```

**Legend:** this is the accepted 2026-11-25 booth demo design recorded in
`docs/MODEL_TIERS.md` §"Booth arena". The **route/model layer is implemented**
(2026-11-24): per-pane pins, T2 allowlists, T1 on/off, Jev tie-break, SQLite
telemetry, 213 mocked tests. The **arena contest runner, the 3-column UI, the
tab-chip promotion flow and the isolated sandbox are GAP** — not built. When
built, the Pi will render the dashboard and make API calls; generated code will
run only in the sandbox, never on the GPIO/bridge path. Green/red/kill remain
the physical gate. Each column keeps 2 main subagents on stage with extra
agents as tab chips. Spec sections: PROVIDERS, SAFETY (sandbox is outside
GUARD's physical-action scope by design).

---

## Cross-reference index

| Diagram | Spec section | Implementation status |
|---|---|---|
| 1. Big picture | all | mixed — see per-node legend |
| 2. State machine | STATE MACHINE | GAP |
| 3. End-to-end flow | FLOW, SAFETY | PARTIAL |
| 4. Safety stack | SAFETY | mixed (GUARD DONE, others GAP/PARTIAL) |
| 5. Memory and state | MEMORY AND STATE, OFFLINE | PARTIAL / GAP |
| 6. Providers and routing | PROVIDERS | DONE in code (4 tiers + Jev with Qwen backup, 213 mocked tests); live calls unverified, check with `python -m si_console.smoke --live` |
| 7. Offline fallback | OFFLINE | GAP (rules engine DONE) |
| 8. External agents | EXTERNAL AGENTS | DONE / aligned |
| 9. Ownership map | OWNERSHIP | informational |
| 10. Booth arena demo | PROVIDERS, SAFETY | route/model layer DONE (mocked); runner/UI/sandbox GAP |

Rendering notes: Mermaid should be supported by GitHub natively. If a viewer
does not render `stateDiagram-v2` or `<br/>` labels, the equivalent text is in
`docs/ARCHITECTURE.md`, which remains the single source of truth.
