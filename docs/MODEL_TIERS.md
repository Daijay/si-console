# Model Tiers — Candidate Roster and Routing Decisions

Status: PROPOSED. This document records the model-tier decision for the agent
runtime. It does **not** change `docs/ARCHITECTURE.md`, which remains the
authoritative spec. The authoritative spec currently says "v1 runtime is
DeepSeek only"; this document proposes the future multi-provider tier table.
Implementation (changes to `code/si_console/models.py`) requires approval from
Jayden and Christopher.

Date: 2026-11-24.

## Sources

Benchmark data was checked on 2026-11-24 against:

- Artificial Analysis Intelligence Index v5 (Nov 2026)
- Arena Agent Arena leaderboard (Nov 22, 2026), via `arena.ai/leaderboard`
- Pricing from provider pages gathered earlier in this review

Where a model has no independent benchmark entry, that is stated explicitly —
marketing claims are not treated as data.

## Division of labor (important for reading the tiers)

There are three distinct jobs. Confusing them leads to wrong tier assignments:

```
Input -> Router (rules) -> Orchestrator (T0 model) -> task prompt
                                                         |
                                                         v
                                              Router (rules) -> Agent (T1/T2/T3)
                                                         |
                                                         v
                                              result back to Orchestrator
```

1. **Router** — deterministic rules only (skill, keywords, length). It runs
   twice: once to pick the orchestrator from the entry signal, and again per
   task to pick the worker tier/model. It is the **only** component that selects
   a model. The tier table in `models.py` is therefore load-bearing.
2. **Orchestrator (T0)** — decomposes the job, writes the worker prompts, picks
   from a fixed 12-action JSON menu, reads results, synthesizes the final
   output. It does **not** decide which model runs. Its core skill is reliable
   tool calling and clear prompt-writing, not raw reasoning — the hard thinking
   is delegated.
3. **Workers (T1/T2/T3)** — do the actual thinking on the prompts they are
   given.

Note: the authoritative spec's flow uses `FAST | THINK` and a rules-only router.
This document proposes four tiers (`T0 | T1 | T2 | T3`) and a router that maps
skill/keywords/length to one of them. That is a spec change to approve, not a
current implementation.

## Tier definitions

| Tier | Job | Call volume | Quality need | Latency | Cost tolerance |
|---|---|---|---|---|---|
| **T0 Orchestrator** | plan, write worker prompts, 12-action menu | Highest (up to 3 rounds/task) | Tool-call discipline, JSON reliability | Strict (human at button) | Low — cheapest reliable model wins |
| **T1 Heavy** | hard reasoning, escalations | Low | Frontier | Loose | High — rare calls justify $2–10/M |
| **T2 Medium** | synthesis, slide drafts, multi-step chains | Medium | Solid reasoning + tool use | Moderate | Mid — $0.10–2.50/M |
| **T3 Small** | summaries, formatting, voice hints, search queries | High | Minimal | Fast | Rock bottom, or $0 |

## The roster

### T0 — Orchestrator (fallback chain)

| # | Model | In/Out $/M | AA / Arena | Reason |
|---|---|---|---|---|
| 1 | **DeepSeek V4.1 Flash 1017** | 0.15–0.30 / 0.60–1.20 | 33 / #30 | Primary. Cheapest verified tool-caller; already integrated and tested (89 tests pass); spec-named fail-closed provider; off-peak and cached-input pricing make the 3-round loop nearly free. |
| 2 | **Hy4** (Tencent) | ~0.83 / 2.50 (CN ¥6/¥18) | 34.6 / #19 | Backup #1. Only backup with real benchmark scores and proven tool calling, native China endpoint. Costs 3–5x DeepSeek, but a backup only fires when the primary is already down, so volume is low. |
| 3 | **GLM 5.4** | ~0.09 / 0.33 | no data | Backup #3, demoted. Cheapest credible model but released 2026-11-23 with no independent benchmark entry. See interim note below. |

