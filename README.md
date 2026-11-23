# SI Console

STATUS: DRAFT REFERENCE. Private repo. Not for Fallen submission as-is.

SI Console is a physical desk console for controlling a team of AI agents, built for Hack Club Fallen. A Raspberry Pi 5 drives a 5 inch status screen, four agent LEDs, and physical controls: green approve, red reject, a latching kill switch, push to talk and an EN/ZH toggle. Voice proposes, a physical button executes, and the system fails closed. The case is laser-cut acrylic. Build deadline is Dec 8, 2026.

## Team

| Person | Role |
| --- | --- |
| Jayden | System, hardware, integration |
| Hasan | CAD and enclosure |
| Christopher | Software architecture |

To add Hasan and Christopher: GitHub, repo `Daijay/si-console`, Settings, Collaborators, Add people (direct link: https://github.com/Daijay/si-console/settings/access). Or from a terminal, once you have their usernames:

```
gh api -X PUT repos/Daijay/si-console/collaborators/<HASAN_USERNAME> -f permission=push
gh api -X PUT repos/Daijay/si-console/collaborators/<CHRISTOPHER_USERNAME> -f permission=push
```

Nobody has been invited yet. Because the repo uses Git LFS, collaborators need `git lfs install` before cloning.

## Current status (2026-11-23)

- BOM Rev R2.1 with both cuts: 791.33 CAD fundable before tax, under the 800 CAD team limit. See `bom/BOM_NOTES.md`.
- R3 drawings and renders exist as PNGs. They are reference only and contain known errors (see open decisions).
- GPIO map is Rev R2 and DRAFT, with an unresolved green LED Vf.
- No laser cut file exists yet. It must come from Hasan's Fusion model (DXF or SVG).
- Code tests: **not run**. The overnight scratch code was not found on the machine that built this repo, so there was nothing to test. Morning notes report 79 mocked tests passing in the original workspace (not re-run, not verified here).

## Decisions made / recommended (details in `docs/decisions.md`)

- Case: clear acrylic now (recommended, final choice pending).
- Mini screen: 5 inch HDMI (recommended, pending).
- Model router: DeepSeek only at the booth (recommended, pending).
- Both BOM cuts applied: no spare microSD, no USB soundbar (monitor speakers over HDMI).

## Open decisions (R3 review, see `docs/decisions.md`)

1. Mini screen cutout 122 x 90.5 mm is the full module size, so the screen would fall through. Hasan decides in CAD.
2. If the soundbar cut stands, remove the grille holes and soundbar from drawings.
3. Pi 5 HDMI and USB-C power are on the long side. Check back panel routing in CAD.
4. AGENT 1 LED changes from red to white. Red is for reject and kill only.
5. Laser cut file must come from Hasan's Fusion model.

## Where to find things

| Thing | Location |
| --- | --- |
| Decisions and open items | `docs/decisions.md` |
| GPIO pin map (only one) | `docs/GPIO_PIN_MAP.md` |
| BOM (only one) and totals | `bom/BOM.csv`, `bom/BOM_NOTES.md` |
| 2D drawings (PNG, R3) | `blueprints/2d/` |
| 3D renders (PNG, R3) | `blueprints/3d/` |
| Scratch code | `code/` (empty, see note) |
| Older material, round 1 research, UI design system | `research/` |
| File index for people and agents | `llms.txt`, `INDEX.json`, `AGENTS.md` |
| History | `CHANGELOG.md` |

## Missing from this repo (not found locally, upload when located)

- `blueprints/3d/`: 24 STEP files, 6 STL files (CadQuery model outputs).
- `code/`: scratch code, tests, pinned requirements.
- `docs/`: `SI_Console_Overview.md`, `SI_Console_Detailed.md`, `ONSHAPE_IMPORT.md`.
- `research/`: `reviews/11-skeptic-r3.md` and other review files.
- `blueprints/2d/`: R3 SVG sources.

Binary files (PNG, STL, STEP) are stored with Git LFS.
