# Changelog

Dated log of decisions and revisions. Newest first.

## 2026-11-24, BOM: soundbar, spare card, API credits
- Restored the USB soundbar (25.99) and the spare microSD 32GB (27.99); added DeepSeek and Bocha API credits (40.00).
- Fundable total 851.13 CAD before tax (was 757.15; the printed wedge removal had taken it from 767.15 to 757.15), 953.27 with tax. Over the 800 CAD team limit by 51.13.
- The soundbar is not in the R5 CAD or wiring diagram yet.

## 2026-11-24, resistor, pin and ground reconciliation
- Final values everywhere: COORD green 150 ohm, AGENT 1 white 100 ohm, AGENT 2 blue 100 ohm, GUARD yellow 220 ohm; button LEDs on 5V through built-in resistors.
- `gpio_map.py`, `gpio_test.py`, tests, `GPIO_PIN_MAP.md` (rewritten around one table), Detailed, Overview, Onshape notes, ARCHITECTURE gap rows, BOM notes and the R5 wiring diagram now agree.
- Kill switch, push to talk and EN/ZH toggle grounds go to the perfboard GND bus, fed from Pi pins 6, 9 and 14.
- Closes the gpio_map mismatch noted in the code bug pass.

## 2026-11-24, R5 submission assets
- New R5 wiring diagram `blueprints/R5/wiring_diagram_R5.svg` and `.png` (generator `cad/wiring_diagram.py`).
- R5 hero, front, top and exploded renders copied to `docs/images/`.
- R3 2D drawings in `blueprints/2d/` marked superseded by R5.
- `cad/build.py` no longer deletes other files in `blueprints/R5/` when it copies finals.

## 2026-11-24, Accepted model roster implemented in code
`code/` no longer routes to DeepSeek only. Implements `docs/MODEL_TIERS.md` (requested by Christopher, router owner). 163 tests pass (was 134); every provider is mocked, and no live call has been made yet.
- `chat_client.py`: one OpenAI-compatible client for DeepSeek, Tencent Hunyuan (Hy4), Zhipu GLM 5.4, Alibaba Bailian/DashScope (Qwen4 Max, Singapore endpoint) and Xiaomi MiMo. Per-provider thinking fields; GLM effort capped at `high`. `deepseek_client.py` is now a wrapper over it.
- `models.py`: T0 DeepSeek -> Hy4 -> GLM; T1 Qwen4 Max -> escalate_to_human; T2 Hy4 -> DeepSeek -> GLM; T3 MiMo -> $0 paths. Unconfigured slots are skipped and failures fall back. Arena panes A/B/C: pin or auto, `_FALLBACK`, T2 allowlists (`none` sends work to T1 or $0), `_T1=off`. Old tier names are aliases.
- `router.py`: rules-only routing by skill, keywords and length. Jev breaks ties only between the pane's allowed tiers, with a T2 default. `dispatch()` returns escalation or the $0 path as a result instead of raising.
- `judge.py`: Jev 1.14 through the OpenRouter Decisions API (`POST /api/alpha/decisions`, `choice` questions). A choice outside the offered options, a refusal, or low confidence is rejected.
- `telemetry.py`: SQLite rows for every chat attempt, judge call and route (pane, tier, slot, model, tokens, latency, cost). No prompt text and no keys.
- Coordinator calls T0 through its pane (`SI_COORDINATOR_PANE`). New keys and pane settings are in `code/.env.example`. `telemetry.sqlite`, `state.json` and `claims.json` are gitignored.
- Open: one live call per provider from Shenzhen; Qwen thinking (T1 runs with thinking off until tested); a worker-dispatch action in the fixed menu (needs a spec change); arena contest runner and UI; ARCHITECTURE.md PROVIDERS text still says DeepSeek only (owners to update).

