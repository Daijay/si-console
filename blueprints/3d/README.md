# blueprints/3d/

DRAFT, REFERENCE ONLY. Superseded by Rev R5 in `blueprints/R5/` (built from `cad/`). Generated from the parametric CadQuery model, R3, 2026-11-23. Tracked with Git LFS.

- `si_console_assembly.step`: full assembly.
- `case_*.step` and `case_*.stl`: bottom, front, back, left, right, top panels. `case_fan.step`.
- Parts (STEP): `pi5`, `mini_screen`, `mini_screen_wedge`, `btn_green`, `btn_red`, `btn_ptt`, `kill_switch`, `toggle_lang`, `led_coord`, `led_agent1`, `led_agent2`, `led_guard`, `perfboard`, `uln2003`, `monitor`, `soundbar`.
- Renders: `render_see_through.png`, `render-hero-R3.png`, `render-exploded-R3.png`, `render-front-R3.png`, `render-top-R3.png`.

Known issues (see `docs/decisions.md`): mini screen cutout is full module size, `soundbar.step` is still in the assembly although the soundbar is cut, Pi 5 port side, AGENT 1 LED colour. The laser cut file must come from Hasan's Fusion model. Import steps: `docs/ONSHAPE_IMPORT.md`.
