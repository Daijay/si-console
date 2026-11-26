# Model Tiers — Final Roster, Selection Rules, and Arena Cost

Status: ACCEPTED roster (2026-11-25). This document records the model-tier
decision for the agent runtime and the booth arena demo. It does **not** change
`docs/ARCHITECTURE.md`, which remains the authoritative spec. The authoritative
spec still says "v1 runtime is DeepSeek only"; this document defines the planned
multi-provider table and the demo configuration. Implementation (changes to
`code/si_console/models.py`) requires approval from Jayden and Christopher.

Date: 2026-11-25. Supersedes the 2026-11-24 PROPOSED draft.

## Total API cost — 2-day booth (Maker Faire Shenzhen, Dec 12–13, 2026)

**Headline: ~$43–77 USD for the whole two-day fair at packed traffic (100
contests/day).** At typical traffic (50/day) it is ~$21–38. The booth has
internet and every model is an API call; these figures are the full expected
spend, no price cap assumed. See the derivation in §"Booth arena — layout and
cost" below.

| Traffic | Contests (2 days) | 1.5k out/iter | 4k out/iter |
|---|---|---|---|
| Slow — 20/day | 40 | ~$8.57 | ~$15.39 |
| Typical — 50/day | 100 | ~$21.42 | ~$38.48 |
| Packed — 100/day | 200 | **~$42.84** | **~$76.96** |

Per-model breakdown at **packed traffic, 4k out/iteration** (the worst realistic
case), 200 contests:

| Model | Role | Per contest | 2-day total |
|---|---|---|---|
| **Qwen4 Max** | sole T1 heavy racer | $0.1800 | **$36.00** (47%) |
| **Hy4** | T0 orchestrator B + T2 primary | $0.1079 | **$21.58** (28%) |
| **DeepSeek V4.1 Flash** | T0 orchestrator A + T2 backup + tabs | $0.0769 | **$15.38** (20%) |
| **GLM 5.4** | T0 orchestrator C + T2 #3 + tabs | $0.0198 | **$3.96** (5%) |
| **Jev 1.14** | judge (output free) | $0.00025 | **$0.05** (<0.1%) |
| **TOTAL** | | **~$0.385** | **~$76.96** |

Cheapest pinned configuration (all orchestrators DeepSeek, T2 pools GLM 5.4
only, T1 off): ~$0.02–0.03/contest → **~$5–6 for two packed days**, but loses
the frontier race. The default configuration keeps Qwen4 Max for the spectacle.
The old ~$110 estimate included Kimi K3.1 Pro as a second racer; Kimi is culled.

## Sources

Benchmark data checked 2026-11-24/25:

- Artificial Analysis Intelligence Index v5 (Nov 2026)
- Arena Agent Arena leaderboard (Nov 22, 2026), via `arena.ai/leaderboard`
- KingBench 4 coding leaderboard (AICodeKing community run, Nov 2026)
- Provider pricing pages and TypeSafe docs for Jev

Where a model has no independent benchmark entry, that is stated explicitly —
marketing claims are not treated as data.

## Division of labor

```
Input -> Router (rules) -> Orchestrator (T0 model) -> task prompt
                                                         |
                                                         v
                                              Router (rules) -> Worker (T1/T2/T3)
                                                         |
                                                         v
                                              result back to Orchestrator
```

1. **Router** — deterministic rules only (skill, keywords, length). It runs
   twice: once at intake to pick the orchestrator, and again per task to pick
   the worker tier/model. It is the only component that selects a model by
   default. The tier table in `models.py` is load-bearing.
2. **Orchestrator (T0)** — decomposes the job, writes worker prompts, picks from
   a fixed 12-action JSON menu, reads results, synthesizes output. It does not
   do the hard thinking — that is delegated. Core skill: reliable tool calling
   and clear prompt-writing.
3. **Workers (T1/T2/T3)** — do the actual thinking on the prompts they receive.
4. **Judge (Jev)** — a decision model, not a worker. Returns typed, calibrated
   decisions in ~100ms. Used for winner selection, tab promotion, and ambiguous
   routing. Cannot write code.