## 2026-11-24, Code bug pass (fail-closed holes)
Review of `code/`. 45 regression tests in `code/tests/test_regression_bugpass.py`; 134 pass (was 89).
- GUARD shell allow list: a prefix match let `ls; rm -rf ~`, `df && curl … | sh`, pipes, redirects and `$(…)` through. Shell control characters are now refused.
- Approval tags: `tag_for_status` existed but the coordinator used the static SAFE tag, so an agent could mark an **order** task done with no green press. New `tools.effective_tag()` reads the target task (fails closed if unreadable). `tag_for_write` now fails closed for paths like `tasks/x.md`.
- `validate_tool_call` claimed to check enums but did not: enums, types, min/max, unknown fields, bool/NaN/inf amounts and `slides/../..` traversal are now rejected.
- Kill/resume (ARCHITECTURE.md state machine: exit KILLED only by switch reset + one green press): releasing the switch auto-resumed the coordinator, and the in-memory pending approval survived a kill so green could approve a stale pre-kill proposal. Added a `resume_required` latch in the bridge and `state.json`; kill clears pending approvals; `request_approval` refuses while frozen; green ignores a still-latched switch and never revives a blocked or done task.
- Coordinator re-reads kill state before every round (a kill mid-task used to wait for the next task) and `serve_forever` survives an unexpected task error (blocks that task, ESCALATE) instead of crash-looping under systemd.
- DeepSeek and Bocha: httpx transport errors other than connect and timeout now become ModelError or an error dict instead of crashing the loop.
- `fetch_url` SSRF: the substring blocklist missed 169.254.169.254, 172.16/12, IPv6 loopback, 0.0.0.0, hosts resolving to private IPs and redirects, and wrongly blocked public URLs containing `10.`. Every hop is now resolved and must be a global address.
- Voice intents: negations were case-sensitive, so STT text "Don't buy XLK" or "Never buy XLE" became a buy proposal. Reject phrases ("do not approve", "不要这个") were unreachable behind the negation check.
- Rules engine: a sector with no price file got momentum 0 and was proposed in any falling market. No history now means no signal; no SPY history means hold cash.
- Vault: a UTF-8 BOM made a note vanish from `list_tasks`; `depends_on` ids and research `task_id` are validated against the id rule.
- Not changed: `gpio_map.py` still lists AGENT 1 as 220 ohm (R2), while `docs/GPIO_PIN_MAP.md` R4.1 says white, 100 ohm. ARCHITECTURE.md leaves this to Jayden + Christopher to reconcile.
- `.env.example` was documented but never committed (`.gitignore` `.env.*` swallowed it); added with names only. Empty path variables in `.env` no longer resolve to the working directory.
- Removed a duplicate `tier_config` in `models.py`.
- Known, not fixed: no real wait for green inside the coordinator (skeleton logs the pause), DNS rebinding between the `fetch_url` check and connect, `SI_DEEPSEEK_DAILY_CAP_USD` is read but not enforced, claims.json has no file lock.

## 2026-11-25, Model tiers accepted and architecture synced
- `docs/MODEL_TIERS.md`: final roster ACCEPTED. T0 DeepSeek V4.1 Flash -> Hy4 -> GLM 5.4; T1 Qwen4 Max -> escalate_to_human; T2 Hy4 -> DeepSeek V4.1 Flash -> GLM 5.4; T3 MiMo 2.6 Flash -> $0 paths; Jev 1.14 as judge ($0.042/M in, output free). Kimi K3.1 Pro, GLM 5.3 Flash, Agnes, Gemini 4 Neon, Qwen 3.8 27B and Inkling 2 Small culled. GLM 5.4 / 5.3 interim note CLOSED (5.4 benchmarked on KingBench 4: 33.2, 7/19, top open model).
- Added configurable model selection: per-orchestrator pinning (any T0 model or auto) and per-pane T2 worker allowlists. Added booth arena design (3 orchestrator columns, 2 main subagent panes + tab chips, touchpad, isolated sandbox) and cost model (~$0.21–0.39/contest; ~$43–77 for 200 contests over two days; cheapest pinned config ~$5–6).
- Synced `docs/ARCHITECTURE.md` and `docs/ARCHITECTURE_DIAGRAMS.md`: removed stale Kimi/Agnes/GLM 5.3 references, updated all four tier chains and Mermaid diagrams, added Jev judge role. No runtime code changed.

## 2026-11-24, Model tier research (proposed)
- `docs/MODEL_TIERS.md` added as PROPOSED with benchmark data (Artificial Analysis Intelligence Index v5, Arena Agent Arena, KingBench 4) and cull reasoning. Pointer added to `docs/ARCHITECTURE.md`. Superseded by the 2026-11-25 accepted roster.

## 2026-11-23, R5 (open frame)
- Redesign: open-frame cyberdeck, no enclosure. Base plate 330 x 220 mm with the Pi 5, perfboard with ULN2003 and the GPIO breakout exposed on standoffs; separate 300 x 70 mm control strip at a 20 degree slope on two laser-cut brackets; mini screen on a small angled laser-cut stand; monitor behind on its own kickstand. No fan, side walls, lid or back panel.
- Wires modelled as colour-coded tubes following the wiring table; cable-tie slot pairs in the base along the routes.
- Parametric CadQuery rebuilt in `cad/` (same `params.py` / `build.py` / checks setup). Checks: no collisions, holes with 5 mm margins, every part fits a 305 x 406 mm sheet, tabs and slots mate, 50 mm and 75 mm clearances against the base, wire and cable lengths, 15 mm margins on the base. All pass.
- Outputs in `blueprints/R5/`: STEP per part and `si_console_assembly_R5.step`, DXF per laser part and 2 nested sheets, dimensioned drawings (SVG, PDF), renders (hero, front, top, exploded).
- BOM: 5V case fan removed, acrylic buy cut from 6 sheets to a 4-pack (2 needed, 2 spare). Fundable total 767.15 CAD (was 791.33; current total 851.13, see 2026-11-24).
- R4.2 (boxed case) moved to `research/R4.2-boxed/` with its source; git tag `r4.2-boxed`. `blueprints/R4.2/` removed from `blueprints/`.

## 2026-11-23, Architecture visualizations
- `docs/ARCHITECTURE_DIAGRAMS.md`: 9 Mermaid diagrams covering the whole merged v1 architecture (big picture, state machine, end-to-end flow, safety stack, memory/state, providers, offline fallback, external agents, ownership). Each has a per-part DONE/PARTIAL/GAP legend. Indexed in README, llms.txt, INDEX.json. Spec remains authoritative.

