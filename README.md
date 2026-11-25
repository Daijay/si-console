# SI Console

STATUS: DRAFT REFERENCE. Private repo. Not for Fallen submission as-is.

SI Console is a physical desk console for controlling a team of AI agents, built for Hack Club Fallen. A Raspberry Pi 5 drives a 5 inch status screen, four agent LEDs, and physical controls: green approve, red reject, a latching kill switch, push to talk and an EN/ZH toggle. Voice proposes, a physical button executes, and the system fails closed. The case is laser-cut acrylic. Build deadline is Dec 8, 2026.

## Team

| Person | Role |
| --- | --- |
| Jayden | System, hardware, integration |
| Hasan | CAD and enclosure |
| Christopher | Software architecture |

Collaborators (private repo, write access):

| Person | GitHub | Status |
| --- | --- | --- |
| Christopher | CascV8 | Invited 2026-11-23, pending acceptance |
| Hasan | not yet added | Pending: waiting for GitHub username |

To add Hasan: GitHub, repo `Daijay/si-console`, Settings, Collaborators, Add people (https://github.com/Daijay/si-console/settings/access). Or from a terminal:

```
gh api -X PUT repos/Daijay/si-console/collaborators/<HASAN_USERNAME> -f permission=push
```

Because the repo uses Git LFS, collaborators need `git lfs install` before cloning.

## Current status (2026-11-25)

- **Rev R5 CAD is built**: open-frame "cyberdeck" (no enclosure) as a parametric CadQuery model in `cad/` (change `cad/params.py`, run `python build.py`). STEP, laser DXF (2 sheets of 12 x 16 in), dimensioned drawings and renders are in `blueprints/R5/`. All automated checks pass (`cad/output/CHECKS.md`). Many dimensions are ASSUMED: measure them with calipers before cutting (`cad/output/ASSUMED.md`). Hasan still needs to review the DXF. The boxed design (R4.2) is the alternative in `research/R4.2-boxed/`.
- BOM: 767.15 CAD fundable before tax after the R5 changes (fan and 2 acrylic sheets removed; 791.33 before), under the 800 CAD team limit. See `bom/BOM_NOTES.md`.
- R3 drawings and renders exist as PNGs. They are reference only and contain known errors, most of them fixed in R4 and R5.
- GPIO map is Rev R2 and DRAFT, with an unresolved green LED Vf.
- A candidate laser cut file now exists from R5 (`blueprints/R5/dxf/`), pending Hasan's review and the caliper measurements.
- Code tests: run once on 2026-11-23, **89 passed** (79 before the R3 bug fixes; mocked DeepSeek and GPIO, no Pi, no API keys). Not tested on the Pi.
- Model tiers: four-tier roster **ACCEPTED 2026-11-25** in `docs/MODEL_TIERS.md` (T0 DeepSeek/Hy4/GLM 5.4, T1 Qwen4 Max, T2 Hy4/DeepSeek/GLM 5.4, T3 MiMo, Jev judge). Accepted for model selection, not yet implemented — `code/` still routes to DeepSeek only.

## Decisions made / recommended (details in `docs/decisions.md`)

- Case: clear acrylic now (recommended, final choice pending).
- Mini screen: 5 inch HDMI (recommended, pending).
- Model router: v1 runtime is DeepSeek only. Four-tier provider roster with Jev judge **accepted 2026-11-25** (`docs/MODEL_TIERS.md`), pending implementation.
- Both BOM cuts applied: no spare microSD, no USB soundbar (monitor speakers over HDMI).

## Open decisions (R3 review, see `docs/decisions.md`; R4 and R5 outcomes noted there)

1. Mini screen cutout: no longer applies in R5, the screen sits on an angled stand instead of in a panel.
2. Soundbar cut: no soundbar and no grille in R4 or R5. Done in CAD.
3. Pi 5 port side: the Pi is rotated 180 degrees so power and HDMI face the back and the cables leave off the back edge. Dry fit the cables.
4. AGENT 1 LED is white with a 100 ohm resistor (closed in R4.1; bench-measure the white Vf).
5. Laser cut file: R5 supplies a candidate DXF. Hasan reviews it before anything is cut.

## Where to find things

| Thing | Location |
| --- | --- |
| Decisions and open items | `docs/decisions.md` |
| Agent runtime spec (authoritative v1) and gaps | `docs/ARCHITECTURE.md` |
| Architecture visualizations (10 Mermaid diagrams) | `docs/ARCHITECTURE_DIAGRAMS.md` |
| Model tiers (accepted roster, selection rules, arena cost) | `docs/MODEL_TIERS.md` |
| GPIO pin map (only one) | `docs/GPIO_PIN_MAP.md` |
| BOM (only one) and totals | `bom/BOM.csv`, `bom/BOM_NOTES.md` |
| R5 CAD (parametric, open frame), outputs and checks | `cad/`, `blueprints/R5/` |
| R4.2 boxed case alternative | `research/R4.2-boxed/` |
| 2D drawings (SVG sources and PNG, R3) | `blueprints/2d/` |
| 3D: STEP per part and assembly, STL, renders | `blueprints/3d/` |
| Onshape / Fusion import steps | `docs/ONSHAPE_IMPORT.md` |
| Overview and detailed docs | `docs/SI_Console_Overview.md`, `docs/SI_Console_Detailed.md` |
| Scratch code, tests, pinned requirements (DRAFT REFERENCE) | `code/` |
| Older material, round 1 research, UI design system | `research/` |
| File index for people and agents | `llms.txt`, `INDEX.json`, `AGENTS.md` |
| History | `CHANGELOG.md` |

## Still missing

- Review files (e.g. `reviews/11-skeptic-r3.md`).
- Note: `blueprints/3d/` still includes `soundbar.step` and `monitor.step` (in the assembly). The soundbar is cut from the BOM, see OPEN 2 in `docs/decisions.md`.

Binary files (PNG, STL, STEP) are stored with Git LFS.