Note: the authoritative spec's flow uses `FAST | THINK`. This document defines
four tiers (`T0 | T1 | T2 | T3`) plus a judge. That is a spec change to approve.

## Final tier chains

```
T0 orchestrator : DeepSeek V4.1 Flash -> Hy4 -> GLM 5.4
T1 heavy        : Qwen4 Max -> escalate_to_human
T2 medium       : Hy4 -> DeepSeek V4.1 Flash -> GLM 5.4
T3 small        : MiMo 2.6 Flash -> $0 code paths
Judge           : Jev 1.14 (typed decisions, output free)
```

### T0 — Orchestrator (fallback chain)

| # | Model | In/Out $/M | Benchmark | Reason |
|---|---|---|---|---|
| 1 | **DeepSeek V4.1 Flash 1017** | 0.15–0.30 / 0.60–1.20 | AA 33 / Arena #30 | Primary. Cheapest verified tool-caller; already integrated and tested (89 tests pass); spec-named fail-closed provider; off-peak + cached-input pricing make the 3-round loop nearly free. |
| 2 | **Hy4** (Tencent) | ~0.83 / 2.50 (CN ¥6/¥18) | AA 34.6 / Arena #19 | Backup #1. Only backup with real benchmark scores and proven tool calling, native China endpoint. 3–5x DeepSeek, but a backup only fires when the primary is down. |
| 3 | **GLM 5.4** | ~0.09 / 0.33 | KingBench 33.2 (7/19, top open) | Backup #3. Cheapest credible tool-caller; capable but unlisted on AA and slow at max effort — third-string only, effort capped at `high`. |

### T1 — Heavy workers

| # | Model | In/Out $/M | Benchmark | Reason |
|---|---|---|---|---|
| 1 | **Qwen4 Max** | 1.50 / 4.50 | AA 43 / Agent Arena **#14** (top Chinese model) | Sole heavy worker. Flagship agentic: parallel tool calls, ~2k calls/session, structured output, 1M context; Alibaba Singapore endpoint is China-accessible (the team's key is a Hong Kong region key, so `code/` defaults to the Hong Kong endpoint; 2026-11-24). Failure goes straight to `escalate_to_human`. |

Kimi K3.1 Pro was removed: at $10/M output it consumed 64% of arena spend for
marginal visible gain over Qwen4 Max on a tool-calling console.

### T2 — Medium workers

| # | Model | In/Out $/M | Benchmark | Reason |
|---|---|---|---|---|
| 1 | **Hy4** | ~0.83 / 2.50 | AA 34.6 / Arena #19 | Primary. True reasoning model at mid pricing, 1M context, tool calling, vision, structured output. Double-duty with T0 backup — one integration, two slots. |
| 2 | **DeepSeek V4.1 Flash** | 0.15–0.30 / 0.60–1.20 | AA 33 | Secondary. Nearly ties Hy4 at ~1/5 price and already tested. As secondary it does not create a new provider failure domain. |
| 3 | **GLM 5.4** (effort=`high`) | ~0.09 / 0.33 | KingBench 33.2 (7/19, top open) | Third. Capability justifies a medium slot; **effort must stay at `high`, never `max`** (max burns ~1.04M reasoning tokens and 431 min on KingBench). |

### T3 — Small tasks

| # | Model | In/Out $/M | Reason |
|---|---|---|---|
| 1 | **MiMo 2.6 Flash** | 0.14 / 0.28 | Sole small model. Near-free cached input ($0.0028) for repeated prompts; full multimodal. Slow (~30 tok/s, 2.5 s TTFT) is acceptable because small tasks are non-blocking. |
| 2 | **$0 code paths** | 0 | `voice_intents.py` fixed EN/ZH matcher + prewritten narration handle some small tasks with no model call. Exhaust before spending anything. |

## Judge — Jev 1.14