*Deliberately excluded from T0:* frontier models (Kimi, Qwen4 Max). The
orchestrator picks from a fixed 12-action menu and does not do the hard
reasoning; at booth volume a frontier orchestrator is affordable (~$0.48–0.80
per day at 100 rounds) but buys little for this narrow job. Revisit via the
promotion trigger in Revisions.

### T1 — Heavy workers (frontier, low volume)

| # | Model | In/Out $/M | AA / Arena | Reason |
|---|---|---|---|---|
| 1 | **Qwen4 Max** | 1.50 / 4.50 | 43 / **#14** (top Chinese model on Agent Arena) | First escalation. Flagship agentic: parallel tool calls, ~2k tool calls/session, structured output, 1M context; Alibaba Singapore endpoint is China-accessible. |
| 2 | **Kimi K3.1 Pro** | 2.00 / 10.00 | **46** (top open-weights) / #21 | Final escalation before `escalate_to_human`. Frontier reasoning, 1M context, multimodal, Moonshot is China-reachable; rare calls justify the price. Non-permissive open-weight license is irrelevant for API-only use. |
| — | **DeepSeek V4 Pro** | unknown | — | Flagged candidate: the authoritative spec names `deepseek-v4-pro` as the THINK model. It was not in the original candidate list; pricing and reachability check pending before placement. |

