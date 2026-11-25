# AGENTS.md

For AI agents (Claude Code, Muse, Hermes). Status: DRAFT.

## Project
SI Console: physical console for supervising AI agents. Raspberry Pi 5 8GB, 5 inch HDMI mini screen, 4 agent LEDs (COORD, AGENT 1, AGENT 2, GUARD) driven by a ULN2003, green approve, red reject, latching kill switch, push to talk, EN/ZH toggle. Laser-cut acrylic case. Design rule: voice proposes, a physical button executes, fail closed. Budget: team limit about 800 CAD, hard max 900 CAD.

## Folder map
- `docs/`: ARCHITECTURE (authoritative agent runtime spec), decisions, GPIO map, Overview, Detailed, ONSHAPE_IMPORT.
- `bom/`: `BOM.csv` (Rev R2.1, both cuts), `BOM_NOTES.md`.
- `cad/`: Rev R5 (open frame) parametric CadQuery model (`params.py`, `build.py`, `README.md`). Regenerate with `python build.py`; do not hand-edit `cad/output/` or `blueprints/R5/`.
- `blueprints/R5/`: R5 finals (STEP, DXF, drawings, renders) copied from `cad/output/`.
- `research/R4.2-boxed/`: the boxed alternative (R4.2), historical; do not edit.
- `blueprints/2d/`: R3 SVG sources and PNGs, reference only.
- `blueprints/3d/`: STEP (one per part plus `si_console_assembly.step`), STL, renders. Generated from a parametric CadQuery model; reference only.
- `code/`: DRAFT REFERENCE scratch code (`si_console/`, `tests/`, `systemd/`, `dashboard/`).
- `research/`: superseded material. Never cite it as current.
- Index files: `README.md` (humans), `llms.txt`, `INDEX.json`, `CHANGELOG.md`.

## Source of truth
- BOM: `bom/BOM.csv` only. GPIO: `docs/GPIO_PIN_MAP.md` only. Drawings: `blueprints/` only. Decisions: `docs/decisions.md`. Agent runtime architecture: `docs/ARCHITECTURE.md` only.
- Anything in `research/` is old. When something is replaced, move the old copy to `research/` and log it in `CHANGELOG.md`.
- Laser cut geometry: R3 drawings are not cut files. The R5 DXFs from `cad/build.py` are candidates, to be reviewed by Hasan and cut only after the ASSUMED dimensions (`cad/output/ASSUMED.md`) are measured.
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
From `code/`: create a venv, `pip install -r requirements.txt`, then `python -m pytest tests/ -v`. Expected: 134 passed (last run 2026-11-24; was 89 before the 2026-11-24 bug pass and 79 before the R3 bug fixes, see `CHANGELOG.md`). Tests use mocked DeepSeek and mocked GPIO and need no Pi and no keys. Never put real keys in `code/`; `.env.example` has names only. Do not hard-code a DeepSeek model name (pin it in `.env`).