| Property | Value |
|---|---|
| Price | **$0.042 / M input, output FREE** (OpenRouter `jev-1.13`/`1.14`, TypeSafe docs) |
| Latency | ~100ms, typed calibrated decisions |
| Cost per decision | $0.000015–0.000030 (364–724 input tokens) |
| Context | 32K |
| Role | Winner pick, tab promotion, ambiguous router fallback, approval pre-check |

Jev is a **decision model**, not a worker — it cannot write code. It is not in
T0–T3; it sits beside GUARD as a deterministic-adjacent judgment layer. GUARD
remains final authority for physical actions; Jev never bypasses it.

### Judge backups — Bailian HK (added 2026-11-26)

Jev is reached from TypeSafe's API, which may be slow or blocked from Shenzhen.
If Jev **does not respond within 5 s** (timeout, network or HTTP error,
unreadable reply), the same question goes to the next backup, each with a 5 s
timeout. If a backend answers, even with low confidence or a refusal, its answer
stands and later backups are not asked. If none responds, routing ties use T2.

| | 1. Jev 1.14 | 2. Bailian decision model | 3. Qwen chat model |
|---|---|---|---|
| What | Purpose-built decision model | Purpose-built decision model, same System One API as Jev | Chat model in JSON mode |
| Confidence | Calibrated | Calibrated | Self-reported, less reliable |
| From Shenzhen | Unknown (US-hosted) | Yes (Hong Kong) | Yes (Hong Kong) |
| Setting | `TYPESAFE_API_KEY`, `JEV_MODEL=jev-1.14.0` | `BAILIAN_WORKSPACE_ID` (model `decision-model`) | `QWEN_JUDGE_MODEL=qwen3.8-flash` |
| Key | TypeSafe | Same `DASHSCOPE_API_KEY` as Qwen4 Max | Same |

The Bailian decision model is served only on the workspace host
(`https://{WorkspaceId}.cn-hongkong.maas.aliyuncs.com/compatible-mode/v1/systemone`);
the plain dashscope host answers 404. In Hong Kong the docs list the stable
`decision-model` (the preview is Beijing and Singapore only). `qwen3.8-flash`
was picked by a live probe on the team's HK workspace (about 1.9 s from Canada).
Every backend only chooses among the options offered; GUARD stays final
authority. The live smoke check tests each one separately.

## Culled

| Model | In/Out $/M | Reason |
|---|---|---|
| **Kimi K3.1 Pro** | 2.00 / 10.00 | 64% of arena cost for marginal visible gain; removed from T1. |
| **GLM 5.3 Flash** | 0.15 / 0.50 | Superseded by 5.4; interim revert note now CLOSED (see below). |
| **Agnes 2.5 Pro Theta** | 0.10 / 0.30 | Unproven trial slot removed; no reliability data. |
| **Gemini 4 Neon** | 3.00 / 15.00 | Culled for booth on mainland-China reachability (GFW), not capability (AA ~61, strongest in exercise). Home-only. |
| **Qwen 3.8 27B** | 0.43 / 2.55 | Dominated everywhere; AA 10.0 (7th percentile). |
| **Inkling 2 Small** | 0.30 / 1.00 | Unproven tool calling, no scores; Jev now fills the decision slot. |

## GLM 5.4 / 5.3 Flash — interim note CLOSED

**Update 2026-11-26 (temporary):** the GLM 5.4 API is not available yet, so
`code/` runs **GLM 5.3 Flash** in the GLM slot (T0 backup #3, T2 #3; slot id
`glm-5.3-flash`; old `glm-5.4` pins still map to it). Team decision by the router
owner; it overrides the note below until 5.4 ships. Then: rename the slot back,
swap the price in `telemetry.py`, and re-pin `GLM_MODEL`.

