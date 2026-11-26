# Contributing

## How the repo is laid out

| Folder | Contents |
| --- | --- |
| `code/` | Python code (`si_console/`), tests, Pi deploy scripts, systemd units and dashboard files |
| `cad/` | Parametric CadQuery model of the current open-frame design (R5). `build.py` writes `cad/output/` and copies finals to `blueprints/R5/` |
| `blueprints/` | Drawings, STEP and DXF files. `R5/` is current, `2d/` and `3d/` are older |
| `pcb/` | KiCad project for the Pi HAT, gerbers and the net check |
| `bom/` | `BOM.csv` (the only current parts list) and `BOM_NOTES.md` |
| `docs/` | Architecture, decisions, pin map and overview documents |
| `research/` | Older, superseded material. Do not treat it as current |

Do not hand-edit `cad/output/` or `blueprints/R5/`; regenerate them with `build.py`. Log changes in `CHANGELOG.md`. PNG, STL and STEP files go through Git LFS (see `.gitattributes`). Never commit API keys, `.env`, addresses, phone numbers or order details. Do not change a price in the BOM without a source.

## Run the tests

From `code/`:

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt        (Windows: .venv\Scripts\pip)
.venv/bin/python -m pytest tests/ -v             (Windows: .venv\Scripts\python)
```

The tests need no Pi and no API keys.

## Run the CAD checks

CadQuery needs Python 3.11. From `cad/`:

```
py -3.11 -m venv .venv                            (macOS, Linux: python3.11 -m venv .venv)
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python build.py
```

`build.py` exits with status 1 if any check fails; `output/CHECKS.md` says which one. Add `--no-render --no-copy` for a quick run that leaves `blueprints/R5/` alone.

## Run the PCB checks

From the repo root:

```
python pcb/check_nets.py
kicad-cli sch erc --severity-all --exit-code-violations pcb/si_console_hat.kicad_sch
kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations pcb/si_console_hat.kicad_pcb
```

The first needs only Python. The other two need KiCad 9.

## GPIO pin map rule

`code/si_console/gpio_map.py` is the source of truth for pins. Import pin numbers from it; do not copy them into other code. `docs/GPIO_PIN_MAP.md`, the wiring diagram and the PCB must match it. Agree any pin change with Jayden first, then update all of them together and run the tests and `pcb/check_nets.py`.

## Commit author rule

Commit under the name and email of the person making the change (Jayden commits as `Jayden Dai <Daijayden5@gmail.com>`). Do not add co-author lines, tool credits or other trailers to commit messages.