Escalation order is Qwen4 Max first, Kimi last. This matches the agentic data
(Qwen #14 vs Kimi #21 on Agent Arena) better than the raw intelligence data
(Kimi 46 vs Qwen 43) — for a tool-calling console, agentic success rate is the
more relevant signal.

### T2 — Medium workers

| # | Model | In/Out $/M | AA | Reason |
|---|---|---|---|---|
| 1 | **Hy4** | ~0.83 / 2.50 | 34.6 | Primary. True reasoning model at mid pricing, 1M context, tool calling, vision, structured output. Deliberate double-duty with T0 backup — one integration, two slots. |
| 2 | **DeepSeek V4.1 Flash** | 0.15–0.30 / 0.60–1.20 | 33 | Secondary. Nearly ties Hy4 on capability at ~1/5 the price, and already tested. As secondary it does not create a new provider failure domain: a DeepSeek outage degrades T0-primary and T2-secondary, while T0 falls to Hy4 and T2 still has Hy4/MiMo/Agnes. |
| 3 | **Agnes 2.5 Pro Theta** | 0.10 / 0.30 | 24.5 | Trial. 188B open weights at tiny prices, potentially the best $/capability here. Unproven (PublicAI agents #25/298, no reliability data): ~20 tool-call tests required before real work. If it passes, may replace Hy4 as primary on price. |
| 4 | **MiMo 2.6 Flash** | 0.14 / 0.28 | 26.7 (46th pct) | Background only. Near-free cached input ($0.0028) for repeated prompts, full multimodal. Excluded from interactive use on latency: ~30 tok/s, 2.5 s TTFT — a visitor at a button would notice; a batch slide-draft job would not. |

### T3 — Small tasks

| # | Model | In/Out $/M | Reason |
|---|---|---|---|
| 1 | **GLM 5.4** | ~0.09 / 0.33 | Primary on price. Cheapest credible call on the list; shares the T0-backup integration. See interim note below. |
| 2 | **MiMo 2.6 Flash** | 0.14 / 0.28 | Secondary. Slow is acceptable for non-blocking small tasks. |
| 3 | **$0 code paths** | 0 | `voice_intents.py` fixed EN/ZH matcher and prewritten narration sentences handle some small tasks with no model call. Exhaust these before spending anything. |

## Interim note: GLM 5.4 vs GLM 5.3 Flash

> ⚠️ **GLM 5.4 is in the roster on price alone.** It released 2026-11-23 and, as
> of this review, has **zero independent benchmark data** — no Artificial
> Analysis page, no Vals score, no Arena entry. A social post claiming "#3 on
> AA Intelligence Index" is unverified marketing and is not treated as data.
>
> Its price ($0.09/$0.33) makes it the cheapest credible option for T3 (shallow
> work, low risk of visible harm) and an acceptable third-string T0 backup.
> But **T0 backup requires proven tool calling**, which 5.4 does not yet have.
>
> **GLM 5.3 Flash is culled only conditionally.** At $0.15/$0.50 it has real
> benchmark pedigree — it topped the Artificial Analysis Cyber Index as an
> open-source model — and is the designated revert for 5.4 in the two slots
> where 5.4 is currently unproven (T0 backup #3 and T3 primary).
>
> **Until 5.4 benches:** treat the 5.4 assignments as provisional. Run ~20
> tool-call reliability tests against it. If AA/Arena scores land poorly, or
> the tool-call tests fail, reinstate **GLM 5.3 Flash** as T0 backup #3 and T3
> primary immediately (Revision R2). If 5.4 scores well, remove this note and
> make the 5.3 cull permanent.

## Culled

| Model | In/Out $/M | Reason | Revert condition |
|---|---|---|---|
| **Qwen 3.8 27B** | 0.43 / 1.88–2.55 | Dominated in every tier: more expensive than GLM 5.4 and MiMo in T3, loses to Qwen4 Max in T1/T2; AA index 10.0 (~7th percentile), the worst score in the exercise. Redundant with Qwen4 Max for Qwen-family behavior. | None. |
| **GLM 5.3 Flash** | 0.15 / 0.50 | Superseded on price by 5.4 — *but 5.4 is unbenchmarked and 5.3 has pedigree*. | **Yes** — see interim note above. |
| **Gemini 4 Neon** | 3.00 / 15.00 | Culled for the booth, not for capability: AA ~61, the strongest model in this whole exercise. The decisive reason is mainland-China reachability (GFW) from a Shenzhen convention center — on-site wifi does not fix that. Also 10–20x DeepSeek and output-billed thinking tokens are unpredictable against a $5/day cap. | Home-only use is fine; keep as a home T1 experiment model. |
| **Inkling 2 Small** | 0.30 / 1.00 | Unproven tool-call reliability and no benchmark score; its shadow-advisor (Jev) slot is optional in the spec. | None. Note: the Jev shadow-advisor slot now has no candidate — leave unfilled (spec allows) or trial Agnes there. |

## Provider diversity at a glance

```
T0 primary = DeepSeek    T1 primary = Qwen4 Max    T2 primary = Hy4    T3 primary = GLM 5.4
```

Each tier's **primary** is a different provider, so no single API outage kills
two primaries. Dual-role models (Hy4 in T0+T2, DeepSeek in T0+T2, GLM in T0+T3)
are permitted as backups/secondaries only.

Cost ladder: $0 small-task code paths → ~$0.09/M small tasks → $0.15–0.83/M
orchestration and medium → $1.50–2/M heavy.

## Revisions log

| # | Change | Reason |
|---|---|---|
| R1 | T0 fallback chain: DeepSeek → **Hy4** → GLM 5.4 | Only Hy4 has real benchmark scores and proven tool calling among backups; GLM 5.4 is unbenchmarked. |
| R2 | GLM 5.3 Flash cull becomes conditional | 5.4 is unscored; 5.3 has benchmark pedigree. See interim note. |
| R3a | T2: Hy4 → **DeepSeek Flash** → Agnes (trial) → MiMo (bg) | Benchmarks show DeepSeek ≈ Hy4 capability at ~1/5 price and it is already tested; earlier "overflow only" note underweighted this. |
| R3b | T0 stays DeepSeek-for-now with a promotion trigger | At booth volume a frontier orchestrator is affordable; but tool-calling is wired/tested only for DeepSeek and the spec names it. Rehearse both: if DeepSeek wastes rounds or escalates noticeably more than Qwen4 Max, promote Qwen4 Max to T0 primary. |
| R3c | Flag DeepSeek V4 Pro as a T1 candidate | The authoritative spec names it as the THINK model; it was absent from the original candidate list. |

## Implementation status

All seven surviving models are **decisions, not code**. `code/si_console/models.py`
currently maps tiers to DeepSeek only. Adding the other providers requires new
API clients and tier-table entries, plus regression tests — outside the scope
of this document.
