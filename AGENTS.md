# AGENTS.md

For AI agents (Claude Code, Muse, Hermes). Status: DRAFT.

## Project
SI Console: physical console for supervising AI agents. Raspberry Pi 5 8GB, 5 inch HDMI mini screen, 4 agent LEDs (COORD, AGENT 1, AGENT 2, GUARD) driven by a ULN2003, green approve, red reject, latching kill switch, push to talk, EN/ZH toggle. Laser-cut acrylic case. Design rule: voice proposes, a physical button executes, fail closed. Budget: team limit about 800 CAD, hard max 900 CAD.

## Folder map
- `docs/`: decisions, GPIO map.
- `bom/`: `BOM.csv` (Rev R2.1, both cuts), `BOM_NOTES.md`.
- `blueprints/2d/`, `blueprints/3d/`: R3 PNGs, reference only.
- `code/`: scratch code (currently empty).
- `research/`: superseded material. Never cite it as current.
- Index files: `README.md` (humans), `llms.txt`, `INDEX.json`, `CHANGELOG.md`.

## Source of truth
- BOM: `bom/BOM.csv` only. GPIO: `docs/GPIO_PIN_MAP.md` only. Drawings: `blueprints/` only. Decisions: `docs/decisions.md`.
- Anything in `research/` is old. When something is replaced, move the old copy to `research/` and log it in `CHANGELOG.md`.
- Laser cut geometry comes only from Hasan's Fusion model (DXF or SVG). R3 drawings are not cut files.
- Status labels: VERIFIED (source page or test seen), LIKELY, ASSUMED, DRAFT. Do not upgrade a label without evidence.

## Naming
- Files: kebab-case or snake_case, revision suffix `-R3`, e.g. `case-panels-R3.png`. Docs in `docs/` use UPPER_SNAKE or lowercase names as already present.
- Prices in CAD before tax unless stated. Dates ISO (2026-11-23).

## Do not edit
- `research/**` (historical).
- `docs/GPIO_PIN_MAP.md` body (verbatim extract, change only through the owner, Jayden).
- `bom/BOM.csv` prices or status without a source.
- Never commit API keys, tokens, `.env`, addresses, phone numbers or order details. Binary files (PNG, STL, STEP) go through Git LFS (`.gitattributes`).

## Tests
No code is in the repo yet, so there is no test command. When code is added under `code/`, document the exact command here (the overnight workspace used Python with mocked DeepSeek and mocked GPIO, 79 tests, not re-verified).
