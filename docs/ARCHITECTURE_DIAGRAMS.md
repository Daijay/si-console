# SI Console — Architecture Visualizations

Status: DRAFT companion to `docs/ARCHITECTURE.md` (the authoritative spec).
Date 2026-11-23. This document only visualizes; it does not change the spec.

Each diagram is Mermaid, so it renders on GitHub and in most Markdown viewers.
A legend after each diagram maps the parts to the spec section and to the
current `code/` skeleton: **DONE** (already implemented and tested),
**PARTIAL** (some of it exists), **GAP** (not implemented yet). Read
`docs/ARCHITECTURE.md` → "Implementation gaps" for the authoritative list.

---

## 1. Big picture — the whole system

```mermaid
flowchart TB
    subgraph H["HARDWARE (Pi 5, R2/R3 pin map)"]
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
        ROUTER["ROUTER<br/>skill / keywords / length<br/>FAST | THINK"]
        COORD["COORDINATOR<br/>DeepSeek flash, fixed JSON menu<br/>max 3 rounds"]
        WORK["WORKERS<br/>FAST=flash / THINK=pro"]
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

    subgraph P["PROVIDERS + OFFLINE"]
        DS["DeepSeek flash + pro"]
        BOCHA["Bocha search"]
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
Bocha are **DONE**; offline recording/replay is **GAP**. External-agent API is
**DONE / aligned** (home-mode, rate limit, claim types).

Spec sections: STATE MACHINE, FLOW, SAFETY, MEMORY AND STATE, PROVIDERS,
OFFLINE, EXTERNAL AGENTS.

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

    ROUTER -->|FAST| CF["COORDINATOR<br/>DeepSeek flash"]
    ROUTER -->|THINK| CP["COORDINATOR<br/>DeepSeek flash (planning)"]
    CF & CP --> MENU["Fixed JSON action menu<br/>max 3 rounds"]
    MENU -->|3 rounds used| ESC["escalate_to_human"]
    MENU -->|action| WORKER["WORKER<br/>FAST = deepseek-v4-flash<br/>THINK = deepseek-v4-pro"]
    WORKER -->|failure| PRO["one escalation to pro"]
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
approval *pause* that only logs). Router, tiered workers, one-pro-escalation,
default-deny policy, exact-command display, process-group execution and result
verification are **GAP**. Spec sections: FLOW, SAFETY, STATE MACHINE.

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
    R{"ROUTER (rules only)<br/>skill · keywords · length"}
    R -->|FAST| F["deepseek-v4-flash<br/>(think disabled for tools)"]
    R -->|THINK| P["deepseek-v4-pro"]
    F -->|one retry on failure| P
    R -.->|"optional, HOME ONLY,<br/>0.8 s limit, ignored on timeout,<br/>logged for comparison"| J["Jev shadow advisor"]
    F --> B["Bocha search<br/>(research notes only,<br/>never feeds ranking)"]
    P --> B
    OTHERS["NOT on critical path:<br/>Claude · Qwen · GLM · Kimi<br/>Booth assumes no Claude access"]
```

**Legend:** DeepSeek-only is **DONE** in `models.py` + `deepseek_client.py`
(the router fails closed to DeepSeek; there is no Anthropic client — deliberately,
because the booth is in Shenzhen). Bocha is **DONE** as a best-effort search that
never blocks and never changes a ranking. The **rules-based tier router** and the
**one-time pro escalation** are **GAP**; today tiers are chosen by caller name
(coordinator/worker/narration/premium). Jev shadow advisor is **GAP / optional**.
Spec section: PROVIDERS.

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
    JAY -->|"hardware + pin map (R2/R3)"| CHRIS
    HASAN -->|"laser-ready geometry"| JAY
```

**Legend:** ownership matches the spec. One open conflict is shown in the
diagram set: the spec says the pin map is R2/R3 only, but `docs/GPIO_PIN_MAP.md`
now also carries a dated R4.1 section — flagged in `ARCHITECTURE.md`'s gaps table
for the two owners to reconcile.

---

## Cross-reference index

| Diagram | Spec section | Implementation status |
|---|---|---|
| 1. Big picture | all | mixed — see per-node legend |
| 2. State machine | STATE MACHINE | GAP |
| 3. End-to-end flow | FLOW, SAFETY | PARTIAL |
| 4. Safety stack | SAFETY | mixed (GUARD DONE, others GAP/PARTIAL) |
| 5. Memory and state | MEMORY AND STATE, OFFLINE | PARTIAL / GAP |
| 6. Providers and routing | PROVIDERS | PARTIAL / GAP |
| 7. Offline fallback | OFFLINE | GAP (rules engine DONE) |
| 8. External agents | EXTERNAL AGENTS | DONE / aligned |
| 9. Ownership map | OWNERSHIP | informational |

Rendering notes: Mermaid should be supported by GitHub natively. If a viewer
does not render `stateDiagram-v2` or `<br/>` labels, the equivalent text is in
`docs/ARCHITECTURE.md`, which remains the single source of truth.