The earlier note made 5.3 Flash a conditional revert while 5.4 was unbenchmarked.
That is resolved: 5.4 now has an independent result (KingBench 4: 33.2/60, 7th
of 19, top open model, +5.7 over 5.3's 27.5), so the capability case for 5.4 is
established. 5.4 is fixed in T0 backup #3 and T2 #3 with effort capped at
`high`. 5.3 Flash is permanently culled. **No revert condition remains.**

## Configurable model selection (booth arena)

The arena gives operators explicit control over which model fills each slot.
The router still decides tiers by default, but every slot can be **pinned**:

### Per-orchestrator selection

Three orchestrator panes; each can be pinned to **any T0 model** or left on
`auto` (fallback chain order):

| Pane | Default (auto) | Operator can pin to |
|---|---|---|
| Orchestrator A | DeepSeek V4.1 Flash | DeepSeek / Hy4 / GLM 5.4 / auto |
| Orchestrator B | Hy4 | DeepSeek / Hy4 / GLM 5.4 / auto |
| Orchestrator C | GLM 5.4 | DeepSeek / Hy4 / GLM 5.4 / auto |

Pinning is a config value per pane (e.g. `SI_ORCH_A=deepseek-v4.1-flash`,
`SI_ORCH_B=hy4`, `SI_ORCH_C=glm-5.4`, or `auto`). `auto` follows the T0 fallback
chain; a pinned model does NOT fall back outside its own chain unless the
operator also enables `allow_fallback=yes`.

### Per-orchestrator worker allowlist

Each orchestrator can be restricted to a **subset of T2 models** for its
subagents — so one orchestrator may use only GLM 5.4, another only DeepSeek
Flash, another only Hy4:

| Pane | Default worker pool | Configurable to |
|---|---|---|
| Orchestrator A | all T2 (Hy4, DeepSeek, GLM 5.4) | any non-empty subset, e.g. `glm-5.4` only |
| Orchestrator B | all T2 | e.g. `deepseek-v4.1-flash` only |
| Orchestrator C | all T2 | e.g. `hy4` only |

Config keys (proposed): `SI_ORCH_A_T2=glm-5.4`, `SI_ORCH_B_T2=deepseek-v4.1-flash`,
`SI_ORCH_C_T2=hy4`. T1 (Qwen4 Max) stays global unless an orchestrator is
explicitly denied it (`SI_ORCH_A_T1=off`).

### Selection rules

1. `auto` = follow tier fallback chain in order.
2. A pinned model is used until it fails; then fall back **within that tier's
   chain** from the pinned position, or stop if `allow_fallback=no`.
3. T2 allowlists are per-orchestrator. An empty allowlist means "no medium
   workers" — tasks that need T2 go straight to T1 or $0 paths.
4. Jev decides ambiguous routing and tab promotion; it cannot pick a model
   outside the operator's allowlist.
5. All selections are logged to SQLite telemetry (route, model, tokens,
   latency, cost) with the orchestrator pane id.

## Provider diversity

```
T0 primary = DeepSeek    T1 primary = Qwen4 Max    T2 primary = Hy4    T3 primary = MiMo
```

Four different primaries — no single API outage kills two primaries. Dual-role
models (Hy4 T0/T2, DeepSeek T0/T2, GLM 5.4 T0/T2) appear only as backups or
secondaries, never as two different primaries.

Cost ladder: $0 code paths → $0.14/M (MiMo) → $0.09/M (GLM 5.4) →
$0.15–0.83/M (DeepSeek/Hy4) → $1.50/M (Qwen4 Max) → $0.042/M judge (Jev).

## Booth arena — layout and cost

### Layout

Large monitor split into 3 orchestrator columns. Each column shows:
- **2 main subagent panes** with status + live product launch/test area
- a **tab strip** (`[3][4][5] ▸ +`) for additional subagents; clicking a chip
  swaps it into a main pane
- the orchestrator's model label and pinned worker pool

Small touchpad next to the Pi selects a column and a chip. Green/red buttons
and the kill switch remain the physical gate. Generated code runs in an
isolated sandbox, never on the Pi's GPIO/bridge path.

### Cost model — one contest

One contest = 3 orchestrators racing; 3 rounds each (2k in / 400 out), 6 main
subagents × 4 iterations (3k in / 1.5k–4k out), 12 tab subagents × 2 iterations
(2k in / 1k out, split 12 calls DeepSeek + 12 calls GLM 5.4), ~10 Jev decisions
× 600 tok in. Rates are the accepted chains' $/M in/out; Hy4 is both an
orchestrator and the T2 primary, DeepSeek is both the T0 primary and a T2
backup, so their costs are summed across those roles.

| Model | Role | Calls | 1.5k-out cost | 4k-out cost |
|---|---|---|---|---|
| DeepSeek Flash | T0 orch (9) + T2 backup (8) + tabs (12) | 29 | $0.0529 | $0.0769 |
| Hy4 | T0 orch (3) + T2 primary (8) | 11 | $0.0579 | $0.1079 |
| GLM 5.4 | T0 orch (3) + T2 #3 (8) + tabs (12) | 23 | $0.0132 | $0.0198 |
| Qwen4 Max | sole heavy racer (6 main subs × 4 iters) | 8 | $0.0900 | $0.1800 |
| Jev | judge (10 × 600 tok in, output free) | 10 | $0.00025 | $0.00025 |
| **Total / contest** | | **81** | **~$0.214** | **~$0.385** |

### Two-day totals (no cap, 200 contests packed)

| Scenario | Cost |
|---|---|
| 1.5k output tokens/iteration | **~$42.84** |
| 4k output tokens/iteration | **~$76.96** |

The earlier ~$110 estimate assumed Kimi as a second frontier racer; with Kimi
culled, Qwen4 Max is the only heavy cost driver but Hy4 as both orchestrator and
T2 primary is the second largest. Per-model share at 4k output: Qwen4 Max
~$36 (47%), Hy4 ~$21.6 (28%), DeepSeek ~$15.4 (20%), GLM 5.4 ~$4.0 (5%), Jev
~$0.05.

At a more typical 50 contests/day (100 over two days): **~$21 (1.5k out) to
~$38 (4k out)**. The $5/day cap only works with the cheapest configuration
below; the default arena assumes no cap.

### Cheapest configuration

Pin all three orchestrators to DeepSeek, set all T2 pools to GLM 5.4 only, and
turn T1 off (no Qwen4 Max). Contest cost drops to ~$0.02–0.03, two-day packed
~$5–6 — near the old $5/day cap but loses the frontier race. Default
configuration keeps Qwen4 Max for the spectacle.

## Implementation status

Implemented 2026-11-24 in `code/` (mocked tests only; no live call to any
provider yet):

- `config.py`: provider keys, base URLs and pinned model ids from `.env`; the
  four chains; `SI_ORCH_{A,B,C}` pins, `_T2` allowlists, `_T1` on/off and
  `_FALLBACK`; `SI_COORDINATOR_PANE`.
- `chat_client.py`: one OpenAI-compatible client for DeepSeek, Hunyuan (Hy4),
  GLM, Bailian/DashScope (Qwen4 Max) and MiMo, with per-provider thinking
  fields (GLM effort capped at `high`).
- `models.py`: chain walk with fallback, unconfigured slots skipped, pane
  rules, T1 -> `EscalationNeeded`, T3 -> `ZeroPathNeeded`.
- `router.py`: rules-only routing (skill, keywords, length), Jev tie-break
  restricted to the pane's allowed tiers, `dispatch()`.
- `judge.py`: Jev direct from TypeSafe (`POST https://api.typesafe.ai/v1/systemone`,
  model `jev-1.14.0`; OpenRouter's Decisions API is the alternate route) (`choice` questions);
  backup: a small Qwen model on Bailian HK when Jev does not respond in 5 s;
  an answer outside the offered options is rejected.
- `telemetry.py`: SQLite rows for every attempt, judge call and route.

Check before the booth: `python -m si_console.smoke` (free: config, DNS, clock,
keys and model ids) and `--live` (one tiny call per model). Pi setup:
`code/deploy/install_pi.sh`.

Still open: live calls per provider (wire shapes are unconfirmed, taken from docs), Qwen
thinking (T1 runs with thinking off until tested), a worker-dispatch action in
the coordinator's fixed menu, the arena contest runner and UI, and model ids
for each provider in `.env`. Owner: Christopher (router/config), Jayden
(integration).
