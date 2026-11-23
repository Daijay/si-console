# Changelog

Dated log of decisions and revisions. Newest first.

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
