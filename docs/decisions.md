# Decisions

STATUS: DRAFT. Figures come from `research/overnight-notes/MORNING_SUMMARY_2026-11-23.md`. "Final choice" stays blank until the team decides. Rev R4 (2026-11-23) built the CAD around the defaults below and closed or narrowed the R3 review items; those lines are marked "R4".

## A. From the overnight run (recommendations, awaiting confirmation)

### 1. Case material
- Options: clear laser-cut acrylic, or nylon print at JLCPCB.
- Cost: acrylic about 103 to 153 CAD with laser, files go today, arrives by Dec 2. Nylon about 125 to 145 CAD all in (ASSUMED), 1 to 2 days of redesign, likely misses Dec 1.
- Recommendation: acrylic now, nylon as a second case later.
- Final choice: R4 builds the case as clear 3 mm laser-cut acrylic with finger joints (360 x 240 x 140 mm outer). Not yet signed off by the team.

### 2. Mini screen
- Options: 5 inch HDMI (Waveshare, 73.95 CAD) or 5 inch DSI LCD (about 73.94 CAD, needs a cable, overlay test, Rev2.2 check and a top panel redraw). The brief's 5.5 inch DSI touchscreen does not exist.
- Recommendation: HDMI.
- Final choice: R4 uses the 5 inch HDMI Waveshare (H) module, 121 x 89.48 mm. Not yet signed off by the team.

### 3. Model router
- Options: DeepSeek only at the booth, or add Claude (claude-fable-5-2, 8 USD input / 40 USD output per 1M tokens, about 27x DeepSeek flash). Anthropic policy does not support use by persons physically in mainland China. The router stub falls back to DeepSeek only.
- Recommendation: DeepSeek only, premium tier maps to deepseek-v4-pro.
- Final choice: _pending_

## B. R3 review notes, OPEN for the team

### OPEN 1. Mini screen cutout (owner: Hasan, in CAD) - R4 DECIDED, caliper check pending
The 122 x 90.5 mm cutout is the full module size, so the screen would fall through. Options:
1. Cut to the visible display area and screw the module underneath.
2. Keep the full cutout and add a printed bezel on top.

R4 decision: option 1 is the default. The top panel window is the visible display area only (109 x 66 mm, ASSUMED) with 4 M2.5 screw holes, and the module hangs under the panel on 3 mm printed spacers. Option 2 is a switch (`SCREEN_MODE = "bezel"` in `cad/params.py`) that gives the full cutout plus a printed bezel STL. Still to do: measure the visible area and the module hole positions on the real Waveshare board.

### OPEN 2. Soundbar cut (owner: Hasan, drawings) - R4 DECIDED
If the soundbar cut is applied (use monitor speakers over HDMI), remove the speaker grille holes and the soundbar from the drawings. The BOM already has the cut applied. `blueprints/3d/soundbar.step` and the R3 assembly still include it.

R4 decision: no speaker, no soundbar, no grille holes in the R4 CAD. Sound comes from the monitor over HDMI. (`ENABLE_SPEAKER_GRILLE` exists in `cad/params.py` and is off.)

### OPEN 3. Pi 5 port side (owner: Hasan, CAD) - R4 DECIDED
Pi 5 HDMI and USB-C power are on its long side, not the USB/Ethernet end. Check back panel cable routing in CAD.

R4 decision: the Pi is rotated 180 degrees so its long power and HDMI edge faces the back panel, with 65 mm of room for plugs and bends. The GPIO header then faces the front toward the perfboard and the USB/Ethernet end faces the left wall (32 mm for the mic plug). The cable-reach check passes with assumed plug lengths; confirm with a dry fit. Details in `cad/README.md`.

### OPEN 4. LED colours (owner: Jayden) - CLOSED in R4.1
AGENT 1 changes from red to white. Red stays for reject and kill only. Update drawings and the resistor table (white LED Vf is not in the current resistor math in `GPIO_PIN_MAP.md`).

R4: the CAD uses COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow, left to right.

R4.1: AGENT 1 white resistor = 100 ohm (Jayden). `docs/GPIO_PIN_MAP.md` has a dated R4.1 section with the math, and `blueprints/2d/electrical-schematic.svg` shows AGENT 1 white, 100 ohm, Vf 3.2 V ASSUMED. The white Vf is still to be measured on the bench like the other colours.

### OPEN 5. Laser cut file source (owner: Hasan) - R4 supplies a candidate DXF, review pending
R3 drawings are reference only. The laser cut file must come from Hasan's Fusion model as DXF or SVG cut lines.

R4: `cad/build.py` now generates DXF cut files with kerf applied, plus a nested layout on 4 sheets of 12 x 16 inch stock (`blueprints/R4/dxf/`). They are NOT ready to cut until Hasan reviews them against his Fusion model and the ASSUMED dimensions in `cad/output/ASSUMED.md` are measured with calipers.

## C. Rev R4 summary (2026-11-23)

What R4 decided, as defaults that are each a switch in `cad/params.py`:

- Case: clear 3 mm acrylic, finger joints (15 mm target), kerf 0.2 mm, outer 360 x 240 x 140 mm.
- Mini screen: Waveshare 5inch HDMI LCD (H), window to the visible area, module under the panel (switch for full cutout plus printed bezel).
- No speaker, no soundbar, no grille.
- Main monitor MSI PRO MP165 E6 sits behind the case on its kickstand, assembly only, never a cut part.
- Front panel: green and red 30 mm buttons, 22 mm kill switch, 12 mm push-to-talk and EN/ZH toggle, 4 status LEDs (green, white, blue, yellow). 50 mm clear behind the arcade buttons, 75 mm behind the kill switch.
- Pi 5 with Active Cooler at rear left on 10 mm standoffs, rotated 180 degrees (see OPEN 3). Perfboard with ULN2003 in the centre on M3 standoffs.
- Back panel: 2 micro-HDMI cutouts, USB-C power, 1 mic USB cutout, 40 mm exhaust fan high up. Intake vents low on the sides. No vents on the bottom.

Not decided by R4: model router (section A.3), BOM changes.

Open after R4: measure every ASSUMED dimension (`cad/output/ASSUMED.md`), have Hasan review the DXF, do a dry fit of the Pi cables.

## D. Rev R4.1 changes (2026-11-23)

- Back panel: the second micro-HDMI cutout is removed (the mini screen HDMI cable stays inside the case). In its place is a small cable hole, 16 x 10 mm (ASSUMED), sized for a USB-A plug, for the mini screen USB power cable that comes from an outside charger.
- AGENT 1 (white) LED resistor = 100 ohm. Closes OPEN 4. `GPIO_PIN_MAP.md` and the schematic updated.
- Fan: the single 31 mm opening is replaced by a grid of 3 mm holes (8.5 mm pitch) across the 37 mm fan area, 13 holes. Each hole keeps at least 5 mm from the fan screw holes and from every other hole. The hole check passes.
- Back view render now hides the monitor so the panel is visible.
- Outputs are named `_R4.1` and live in `blueprints/R4.1/` (the R4 folder was removed, its history stays in git).

## E. Rev R4.2 change (2026-11-23)

- Fan: the R4.1 grid of 3 mm holes is dropped. Vent holes are now exempt from the 5 mm hole to hole rule. A 4 mm hole, 1.5 mm web grille across the 37 mm area reaches only 50% of the plain 31 mm opening's area (limit set at 60%), so the single 31 mm opening is back. To get a grille that passes, use smaller webs or a bigger area; the numbers are in `cad/output/CHECKS.md`.

