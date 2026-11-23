# Changelog

Dated log of decisions and revisions. Newest first.

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
- BOM Rev R2.1 finalised with both cuts: no spare microSD, no USB soundbar (monitor speakers over HDMI). Fundable total 791.33 CAD before tax.
- R3 review notes logged as OPEN items in `docs/decisions.md`.
- Second drop added: 24 STEP, 6 STL, render, 5 R3 SVGs, code with tests (79 passed), Overview, Detailed, ONSHAPE_IMPORT.

## 2026-11-23, R2.1
- Spare microSD changed from 128GB to 32GB, speaker out of stock so replaced by a soundbar, 5V case fan added, travel adapter moved to REF ONLY.

## 2026-11-22, R2
- New lines: GPIO breakout, M2.5 standoff kit. Microphone link fixed. GPIO map extracted from ARCHITECTURE.md.

## 2026-11-20, R1
- First blueprint, log, open questions and parts list from research round 1 (see `research/`).