## 2026-11-23, Agent architecture v1 (Jayden + Christopher)
- `docs/ARCHITECTURE.md`: authoritative merged v1 agent runtime spec (state machine, flow, safety, memory, providers, offline, external agents, ownership) plus a DRAFT implementation-gap table reconciling it with `code/`. Indexed in `README.md`, `llms.txt`, `INDEX.json`. No runtime code changed by this entry.

## 2026-11-23, R4.2
- Fan grille rule: vent holes are exempt from the 5 mm hole to hole spacing (they still keep 5 mm from the fan screw holes and from panel edges). Tried 4 mm holes with 1.5 mm webs in a staggered pattern across the 37 mm area: 30 holes, 377 mm2, which is 50% of the plain 31 mm opening (755 mm2), under the 60% threshold. Reverted to the single 31 mm opening. The grille is kept as code in `cad/panels.py` and switches in automatically if it reaches 60%.
- All checks pass. Finals now in `blueprints/R4.2/` with `_R4.2` file names; `blueprints/R4.1/` removed.

## 2026-11-23, R4.1
- Back panel: second micro-HDMI cutout removed; new 16 x 10 mm (ASSUMED) cable hole for the mini screen USB power cable from an outside charger. Screen HDMI stays inside the case.
- AGENT 1 white LED resistor set to 100 ohm. `docs/GPIO_PIN_MAP.md` (dated R4.1 section) and the schematic and wiring SVG updated. Closes OPEN 4.
- Fan: 31 mm opening replaced by a grid of 3 mm holes across the 37 mm fan area, 5 mm clear of the screw holes.
- CAD rebuilt: all checks pass. Finals now in `blueprints/R4.1/` with `_R4.1` file names; `blueprints/R4/` removed.

## 2026-11-23, R3 bug fixes (code review)
- Coordinator: `__main__` block moved to end of file (the service crash-looped with `NameError` on `pick_next_task`); `timezone` imported at module level (the stuck watchdog crashed on first run).
- Coordinator: `serve_forever` refreshes kill state from `state.json` each iteration and fails closed when it cannot be read, so a kill reaches the loop.
- Bridge: `on_kill(False)` now writes `kill_active=False` (the screens showed KILL ACTIVE forever after release).
- Vault: `create_task` takes an `initial_status` (default `queued`, validated against `STATUSES`); escalation notes are created `blocked`, so the queue no longer re-runs them and burns API credit.
- Tests: 79 → 89 passed. New `code/tests/test_regression_r3.py` covers all five fixes.

## 2026-11-23, R4 (parametric CAD)
- New `cad/`: CadQuery model driven by one `params.py` (each value tagged VERIFIED, ASSUMED or DESIGN). `python build.py` regenerates everything.
- Outputs in `cad/output/` and copied to `blueprints/R4/`: 26 STEP files plus `si_console_assembly_R4.step`, STL for printed parts, DXF per panel with kerf applied, nested layout on 4 sheets of 12 x 16 inch, dimensioned drawings (SVG and PDF), 6 labelled renders, `CHECKS.md`, `ASSUMED.md`.
- Design changes from R3: window cut to the visible display only with the module mounted under the panel (bezel kept as a switch), no soundbar and no grille, Pi 5 rotated 180 degrees so power and HDMI face the back, AGENT 1 LED white, 40 mm exhaust fan on the back, intake vents low on the sides, 4 rubber feet.
- All 6 required checks pass (collisions, holes, sheet fit, finger joints, button clearances, Pi cable reach). Many dimensions are ASSUMED and must be measured before cutting.
- Official Raspberry Pi 5 STEP downloaded and used only to cross-check the envelope (77 MB, not stored). The Pi model is built from the official mechanical drawing.
- `docs/decisions.md`: OPEN 1, 2, 3 marked R4 decided, OPEN 4 partly, OPEN 5 has a candidate DXF pending review.
- R3 files stay in `blueprints/2d` and `blueprints/3d` as reference.

## 2026-11-23, R3 review (repo created)
- R3 drawings (case panels, schematic, wiring, power, connection) and renders are REFERENCE ONLY. The laser cut file must come from Hasan's Fusion model.
- BOM Rev R2.1 finalised with both cuts: no spare microSD, no USB soundbar (monitor speakers over HDMI). Fundable total 791.33 CAD before tax (superseded; current total 851.13).
- R3 review notes logged as OPEN items in `docs/decisions.md`.
- Second drop added: 24 STEP, 6 STL, render, 5 R3 SVGs, code with tests (79 passed), Overview, Detailed, ONSHAPE_IMPORT.

## 2026-11-23, R2.1
- Spare microSD changed from 128GB to 32GB, speaker out of stock so replaced by a soundbar, 5V case fan added, travel adapter moved to REF ONLY.

## 2026-11-22, R2
- New lines: GPIO breakout, M2.5 standoff kit. Microphone link fixed. GPIO map extracted from ARCHITECTURE.md.

## 2026-11-20, R1
- First blueprint, log, open questions and parts list from research round 1 (see `research/`).
