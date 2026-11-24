# R4.2, the boxed alternative

Rev R4.2 of SI Console: a 360 x 240 x 140 mm finger-jointed clear acrylic case with a mini screen under the top panel, a 40 mm exhaust fan, and the Pi 5 inside. It was replaced by the open-frame design Rev R5 (`cad/`, `blueprints/R5/`) but is kept here in case the team wants an enclosed case. All checks passed for R4.2 (see `blueprints/CHECKS.md`), 4 laser sheets, ASSUMED dimensions still to be measured (`blueprints/ASSUMED.md`).

- `blueprints/`: STEP per part and `si_console_assembly_R4.2.step`, STL for the printed screen spacers, nested DXF, dimensioned drawings, renders.
- `cad-source/`: the CadQuery source as it was (`params.py`, `build.py`, `panels.py`, `parts.py`, `checks.py`, `outputs.py`, `render.py`, `README.md`, `requirements.txt`). To rebuild, copy it into a folder named `cad`, create a Python 3.11 venv, `pip install -r requirements.txt`, run `python build.py --no-copy`.
- Git tag `r4.2-boxed` marks the commit where R4.2 was the current design.
