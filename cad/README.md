# SI Console CAD, Rev R4.2

Parametric CadQuery model of the whole console. Change one number in `params.py`, run `build.py`, and every part, laser file, drawing, render and check is regenerated.

Status: DRAFT. The geometry is complete and every automated check passes (`output/CHECKS.md`), but some dimensions are estimates. See [Measure with calipers before cutting](#measure-with-calipers-before-cutting) at the bottom before sending anything to a laser.

## Run it

Tested on Python 3.11. The CadQuery OCP wheels for Python 3.14 were not available when this was built.

```
cd cad
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt     (Windows)
# source .venv/bin/activate && pip install -r requirements.txt   (macOS, Linux)

python build.py              # everything, about a minute
python build.py --no-render  # skip the PNG renders (about 30 s)
python build.py --no-copy    # do not copy finals into ../blueprints/R4
```

`build.py` exits with status 1 and prints a banner if any check fails. It still writes all outputs so you can look at the problem, and `output/CHECKS.md` says what failed.

## Change things

| I want to ... | Edit in `params.py` |
| --- | --- |
| Use a different acrylic thickness | `T` (finger slots follow, kerf follows) |
| Change the kerf or finger width | `KERF`, `FINGER_W` |
| Resize the case | `CASE_W`, `CASE_D`, `CASE_H` |
| Move a button or LED | `GREEN_X`, `RED_X`, `KILL_X`, `PTT_X`, `TOGGLE_X`, `BTN_Z`, `LED_Z`, `LED_PITCH` |
| Switch the mini screen to a printed bezel | `SCREEN_MODE = "bezel"` |
| Fix the screen window after measuring | `SCREEN_VIS_W`, `SCREEN_VIS_D`, `SCREEN_VIS_OFFSET_X`, `SCREEN_VIS_OFFSET_Y` |
| Move the Pi | `PI_X0`, `PI_BACK_GAP` |
| Turn the fan, side vents, monitor, speaker grille or bottom vents on or off | `ENABLE_FAN`, `ENABLE_SIDE_VENTS`, `INCLUDE_MONITOR`, `ENABLE_SPEAKER_GRILLE`, `ENABLE_BOTTOM_VENTS` |

Every line in `params.py` ends with a tag:

- `VERIFIED`: from the brief, a manufacturer drawing, or the official Raspberry Pi STEP. Safe to cut from.
- `ASSUMED`: an estimate. Measure before cutting. These are listed at the bottom of this file and on `output/ASSUMED.md`, and drawn in orange with an "A" on the panel drawings.
- `DESIGN`: a free layout choice. Nothing to measure.

If a change breaks a rule (a hole too close to an edge, two parts colliding, a cable that cannot reach), the check fails and says which one.

## Files

| File | What it does |
| --- | --- |
| `params.py` | Every dimension and switch, one comment and one tag per line |
| `build.py` | Runs everything and writes the outputs |
| `panels.py` | Finger-jointed panel outlines and holes, as one 2D model used for STEP, DXF and drawings |
| `parts.py` | Buttons, Pi 5, screen, fan and the rest, plus the assembly |
| `checks.py` | The six required checks plus a parameter sanity check |
| `outputs.py` | STEP, STL, DXF, nesting and the dimensioned drawings |
| `render.py` | Labelled PNG renders (VTK, offscreen) |
| `requirements.txt` | Pinned versions |

## Outputs (all in `output/`, finals also copied to `../blueprints/R4.2/`)

| Folder or file | Contents |
| --- | --- |
| `step/` | One STEP per part |
| `si_console_assembly_R4.2.step` | Whole assembly with names and colours |
| `stl/` | 3D printed parts: `screen_spacer_R4.2.stl` (4 spacers). With `SCREEN_MODE = "bezel"` it is `screen_bezel_R4.2.stl` instead |
| `dxf/panel_*_R4.2.dxf` | Each panel as clean cut lines on layer `CUT`, kerf applied |
| `dxf/nested_sheet_N_R4.2.dxf` | Nested sheets for 12 x 16 in (305 x 406 mm) stock. Part names are on layer `LABEL_NOCUT`, which a laser should not cut |
| `dxf/nested_layout_R4.2.png` | Picture of the nested sheets |
| `drawings/panel_*_R4.2.svg`, `panels_R4.2.pdf` | Dimensioned drawing of every panel with every hole position and size |
| `renders/` | hero, front, top, back, exploded, see-through, all labelled |
| `CHECKS.md` | Check results |
| `ASSUMED.md` | The ASSUMED list |

Sheets used: **4** (top, bottom, front plus back, left plus right). The two 360 x 240 plates cannot share a sheet because 240 mm leaves only 65 mm of the 305 mm width. Counts update in `CHECKS.md` if you change sizes.

## Case construction

- Outer 360 W x 240 D x 140 H, 3 mm clear acrylic.
- Top and bottom plates are the full 360 x 240 footprint and own the 8 corner cubes. Front and back are 360 wide with 134 mm between the plates (140 mm overall with their finger tabs). Left and right sit between front and back.
- Every joint is a finger joint with an odd number of equal fingers, closest to the 15 mm target (23, 15 or 9 fingers per edge, 14.9 to 15.6 mm wide). Neighbouring panels get the complementary pattern, so they mate by construction, and the check proves it in 3D by testing that every edge bar is filled exactly once.
- Kerf: DXF cut paths are offset by `KERF / 2` outward on outlines and inward on holes, so finished parts come out at nominal size and fingers fit. STEP files and drawings are nominal (no kerf).
- Views: top, front, back, left, right are drawn as seen from outside. The bottom is drawn as a plan view from above.

## Inside the case

### How the Pi 5 is oriented (open decision 3)

The Pi 5's USB-C power port and both micro-HDMI ports are on its long (85 mm) edge, not on the USB/Ethernet end. The board is rotated 180 degrees from its usual orientation so that long edge faces the back panel:

- Power and HDMI plugs point straight at the back panel, with 65 mm between the board edge and the panel (`PI_BACK_GAP`) for the plug (about 25 mm) and an S-bend.
- The three ports sit only 13.5 to 14.6 mm apart but the cutouts are about 30 mm apart, so each cable steps sideways by up to 16 mm. The check computes the run each S-bend needs (bend radius 20 mm, at most 45 degrees off the plug axis) and compares it to the room available.
- The GPIO header ends up on the front long edge, facing the perfboard and the GPIO ribbon breakout in the middle of the case.
- The USB/Ethernet end faces the left wall. That leaves 32 mm for the mic USB-A plug, which then turns and runs along the left wall to its cutout on the back panel.
- Active Cooler, standoffs 10 mm (M2.5, 58 x 49 mm hole pattern, 3.5 mm from edges).
- The microSD slot is on the underside at the board's left end in the drawing's orientation, which after the turn faces into the case toward the perfboard. Insert the card before fitting the board.

### Raspberry Pi model

The official Raspberry Pi 5 STEP model was downloaded from `datasheets.raspberrypi.com/rpi5/RaspberryPi5-step.zip` (MIT licence, 77 MB, `rpi-5b_no_graphics.step`). It is too heavy to embed: the assembly would be about 80 MB and every collision test would crawl. So the Pi in this model is built from the official mechanical drawing (`datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf`), and the official STEP was used to cross-check the envelope: board edge overhangs (3.0 mm at the USB end, 1.6 mm at the HDMI edge) and USB stack height (15.9 mm above the PCB). The STEP itself is not stored in this repo.

### Other

- Perfboard (70 x 90) with the ULN2003 in the centre on four 10 mm M3 standoffs. GPIO ribbon breakout between the Pi header and the perfboard.
- Mini screen module (Waveshare 5 inch HDMI LCD (H), 121 x 89.48 mm) hangs under the top panel on 3 mm printed spacers. The top panel window is only the visible area, so the module cannot fall through. `SCREEN_MODE = "bezel"` gives the alternative: full cutout plus a printed bezel with screw bosses.
- Front panel: green 30 mm, red 30 mm, kill switch 22 mm, push-to-talk 12 mm, EN/ZH toggle 12 mm, and four 5 mm LEDs in a row above (COORD green, AGENT 1 white, AGENT 2 blue, GUARD yellow). Clear space: 50 mm behind the arcade buttons, 75 mm behind the kill switch.
- Back panel: 1 micro-HDMI cable cutout (main monitor), Pi USB-C power, 1 USB cable out for the mic, a small hole for the mini screen USB power cable (it comes from an outside charger; the screen HDMI stays inside), and a 40 mm fan mount (32 mm hole spacing) high on the back for exhaust. The fan opening is a single 31 mm hole (the largest that keeps 5 mm from the screw holes). `build.py` first tries a staggered grille of 4 mm holes with 1.5 mm webs across the 37 mm area (vent holes are exempt from the hole to hole rule, but keep 5 mm from screw holes and edges). It uses the grille only if its open area is at least 60% of the plain opening; with the current numbers it reaches about 50%, so it falls back to the plain opening. `CHECKS.md` reports the numbers.
- Sides: intake slots low down. Bottom: Pi standoff holes, perfboard standoff holes, 4 rubber-foot holes, no vents.
- No speaker, soundbar or grille. Sound comes from the monitor over HDMI.
- MSI PRO MP165 E6 (356.5 x 210.35 x 13.85 mm) is in the assembly only, standing behind the case on a tilted kickstand with a 45 mm air gap. It is never a cut part.

## What the checks do

| Check | How |
| --- | --- |
| No collisions | Every pair of parts is intersected in 3D. Touching is fine, overlap above 0.5 mm3 fails |
| Holes | Each hole must be inside its panel outline (finger notches included), at least 5 mm from any edge and from any other hole |
| Sheet fit | Each panel with kerf must fit the 305 x 406 mm sheet minus a 5 mm margin |
| Finger joints | All 12 edge bars and 8 corner cubes are intersected with the two panels that share them and must be filled exactly once |
| Clearances | A box behind each control (hole size plus 5 mm each side) must contain no other part, and the control's own body must be shorter than the required clearance |
| Cables | S-bend geometry for the Pi cables, mic USB plug room and path length, GPIO ribbon length |

The cable check is geometry with assumed plug lengths and bend radius, not a physical test. Do a dry fit with the real cables.

## Measure with calipers before cutting

Everything below is tagged `ASSUMED` in `params.py`. Measure the real part, change the number, and re-run `build.py`. This list is regenerated by `build.py` from `params.py`.

<!-- ASSUMED:START (generated by build.py, do not edit by hand) -->

| Parameter | Value | What it is |
| --- | --- | --- |
| `T` | `3.0` | Acrylic thickness as delivered (brief says 3 mm, cast sheet varies 2.9 to 3.2). Finger fit depends on it. |
| `SCREEN_MODULE_H` | `13.0` | Module thickness incl. glass and rear connectors; check the Waveshare drawing. |
| `SCREEN_VIS_W` | `109.0` | Visible display width (brief: about 109). Check the Waveshare drawing. |
| `SCREEN_VIS_D` | `66.0` | Visible display height (brief: about 66). Check the Waveshare drawing. |
| `SCREEN_VIS_OFFSET_X` | `0.0` | Visible area centre offset from module centre, X. Real modules are often off-centre. |
| `SCREEN_VIS_OFFSET_Y` | `0.0` | Visible area centre offset from module centre, Y. |
| `SCREEN_HOLE_INSET` | `3.5` | Module mounting hole centre, distance from each module edge. |
| `SCREEN_GAP` | `3.0` | Space between panel underside and module top face (printed spacer length). |
| `MON_TILT` | `15.0` | Kickstand tilt from vertical, degrees. |
| `BTN_FLANGE_D` | `36.0` | Arcade button front flange diameter. |
| `BTN_CAP_PROUD` | `10.0` | Arcade cap height in front of the panel. |
| `ARCADE_REAR` | `30.0` | Arcade body depth behind the panel inner face (incl. microswitch). |
| `KILL_HEAD_D` | `40.0` | Kill switch mushroom head diameter. |
| `KILL_HEAD_H` | `22.0` | Kill switch head height in front of the panel. |
| `KILL_REAR` | `55.0` | Kill switch body depth behind the panel inner face. |
| `PTT_HEAD_D` | `14.0` |  |
| `PTT_HEAD_H` | `6.0` |  |
| `PTT_REAR` | `20.0` |  |
| `TOGGLE_LEVER_D` | `4.0` |  |
| `TOGGLE_LEVER_H` | `15.0` |  |
| `TOGGLE_REAR` | `20.0` |  |
| `LED_FLANGE_D` | `5.9` | LED rim, sits behind the panel. |
| `LED_DOME_PROUD` | `1.0` | LED dome in front of the panel. |
| `LED_REAR` | `8.0` | LED body behind the panel. |
| `PI_PORT_Z` | `1.7` | Height of the USB-C and micro-HDMI port centres above the PCB top. |
| `PI_USB_STACK` | `(17.0, 14.5, 15.9)` | VERIFIED height (official STEP, top at 17.5 above PCB underside); length and width ASSUMED. |
| `PI_ETH_BOX` | `(21.0, 16.0, 13.5)` | Ethernet length (along BY), width (along BX, inside board), height. |
| `COOLER_SIZE` | `(40.0, 40.0, 15.0)` | Active Cooler footprint X, Y and height above the PCB top. |
| `COOLER_BX` | `34.0` | Cooler centre along the length. |
| `COOLER_BY` | `26.0` | Cooler centre from the HDMI long edge. |
| `PERF_X` | `70.0` | Perfboard size along X (7 x 9 cm board). |
| `PERF_Y` | `90.0` | Perfboard size along Y. |
| `PERF_T` | `1.6` |  |
| `PERF_HOLE_INSET` | `4.0` | Mounting hole inset from each edge. |
| `ULN_SIZE` | `(19.5, 6.5, 4.6)` | ULN2003 DIP-16 length, width, height. |
| `BREAKOUT_SIZE` | `(52.0, 22.0, 8.0)` | GPIO ribbon breakout board. |
| `GPIO_RIBBON_LEN` | `150.0` | Ribbon cable length available. |
| `FOOT_D` | `15.0` | Rubber foot diameter. |
| `FOOT_H` | `6.0` | Rubber foot height. |
| `FOOT_HOLE_D` | `4.2` | Foot screw hole (M4). |
| `HDMI_CUT` | `(24.0, 12.0)` | micro-HDMI to HDMI adapter cable to the main monitor, plug passes through. Width, height. |
| `USBC_CUT` | `(18.0, 10.0)` | Pi USB-C power plug passes through. |
| `MIC_CUT` | `(16.0, 10.0)` | USB-A plug of the mic cable passes through. |
| `SCREEN_PWR_CUT` | `(16.0, 10.0)` | Cable hole for the mini screen USB power cable (from an outside charger); a USB-A plug passes through. Width, height. |
| `SCREEN_PWR_CABLE_LEN` | `450.0` | Length of the screen power cable available inside the case. |
| `FAN_T` | `10.0` | Fan thickness. |
| `HDMI_PLUG_LEN` | `25.0` | Straight, stiff length of a micro-HDMI plug plus strain relief. |
| `USBC_PLUG_LEN` | `22.0` | Same for the USB-C power plug. |
| `CABLE_MIN_BEND_R` | `20.0` | Smallest comfortable cable bend radius. |
| `USB_PLUG_CLEAR` | `30.0` | Room needed left of the Pi for the mic USB-A plug. |
| `MIC_CABLE_LEN` | `500.0` | Mic cable length available inside the case. |

<!-- ASSUMED:END -->
