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

## Current status (2026-11-23)

- **Rev R4.2 CAD is built**: parametric CadQuery model in `cad/` (change `cad/params.py`, run `python build.py`). STEP, STL, laser DXF (4 sheets of 12 x 16 in), dimensioned drawings and renders are in `blueprints/R4.2/`. All six automated checks pass (`cad/output/CHECKS.md`). Many dimensions are ASSUMED: measure them with calipers before cutting (`cad/output/ASSUMED.md`). Hasan still needs to review the DXF.
- BOM Rev R2.1 with both cuts: 791.33 CAD fundable before tax, under the 800 CAD team limit. See `bom/BOM_NOTES.md`.
- R3 drawings and renders exist as PNGs. They are reference only and contain known errors, most of them fixed in R4.
- GPIO map is Rev R2 and DRAFT, with an unresolved green LED Vf.
- A candidate laser cut file now exists from R4 (`blueprints/R4.2/dxf/`), pending Hasan's review and the caliper measurements.
- Code tests: run once on 2026-11-23, **89 passed** (79 before the R3 bug fixes; mocked DeepSeek and GPIO, no Pi, no API keys). Not tested on the Pi.

## Decisions made / recommended (details in `docs/decisions.md`)

- Case: clear acrylic now (recommended, final choice pending).
- Mini screen: 5 inch HDMI (recommended, pending).
- Model router: DeepSeek only at the booth (recommended, pending).
- Both BOM cuts applied: no spare microSD, no USB soundbar (monitor speakers over HDMI).

## Open decisions (R3 review, see `docs/decisions.md`; R4 outcomes noted there)

1. Mini screen cutout: R4 cuts the window to the visible area and mounts the module under the panel (bezel is a switch). Measure the real visible area.
2. Soundbar cut: R4 has no soundbar and no grille. Done in CAD.
3. Pi 5 port side: R4 rotates the Pi 180 degrees so power and HDMI face the back. Dry fit the cables.
4. AGENT 1 LED is white with a 100 ohm resistor (closed in R4.1; bench-measure the white Vf).
5. Laser cut file: R4 supplies a candidate DXF. Hasan reviews it before anything is cut.

## Where to find things

| Thing | Location |
| --- | --- |
| Decisions and open items | `docs/decisions.md` |
| Agent runtime spec (authoritative v1) and gaps | `docs/ARCHITECTURE.md` |
| GPIO pin map (only one) | `docs/GPIO_PIN_MAP.md` |
| BOM (only one) and totals | `bom/BOM.csv`, `bom/BOM_NOTES.md` |
| R4 CAD (parametric), outputs and checks | `cad/`, `blueprints/R4.2/` |
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
